from typing import TypedDict
from typing import Optional
from typing import Literal
from typing import List
from typing import Any
from typing import Dict


class AgentState(TypedDict):
    input_type: Literal["url", "pdf", "text"]
    value: str
    text: Optional[str]
    error: Optional[str]
    next: Optional[str]
    label: Optional[str]
    confidence: Optional[float]
    explanation: Optional[str]
    fallback_used: Optional[bool]
    guardrail_violations: Optional[List[str]]
    hallucination: Optional[Dict[str, Any]]
