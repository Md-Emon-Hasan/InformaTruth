from unittest.mock import MagicMock

import torch

import config
from app.agents.executor import Executor
from app.utils.hallucination import (
    assess_hallucination_risk,
    grounding_score,
    self_consistency,
    verdict_consistency,
)

# --- verdict_consistency --------------------------------------------------


def test_verdict_consistency_flags_contradiction_fake_label_real_stance():
    result = verdict_consistency("Fake", "This appears accurate and truthful.")
    assert result["consistent"] is False
    assert result["stance"] == "real"
    assert result["expected_stance"] == "fake"


def test_verdict_consistency_flags_contradiction_real_label_fake_stance():
    result = verdict_consistency("Real", "This is misleading and fabricated.")
    assert result["consistent"] is False
    assert result["stance"] == "fake"


def test_verdict_consistency_accepts_matching_stance():
    result = verdict_consistency("Fake", "This is false and misleading.")
    assert result["consistent"] is True
    assert result["stance"] == "fake"


def test_verdict_consistency_treats_neutral_wording_as_consistent():
    result = verdict_consistency("Fake", "There is not enough context to verify this.")
    assert result["stance"] == "neutral"
    assert result["consistent"] is True


def test_verdict_consistency_handles_negation():
    # "not true" should read as a fake-leaning stance, not a real-leaning one.
    result = verdict_consistency("Fake", "This is not true based on the claims made.")
    assert result["stance"] == "fake"
    assert result["consistent"] is True


# --- grounding_score --------------------------------------------------------


def test_grounding_score_full_when_all_terms_in_source():
    source = "The mayor announced a new budget for the city council today."
    explanation = "The mayor announced a new budget for the council."
    result = grounding_score(explanation, source)
    assert result["score"] == 1.0
    assert result["ungrounded_terms"] == []


def test_grounding_score_low_for_invented_entities():
    source = "A local business opened downtown this week."
    explanation = "Senator Zorblatt from Wexonia confirmed the alien invasion."
    result = grounding_score(explanation, source)
    assert result["score"] < 0.5
    assert (
        "Zorblatt" in result["ungrounded_terms"]
        or "Wexonia" in result["ungrounded_terms"]
    )


def test_grounding_score_considers_evidence_text():
    source = "Short article."
    evidence = "Senator Diaz spoke about the new policy in the press briefing."
    explanation = "Senator Diaz spoke about the new policy."
    result = grounding_score(explanation, source, evidence_text=evidence)
    assert result["score"] == 1.0


def test_grounding_score_handles_empty_explanation():
    result = grounding_score("", "some source text")
    assert result["score"] == 1.0
    assert result["ungrounded_terms"] == []


# --- self_consistency --------------------------------------------------------


def test_self_consistency_full_agreement():
    tokenizer = MagicMock()
    inputs = MagicMock()
    inputs.to.return_value = inputs
    tokenizer.return_value = inputs
    tokenizer.decode.return_value = "This is false and misleading."

    model = MagicMock()
    model.generate.return_value = torch.tensor([[1, 2, 3]])

    result = self_consistency(tokenizer, model, "some prompt", n_samples=3)
    assert result["agreement"] == 1.0
    assert result["majority_stance"] == "fake"
    assert len(result["samples"]) == 3
    assert model.generate.call_count == 3


def test_self_consistency_partial_disagreement():
    tokenizer = MagicMock()
    inputs = MagicMock()
    inputs.to.return_value = inputs
    tokenizer.return_value = inputs
    tokenizer.decode.side_effect = [
        "This is false.",
        "This is true.",
        "This is false.",
    ]

    model = MagicMock()
    model.generate.return_value = torch.tensor([[1, 2, 3]])

    result = self_consistency(tokenizer, model, "some prompt", n_samples=3)
    assert result["agreement"] == round(2 / 3, 4)
    assert result["majority_stance"] == "fake"


# --- assess_hallucination_risk -----------------------------------------------


def test_assess_hallucination_risk_flags_contradictory_explanation_as_high():
    source = "The city council approved a new park budget yesterday."
    explanation = "This appears to be completely accurate and truthful reporting."
    result = assess_hallucination_risk("Fake", explanation, source)

    assert result["hallucination_risk"] == "high"
    assert "verdict_contradiction" in result["reasons"]


def test_assess_hallucination_risk_low_for_consistent_grounded_explanation():
    source = "The city council approved a new park budget yesterday in a public vote."
    explanation = "This appears false because the city council vote lacks sources."
    result = assess_hallucination_risk("Fake", explanation, source)

    assert result["hallucination_risk"] in ("low", "medium")
    assert "verdict_contradiction" not in result["reasons"]


def test_assess_hallucination_risk_high_for_low_self_consistency_agreement():
    source = "An article about a local election result."
    explanation = "This is false because the numbers do not add up."
    weak_agreement = {"agreement": 0.33, "majority_stance": "fake", "stances": []}
    result = assess_hallucination_risk(
        "Fake", explanation, source, self_consistency_result=weak_agreement
    )
    assert result["hallucination_risk"] == "high"
    assert "low_self_consistency" in result["reasons"]


# --- Executor wiring ----------------------------------------------------------


def _make_executor(decode_value="This is false and misleading."):
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = (1, 0.9)

    mock_tok = MagicMock()
    mock_inputs = MagicMock()
    mock_inputs.to.return_value = mock_inputs
    mock_tok.return_value = mock_inputs
    mock_tok.decode.return_value = decode_value

    mock_model = MagicMock()
    mock_model.generate.return_value = torch.tensor([[1, 2, 3]])

    return Executor(mock_classifier, mock_tok, mock_model), mock_model


def test_executor_attaches_hallucination_assessment():
    executor, _ = _make_executor()
    result = executor.execute({"text": "some fake-looking article content here"})

    assert "hallucination" in result
    assert result["hallucination"]["hallucination_risk"] in ("low", "medium", "high")


def test_executor_skips_self_consistency_by_default(monkeypatch):
    monkeypatch.setattr(config, "HALLUCINATION_SELF_CONSISTENCY_ENABLED", False)
    executor, mock_model = _make_executor()
    executor.execute({"text": "some article content for classification"})

    # Only the primary explanation generation call, no resampling.
    assert mock_model.generate.call_count == 1


def test_executor_runs_self_consistency_when_enabled(monkeypatch):
    monkeypatch.setattr(config, "HALLUCINATION_SELF_CONSISTENCY_ENABLED", True)
    monkeypatch.setattr(config, "HALLUCINATION_SELF_CONSISTENCY_SAMPLES", 2)
    executor, mock_model = _make_executor()
    result = executor.execute({"text": "some article content for classification"})

    # 1 primary generation + 2 resamples.
    assert mock_model.generate.call_count == 3
    assert "self_consistency" in result["hallucination"]


def test_executor_skips_hallucination_assessment_when_explanation_degraded():
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = (0, 0.8)
    mock_model = MagicMock()
    mock_model.generate.side_effect = Exception("boom")

    executor = Executor(mock_classifier, MagicMock(), mock_model)
    result = executor.execute({"text": "some article text"})

    assert result["explanation_unavailable"] is True
    assert result["hallucination"]["hallucination_risk"] == "unknown"
    assert "explanation_unavailable" in result["hallucination"]["reasons"]
