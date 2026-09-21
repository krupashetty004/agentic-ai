from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    conversation_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    rating: Literal["up", "down"]
    comment: Optional[str] = None
    approved: bool = False


class FeedbackResponse(BaseModel):
    status: str
    feedback_id: str
    review_required: bool


class FeedbackMetrics(BaseModel):
    total: int
    positive: int
    negative: int
    approval_rate: float
    review_queue: int
    recent_comments: List[str]
