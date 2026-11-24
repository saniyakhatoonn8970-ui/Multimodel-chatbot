import hashlib
import math
import httpx
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.core.exceptions import ProviderException
from backend.app.core.logging import logger
from backend.app.providers.base import BaseEmbeddingProvider


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic, offline embedding provider generating 128-dimensional normalized vectors
    based on character trigram and word hashing. Guarantees realistic cosine similarity ranking.
    """
    DIMENSIONS = 128

    def _generate_vector(self, text: str) -> List[float]:
        vec = [0.0] * self.DIMENSIONS
        cleaned = text.lower().strip()
        words = cleaned.split()
        
        # Word-level features
        for w in words:
            h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            idx = h % self.DIMENSIONS
            vec[idx] += 1.0

        # Trigram features
        for i in range(len(cleaned) - 2):
            tri = cleaned[i:i+3]
            h = int(hashlib.sha256(tri.encode("utf-8")).hexdigest(), 16)
            idx = h % self.DIMENSIONS
            vec[idx] += 0.5

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0.0:
            vec = [v / norm for v in vec]
        else:
            vec[0] = 1.0
        return vec

    async def get_embedding(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str, model_name: str = "text-embedding-004"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:embedContent"

    async def get_embedding(self, text: str) -> List[float]:
        if not self.api_key:
            raise ProviderException("gemini_embedding", "Gemini API key is not configured.")
        payload = {
            "model": f"models/{self.model_name}",
            "content": {"parts": [{"text": text}]}
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    f"{self.endpoint}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                if res.status_code != 200:
                    raise ProviderException("gemini_embedding", f"API returned status {res.status_code}")
                data = res.json()
                return data.get("embedding", {}).get("values", [])
        except Exception as e:
            if isinstance(e, ProviderException):
                raise
            raise ProviderException("gemini_embedding", str(e))

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [await self.get_embedding(t) for t in texts]


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = "https://api.openai.com/v1/embeddings"

    async def get_embedding(self, text: str) -> List[float]:
        res = await self.get_embeddings([text])
        return res[0]

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise ProviderException("openai_embedding", "OpenAI API key is not configured.")
        payload = {
            "model": self.model_name,
            "input": texts
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    self.endpoint,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                if res.status_code != 200:
                    raise ProviderException("openai_embedding", f"API returned status {res.status_code}")
                data = res.json()
                return [item["embedding"] for item in data["data"]]
        except Exception as e:
            if isinstance(e, ProviderException):
                raise
            raise ProviderException("openai_embedding", str(e))


def get_embedding_provider() -> BaseEmbeddingProvider:
    provider = settings.EMBEDDING_PROVIDER.lower()
    api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY or ""
    if (provider == "gemini" or (api_key and provider == "mock")) and api_key:
        return GeminiEmbeddingProvider(api_key=api_key, model_name=settings.EMBEDDING_MODEL)
    elif provider == "openai" and api_key:
        return OpenAIEmbeddingProvider(api_key=api_key, model_name=settings.EMBEDDING_MODEL)
    elif provider == "gemini":
        return GeminiEmbeddingProvider(api_key=api_key, model_name=settings.EMBEDDING_MODEL)
    return MockEmbeddingProvider()
