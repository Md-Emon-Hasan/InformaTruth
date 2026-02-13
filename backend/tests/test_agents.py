from unittest.mock import MagicMock, patch
from app.agents.input_handler import InputHandler
from app.agents.planner import Planner
from app.agents.fallback_search import FallbackSearch
from app.agents.router import Router


def test_input_handler_text():
    state = {"input_type": "text", "value": "test content"}
    result = InputHandler.process(state)
    assert result["text"] == "test content"


@patch("newspaper.Article")
def test_input_handler_url(mock_article):
    mock_instance = mock_article.return_value
    mock_instance.text = "url content"
    state = {"input_type": "url", "value": "http://example.com"}
    result = InputHandler.process(state)
    assert result["text"] == "url content"


@patch("fitz.open")
def test_input_handler_pdf(mock_fitz):
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "pdf content"
    mock_doc.__iter__.return_value = [mock_page]
    mock_doc.__enter__.return_value = mock_doc
    mock_fitz.return_value = mock_doc

    state = {"input_type": "pdf", "value": "test.pdf"}
    result = InputHandler.process(state)
    assert result["text"] == "pdf content"


def test_planner_short_text():
    state = {"text": "short"}
    result = Planner.decide_flow(state)
    assert result["next"] == "FallbackSearch"


def test_planner_long_text():
    state = {
        "text": "A very long text that exceeds the minimum required length for the planner to proceed to classification."
        * 5
    }
    result = Planner.decide_flow(state)
    assert result["next"] == "Router"


@patch("duckduckgo_search.DDGS.text")
def test_fallback_search(mock_ddgs):
    mock_ddgs.return_value = iter([{"title": "title", "body": "body"}])
    state = {"value": "query"}
    result = FallbackSearch.search(state)
    assert result["text"] == "body"
    assert result["fallback_used"] is True


def test_router():
    state = {"data": "test"}
    result = Router.route(state)
    assert result == state
