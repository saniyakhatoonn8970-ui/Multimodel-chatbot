import httpx
from typing import Dict, Any, Optional

from backend.app.core.config import settings
from backend.app.core.exceptions import ProviderException
from backend.app.core.logging import logger
from backend.app.providers.base import BaseSTTProvider


class MockSTTProvider(BaseSTTProvider):
    """Offline STT provider for testing and local operation."""
    async def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        size_kb = len(audio_bytes) / 1024
        # Estimate duration assuming 16kHz 16-bit mono (~32 KB/sec)
        est_duration = max(1.0, round(size_kb / 32, 1))
        
        return {
            "text": f"This is a transcribed message from the uploaded audio file ({size_kb:.1f} KB).",
            "detected_language": language or "en",
            "duration_seconds": est_duration
        }


class OpenAISTTProvider(BaseSTTProvider):
    def __init__(self, api_key: str, model_name: str = "whisper-1"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = "https://api.openai.com/v1/audio/transcriptions"

    async def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderException("openai_stt", "OpenAI API key is not configured for STT.")

        ext = mime_type.split("/")[-1]
        filename = f"audio_input.{ext}"
        
        files = {
            "file": (filename, audio_bytes, mime_type)
        }
        data = {
            "model": self.model_name
        }
        if language:
            data["language"] = language

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                    data=data
                )
                if res.status_code != 200:
                    raise ProviderException("openai_stt", f"STT API returned status {res.status_code}: {res.text}")
                result = res.json()
                return {
                    "text": result.get("text", ""),
                    "detected_language": language or "en",
                    "duration_seconds": result.get("duration")
                }
        except Exception as e:
            if isinstance(e, ProviderException):
                raise
            raise ProviderException("openai_stt", str(e))


def get_stt_provider() -> BaseSTTProvider:
    provider = settings.STT_PROVIDER.lower()
    if provider == "openai":
        return OpenAISTTProvider(api_key=settings.STT_API_KEY or "", model_name=settings.STT_MODEL)
    return MockSTTProvider()
