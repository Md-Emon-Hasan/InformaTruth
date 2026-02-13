from transformers import RobertaTokenizer
from transformers import RobertaForSequenceClassification
import torch


class FakeNewsDetector:
    def __init__(self, model_path):
        self.model = RobertaForSequenceClassification.from_pretrained(model_path)
        self.tokenizer = RobertaTokenizer.from_pretrained(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def predict(self, text):
        """Predict whether text is fake news"""
        inputs = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=128,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = torch.softmax(outputs.logits, dim=1)
        pred = torch.argmax(probs).item()

        return {
            "prediction": "fake" if pred == 1 else "real",
            "confidence": probs[0][pred].item(),
        }
