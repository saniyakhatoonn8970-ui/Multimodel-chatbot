import io
import math
import struct
import wave
import base64
import httpx
from typing import Dict, Any, Optional

from backend.app.core.config import settings
from backend.app.core.exceptions import ProviderException
from backend.app.core.logging import logger
from backend.app.providers.base import BaseTTSProvider


class MockTTSProvider(BaseTTSProvider):
    """
    Offline TTS provider that synthesizes a pure tone WAV audio signal programmatically
    so that audio synthesis and frontend audio playback are fully functioning without external APIs.
    """
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = "alloy"
    ) -> Dict[str, Any]:
        sample_rate = 16000
        # Duration proportional to text length, clamped between 1.0 and 4.0 seconds
        duration = min(4.0, max(1.0, len(text.split()) * 0.25))
        num_samples = int(sample_rate * duration)
        
        # Generate soft pleasant chord (440Hz + 554Hz)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            raw_data = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                # Envelope to avoid clicks
                envelope = min(1.0, t / 0.1) * min(1.0, (duration - t) / 0.1)
                sample = 0.25 * (math.sin(2 * math.pi * 440 * t) + math.sin(2 * math.pi * 554.37 * t))
                val = int(sample * envelope * 32767)
                raw_data.extend(struct.pack("<h", val))
                
            wav_file.writeframes(raw_data)
            
        audio_bytes = buf.getvalue()
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return {
            "audio_base64": b64,
            "content_type": "audio/wav"
        }


class OpenAITTSProvider(BaseTTSProvider):
    def __init__(self, api_key: str, model_name: str = "tts-1"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = "https://api.openai.com/v1/audio/speech"

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = "alloy"
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderException("openai_tts", "OpenAI API key is not configured for TTS.")

        payload = {
            "model": self.model_name,
            "input": text[:4000],
            "voice": voice or "alloy",
            "response_format": "mp3"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    self.endpoint,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                if res.status_code != 200:
                    raise ProviderException("openai_tts", f"TTS API returned status {res.status_code}")
                b64 = base64.b64encode(res.content).decode("utf-8")
                return {
                    "audio_base64": b64,
                    "content_type": "audio/mp3"
                }
        except Exception as e:
            if isinstance(e, ProviderException):
                raise
            raise ProviderException("openai_tts", str(e))


def get_tts_provider() -> BaseTTSProvider:
    provider = settings.TTS_PROVIDER.lower()
    if provider == "openai":
        return OpenAITTSProvider(api_key=settings.TTS_API_KEY or "", model_name=settings.TTS_MODEL)
    return MockTTSProvider()
