import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from backend.app.db.models.document import Document, DocumentChunk
from backend.app.vector_store.base import BaseVectorStore


class RelationalVectorStore(BaseVectorStore):
    """
    Vector retrieval implementation persisting embeddings directly in MySQL DocumentChunk records
    and performing high-performance vectorized cosine similarity ranking via NumPy.
    Ensures 100% compatibility with standard MySQL 8.0 without special extensions.
    """
    def __init__(self, db: Session):
        self.db = db

    def add_documents(self, chunks: List[Dict[str, Any]]) -> int:
        added_count = 0
        for item in chunks:
            chunk = DocumentChunk(
                document_id=item["document_id"],
                chunk_index=item["chunk_index"],
                chunk_text=item["chunk_text"],
                page_number=item.get("page_number"),
                embedding=item.get("embedding")
            )
            self.db.add(chunk)
            added_count += 1
        self.db.commit()
        return added_count

    def search_similar(
        self,
        session_id: str,
        query_embedding: List[float],
        top_k: int = 4,
        threshold: float = 0.35
    ) -> List[Dict[str, Any]]:
        if not query_embedding:
            return []

        # Query all chunks belonging to session's indexed documents
        stmt = (
            select(
                DocumentChunk.id,
                DocumentChunk.document_id,
                DocumentChunk.chunk_index,
                DocumentChunk.chunk_text,
                DocumentChunk.page_number,
                DocumentChunk.embedding,
                Document.filename
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                Document.session_id == session_id,
                Document.processing_status == "indexed",
                DocumentChunk.embedding.is_not(None)
            )
        )
        rows = self.db.execute(stmt).all()
        if not rows:
            return []

        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        scored_results = []
        for row in rows:
            chunk_id, doc_id, chunk_idx, text, page_num, emb_list, fname = row
            if not emb_list or len(emb_list) != len(query_vec):
                continue
            
            chunk_vec = np.array(emb_list, dtype=np.float32)
            chunk_norm = np.linalg.norm(chunk_vec)
            if chunk_norm == 0:
                continue

            # Cosine similarity
            cosine_sim = float(np.dot(query_vec, chunk_vec) / (query_norm * chunk_norm))
            
            if cosine_sim >= threshold:
                scored_results.append({
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "filename": fname,
                    "page_number": page_num,
                    "chunk_index": chunk_idx,
                    "chunk_text": text,
                    "score": round(cosine_sim, 4)
                })

        # Sort descending by score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def delete_document(self, document_id: str, session_id: str) -> bool:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.session_id == session_id
        )
        doc = self.db.scalar(stmt)
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        return True

    def delete_document_chunks(self, document_id: str) -> int:
        stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
