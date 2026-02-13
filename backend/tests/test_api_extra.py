from fastapi.testclient import TestClient
from app.main import app
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
