import threading
from unittest.mock import MagicMock, patch

from sqlmodel import Session, select

from app.models.db import AnalysisResult


def _mock_pipeline(**overrides):
    result = {"label": "Real", "confidence": 0.9, "explanation": "ok"}
    result.update(overrides)
    mock_pipeline = MagicMock()
    mock_pipeline.invoke.return_value = result
    return mock_pipeline


def test_db_write_happens_after_response(isolated_client, isolated_db):
    with patch("app.main.pipeline", _mock_pipeline()):
        response = isolated_client.post(
            "/analyze", json={"inputType": "text", "content": "some article text"}
        )
    assert response.status_code == 200

    with Session(isolated_db) as session:
        rows = session.exec(select(AnalysisResult)).all()
    assert len(rows) == 1
    assert rows[0].label == "Real"


def test_background_task_exception_does_not_fail_request(isolated_client):
    with (
        patch("app.main.pipeline", _mock_pipeline()),
        patch("app.main.AnalysisResult", side_effect=Exception("db exploded")),
    ):
        response = isolated_client.post(
            "/analyze", json={"inputType": "text", "content": "some article text"}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Real"


def test_concurrent_writes_and_reads_do_not_deadlock(isolated_client, isolated_db):
    with patch("app.main.pipeline", _mock_pipeline()):

        def post_analysis():
            isolated_client.post(
                "/analyze",
                json={"inputType": "text", "content": "concurrent article text"},
            )

        threads = [threading.Thread(target=post_analysis) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        response = isolated_client.get("/api/history")
    assert response.status_code == 200
    assert response.json()["total"] >= 1
