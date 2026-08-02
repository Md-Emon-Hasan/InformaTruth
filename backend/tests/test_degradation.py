import logging
from unittest.mock import MagicMock

from app.agents.executor import EXPLANATION_UNAVAILABLE_MESSAGE, Executor
from app.agents.fallback_search import FallbackSearch
from app.utils.cache import get_cached_classification, get_cached_search


def test_explanation_failure_still_returns_classification(caplog):
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = (0, 0.87)

    mock_tokenizer = MagicMock()
    mock_model = MagicMock()
    mock_model.generate.side_effect = Exception("flan-t5 timed out")

    executor = Executor(mock_classifier, mock_tokenizer, mock_model)

    with caplog.at_level(logging.WARNING):
        result = executor.execute({"text": "some article text to classify"})

    assert result["label"] == "Real"
    assert result["confidence"] == 0.87
    assert result["explanation"] == EXPLANATION_UNAVAILABLE_MESSAGE
    assert result["explanation_unavailable"] is True
    assert any("flan-t5 timed out" in r.message for r in caplog.records)


def test_explanation_failure_does_not_poison_classify_cache():
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = (1, 0.6)
    mock_model = MagicMock()
    mock_model.generate.side_effect = Exception("boom")

    executor = Executor(mock_classifier, MagicMock(), mock_model)
    text = "unique text for degraded explanation caching check"
    executor.execute({"text": text})

    assert get_cached_classification(text) is None


def test_classification_failure_returns_honest_error_no_fabricated_verdict():
    mock_classifier = MagicMock()
    mock_classifier.classify.side_effect = Exception("model crashed")

    executor = Executor(mock_classifier, MagicMock(), MagicMock())
    result = executor.execute({"text": "some text"})

    assert "error" in result
    assert "label" not in result
    assert "confidence" not in result


def test_search_failure_marks_result_as_lacking_external_context(caplog, monkeypatch):
    import config

    monkeypatch.setattr(config, "SEARCH_MAX_RETRIES", 1)

    class BoomDDGS:
        def __init__(self, *args, **kwargs):
            pass

        def text(self, *args, **kwargs):
            raise Exception("duckduckgo unavailable")

    monkeypatch.setattr("app.agents.fallback_search.DDGS", BoomDDGS)

    with caplog.at_level(logging.WARNING):
        result = FallbackSearch.search({"value": "some unique fallback query"})

    assert result["search_unavailable"] is True
    assert result["fallback_used"] is True
    assert "error" in result
    assert any(
        "duckduckgo unavailable" in r.message or "failed" in r.message.lower()
        for r in caplog.records
    )


def test_search_failure_not_cached(monkeypatch):
    import config

    monkeypatch.setattr(config, "SEARCH_MAX_RETRIES", 1)

    class BoomDDGS:
        def __init__(self, *args, **kwargs):
            pass

        def text(self, *args, **kwargs):
            raise Exception("down")

    monkeypatch.setattr("app.agents.fallback_search.DDGS", BoomDDGS)

    query = "another unique query for cache check"
    FallbackSearch.search({"value": query})
    assert get_cached_search(query) is None


def test_search_timeout_triggers_degradation(monkeypatch):
    import config

    monkeypatch.setattr(config, "SEARCH_MAX_RETRIES", 1)

    class TimeoutDDGS:
        def __init__(self, *args, **kwargs):
            pass

        def text(self, *args, **kwargs):
            raise TimeoutError("timed out")

    monkeypatch.setattr("app.agents.fallback_search.DDGS", TimeoutDDGS)

    result = FallbackSearch.search({"value": "timeout query unique"})
    assert result["search_unavailable"] is True
    assert result["text"] == "Search failed"
