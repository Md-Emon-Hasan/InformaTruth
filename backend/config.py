import os
import torch
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


def _env_str(name: str, default: str) -> str:
    return os.getenv(name, default)


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


# Guardrails (prompt-injection sanitisation + output safety checks)
GUARDRAILS_ENABLED = _env_bool("GUARDRAILS_ENABLED", True)

# Hallucination detection
# Self-consistency resampling roughly triples FLAN-T5 latency per request,
# so it is off by default.
HALLUCINATION_SELF_CONSISTENCY_ENABLED = _env_bool(
    "HALLUCINATION_SELF_CONSISTENCY_ENABLED", False
)
HALLUCINATION_SELF_CONSISTENCY_SAMPLES = _env_int(
    "HALLUCINATION_SELF_CONSISTENCY_SAMPLES", 3
)

# Caching
CACHE_ENABLED = _env_bool("CACHE_ENABLED", True)

URL_CACHE_TTL = _env_int("URL_CACHE_TTL", 60 * 60 * 6)  # 6 hours
URL_CACHE_MAXSIZE = _env_int("URL_CACHE_MAXSIZE", 512)

CLASSIFY_CACHE_TTL = _env_int("CLASSIFY_CACHE_TTL", 60 * 30)  # 30 minutes
CLASSIFY_CACHE_MAXSIZE = _env_int("CLASSIFY_CACHE_MAXSIZE", 1024)

SEARCH_CACHE_TTL = _env_int("SEARCH_CACHE_TTL", 60 * 5)  # 5 minutes
SEARCH_CACHE_MAXSIZE = _env_int("SEARCH_CACHE_MAXSIZE", 256)


# Rate limiting
RATE_LIMIT_ENABLED = _env_bool("RATE_LIMIT_ENABLED", True)

RATE_LIMIT_TEXT = _env_str("RATE_LIMIT_TEXT", "10/minute")
RATE_LIMIT_URL = _env_str("RATE_LIMIT_URL", "5/minute")
RATE_LIMIT_PDF = _env_str("RATE_LIMIT_PDF", "5/minute")
RATE_LIMIT_HISTORY = _env_str("RATE_LIMIT_HISTORY", "60/minute")
RATE_LIMIT_STATS = _env_str("RATE_LIMIT_STATS", "60/minute")


# Input validation
MIN_TEXT_CHARS = _env_int("MIN_TEXT_CHARS", 10)
MAX_TEXT_CHARS = _env_int("MAX_TEXT_CHARS", 20000)

MAX_PDF_BYTES = _env_int("MAX_PDF_BYTES", 10 * 1024 * 1024)  # ~10MB
MAX_PDF_PAGES = _env_int("MAX_PDF_PAGES", 50)

MIN_URL_TEXT_CHARS = _env_int("MIN_URL_TEXT_CHARS", 10)

URL_MAX_REDIRECTS = _env_int("URL_MAX_REDIRECTS", 3)
URL_MAX_RESPONSE_BYTES = _env_int("URL_MAX_RESPONSE_BYTES", 5 * 1024 * 1024)  # ~5MB


# Timeouts & degradation
HTTP_TIMEOUT_SECONDS = _env_float("HTTP_TIMEOUT_SECONDS", 10.0)
SEARCH_TIMEOUT_SECONDS = _env_float("SEARCH_TIMEOUT_SECONDS", 8.0)
SEARCH_MAX_RETRIES = _env_int("SEARCH_MAX_RETRIES", 2)


# History / stats pagination
HISTORY_DEFAULT_LIMIT = _env_int("HISTORY_DEFAULT_LIMIT", 20)
HISTORY_MAX_LIMIT = _env_int("HISTORY_MAX_LIMIT", 100)
HISTORY_TEXT_TRUNCATE_CHARS = _env_int("HISTORY_TEXT_TRUNCATE_CHARS", 200)
STATS_RECENT_DAYS = _env_int("STATS_RECENT_DAYS", 30)
