import torch
from pathlib import Path

# Get absolute path to sibling 'fine_tuned_liar_detector'
MODEL_DIR = Path(__file__).parent / "fine_tuned_liar_detector"

if not MODEL_DIR.exists():
    raise FileNotFoundError(f"Model directory not found at: {MODEL_DIR}")

# MODEL_DIR
ROBERTA_BASE_NAME = "roberta-base"
FLAN_MODEL_NAME = "google/flan-t5-base"

# Model Configuration
MAX_LENGTH = 128
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"


# Pipeline Configuration
class PipelineConfig:
    FALLBACK_SEARCH_QUERY = "latest news fake"
    MIN_TEXT_LENGTH = 50
    MAX_EXPLANATION_TOKENS = 100
