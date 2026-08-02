import config


def test_model_info_has_all_expected_fields(client):
    response = client.get("/api/model-info")
    assert response.status_code == 200
    data = response.json()

    assert "classifier" in data
    assert "explanation_model" in data
    assert "test_set_metrics" in data
    assert "input_limits" in data

    assert data["classifier"]["base_model"] == config.ROBERTA_BASE_NAME
    assert data["explanation_model"]["name"] == config.FLAN_MODEL_NAME
    assert "loaded" in data["classifier"]
    assert "loaded" in data["explanation_model"]


def test_model_info_limits_come_from_config(client):
    response = client.get("/api/model-info")
    limits = response.json()["input_limits"]
    assert limits["min_text_chars"] == config.MIN_TEXT_CHARS
    assert limits["max_text_chars"] == config.MAX_TEXT_CHARS
    assert limits["max_pdf_bytes"] == config.MAX_PDF_BYTES
    assert limits["max_pdf_pages"] == config.MAX_PDF_PAGES


def test_model_info_is_unlimited(client, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_TEXT", "1/minute")
    for _ in range(10):
        response = client.get("/api/model-info")
        assert response.status_code == 200


def test_model_info_reflects_loaded_state_before_lifespan(client):
    response = client.get("/api/model-info")
    data = response.json()
    assert data["classifier"]["loaded"] is False
    assert data["explanation_model"]["loaded"] is False
