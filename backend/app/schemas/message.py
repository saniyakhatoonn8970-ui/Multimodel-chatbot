from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    filename: str
    page_number: Optional[int] = None
    chunk_index: int
    snippet: str
    score: float


class MessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=20000)
    input_modality: str = Field(default="text")
    output_modality: str = Field(default="text")
    message_metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    input_modality: str
    output_modality: str
    message_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
