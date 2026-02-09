from unittest.mock import MagicMock, patch
import torch
from app.models.classifier import Classifier
from app.models.loader import ModelLoader


def test_classifier_logic():
    # Mock tokenizer and model
    mock_tokenizer = MagicMock()
    mock_model = MagicMock()

    # Mock tokenizer output as a Mock object that supports .to()
    mock_inputs = MagicMock()
    mock_inputs.to.return_value = mock_inputs
    mock_tokenizer.return_value = mock_inputs

    # Mock model output (logits)
    mock_output = MagicMock()
    mock_output.logits = torch.tensor([[2.0, -1.0]])  # Real
    mock_model.return_value = mock_output

    classifier = Classifier(mock_tokenizer, mock_model)
    label, confidence = classifier.classify("test text")

    assert label == 0
    assert confidence > 0.5


@patch("app.models.loader.AutoTokenizer.from_pretrained")
@patch("app.models.loader.AutoModelForSequenceClassification.from_pretrained")
@patch("app.models.loader.PeftModel.from_pretrained")
@patch("app.models.loader.AutoModelForSeq2SeqLM.from_pretrained")
def test_model_loader(mock_flan_model, mock_peft_model, mock_rob_model, mock_rob_tok):
    loader = ModelLoader()
    mock_rob_tok.return_value = MagicMock()
    mock_rob_model.return_value = MagicMock()
    mock_peft_model.return_value = MagicMock()
    mock_flan_model.return_value = MagicMock()

    success = loader.load_models()
    assert success is True
    assert loader.roberta_tokenizer is not None
    assert loader.roberta_model is not None
    assert loader.flan_model is not None
