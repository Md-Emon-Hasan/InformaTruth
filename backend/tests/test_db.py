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


def test_migration_adds_missing_columns_to_pre_existing_table(tmp_path, monkeypatch):
    import app.db as db_module

    legacy_engine = create_engine(
        f"sqlite:///{tmp_path / 'legacy.db'}",
        connect_args={"check_same_thread": False},
    )
    with legacy_engine.connect() as conn:
        conn.exec_driver_sql("""
            CREATE TABLE analysisresult (
                id INTEGER PRIMARY KEY,
                text VARCHAR NOT NULL,
                input_type VARCHAR NOT NULL,
                label VARCHAR NOT NULL,
                confidence FLOAT NOT NULL,
                explanation VARCHAR NOT NULL,
                created_at DATETIME NOT NULL
            )
            """)
        conn.commit()

    monkeypatch.setattr(db_module, "engine", legacy_engine)
    db_module._migrate_analysis_result_columns()

    with legacy_engine.connect() as conn:
        columns = {
            row[1] for row in conn.exec_driver_sql("PRAGMA table_info(analysisresult)")
        }
    assert {"needs_review", "review_status", "human_verdict", "reviewed_at"} <= columns


def test_migration_is_a_noop_when_columns_already_exist(tmp_path, monkeypatch):
    import app.db as db_module

    fresh_engine = create_engine(
        f"sqlite:///{tmp_path / 'fresh.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(fresh_engine)

    monkeypatch.setattr(db_module, "engine", fresh_engine)
    # Should not raise even though every column already exists.
    db_module._migrate_analysis_result_columns()
