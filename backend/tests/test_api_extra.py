from fastapi import Request
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded
from app.main import app, _rate_limit_exceeded_handler
from app.utils.validation import ContentValidationError
from unittest.mock import patch, MagicMock

client = TestClient(app)


def test_analyze_endpoint_exception():
    mock_pipeline = MagicMock()
    mock_pipeline.invoke.side_effect = Exception("pipeline crash")
    with patch("app.main.pipeline", mock_pipeline):
        response = client.post(
            "/analyze", json={"inputType": "text", "content": "test content"}
        )
        assert response.status_code == 500
        assert "error" in response.json()


def test_analyze_invalid_payload():
    response = client.post("/analyze", json={"wrong": "data"})
    assert response.status_code == 422  # Unprocessable Entity


def test_analyze_text_too_short_returns_422():
    response = client.post("/analyze", json={"inputType": "text", "content": "hi"})
    assert response.status_code == 422


def test_analyze_classification_failure_returns_500_with_message():
    mock_pipeline = MagicMock()
    mock_pipeline.invoke.return_value = {"error": "model crashed mid-inference"}
    with patch("app.main.pipeline", mock_pipeline):
        response = client.post(
            "/analyze", json={"inputType": "text", "content": "some article text"}
        )
    assert response.status_code == 500
    assert response.json()["error"] == "model crashed mid-inference"


def test_analyze_reports_degraded_components():
    mock_pipeline = MagicMock()
    mock_pipeline.invoke.return_value = {
        "label": "Real",
        "confidence": 0.9,
        "explanation": "fallback explanation",
        "explanation_unavailable": True,
        "search_unavailable": True,
        "fallback_used": True,
    }
    with patch("app.main.pipeline", mock_pipeline):
        response = client.post(
            "/analyze", json={"inputType": "text", "content": "some article text"}
        )
    data = response.json()
    assert data["degraded"] is True
    assert set(data["degraded_components"]) == {"explanation", "search"}
    assert data["fallback_used"] is True


def test_analyze_propagates_content_validation_error_from_pipeline():
    mock_pipeline = MagicMock()
    mock_pipeline.invoke.side_effect = ContentValidationError("bad url content")
    with patch("app.main.pipeline", mock_pipeline):
        response = client.post(
            "/analyze", json={"inputType": "url", "content": "http://example.com"}
        )
    assert response.status_code == 400
    assert "bad url content" in response.json()["detail"]


def test_analyze_passes_through_http_exceptions_from_pipeline():
    from fastapi import HTTPException

    mock_pipeline = MagicMock()
    mock_pipeline.invoke.side_effect = HTTPException(
        status_code=418, detail="teapot from deep in the pipeline"
    )
    with patch("app.main.pipeline", mock_pipeline):
        response = client.post(
            "/analyze", json={"inputType": "text", "content": "some article text"}
        )
    assert response.status_code == 418
    assert response.json()["detail"] == "teapot from deep in the pipeline"


def test_rate_limit_exceeded_handler_returns_429_with_retry_after():
    limit = MagicMock()
    limit.error_message = None
    limit.limit = "5 per 1 minute"
    exc = RateLimitExceeded(limit)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/analyze",
        "headers": [],
        "client": ("127.0.0.1", 12345),
    }
    request = Request(scope)

    response = _rate_limit_exceeded_handler(request, exc)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
