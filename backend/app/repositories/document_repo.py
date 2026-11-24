from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from backend.app.db.models.document import Document, DocumentChunk


class DocumentRepository:
    @staticmethod
    def create(
        db: Session,
        session_id: str,
        filename: str,
        content_type: str,
        file_size: int,
        status: str = "pending"
    ) -> Document:
        doc = Document(
            session_id=session_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            processing_status=status
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_by_id_and_session(db: Session, document_id: str, session_id: str) -> Optional[Document]:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.session_id == session_id
        )
        return db.scalar(stmt)

    @staticmethod
    def list_by_session(db: Session, session_id: str) -> List[Document]:
        stmt = select(Document).where(
            Document.session_id == session_id
        ).order_by(desc(Document.created_at))
        return list(db.scalars(stmt).all())

    @staticmethod
    def update_status(db: Session, document_id: str, status: str, error_code: Optional[str] = None) -> Optional[Document]:
        doc = db.get(Document, document_id)
        if not doc:
            return None
        doc.processing_status = status
        doc.error_code = error_code
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def delete(db: Session, document_id: str, session_id: str) -> bool:
        doc = DocumentRepository.get_by_id_and_session(db, document_id, session_id)
        if not doc:
            return False
        db.delete(doc)
        db.commit()
        return True

    @staticmethod
    def add_chunks(
        db: Session,
        document_id: str,
        chunk_data_list: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        chunk_data_list contains dicts with:
        chunk_index, chunk_text, page_number, embedding
        """
        chunks = []
        for item in chunk_data_list:
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=item["chunk_index"],
                chunk_text=item["chunk_text"],
                page_number=item.get("page_number"),
                embedding=item.get("embedding")
            )
            chunks.append(chunk)
            db.add(chunk)
        db.commit()
        for c in chunks:
            db.refresh(c)
        return chunks

    @staticmethod
    def get_chunks_for_session(db: Session, session_id: str) -> List[DocumentChunk]:
        """Retrieve all document chunks belonging to indexed documents for the session."""
        stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                Document.session_id == session_id,
                Document.processing_status == "indexed"
            )
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_chunks_by_document(db: Session, document_id: str) -> List[DocumentChunk]:
        stmt = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index)
        return list(db.scalars(stmt).all())
