from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseVectorStore(ABC):
    @abstractmethod
    def add_documents(
        self,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """Store chunk records with their vector embeddings."""
        pass

    @abstractmethod
    def search_similar(
        self,
        session_id: str,
        query_embedding: List[float],
        top_k: int = 4,
        threshold: float = 0.35
    ) -> List[Dict[str, Any]]:
        """
        Search for most similar chunks belonging to the session.
        Returns list of dicts with:
        chunk_id, document_id, filename, page_number, chunk_index, chunk_text, score
        """
        pass

    @abstractmethod
    def delete_document(self, document_id: str, session_id: str) -> bool:
        """Remove document and all associated vector chunks."""
        pass

    @abstractmethod
    def delete_document_chunks(self, document_id: str) -> int:
        """Remove all chunks for a specific document."""
        pass
