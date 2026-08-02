from unittest.mock import MagicMock

import config


def test_model_info_includes_lora_config_when_peft_present(client, monkeypatch):
    import app.main as main_module

    trainable_param = MagicMock(requires_grad=True)
    trainable_param.numel.return_value = 100
    frozen_param = MagicMock(requires_grad=False)
    frozen_param.numel.return_value = 900

    lora_cfg = MagicMock(
        r=8, lora_alpha=16, lora_dropout=0.1, target_modules=["query", "value"]
    )
    fake_model = MagicMock()
    fake_model.peft_config = {"default": lora_cfg}
    fake_model.parameters.return_value = [trainable_param, frozen_param]

    fake_loader = MagicMock()
    fake_loader.roberta_model = fake_model
    fake_loader.flan_model = MagicMock()
    monkeypatch.setattr(main_module, "model_loader", fake_loader)

    response = client.get("/api/model-info")
    data = response.json()

    assert data["classifier"]["loaded"] is True
    assert data["classifier"]["lora"]["r"] == 8
    assert data["classifier"]["lora"]["target_modules"] == ["query", "value"]
    assert data["classifier"]["trainable_parameters"] == 100
    assert data["classifier"]["total_parameters"] == 1000
    assert data["classifier"]["trainable_percentage"] == 10.0


def test_model_info_handles_parameter_count_failure(client, monkeypatch):
    import app.main as main_module

    fake_model = MagicMock()
    fake_model.peft_config = None
    fake_model.parameters.side_effect = Exception("boom")

    fake_loader = MagicMock()
    fake_loader.roberta_model = fake_model
    fake_loader.flan_model = MagicMock()
    monkeypatch.setattr(main_module, "model_loader", fake_loader)

    response = client.get("/api/model-info")
    data = response.json()

    assert data["classifier"]["loaded"] is True
    assert data["classifier"]["lora"] == {}
    assert data["classifier"]["trainable_parameters"] is None
    assert data["classifier"]["total_parameters"] is None
    assert data["classifier"]["trainable_percentage"] is None


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
