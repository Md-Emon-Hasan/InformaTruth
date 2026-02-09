import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.models.loader import ModelLoader
from app.models.classifier import Classifier
from app.graph.builder import PipelineBuilder
from app.utils.logger import setup_logging

# Initialize logging first
setup_logging()
logger = logging.getLogger(__name__)


# Global variables for models/pipeline
pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    try:
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

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")


class AnalyzeRequest(BaseModel):
    inputType: str
    content: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        logger.info(f"Analyzing input type: {request.inputType}")
        result = pipeline.invoke(
            {"input_type": request.inputType, "value": request.content}
        )

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
