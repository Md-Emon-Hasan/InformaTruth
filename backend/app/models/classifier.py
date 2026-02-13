import torch
import logging
from config import MAX_LENGTH
from config import DEVICE

logger = logging.getLogger(__name__)


class Classifier:
    def __init__(self, tokenizer, model):
        self.tokenizer = tokenizer
        self.model = model

    def classify(self, text):
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
            return pred, confidence
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            raise
