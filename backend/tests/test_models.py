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
@patch("app.models.loader.get_quantization_config", return_value=None)
def test_model_loader(
    mock_quant, mock_flan_model, mock_peft_model, mock_rob_model, mock_rob_tok
):
    # CPU / full-precision path: get_quantization_config() returns None so the
    # loader attaches the LoRA adapter to a full-precision base.
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
    # Full-precision base is loaded without a quantization_config kwarg.
    assert "quantization_config" not in mock_rob_model.call_args.kwargs


@patch("app.models.loader.USE_4BIT", True)
@patch("app.models.loader.AutoTokenizer.from_pretrained")
@patch("app.models.loader.AutoModelForSequenceClassification.from_pretrained")
@patch("app.models.loader.PeftModel.from_pretrained")
@patch("app.models.loader.AutoModelForSeq2SeqLM.from_pretrained")
@patch("app.models.loader.get_quantization_config")
def test_model_loader_qlora_4bit(
    mock_quant, mock_flan_model, mock_peft_model, mock_rob_model, mock_rob_tok
):
    # QLoRA / GPU path: get_quantization_config() returns a 4-bit config, so the
    # base is loaded quantized (device_map pinned to GPU) and the adapter is
    # attached without an extra .to(DEVICE) move.
    fake_quant_config = MagicMock()
    mock_quant.return_value = fake_quant_config
    loader = ModelLoader()
    mock_rob_tok.return_value = MagicMock()
    mock_rob_model.return_value = MagicMock()
    peft_model = MagicMock()
    mock_peft_model.return_value = peft_model
    mock_flan_model.return_value = MagicMock()

    success = loader.load_models()
    assert success is True
    assert loader.roberta_model is peft_model
    # 4-bit base is loaded with the quantization config and pinned to GPU 0.
    kwargs = mock_rob_model.call_args.kwargs
    assert kwargs["quantization_config"] is fake_quant_config
    assert kwargs["device_map"] == {"": 0}
    # A 4-bit base is already on GPU via device_map; the loader must NOT call
    # .to(DEVICE) on it (that would raise for a quantized model).
    peft_model.to.assert_not_called()
