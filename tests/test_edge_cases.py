import pytest
from unittest.mock import MagicMock, patch
from app.agents.input_handler import InputHandler
from app.agents.fallback_search import FallbackSearch
from app.agents.executor import Executor
from app.models.loader import ModelLoader


def test_input_handler_unsupported():
    state = {"input_type": "unknown", "value": "test"}
    result = InputHandler.process(state)
    assert result["text"] == ""


def test_input_handler_exception():
    with patch("newspaper.Article", side_effect=Exception("parse error")):
        state = {"input_type": "url", "value": "http://bad.com"}
        result = InputHandler.process(state)
        assert "error" in result
        assert result["text"] == ""


@patch("duckduckgo_search.DDGS.text")
def test_fallback_search_no_results(mock_ddgs):
    mock_ddgs.return_value = iter([])
    state = {"value": "query"}
    result = FallbackSearch.search(state)
    assert result["text"] == "No information found"


@patch("duckduckgo_search.DDGS.text", side_effect=Exception("api down"))
def test_fallback_search_exception(mock_ddgs):
    state = {"value": "query"}
    result = FallbackSearch.search(state)
    assert "error" in result
    assert result["text"] == "Search failed"


def test_executor_exception():
    mock_cls = MagicMock()
    mock_cls.classify.side_effect = Exception("model error")
    executor = Executor(mock_cls, MagicMock(), MagicMock())
    state = {"text": "test"}
    result = executor.execute(state)
    assert "error" in result


@patch(
    "app.models.loader.AutoTokenizer.from_pretrained",
    side_effect=Exception("load fail"),
)
def test_model_loader_exception(mock_tok):
    loader = ModelLoader()
    with pytest.raises(Exception):
        loader.load_models()
