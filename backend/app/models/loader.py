import logging
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
)
from peft import PeftModel
from config import MODEL_DIR, FLAN_MODEL_NAME, ROBERTA_BASE_NAME, DEVICE

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

            # Load base model first
            logger.info(f"Loading base model: {ROBERTA_BASE_NAME}")
            base_model = AutoModelForSequenceClassification.from_pretrained(
                ROBERTA_BASE_NAME,
                num_labels=2,  # Adjust based on your liar dataset labels
            )

            # Load the PEFT adapter
            logger.info("Attaching PEFT adapter...")
            self.roberta_model = PeftModel.from_pretrained(base_model, str(MODEL_DIR))
            self.roberta_model.to(DEVICE)

            logger.info("Loading FLAN-T5 explanation model...")
            self.flan_tokenizer = AutoTokenizer.from_pretrained(FLAN_MODEL_NAME)
            self.flan_model = AutoModelForSeq2SeqLM.from_pretrained(FLAN_MODEL_NAME)
            self.flan_model.to(DEVICE)

            logger.info("All models loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Model loading failed: {str(e)}")
            raise
