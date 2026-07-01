import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    BitsAndBytesConfig,
)
from peft import PeftModel

from train.config import MODEL_NAME, MAX_LENGTH


class FakeNewsDetector:
    """Inference wrapper for the QLoRA fake-news detector.

    Loads the 4-bit NF4 base + LoRA adapter on GPU; on CPU bitsandbytes 4-bit
    is unavailable, so it attaches the same adapter to a full-precision base.
    """

    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        if self.device.type == "cuda":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                llm_int8_skip_modules=["classifier"],
            )
            base_model = AutoModelForSequenceClassification.from_pretrained(
                MODEL_NAME,
                num_labels=2,
                quantization_config=bnb_config,
                device_map={"": 0},
            )
            self.model = PeftModel.from_pretrained(base_model, model_path)
        else:
            base_model = AutoModelForSequenceClassification.from_pretrained(
                MODEL_NAME, num_labels=2
            )
            self.model = PeftModel.from_pretrained(base_model, model_path)
            self.model.to(self.device)

        self.model.eval()

    def predict(self, text):
        """Predict whether text is fake news"""
        inputs = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt",
        ).to(self.model.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = torch.softmax(outputs.logits, dim=1)
        pred = torch.argmax(probs).item()

        return {
            "prediction": "fake" if pred == 1 else "real",
            "confidence": probs[0][pred].item(),
        }
