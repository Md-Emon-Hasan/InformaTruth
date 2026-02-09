import pytest
from fastapi.testclient import TestClient
from app.main import app

from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    # Mock model loading to speed up tests and avoid missing file errors
    with patch("app.main.ModelLoader.load_models", return_value=True), patch(
        "app.main.PipelineBuilder.build_graph", return_value=MagicMock()
    ):
        return TestClient(app)
