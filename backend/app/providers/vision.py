import base64
import io
import httpx
from PIL import Image
from typing import Optional

from backend.app.core.config import settings
from backend.app.core.exceptions import ProviderException
from backend.app.core.logging import logger
from backend.app.providers.base import BaseVisionProvider


class MockVisionProvider(BaseVisionProvider):
    """Offline vision provider analyzing image metadata via Pillow and answering the prompt."""
    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        user_prompt: str
    ) -> str:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            format_name = img.format or mime_type.split("/")[-1].upper()
            mode = img.mode

            # Aspect ratio descriptor
            ratio = width / height
            if ratio > 1.2:
                orientation = f"Landscape ({width}:{height}, {ratio:.2f} ratio)"
            elif ratio < 0.8:
                orientation = f"Portrait ({width}:{height}, {ratio:.2f} ratio - typical mobile screenshot/photo)"
            else:
                orientation = f"Square-like ({width}x{height} px)"

            # Thumbnail color analysis
            thumb = img.copy().convert("RGB")
            thumb.thumbnail((50, 50))
            pixels = list(thumb.getdata())
            avg_r = sum(p[0] for p in pixels) / len(pixels)
            avg_g = sum(p[1] for p in pixels) / len(pixels)
            avg_b = sum(p[2] for p in pixels) / len(pixels)
            brightness = (avg_r * 299 + avg_g * 587 + avg_b * 114) / 1000
            brightness_desc = "Bright" if brightness > 150 else ("Dark/Low-light" if brightness < 80 else "Balanced lighting")

            prompt_text = user_prompt.strip() or "Describe this image"
            
            return (
                f"### 🖼️ Image Inspection & Visual Analysis\n\n"
                f"- **Format**: `{format_name}`\n"
                f"- **Dimensions**: `{width} × {height} px`\n"
                f"- **Orientation**: {orientation}\n"
                f"- **Lighting**: {brightness_desc} (Avg RGB: `{int(avg_r)}, {int(avg_g)}, {int(avg_b)}`)\n\n"
                f"**Regarding your question:** *\"{prompt_text}\"*\n\n"
                f"The image was validated and processed cleanly. Detailed semantic object and OCR recognition requires an active vision model.\n\n"
                f"> 💡 **To enable full AI image understanding (Gemini Vision)**: Add your free Google AI Studio key to `.env` as `VISION_API_KEY=<key>` and `VISION_PROVIDER=gemini`."
            )
        except Exception as e:
            return f"The uploaded image could not be decoded: {str(e)}"


class GeminiVisionProvider(BaseVisionProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        user_prompt: str
    ) -> str:
        if not self.api_key:
            raise ProviderException("gemini_vision", "Gemini API key is not configured.")

        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        prompt_text = user_prompt.strip() or "Describe this image and identify its main components accurately."

        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": prompt_text},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": b64_data
                        }
                    }
                ]
            }],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048}
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(
                    f"{self.endpoint}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                if res.status_code != 200:
                    raise ProviderException("gemini_vision", f"API returned status {res.status_code}")
                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return "Could not generate analysis for the provided image."
                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts)
        except Exception as e:
            if isinstance(e, ProviderException):
                raise
            raise ProviderException("gemini_vision", str(e))


class OpenAIVisionProvider(BaseVisionProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        user_prompt: str
    ) -> str:
        if not self.api_key:
            raise ProviderException("openai_vision", "OpenAI API key is not configured.")

        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{b64_data}"
        prompt_text = user_prompt.strip() or "Describe this image accurately."

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": data_uri}}
                    ]
                }
            ],
            "max_tokens": 1000
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(
                    self.endpoint,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                if res.status_code != 200:
                    raise ProviderException("openai_vision", f"API returned status {res.status_code}")
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            if isinstance(e, ProviderException):
                raise
            raise ProviderException("openai_vision", str(e))


def get_vision_provider() -> BaseVisionProvider:
    provider = settings.VISION_PROVIDER.lower()
    api_key = settings.VISION_API_KEY or settings.LLM_API_KEY or ""
    if (provider == "gemini" or (api_key and provider == "mock")) and api_key:
        return GeminiVisionProvider(api_key=api_key, model_name=settings.VISION_MODEL)
    elif provider == "openai" and api_key:
        return OpenAIVisionProvider(api_key=api_key, model_name=settings.VISION_MODEL)
    elif provider == "gemini":
        return GeminiVisionProvider(api_key=api_key, model_name=settings.VISION_MODEL)
    return MockVisionProvider()
