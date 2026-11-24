from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.providers.embeddings import get_embedding_provider
from backend.app.prompts.rag import build_rag_prompt
from backend.app.schemas.message import Citation
from backend.app.vector_store.relational_store import RelationalVectorStore


class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_provider = get_embedding_provider()
        self.vector_store = RelationalVectorStore(db)

    async def retrieve_context_and_build_prompt(
        self,
        session_id: str,
        user_query: str,
        rag_only: bool = False,
        top_k: int = 4,
        threshold: float = 0.35
    ) -> Tuple[str, List[Citation]]:
        """
        Embeds user query, retrieves relevant chunks for the session, 
        and constructs a security-hardened RAG prompt.
        """
        # 1. Embed query
        try:
            query_embedding = await self.embedding_provider.get_embedding(user_query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            query_embedding = []

        if not query_embedding:
            return user_query, []

        # 2. Retrieve similar chunks
        retrieved_raw = self.vector_store.search_similar(
            session_id=session_id,
            query_embedding=query_embedding,
            top_k=top_k or settings.RAG_TOP_K,
            threshold=threshold or settings.RAG_RELEVANCE_THRESHOLD
        )

        citations: List[Citation] = []
        for r in retrieved_raw:
            citations.append(
                Citation(
                    document_id=r["document_id"],
                    filename=r["filename"],
                    page_number=r.get("page_number"),
                    chunk_index=r["chunk_index"],
                    snippet=r["chunk_text"][:250],
                    score=r["score"]
                )
            )

        # 3. Build RAG prompt
        augmented_prompt = build_rag_prompt(
            user_query=user_query,
            retrieved_chunks=retrieved_raw,
            rag_only=rag_only
        )

        return augmented_prompt, citations
