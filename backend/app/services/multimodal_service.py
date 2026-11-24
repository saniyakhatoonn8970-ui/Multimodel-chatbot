from typing import Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.exceptions import FileValidationException
from backend.app.core.security import validate_file_signature
from backend.app.providers.vision import get_vision_provider
from backend.app.providers.speech_to_text import get_stt_provider
from backend.app.providers.text_to_speech import get_tts_provider


class MultimodalService:
    def __init__(self):
        self.vision_provider = get_vision_provider()
        self.stt_provider = get_stt_provider()
        self.tts_provider = get_tts_provider()

    async def process_image(
        self,
        image_bytes: bytes,
        content_type: str,
        user_prompt: str
    ) -> str:
        # Validate size
        max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if len(image_bytes) > max_bytes:
            raise FileValidationException(
                f"Image size ({len(image_bytes)/(1024*1024):.1f}MB) exceeds limit of {settings.MAX_IMAGE_SIZE_MB}MB."
            )

        # Validate signature
        is_valid, detected_type = validate_file_signature(image_bytes, content_type)
        if not is_valid or not detected_type.startswith("image/"):
            raise FileValidationException(f"Invalid image format: {detected_type}")

        return await self.vision_provider.analyze_image(
            image_bytes=image_bytes,
            mime_type=detected_type,
            user_prompt=user_prompt
        )

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        content_type: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        # Validate size
        max_bytes = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
        if len(audio_bytes) > max_bytes:
            raise FileValidationException(
                f"Audio size ({len(audio_bytes)/(1024*1024):.1f}MB) exceeds limit of {settings.MAX_AUDIO_SIZE_MB}MB."
            )

        # Validate signature
        is_valid, detected_type = validate_file_signature(audio_bytes, content_type)
        if not is_valid or not (detected_type.startswith("audio/") or detected_type == "application/octet-stream"):
            raise FileValidationException(f"Invalid or unsupported audio file signature: {detected_type}")

        return await self.stt_provider.transcribe(
            audio_bytes=audio_bytes,
            mime_type=detected_type,
            language=language
        )

    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.tts_provider.synthesize(text=text, voice=voice)
