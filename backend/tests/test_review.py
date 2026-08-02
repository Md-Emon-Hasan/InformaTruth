from unittest.mock import MagicMock, patch

from sqlmodel import Session

from app.main import _needs_review
from app.models.db import AnalysisResult


def _seed(
    engine,
    n=3,
    label="Real",
    input_type="text",
    needs_review=False,
    review_status="none",
    human_verdict=None,
):
    ids = []
    with Session(engine) as session:
        for i in range(n):
            entry = AnalysisResult(
                text=f"article number {i} " * 20,
                input_type=input_type,
                label=label,
                confidence=0.5 + i * 0.01,
                explanation=f"explanation number {i} " * 20,
                needs_review=needs_review,
                review_status=review_status,
                human_verdict=human_verdict,
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)
            ids.append(entry.id)
    return ids


def _mock_pipeline(
    confidence=0.9, label="Real", hallucination_risk="low", guardrail_violations=None
):
    mock_pipeline = MagicMock()
    mock_pipeline.invoke.return_value = {
        "label": label,
        "confidence": confidence,
        "explanation": "ok",
        "hallucination": {"hallucination_risk": hallucination_risk},
        "guardrail_violations": guardrail_violations or [],
    }
    return mock_pipeline


# --- Flagging logic -----------------------------------------------------


def test_needs_review_flags_low_confidence():
    assert _needs_review(0.51, "low", []) is True


def test_needs_review_flags_high_hallucination_risk():
    assert _needs_review(0.95, "high", []) is True


def test_needs_review_flags_guardrail_violation():
    assert _needs_review(0.95, "low", ["prompt_injection:x"]) is True


def test_needs_review_false_for_clean_confident_result():
    assert _needs_review(0.95, "low", []) is False


def test_analyze_flags_low_confidence_result_for_review(isolated_client, isolated_db):
    with patch("app.main.pipeline", _mock_pipeline(confidence=0.51)):
        response = isolated_client.post(
            "/analyze",
            json={"inputType": "text", "content": "some borderline article"},
        )
    assert response.status_code == 200
    assert response.json()["needs_review"] is True

    queue = isolated_client.get("/api/review").json()
    assert queue["total"] == 1


def test_analyze_does_not_flag_confident_clean_result(isolated_client, isolated_db):
    with patch("app.main.pipeline", _mock_pipeline(confidence=0.95)):
        response = isolated_client.post(
            "/analyze",
            json={"inputType": "text", "content": "a very confident article"},
        )
    assert response.json()["needs_review"] is False

    queue = isolated_client.get("/api/review").json()
    assert queue["total"] == 0


def test_analyze_flags_high_hallucination_risk_result(isolated_client, isolated_db):
    with patch(
        "app.main.pipeline",
        _mock_pipeline(confidence=0.95, hallucination_risk="high"),
    ):
        response = isolated_client.post(
            "/analyze", json={"inputType": "text", "content": "some article"}
        )
    assert response.json()["needs_review"] is True


def test_analyze_flags_guardrail_violation_result(isolated_client, isolated_db):
    with patch(
        "app.main.pipeline",
        _mock_pipeline(confidence=0.95, guardrail_violations=["prompt_injection:x"]),
    ):
        response = isolated_client.post(
            "/analyze", json={"inputType": "text", "content": "some article"}
        )
    assert response.json()["needs_review"] is True


# --- Queue pagination --------------------------------------------------------


def test_review_queue_only_returns_pending_flagged_items(isolated_client, isolated_db):
    _seed(isolated_db, n=2, needs_review=True, review_status="pending")
    _seed(isolated_db, n=3, needs_review=False, review_status="none")

    response = isolated_client.get("/api/review")
    data = response.json()
    assert data["total"] == 2
    assert all(item["needs_review"] is True for item in data["items"])


def test_review_queue_excludes_already_reviewed_items(isolated_client, isolated_db):
    _seed(isolated_db, n=1, needs_review=True, review_status="pending")
    _seed(
        isolated_db,
        n=1,
        needs_review=True,
        review_status="reviewed",
        human_verdict="Real",
    )

    response = isolated_client.get("/api/review")
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["review_status"] == "pending"


def test_review_queue_pagination(isolated_client, isolated_db):
    _seed(isolated_db, n=5, needs_review=True, review_status="pending")

    response = isolated_client.get("/api/review", params={"limit": 2, "offset": 1})
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 1


def test_review_queue_filters_by_input_type(isolated_client, isolated_db):
    _seed(
        isolated_db,
        n=1,
        needs_review=True,
        review_status="pending",
        input_type="url",
    )
    _seed(
        isolated_db,
        n=1,
        needs_review=True,
        review_status="pending",
        input_type="text",
    )

    response = isolated_client.get("/api/review", params={"input_type": "url"})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["input_type"] == "url"


def test_review_queue_empty_db_returns_zero_total(isolated_client):
    response = isolated_client.get("/api/review")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


# --- Verdict submission ------------------------------------------------------


def test_submit_review_verdict_records_without_overwriting_model_prediction(
    isolated_client, isolated_db
):
    ids = _seed(
        isolated_db, n=1, label="Fake", needs_review=True, review_status="pending"
    )
    result_id = ids[0]

    response = isolated_client.post(
        f"/api/review/{result_id}", json={"human_verdict": "real"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Fake"  # original model prediction untouched
    assert data["human_verdict"] == "Real"
    assert data["review_status"] == "reviewed"
    assert data["agrees_with_model"] is False
    assert data["reviewed_at"] is not None

    queue = isolated_client.get("/api/review").json()
    assert queue["total"] == 0  # no longer pending


def test_submit_review_verdict_agrees_with_model(isolated_client, isolated_db):
    ids = _seed(
        isolated_db, n=1, label="Real", needs_review=True, review_status="pending"
    )
    response = isolated_client.post(
        f"/api/review/{ids[0]}", json={"human_verdict": "Real"}
    )
    assert response.json()["agrees_with_model"] is True


def test_submit_review_invalid_id_returns_404(isolated_client, isolated_db):
    response = isolated_client.post(
        "/api/review/999999", json={"human_verdict": "Real"}
    )
    assert response.status_code == 404


def test_submit_review_invalid_verdict_returns_422(isolated_client, isolated_db):
    ids = _seed(isolated_db, n=1, needs_review=True, review_status="pending")
    response = isolated_client.post(
        f"/api/review/{ids[0]}", json={"human_verdict": "Maybe"}
    )
    assert response.status_code == 422


# --- Stats extension ----------------------------------------------------------


def test_stats_review_queue_counts_and_agreement_rate(isolated_client, isolated_db):
    _seed(isolated_db, n=2, needs_review=True, review_status="pending")
    _seed(
        isolated_db,
        n=2,
        label="Real",
        needs_review=True,
        review_status="reviewed",
        human_verdict="Real",
    )
    _seed(
        isolated_db,
        n=1,
        label="Fake",
        needs_review=True,
        review_status="reviewed",
        human_verdict="Real",
    )

    response = isolated_client.get("/api/stats")
    data = response.json()
    assert data["review_queue"]["pending"] == 2
    assert data["review_queue"]["reviewed"] == 3
    assert data["review_queue"]["agreement_rate"] == round(2 / 3, 4)


def test_stats_review_queue_agreement_rate_none_when_nothing_reviewed(
    isolated_client, isolated_db
):
    _seed(isolated_db, n=1)
    response = isolated_client.get("/api/stats")
    assert response.json()["review_queue"]["agreement_rate"] is None
