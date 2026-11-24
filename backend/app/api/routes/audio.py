from fastapi import APIRouter, Depends, UploadFile, File, Query
from typing import Optional

from backend.app.api.dependencies import get_current_session_id
from backend.app.schemas.audio import TranscriptionResponse, SynthesisRequest, SynthesisResponse
from backend.app.services.multimodal_service import MultimodalService

router = APIRouter(prefix="/api/audio", tags=["Audio & Speech"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Query(None),
    session_id: str = Depends(get_current_session_id)
):
    """
    Transcribe speech audio file (WAV, MP3, WebM) to text using configured STT provider.
    """
    audio_bytes = await file.read()
    content_type = file.content_type or "audio/wav"
    service = MultimodalService()
    result = await service.transcribe_audio(
        audio_bytes=audio_bytes,
        content_type=content_type,
        language=language
    )
    return TranscriptionResponse(
        text=result["text"],
        detected_language=result.get("detected_language", "en"),
        duration_seconds=result.get("duration_seconds")
    )


@router.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_speech(
    payload: SynthesisRequest,
    session_id: str = Depends(get_current_session_id)
):
    """
    Synthesize text into speech audio bytes using configured TTS provider.
    """
    service = MultimodalService()
    result = await service.synthesize_speech(text=payload.text, voice=payload.voice)
    return SynthesisResponse(
        audio_base64=result["audio_base64"],
        content_type=result.get("content_type", "audio/wav")
    )
