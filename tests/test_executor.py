from unittest.mock import MagicMock
from app.agents.executor import Executor
import torch


def test_executor_full_flow():
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = (0, 0.99)

    mock_tok = MagicMock()
    mock_inputs = MagicMock()
    mock_inputs.to.return_value = mock_inputs
    mock_tok.return_value = mock_inputs
    mock_tok.decode.return_value = "Test explanation"

    mock_model = MagicMock()
    mock_model.generate.return_value = torch.tensor([[1, 2, 3]])

    executor = Executor(mock_classifier, mock_tok, mock_model)
    state = {"text": "some input news text content"}

    result = executor.execute(state)
    assert result["label"] == "Real"
    assert result["confidence"] == 0.99
    assert result["explanation"] == "Test explanation"
