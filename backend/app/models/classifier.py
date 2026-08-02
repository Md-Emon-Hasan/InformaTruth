import torch
import logging
from config import MAX_LENGTH
from config import DEVICE
from app.utils.cache import get_cached_classification, set_cached_classification

logger = logging.getLogger(__name__)


class Classifier:
    def __init__(self, tokenizer, model):
        self.tokenizer = tokenizer
        self.model = model

    def classify(self, text):
        cached = get_cached_classification(text)
        if cached is not None:
            logger.info("Classification cache hit, skipping RoBERTa inference")
            return cached

        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding="max_length",
                max_length=MAX_LENGTH,
            ).to(DEVICE)

            with torch.no_grad():
                logits = self.model(**inputs).logits

            probs = torch.softmax(logits, dim=1)
            pred = torch.argmax(probs, dim=1).item()
            confidence = probs[0][pred].item()

            logger.debug(
                f"Classification completed - Label: {'Real' if pred == 0 else 'Fake'}, "
                f"Confidence: {confidence:.2f}"
            )
            set_cached_classification(text, (pred, confidence))
            return pred, confidence
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            raise
