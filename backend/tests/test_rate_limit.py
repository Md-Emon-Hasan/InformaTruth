from unittest.mock import MagicMock, patch

import config


def _mock_pipeline():
    mock_pipeline = MagicMock()
    mock_pipeline.invoke.return_value = {
        "label": "Real",
        "confidence": 0.9,
        "explanation": "ok",
    }
    return mock_pipeline


def test_under_limit_succeeds(client):
    with patch("app.main.pipeline", _mock_pipeline()):
        response = client.post(
            "/analyze", json={"inputType": "text", "content": "hello there world"}
        )
        assert response.status_code == 200


def test_over_limit_returns_429(client, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_TEXT", "2/minute")
    with patch("app.main.pipeline", _mock_pipeline()):
        for _ in range(2):
            response = client.post(
                "/analyze", json={"inputType": "text", "content": "hello world text"}
            )
            assert response.status_code == 200

        response = client.post(
            "/analyze", json={"inputType": "text", "content": "hello world text"}
        )
        assert response.status_code == 429
        assert "detail" in response.json()
        assert "Retry-After" in response.headers


def test_different_forwarded_for_gets_separate_buckets(client, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_TEXT", "1/minute")
    with patch("app.main.pipeline", _mock_pipeline()):
        r1 = client.post(
            "/analyze",
            json={"inputType": "text", "content": "hello world text a"},
            headers={"X-Forwarded-For": "1.1.1.1"},
        )
        assert r1.status_code == 200

        r2 = client.post(
            "/analyze",
            json={"inputType": "text", "content": "hello world text a"},
            headers={"X-Forwarded-For": "1.1.1.1"},
        )
        assert r2.status_code == 429

        r3 = client.post(
            "/analyze",
            json={"inputType": "text", "content": "hello world text a"},
            headers={"X-Forwarded-For": "2.2.2.2"},
        )
        assert r3.status_code == 200


def test_model_info_and_health_never_limited(client, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_TEXT", "1/minute")
    for _ in range(5):
        response = client.get("/api/model-info")
        assert response.status_code == 200


def test_pdf_and_url_budgets_tracked_separately(client, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_TEXT", "1/minute")
    monkeypatch.setattr(config, "RATE_LIMIT_URL", "1/minute")
    with patch("app.main.pipeline", _mock_pipeline()):
        r_text = client.post(
            "/analyze", json={"inputType": "text", "content": "hello world text b"}
        )
        assert r_text.status_code == 200

        r_url = client.post(
            "/analyze",
            json={"inputType": "url", "content": "http://example.com"},
        )
        assert r_url.status_code != 429


def test_rate_limit_disabled_allows_all(client, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", False)
    monkeypatch.setattr(config, "RATE_LIMIT_TEXT", "1/minute")
    with patch("app.main.pipeline", _mock_pipeline()):
        for _ in range(5):
            response = client.post(
                "/analyze", json={"inputType": "text", "content": "hello world text c"}
            )
            assert response.status_code == 200
