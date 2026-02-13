from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock


def test_app_lifespan():
    # Mock dependencies to avoid actual model loading during lifespan test
    with (
        patch("app.main.ModelLoader.load_models", return_value=True),
        patch("app.main.PipelineBuilder.build_graph", return_value=MagicMock()),
    ):
        # Using 'with' statement triggers the lifespan events
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 404
