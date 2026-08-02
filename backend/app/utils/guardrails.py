"""Prompt-level and output-level guardrails.

`app/utils/validation.py` already rejects malformed/unsafe *input* (length,
PDF size/pages, URL scheme, SSRF) before anything is trusted. This module
operates one step later, on content that has already passed validation:

- `sanitize_input` neutralises instruction-like content in text scraped from
  URLs/PDFs before it reaches a FLAN-T5 prompt (prompt-injection defence).
- `check_output` screens a generated explanation for empty/degenerate text,
  runaway repetition, leaked prompt fragments, and PII that was not present
  in the source text.

Both functions are pure and side-effect-free: they never raise and never
reject a document outright (scraped news legitimately contains quoted
speech that can superficially resemble an instruction). They return a
structured result and let the caller decide what to do, mirroring the
existing degrade-don't-fail pattern used elsewhere in the pipeline.
"""

import re
from typing import Any, Dict, List

import config

# --- Prompt-injection detection --------------------------------------------
#
# Each pattern targets a specific instruction-injection technique. Matches
# are replaced with "[filtered]" rather than causing rejection of the whole
# document, since legitimate scraped text can quote speech containing
# similar phrasing (e.g. a news article quoting someone saying "ignore what
# they told you").

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
    """Neutralise instruction-like content in `text`.

    Returns {"passed": bool, "violations": [...], "sanitised_text": str}.
    `passed` is False when at least one injection-like pattern was found and
    neutralised - the request is NOT rejected, `sanitised_text` is always
    safe to use downstream.
    """
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
# Unvalidated starting point: flags an explanation where one word makes up
# more than 40% of all words (only evaluated once there are >= 6 words).
_MAX_WORD_REPEAT_RATIO = 0.4
_MIN_WORDS_FOR_REPETITION_CHECK = 6

# Fragments of the executor's own prompt template (see
# app/agents/executor.py::_generate_explanation) that should never appear
# verbatim in a generated explanation - their presence indicates the model
# echoed the prompt instead of answering it.
_LEAKED_PROMPT_FRAGMENTS = [
    "explain why this might be",
    "in one sentence",
]

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")


def check_output(explanation: str, source_text: str = "") -> Dict[str, Any]:
    """Screen a generated explanation for degenerate/unsafe output.

    Checks (in order): empty/degenerate text, runaway word repetition,
    leaked prompt fragments, and PII (emails/phone numbers) that does not
    appear anywhere in `source_text`. PII and leaked fragments are redacted
    from `sanitised_text`; empty/degenerate and repetition violations are
    reported but left for the caller to replace (there is nothing safe to
    salvage from a degenerate string).
    """
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
