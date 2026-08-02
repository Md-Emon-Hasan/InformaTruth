import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

import limits as limits_lib
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import func
from sqlmodel import Session, select

import config
from app.models.loader import ModelLoader
from app.models.classifier import Classifier
from app.graph.builder import PipelineBuilder
from app.utils.logger import setup_logging
from app.utils.cache import cache_stats
from app.utils.validation import ContentValidationError, validate_text
from app.db import create_db_and_tables, get_session
from app.models.db import AnalysisResult

# Initialize logging first
setup_logging()
logger = logging.getLogger(__name__)


# Global variables for models/pipeline
pipeline = None
model_loader = None


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=get_client_ip)


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"Rate limit exceeded for {get_client_ip(request)}: {exc.detail}")
    response = JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )
    response.headers["Retry-After"] = "60"
    return response


def _enforce_rate_limit(request: Request, limit_str: str, bucket: str) -> None:
    if not config.RATE_LIMIT_ENABLED:
        return

    item = limits_lib.parse(limit_str)
    key = f"{bucket}:{get_client_ip(request)}"
    if not limiter._limiter.hit(item, key):
        retry_after = item.get_expiry()
        logger.warning(
            f"Rate limit exceeded - bucket={bucket} limit={limit_str} key={key}"
        )
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({limit_str}) for {bucket} requests. "
            "Please slow down.",
            headers={"Retry-After": str(retry_after)},
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline, model_loader
    try:
        logger.info("Starting up: Initializing database...")
        create_db_and_tables()
        logger.info("Database initialized.")

        logger.info("Starting up: Loading models...")
        model_loader = ModelLoader()
        model_loader.load_models()
        classifier = Classifier(
            model_loader.roberta_tokenizer, model_loader.roberta_model
        )
        pipeline = PipelineBuilder.build_graph(
            classifier, model_loader.flan_tokenizer, model_loader.flan_model
        )
        logger.info("Startup complete: Models loaded successfully.")
        yield
    except Exception as e:
        logger.critical(f"Startup failed: {str(e)}")
        raise


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity (or specify React app URL)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    inputType: str
    content: str

    @field_validator("content")
    @classmethod
    def _validate_content(cls, value, info):
        input_type = info.data.get("inputType")
        if input_type == "text":
            try:
                validate_text(value)
            except ContentValidationError as e:
                raise ValueError(str(e))
        return value


def _persist_analysis(
    content: str,
    input_type: str,
    label: str,
    confidence: float,
    explanation: str,
    session: Session,
) -> None:
    try:
        db_entry = AnalysisResult(
            text=content[:5000],  # Truncate if too long to be safe
            input_type=input_type,
            label=label,
            confidence=float(confidence),
            explanation=explanation,
        )
        session.add(db_entry)
        session.commit()
        session.refresh(db_entry)
        logger.info(f"Analysis saved to database with ID: {db_entry.id}")
    except Exception as e:
        logger.error(f"Background persistence failed: {str(e)}")


@app.post("/analyze")
def analyze(
    request: Request,
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    limit_map = {
        "text": config.RATE_LIMIT_TEXT,
        "url": config.RATE_LIMIT_URL,
        "pdf": config.RATE_LIMIT_PDF,
    }
    limit_str = limit_map.get(payload.inputType, config.RATE_LIMIT_TEXT)
    _enforce_rate_limit(request, limit_str, payload.inputType)

    try:
        logger.info(f"Analyzing input type: {payload.inputType}")
        result = pipeline.invoke(
            {"input_type": payload.inputType, "value": payload.content}
        )

        if not result.get("label"):
            error_message = result.get("error", "Classification failed.")
            logger.error(f"Analysis failed to produce a verdict: {error_message}")
            return JSONResponse(content={"error": error_message}, status_code=500)

        degraded_components = []
        if result.get("explanation_unavailable"):
            degraded_components.append("explanation")
        if result.get("search_unavailable"):
            degraded_components.append("search")

        guardrail_violations = result.get("guardrail_violations") or []

        response_body = {
            "label": result["label"],
            "confidence": f"{result['confidence']:.2f}",
            "explanation": result["explanation"],
            "guardrails": {
                "passed": not guardrail_violations,
                "violations": guardrail_violations,
            },
        }
        if degraded_components:
            response_body["degraded"] = True
            response_body["degraded_components"] = degraded_components
        if result.get("fallback_used"):
            response_body["fallback_used"] = True

        background_tasks.add_task(
            _persist_analysis,
            payload.content,
            payload.inputType,
            result["label"],
            float(result["confidence"]),
            result["explanation"],
            session,
        )

        return JSONResponse(response_body)
    except ContentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/history")
def get_history(
    request: Request,
    limit: int = Query(config.HISTORY_DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    label: Optional[str] = Query(None),
    input_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: Session = Depends(get_session),
):
    _enforce_rate_limit(request, config.RATE_LIMIT_HISTORY, "history")

    limit = min(limit, config.HISTORY_MAX_LIMIT)

    query = select(AnalysisResult)
    count_query = select(func.count()).select_from(AnalysisResult)

    if label:
        query = query.where(AnalysisResult.label == label)
        count_query = count_query.where(AnalysisResult.label == label)
    if input_type:
        query = query.where(AnalysisResult.input_type == input_type)
        count_query = count_query.where(AnalysisResult.input_type == input_type)
    if start_date:
        query = query.where(AnalysisResult.created_at >= start_date)
        count_query = count_query.where(AnalysisResult.created_at >= start_date)
    if end_date:
        query = query.where(AnalysisResult.created_at <= end_date)
        count_query = count_query.where(AnalysisResult.created_at <= end_date)

    total = session.exec(count_query).one()

    query = query.order_by(AnalysisResult.created_at.desc()).offset(offset).limit(limit)
    rows = session.exec(query).all()

    truncate_at = config.HISTORY_TEXT_TRUNCATE_CHARS
    items = []
    for row in rows:
        text_truncated = len(row.text) > truncate_at
        explanation_truncated = len(row.explanation) > truncate_at
        items.append(
            {
                "id": row.id,
                "input_type": row.input_type,
                "label": row.label,
                "confidence": row.confidence,
                "text": row.text[:truncate_at],
                "text_truncated": text_truncated,
                "explanation": row.explanation[:truncate_at],
                "explanation_truncated": explanation_truncated,
                "created_at": row.created_at.isoformat(),
            }
        )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/stats")
def get_stats(request: Request, session: Session = Depends(get_session)):
    _enforce_rate_limit(request, config.RATE_LIMIT_STATS, "stats")

    total = session.exec(select(func.count()).select_from(AnalysisResult)).one()

    if total == 0:
        return {
            "total_analyses": 0,
            "today": 0,
            "last_7_days": 0,
            "last_30_days": 0,
            "by_label": {},
            "by_input_type": {},
            "avg_text_length": 0,
            "avg_confidence": 0,
            "daily_counts": [],
            "cache_stats": cache_stats(),
        }

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=config.STATS_RECENT_DAYS)

    today_count = session.exec(
        select(func.count())
        .select_from(AnalysisResult)
        .where(AnalysisResult.created_at >= today_start)
    ).one()
    last_7_days = session.exec(
        select(func.count())
        .select_from(AnalysisResult)
        .where(AnalysisResult.created_at >= seven_days_ago)
    ).one()
    last_30_days = session.exec(
        select(func.count())
        .select_from(AnalysisResult)
        .where(AnalysisResult.created_at >= thirty_days_ago)
    ).one()

    by_label_rows = session.exec(
        select(AnalysisResult.label, func.count()).group_by(AnalysisResult.label)
    ).all()
    by_input_type_rows = session.exec(
        select(AnalysisResult.input_type, func.count()).group_by(
            AnalysisResult.input_type
        )
    ).all()

    avg_confidence = session.exec(select(func.avg(AnalysisResult.confidence))).one()
    avg_text_length = session.exec(
        select(func.avg(func.length(AnalysisResult.text)))
    ).one()

    daily_rows = session.exec(
        select(func.date(AnalysisResult.created_at), func.count())
        .where(AnalysisResult.created_at >= thirty_days_ago)
        .group_by(func.date(AnalysisResult.created_at))
        .order_by(func.date(AnalysisResult.created_at))
    ).all()

    return {
        "total_analyses": total,
        "today": today_count,
        "last_7_days": last_7_days,
        "last_30_days": last_30_days,
        "by_label": {label: count for label, count in by_label_rows},
        "by_input_type": {itype: count for itype, count in by_input_type_rows},
        "avg_text_length": round(avg_text_length, 2) if avg_text_length else 0,
        "avg_confidence": round(avg_confidence, 4) if avg_confidence else 0,
        "daily_counts": [{"date": str(d), "count": c} for d, c in daily_rows],
        "cache_stats": cache_stats(),
    }


@app.get("/api/model-info")
def get_model_info():
    classifier_loaded = bool(
        model_loader and getattr(model_loader, "roberta_model", None)
    )
    explanation_loaded = bool(
        model_loader and getattr(model_loader, "flan_model", None)
    )

    lora_config = {}
    if classifier_loaded:
        peft_config = getattr(model_loader.roberta_model, "peft_config", None)
        if peft_config:
            active_config = next(iter(peft_config.values()))
            lora_config = {
                "r": getattr(active_config, "r", None),
                "lora_alpha": getattr(active_config, "lora_alpha", None),
                "lora_dropout": getattr(active_config, "lora_dropout", None),
                "target_modules": list(
                    getattr(active_config, "target_modules", []) or []
                ),
            }

    trainable_params = None
    total_params = None
    trainable_pct = None
    if classifier_loaded:
        try:
            trainable_params = sum(
                p.numel()
                for p in model_loader.roberta_model.parameters()
                if p.requires_grad
            )
            total_params = sum(
                p.numel() for p in model_loader.roberta_model.parameters()
            )
            trainable_pct = (
                round(100 * trainable_params / total_params, 4)
                if total_params
                else None
            )
        except Exception as e:
            logger.warning(f"Could not compute parameter counts: {e}")

    return {
        "classifier": {
            "base_model": config.ROBERTA_BASE_NAME,
            "loaded": classifier_loaded,
            "lora": lora_config,
            "trainable_parameters": trainable_params,
            "total_parameters": total_params,
            "trainable_percentage": trainable_pct,
        },
        "explanation_model": {
            "name": config.FLAN_MODEL_NAME,
            "loaded": explanation_loaded,
        },
        "test_set_metrics": {
            "source": "LIAR test-set evaluation (recorded in README.md)",
            "accuracy": 0.6954,
            "f1": 0.6882,
            "precision": 0.6846,
            "recall": 0.6954,
        },
        "input_limits": {
            "min_text_chars": config.MIN_TEXT_CHARS,
            "max_text_chars": config.MAX_TEXT_CHARS,
            "max_pdf_bytes": config.MAX_PDF_BYTES,
            "max_pdf_pages": config.MAX_PDF_PAGES,
            "min_url_text_chars": config.MIN_URL_TEXT_CHARS,
        },
    }
