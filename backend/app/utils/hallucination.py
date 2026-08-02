"""Hallucination-risk signals for FLAN-T5 explanations. No new model - just
stance matching, a grounding heuristic, and optional FLAN-T5 resampling.
Thresholds are unvalidated starting points, not tuned on real data."""

import re
from typing import Any, Dict, List, Optional, Tuple

import config

# --- Verdict consistency ----------------------------------------------------

_REAL_STANCE_WORDS = {
    "real",
    "true",
    "truthful",
    "accurate",
    "credible",
    "legitimate",
    "factual",
    "verified",
    "trustworthy",
    "genuine",
}
_FAKE_STANCE_WORDS = {
    "fake",
    "false",
    "misleading",
    "unreliable",
    "fabricated",
    "hoax",
    "deceptive",
    "inaccurate",
    "untrue",
    "disinformation",
    "misinformation",
}
_NEGATIONS = {"not", "never", "no", "isn't", "wasn't", "doesn't", "aren't"}


def _stance_counts(text: str) -> Tuple[int, int]:
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    real_hits = 0
    fake_hits = 0
    for i, token in enumerate(tokens):
        negated = i > 0 and tokens[i - 1] in _NEGATIONS
        if token in _REAL_STANCE_WORDS:
            fake_hits += 1 if negated else 0
            real_hits += 0 if negated else 1
        elif token in _FAKE_STANCE_WORDS:
            real_hits += 1 if negated else 0
            fake_hits += 0 if negated else 1
    return real_hits, fake_hits


def _stance_label(real_hits: int, fake_hits: int) -> str:
    if real_hits == fake_hits:
        return "neutral"
    return "real" if real_hits > fake_hits else "fake"


def verdict_consistency(label: str, explanation: str) -> Dict[str, Any]:
    """Does the explanation's stance contradict the classifier's label?
    Neutral wording (no clear stance) counts as consistent."""
    real_hits, fake_hits = _stance_counts(explanation or "")
    stance = _stance_label(real_hits, fake_hits)
    expected = "real" if (label or "").lower() == "real" else "fake"

    total = real_hits + fake_hits
    confidence = (abs(real_hits - fake_hits) / total) if total else 0.0

    return {
        "consistent": stance in (expected, "neutral"),
        "stance": stance,
        "expected_stance": expected,
        "confidence": round(confidence, 4),
    }


# --- Grounding score ---------------------------------------------------------

_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "if",
    "then",
    "than",
    "so",
    "because",
    "this",
    "that",
    "these",
    "those",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "of",
    "in",
    "on",
    "at",
    "to",
    "for",
    "with",
    "as",
    "by",
    "it",
    "its",
    "from",
    "not",
    "no",
    "which",
    "who",
    "whom",
    "what",
    "when",
    "where",
    "why",
    "how",
    "there",
    "here",
    "also",
    "may",
    "might",
    "can",
    "could",
    "would",
    "should",
    "will",
    "shall",
    "has",
    "have",
    "had",
    "do",
    "does",
    "did",
    "about",
    "into",
    "over",
    "under",
    "after",
    "before",
    "between",
    "out",
    "up",
    "down",
    "very",
    "more",
    "most",
    "some",
    "such",
    "only",
    "just",
    "even",
    "news",
    "article",
    "appears",
    "appear",
    "seems",
    "seem",
    "explain",
    "sentence",
}


def _content_words(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z]{3,}", text)
    return [t for t in tokens if t.lower() not in _STOPWORDS]


def _capitalised_entities(text: str) -> List[str]:
    words = text.split()
    entities = []
    for i, word in enumerate(words):
        cleaned = re.sub(r"[^A-Za-z]", "", word)
        if len(cleaned) < 2 or i == 0:
            continue
        if cleaned[0].isupper() and cleaned.lower() not in _STOPWORDS:
            entities.append(cleaned)
    return entities


def grounding_score(
    explanation: str, source_text: str, evidence_text: str = ""
) -> Dict[str, Any]:
    """Fraction of the explanation's content words/entities seen in the
    source. Entities are weighted higher - a made-up name matters more
    than an ungrounded adjective."""
    combined_source = f"{source_text or ''} {evidence_text or ''}".lower()

    content_words = _content_words(explanation or "")
    entities = _capitalised_entities(explanation or "")

    ungrounded_words = [w for w in content_words if w.lower() not in combined_source]
    ungrounded_entities = [e for e in entities if e.lower() not in combined_source]

    word_score = (
        1.0 if not content_words else 1 - len(ungrounded_words) / len(content_words)
    )
    entity_score = (
        None if not entities else 1 - len(ungrounded_entities) / len(entities)
    )

    combined = (0.4 * word_score) + (0.6 * entity_score) if entities else word_score

    return {
        "score": round(combined, 4),
        "word_score": round(word_score, 4),
        "entity_score": round(entity_score, 4) if entities else None,
        "ungrounded_terms": sorted(set(ungrounded_words) | set(ungrounded_entities))[
            :10
        ],
    }


# --- Self-consistency (opt-in, resamples FLAN-T5) ----------------------------


def self_consistency(
    flan_tokenizer,
    flan_model,
    prompt: str,
    n_samples: int = 3,
    max_new_tokens: int = 100,
) -> Dict[str, Any]:
    """Resample the explanation and check stance agreement across samples."""
    inputs = flan_tokenizer(
        prompt, return_tensors="pt", truncation=True, max_length=config.MAX_LENGTH
    ).to(config.DEVICE)

    stances = []
    samples = []
    for _ in range(n_samples):
        output_ids = flan_model.generate(
            inputs["input_ids"],
            max_new_tokens=max_new_tokens,
            do_sample=True,
            top_k=50,
            temperature=0.9,
        )
        text = flan_tokenizer.decode(output_ids[0], skip_special_tokens=True)
        samples.append(text)
        real_hits, fake_hits = _stance_counts(text)
        stances.append(_stance_label(real_hits, fake_hits))

    if not stances:
        return {"agreement": 1.0, "stances": [], "samples": []}

    most_common = max(set(stances), key=stances.count)
    agreement = stances.count(most_common) / len(stances)

    return {
        "agreement": round(agreement, 4),
        "majority_stance": most_common,
        "stances": stances,
        "samples": samples,
    }


# --- Combined risk assessment -------------------------------------------------

# Unvalidated starting points (see module docstring) - not calibrated
# against any labelled hallucination dataset.
GROUNDING_HIGH_RISK_THRESHOLD = 0.35
GROUNDING_MEDIUM_RISK_THRESHOLD = 0.6
SELF_CONSISTENCY_HIGH_RISK_THRESHOLD = 0.4
SELF_CONSISTENCY_MEDIUM_RISK_THRESHOLD = 0.66


def assess_hallucination_risk(
    label: str,
    explanation: str,
    source_text: str,
    evidence_text: str = "",
    self_consistency_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    consistency = verdict_consistency(label, explanation)
    grounding = grounding_score(explanation, source_text, evidence_text)

    risk = "low"
    reasons: List[str] = []

    if not consistency["consistent"]:
        risk = "high"
        reasons.append("verdict_contradiction")

    if grounding["score"] < GROUNDING_HIGH_RISK_THRESHOLD:
        risk = "high"
        reasons.append("low_grounding")
    elif grounding["score"] < GROUNDING_MEDIUM_RISK_THRESHOLD and risk == "low":
        risk = "medium"
        reasons.append("moderate_grounding")

    if self_consistency_result is not None:
        agreement = self_consistency_result.get("agreement", 1.0)
        if agreement < SELF_CONSISTENCY_HIGH_RISK_THRESHOLD:
            risk = "high"
            reasons.append("low_self_consistency")
        elif agreement < SELF_CONSISTENCY_MEDIUM_RISK_THRESHOLD and risk == "low":
            risk = "medium"
            reasons.append("moderate_self_consistency")

    result: Dict[str, Any] = {
        "hallucination_risk": risk,
        "reasons": reasons,
        "verdict_consistency": consistency,
        "grounding": grounding,
    }
    if self_consistency_result is not None:
        result["self_consistency"] = self_consistency_result
    return result
