import logging
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
)
from peft import PeftModel
from config import (
    MODEL_DIR,
    FLAN_MODEL_NAME,
    ROBERTA_BASE_NAME,
    DEVICE,
    USE_4BIT,
    get_quantization_config,
)

logger = logging.getLogger(__name__)


class ModelLoader:
    def __init__(self):
        self.roberta_tokenizer = None
        self.roberta_model = None
        self.flan_tokenizer = None
        self.flan_model = None

    def load_models(self):
        try:
            logger.info(f"Loading RoBERTa base and adapter from {MODEL_DIR}...")
            # Load tokenizer from the adapter directory (contains vocab files)
            self.roberta_tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))

            # Load the base model. With QLoRA the base is quantized to 4-bit
            # (NF4) on GPU; on CPU bitsandbytes 4-bit is unavailable so we load
            # the base in full precision and attach the same LoRA adapter.
            quant_config = get_quantization_config()
            if quant_config is not None:
                logger.info(
                    f"Loading base model {ROBERTA_BASE_NAME} in 4-bit (QLoRA)..."
                )
                base_model = AutoModelForSequenceClassification.from_pretrained(
                    ROBERTA_BASE_NAME,
                    num_labels=2,  # Adjust based on your liar dataset labels
                    quantization_config=quant_config,
                    device_map={"": 0},  # pin to GPU 0 (keeps 4-bit state intact)
                )
            else:
                logger.info(
                    f"CUDA unavailable; loading base model {ROBERTA_BASE_NAME} "
                    "in full precision (CPU fallback for QLoRA adapter)."
                )
                base_model = AutoModelForSequenceClassification.from_pretrained(
                    ROBERTA_BASE_NAME,
                    num_labels=2,  # Adjust based on your liar dataset labels
                )

            # Load the PEFT adapter
            logger.info("Attaching PEFT adapter...")
            self.roberta_model = PeftModel.from_pretrained(base_model, str(MODEL_DIR))
            # A 4-bit base is already placed on GPU via device_map; only move the
            # model when we loaded it in full precision (CPU / non-quantized).
            if not USE_4BIT:
                self.roberta_model.to(DEVICE)
            self.roberta_model.eval()

            logger.info("Loading FLAN-T5 explanation model...")
            self.flan_tokenizer = AutoTokenizer.from_pretrained(FLAN_MODEL_NAME)
            self.flan_model = AutoModelForSeq2SeqLM.from_pretrained(FLAN_MODEL_NAME)
            self.flan_model.to(DEVICE)

            logger.info("All models loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Model loading failed: {str(e)}")
            raise
