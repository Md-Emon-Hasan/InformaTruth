"""Guardrails on top of validation.py: sanitise scraped text before it hits a
prompt, and screen generated explanations before they go out."""

import re
from typing import Any, Dict, List

import config

# Injection patterns get filtered, not rejected outright - scraped articles
# can legitimately quote speech that looks similar.
_INJECTION_PATTERNS = [
    re.compile(
        r"ignore\s+(all|any|the)?\s*(previous|prior|above)\s+instructions?", re.I
    ),
    re.compile(
        r"disregard\s+(all|any|the)?\s*(previous|prior|above)\s+instructions?", re.I
    ),
    re.compile(
        r"forget\s+(everything|all)\s+(you\s+(were|have\s+been)\s+told|above)", re.I
    ),
    re.compile(r"you\s+are\s+now\s+(a|an)?\s*[\w\- ]{1,40}", re.I),
    # Narrowly scoped to AI-roleplay hijacking so ordinary phrases like
    # "act as a mediator" or "act as a united community" are not flagged.
    re.compile(
        r"act\s+as\s+(if\s+you\s+(are|were)\s+)?(an?\s+)?"
        r"(ai|assistant|chatbot|language model|dan)\b",
        re.I,
    ),
    re.compile(r"new\s+instructions?\s*:", re.I),
    re.compile(r"\bsystem\s*:\s*", re.I),
    re.compile(r"\bassistant\s*:\s*", re.I),
    re.compile(r"\buser\s*:\s*", re.I),
    re.compile(r"<\|.*?\|>"),  # fake special tokens, e.g. <|im_start|>
    re.compile(r"\[\[\s*(system|instruction)[^\]]*\]\]", re.I),
    re.compile(r"#{2,}\s*(system|instruction)\w*", re.I),
]

_FILTER_MARKER = "[filtered]"


def sanitize_input(text: str) -> Dict[str, Any]:
    """Filter instruction-like content out of `text`. Never rejects, only redacts."""
    if not config.GUARDRAILS_ENABLED or not text:
        return {"passed": True, "violations": [], "sanitised_text": text}

    violations: List[str] = []
    sanitised = text
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(sanitised):
            violations.append(f"prompt_injection:{pattern.pattern[:40]}")
            sanitised = pattern.sub(_FILTER_MARKER, sanitised)

    return {
        "passed": not violations,
        "violations": violations,
        "sanitised_text": sanitised,
    }


# --- Output checks -----------------------------------------------------------

_MIN_OUTPUT_CHARS = 5
_MAX_WORD_REPEAT_RATIO = 0.4  # unvalidated starting point
_MIN_WORDS_FOR_REPETITION_CHECK = 6

# Prompt fragments from executor.py's template - if these leak into an
# explanation, the model echoed the prompt instead of answering it.
_LEAKED_PROMPT_FRAGMENTS = [
    "explain why this might be",
    "in one sentence",
]

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")


def check_output(explanation: str, source_text: str = "") -> Dict[str, Any]:
    """Screen a generated explanation: empty/degenerate text, repetition,
    leaked prompt fragments, and PII not present in the source."""
    explanation = explanation or ""
    source_text = source_text or ""

    if not config.GUARDRAILS_ENABLED:
        return {"passed": True, "violations": [], "sanitised_text": explanation}

    violations: List[str] = []
    sanitised = explanation

    stripped = sanitised.strip()
    if not stripped or len(stripped) < _MIN_OUTPUT_CHARS:
        violations.append("empty_or_degenerate_output")

    words = stripped.split()
    if len(words) >= _MIN_WORDS_FOR_REPETITION_CHECK:
        most_common_count = max(words.count(w) for w in set(words))
        if most_common_count / len(words) > _MAX_WORD_REPEAT_RATIO:
            violations.append("runaway_repetition")

    lowered = sanitised.lower()
    for fragment in _LEAKED_PROMPT_FRAGMENTS:
        if fragment in lowered:
            violations.append(f"leaked_prompt_fragment:{fragment}")
            sanitised = re.sub(re.escape(fragment), "", sanitised, flags=re.I)

    for label, pattern in (("email", _EMAIL_RE), ("phone", _PHONE_RE)):
        for match in pattern.findall(sanitised):
            if match and match not in source_text:
                violations.append(f"pii_{label}_not_in_source")
                sanitised = pattern.sub("[redacted]", sanitised)

    return {
        "passed": not violations,
        "violations": violations,
        "sanitised_text": sanitised.strip(),
    }
