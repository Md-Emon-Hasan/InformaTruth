from typing import TypedDict
from typing import Optional
from typing import Literal
from langgraph.graph import END

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