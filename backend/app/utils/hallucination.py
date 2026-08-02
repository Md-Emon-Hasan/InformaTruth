"""Hallucination detection signals for FLAN-T5-generated explanations.

Constraint: no new ML model may be added (Render RAM budget already holds
RoBERTa + FLAN-T5). Every signal here is either pure string/token analysis
or reuses FLAN-T5 with a different sampling strategy - never a new model.

Three signals, in increasing cost order:

1. `verdict_consistency` - does the explanation's stance (real/fake wording)
   contradict the classifier's label? Cheapest and most valuable signal.
2. `grounding_score` - what fraction of content words and named entities in
   the explanation also appear in the source text (+ retrieved evidence)?
   No spaCy/NLTK dependency exists in this project, so named entities are
   approximated with a capitalised-token heuristic (any non-sentence-initial
   token starting with an uppercase letter). This heuristic misses lowercase
   entities (e.g. "the who", genuinely rare) and can be fooled by mid-
   sentence capitalisation for emphasis - it is a cheap proxy, not NER.
3. `self_consistency` - resample the explanation 2-3 times with sampling
   enabled and measure stance agreement across samples. This roughly
   triples FLAN-T5 latency per request, so it is opt-in only
   (`HALLUCINATION_SELF_CONSISTENCY_ENABLED`, default off).

All thresholds below are unvalidated starting points - they were not
tuned against any labelled hallucination dataset. Treat `hallucination_risk`
as a rough triage signal for the review queue, not a certified judgement.
"""

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

    A "neutral" explanation stance (no clear real/fake wording detected) is
    treated as consistent - we only flag an explicit contradiction, not the
    absence of an opinion.
    """
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
    """Fraction of the explanation's content words/entities seen in the source.

    See module docstring for the capitalised-token entity heuristic and its
    limitations. Entities are weighted more heavily than generic content
    words since a hallucinated proper noun (invented person/place/org) is a
    stronger signal than an ungrounded adjective.
    """
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
    """Resample the explanation `n_samples` times and measure stance agreement.

    Off by default behind `HALLUCINATION_SELF_CONSISTENCY_ENABLED` since this
    multiplies FLAN-T5 latency by roughly `n_samples`.
    """
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
