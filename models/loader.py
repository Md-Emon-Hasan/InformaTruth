import torch
import logging
from transformers import RobertaTokenizer
from transformers import RobertaForSequenceClassification
from transformers import AutoTokenizer
from transformers import AutoModelForSeq2SeqLM
from config import MODEL_DIR
from config import FLAN_MODEL_NAME
from config import DEVICE

logger = logging.getLogger(__name__)

class ModelLoader:
    def __init__(self):
        self.roberta_tokenizer = None
        self.roberta_model = None
        self.flan_tokenizer = None
        self.flan_model = None

    def load_models(self):
        try:
            logger.info("Loading RoBERTa classifier model...")
            self.roberta_tokenizer = RobertaTokenizer.from_pretrained(MODEL_DIR)
            self.roberta_model = RobertaForSequenceClassification.from_pretrained(MODEL_DIR)
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