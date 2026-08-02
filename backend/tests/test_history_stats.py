from unittest.mock import MagicMock, patch

from sqlmodel import Session

from app.models.db import AnalysisResult


def _seed(engine, n=3, label="Real", input_type="text"):
    with Session(engine) as session:
        for i in range(n):
            session.add(
                AnalysisResult(
                    text=f"article number {i} " * 20,
                    input_type=input_type,
                    label=label,
                    confidence=0.5 + i * 0.01,
                    explanation=f"explanation number {i} " * 20,
                )
            )
        session.commit()


def _mock_pipeline():
    mock_pipeline = MagicMock()
    mock_pipeline.invoke.return_value = {
        "label": "Real",
        "confidence": 0.9,
        "explanation": "ok",
    }
    return mock_pipeline


def test_history_empty_db_returns_zero_total(isolated_client):
    response = isolated_client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_history_pagination_bounds(isolated_client, isolated_db):
    _seed(isolated_db, n=5)

    response = isolated_client.get("/api/history", params={"limit": 2, "offset": 1})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 1


def test_history_limit_is_capped_at_max(isolated_client, isolated_db):
    import config

    _seed(isolated_db, n=3)
    response = isolated_client.get(
        "/api/history", params={"limit": config.HISTORY_MAX_LIMIT + 500}
    )
    assert response.status_code == 200
    assert response.json()["limit"] == config.HISTORY_MAX_LIMIT


def test_history_filter_by_label(isolated_client, isolated_db):
    _seed(isolated_db, n=2, label="Real")
    _seed(isolated_db, n=3, label="Fake")

    response = isolated_client.get("/api/history", params={"label": "Fake"})
    data = response.json()
    assert data["total"] == 3
    assert all(item["label"] == "Fake" for item in data["items"])


def test_history_filter_by_date_range(isolated_client, isolated_db):
    _seed(isolated_db, n=2)

    from datetime import datetime, timedelta

    start_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
    end_date = (datetime.utcnow() + timedelta(days=1)).isoformat()

    response = isolated_client.get(
        "/api/history", params={"start_date": start_date, "end_date": end_date}
    )
    assert response.json()["total"] == 2

    far_future_start = (datetime.utcnow() + timedelta(days=30)).isoformat()
    response = isolated_client.get(
        "/api/history", params={"start_date": far_future_start}
    )
    assert response.json()["total"] == 0


def test_history_filter_by_input_type(isolated_client, isolated_db):
    _seed(isolated_db, n=2, input_type="text")
    _seed(isolated_db, n=1, input_type="url")

    response = isolated_client.get("/api/history", params={"input_type": "url"})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["input_type"] == "url"


def test_history_truncates_long_text(isolated_client, isolated_db):
    import config

    _seed(isolated_db, n=1)

    response = isolated_client.get("/api/history")
    item = response.json()["items"][0]
    assert len(item["text"]) <= config.HISTORY_TEXT_TRUNCATE_CHARS
    assert item["text_truncated"] is True


def test_history_newest_first_by_default(isolated_client, isolated_db):
    _seed(isolated_db, n=3)
    response = isolated_client.get("/api/history")
    items = response.json()["items"]
    timestamps = [item["created_at"] for item in items]
    assert timestamps == sorted(timestamps, reverse=True)


def test_stats_empty_db_returns_zeros_not_500(isolated_client):
    response = isolated_client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_analyses"] == 0
    assert data["by_label"] == {}
    assert data["daily_counts"] == []


def test_stats_total_count_correct(isolated_client, isolated_db):
    _seed(isolated_db, n=4, label="Real")
    _seed(isolated_db, n=2, label="Fake")

    response = isolated_client.get("/api/stats")
    data = response.json()
    assert data["total_analyses"] == 6
    assert data["by_label"]["Real"] == 4
    assert data["by_label"]["Fake"] == 2


def test_stats_includes_cache_stats(isolated_client, isolated_db):
    response = isolated_client.get("/api/stats")
    assert "cache_stats" in response.json()


def test_analyze_then_history_reflects_it(isolated_client, isolated_db):
    with patch("app.main.pipeline", _mock_pipeline()):
        isolated_client.post(
            "/analyze", json={"inputType": "text", "content": "brand new article"}
        )

    response = isolated_client.get("/api/history")
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["label"] == "Real"
