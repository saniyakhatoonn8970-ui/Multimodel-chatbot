from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    message_id: str
    feedback_type: str = Field(..., pattern="^(helpful|unhelpful)$")
    comment: Optional[str] = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    id: str
    message_id: str
    feedback_type: str
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
