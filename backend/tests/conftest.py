import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from app.main import app, limiter
from app.main import get_session
from app.utils.cache import clear_all_caches

from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    # Mock model loading to speed up tests and avoid missing file errors
    with (
        patch("app.main.ModelLoader.load_models", return_value=True),
        patch("app.main.PipelineBuilder.build_graph", return_value=MagicMock()),
    ):
        return TestClient(app)


@pytest.fixture
def isolated_db(tmp_path):
    db_path = tmp_path / "test_isolated.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    yield engine
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def isolated_client(isolated_db):
    with (
        patch("app.main.ModelLoader.load_models", return_value=True),
        patch("app.main.PipelineBuilder.build_graph", return_value=MagicMock()),
    ):
        return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_cache_and_limiter():
    clear_all_caches()
    limiter.reset()
    yield
    clear_all_caches()
    limiter.reset()
