import json
import httpx
from typing import List, Dict, Any, Optional

from backend.app.core.config import settings
from backend.app.core.exceptions import ProviderException
from backend.app.core.logging import logger
from backend.app.providers.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Deterministic, offline LLM provider for tests and local development."""
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_instruction: Optional[str] = None
    ) -> str:
        last_user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_message = m.get("content", "")
                break

        # Check if this is a RAG prompt with retrieved context
        if "<retrieved_context" in last_user_message or "RETRIEVED CONTEXT:" in last_user_message:
            # Check if there is actual chunk content inside retrieved_context tags
            import re
            contexts = re.findall(r'<retrieved_context[^>]*>(.*?)</retrieved_context>', last_user_message, re.DOTALL)
            non_empty_contexts = [c.strip() for c in contexts if c.strip()]
            
            if non_empty_contexts:
                # Find citations
                citation_matches = re.findall(r'<retrieved_context\s+doc="([^"]+)"(?:\s+page="([^"]+)")?', last_user_message)
                cite_str = ""
                if citation_matches:
                    doc_name, page = citation_matches[0]
                    page_str = f", p. {page}" if page and page != "None" else ""
                    cite_str = f" [Doc: {doc_name}{page_str}]"
                return f"Based on the provided documents: {non_empty_contexts[0][:200]}...{cite_str}"
            else:
                return "The available documents do not contain enough information to answer your question."

        # Empathetic conversational response
        return (
            f"Thank you for sharing that with me. I hear what you're saying about: \"{last_user_message[:80]}\". "
            "How can I best support you with this today?"
        )


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_instruction: Optional[str] = None
    ) -> str:
        if not self.api_key:
            raise ProviderException("gemini", "Gemini API key is not configured in environment variables.")

        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{self.endpoint}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                if res.status_code != 200:
                    logger.error(f"Gemini API returned status {res.status_code}: {res.text}")
                    raise ProviderException("gemini", f"API request failed with code {res.status_code}")
                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return "No response could be generated."
                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts)
        except httpx.TimeoutException:
            raise ProviderException("gemini", "Request to Gemini API timed out after 30 seconds.")
        except Exception as e:
            if isinstance(e, ProviderException):
                raise
            raise ProviderException("gemini", str(e))


class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_instruction: Optional[str] = None
    ) -> str:
        if not self.api_key:
            raise ProviderException("openai", "OpenAI API key is not configured in environment variables.")

        formatted_messages = []
        if system_instruction:
            formatted_messages.append({"role": "system", "content": system_instruction})
        for m in messages:
            formatted_messages.append({"role": m["role"], "content": m["content"]})

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
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
                    raise ProviderException("openai", f"API returned status {res.status_code}")
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            raise ProviderException("openai", "Request to OpenAI API timed out.")
        except Exception as e:
            if isinstance(e, ProviderException):
                raise
            raise ProviderException("openai", str(e))


def get_llm_provider() -> BaseLLMProvider:
    provider = settings.LLM_PROVIDER.lower()
    api_key = settings.LLM_API_KEY or ""
    if (provider == "gemini" or (api_key and provider == "mock")) and api_key:
        return GeminiLLMProvider(api_key=api_key, model_name=settings.LLM_MODEL)
    elif provider == "openai" and api_key:
        return OpenAILLMProvider(api_key=api_key, model_name=settings.LLM_MODEL)
    elif provider == "gemini":
        return GeminiLLMProvider(api_key=api_key, model_name=settings.LLM_MODEL)
    return MockLLMProvider()
