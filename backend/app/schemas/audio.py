from typing import Optional
from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    text: str
    detected_language: Optional[str] = "en"
    duration_seconds: Optional[float] = None


class SynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    voice: Optional[str] = "alloy"


class SynthesisResponse(BaseModel):
    audio_base64: str
    content_type: str = "audio/wav"
