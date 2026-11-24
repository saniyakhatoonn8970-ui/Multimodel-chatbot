from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from backend.app.schemas.message import Citation, MessageResponse


class ChatRequest(BaseModel):
    conversation_id: str
    message: str = Field(..., min_length=1, max_length=20000)
    use_rag: bool = True
    rag_only: bool = False  # If true, only answer from uploaded documents
    enable_audio_response: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    citations: List[Citation] = []
    audio_base64: Optional[str] = None
    crisis_triggered: bool = False
    warning: Optional[str] = None
