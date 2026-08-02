from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class AnalysisResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str = Field(index=True)  # Store the input text (or a snippet if too long)
    input_type: str
    label: str
    confidence: float
    explanation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Human-in-the-loop review queue. `human_verdict` is recorded alongside
    # the model's own `label`/`confidence` - it never overwrites them.
    needs_review: bool = Field(default=False, index=True)
    review_status: str = Field(default="none")  # "none" | "pending" | "reviewed"
    human_verdict: Optional[str] = Field(default=None)
    reviewed_at: Optional[datetime] = Field(default=None)
