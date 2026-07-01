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
# The QLoRA adapter was trained with max_length=256, so inference tokenization
# must match to keep the same input shape the adapter saw during training.
MAX_LENGTH = 256
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- QLoRA / 4-bit quantization ---------------------------------------------
# The RoBERTa adapter was fine-tuned with QLoRA (a 4-bit NF4 base + LoRA).
# bitsandbytes 4-bit kernels require a CUDA GPU, so we only quantize the base
# when CUDA is available. On CPU we attach the same LoRA adapter to a
# full-precision base instead (the adapter weights are identical either way).
USE_4BIT = DEVICE == "cuda"


def get_quantization_config():
    """Return the 4-bit BitsAndBytesConfig used for QLoRA, or None on CPU.

    Mirrors the notebook (Experiment_QLoRA): NF4 quant type, double quant,
    bfloat16 compute dtype, and the classifier head kept in full precision so
    the trained `modules_to_save` head weights load cleanly.
    """
    if not USE_4BIT:
        return None

    from transformers import BitsAndBytesConfig

    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        llm_int8_skip_modules=["classifier"],
    )

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"


# Pipeline Configuration
class PipelineConfig:
    FALLBACK_SEARCH_QUERY = "latest news fake"
    MIN_TEXT_LENGTH = 50
    MAX_EXPLANATION_TOKENS = 100
