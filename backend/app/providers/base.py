from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_instruction: Optional[str] = None
    ) -> str:
        """Generate text completion from conversation messages."""
        pass


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for a single string."""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple strings."""
        pass


class BaseVisionProvider(ABC):
    @abstractmethod
    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        user_prompt: str
    ) -> str:
        """Analyze image and respond to the user prompt."""
        pass


class BaseSTTProvider(ABC):
    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio bytes to text."""
        pass


class BaseTTSProvider(ABC):
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synthesize text to audio bytes and return base64 encoded payload."""
        pass
