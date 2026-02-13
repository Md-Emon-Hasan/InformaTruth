import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from pydantic import BaseModel
from app.models.loader import ModelLoader
from app.models.classifier import Classifier
from app.graph.builder import PipelineBuilder
from app.utils.logger import setup_logging
from app.db import create_db_and_tables, get_session
from app.models.db import AnalysisResult

# Initialize logging first
setup_logging()
logger = logging.getLogger(__name__)


# Global variables for models/pipeline
pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
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


@app.post("/analyze")
async def analyze(request: AnalyzeRequest, session: Session = Depends(get_session)):
    try:
        logger.info(f"Analyzing input type: {request.inputType}")
        result = pipeline.invoke(
            {"input_type": request.inputType, "value": request.content}
        )

        # Save to database
        db_entry = AnalysisResult(
            text=request.content[:5000],  # Truncate if too long to be safe
            input_type=request.inputType,
            label=result["label"],
            confidence=float(result["confidence"]),
            explanation=result["explanation"],
        )
        session.add(db_entry)
        session.commit()
        session.refresh(db_entry)
        logger.info(f"Analysis saved to database with ID: {db_entry.id}")

        return JSONResponse(
            {
                "label": result["label"],
                "confidence": f"{result['confidence']:.2f}",
                "explanation": result["explanation"],
            }
        )
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
