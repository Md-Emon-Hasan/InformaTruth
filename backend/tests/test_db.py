from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from app.main import app, get_session
from app.models.db import AnalysisResult
import pytest

# Setup in-memory SQLite for testing
sqlite_file_name = "database/test_database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_analyze_saves_to_db(client: TestClient, session: Session):
    # Mock input
    payload = {"inputType": "text", "content": "This is a test news article."}

    # We need to mock the pipeline invocation since it loads heavy models
    # Patching pipeline.invoke in app.main
    from unittest.mock import MagicMock

    # If pipeline is None (because lifespan didn't run fully or mocked), we mock it.
    # In TestClient with lifespan, it might load models.
    # For speed, we can mock the pipeline if we can access it,
    # but lifespan runs in TestClient.
    # Let's rely on the fact that if models load, it's fine,
    # or we can mock the pipeline global.

    # Note: Modifying global 'pipeline' in app.main might be tricky
    # with TestClient lifespan
    # However, since we are doing an integration test, let's see if we can just run it.
    # If loading models takes too long, we might need to mock.

    # Let's try to mock the pipeline attribute on the app or global
    import app.main

    app.main.pipeline = MagicMock()
    app.main.pipeline.invoke.return_value = {
        "label": "Real",
        "confidence": 0.95,
        "explanation": "Test explanation",
    }

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Real"

    # Verify DB
    from sqlmodel import select

    results = session.exec(select(AnalysisResult)).all()

    assert len(results) == 1
    entry = results[0]
    assert entry.text == "This is a test news article."
    assert entry.label == "Real"
    assert entry.explanation == "Test explanation"
