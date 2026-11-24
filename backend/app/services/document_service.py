import pymupdf as fitz
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import FileValidationException, ResourceNotFoundException
from backend.app.core.logging import logger
from backend.app.core.security import sanitize_filename, validate_file_signature
from backend.app.db.models.document import Document
from backend.app.providers.embeddings import get_embedding_provider
from backend.app.repositories.document_repo import DocumentRepository
from backend.app.schemas.document import DocumentResponse, DocumentListResponse


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_provider = get_embedding_provider()

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[str]:
        """
        Split text into overlapping chunks cleanly preserving word boundaries where possible.
        """
        if not text:
            return []
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            if end >= text_len:
                chunk = text[start:text_len].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Try to break on newline or space within the last 50 chars of the window
            break_pt = text.rfind("\n", start + chunk_size - 60, end)
            if break_pt == -1:
                break_pt = text.rfind(" ", start + chunk_size - 60, end)
            if break_pt != -1 and break_pt > start:
                end = break_pt

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - chunk_overlap
            if start < 0 or start >= text_len:
                break

        return chunks

    def extract_text_from_pdf(self, content_bytes: bytes) -> List[Tuple[int, str]]:
        """
        Extract text page-by-page from PDF using PyMuPDF.
        Returns list of tuples: (page_number_1_indexed, text).
        """
        try:
            doc = fitz.open(stream=content_bytes, filetype="pdf")
        except Exception as e:
            raise FileValidationException(f"Failed to parse PDF: corrupted or invalid format ({str(e)})")

        page_count = len(doc)
        if page_count == 0:
            raise FileValidationException("The PDF file contains 0 pages.")
        if page_count > settings.MAX_PDF_PAGES:
            raise FileValidationException(
                f"PDF exceeds maximum page limit of {settings.MAX_PDF_PAGES} pages (uploaded: {page_count})."
            )

        extracted = []
        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            if page_text:
                extracted.append((page_idx + 1, page_text))
        
        doc.close()
        return extracted

    def extract_text_from_txt(self, content_bytes: bytes) -> List[Tuple[Optional[int], str]]:
        """Extract text from TXT file."""
        try:
            text = content_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                text = content_bytes.decode("latin-1").strip()
            except Exception as e:
                raise FileValidationException(f"Unable to decode text file: {str(e)}")
        
        if not text:
            raise FileValidationException("The uploaded text document is empty.")
        return [(None, text)]

    async def ingest_document(
        self,
        session_id: str,
        filename: str,
        content_bytes: bytes,
        content_type: str
    ) -> DocumentResponse:
        # 1. Enforce size limit
        file_size = len(content_bytes)
        max_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise FileValidationException(
                f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum limit of {settings.MAX_DOCUMENT_SIZE_MB} MB."
            )

        # 2. Sanitize filename and validate file signature
        safe_filename = sanitize_filename(filename)
        is_valid, detected_type = validate_file_signature(content_bytes, content_type)
        if not is_valid:
            raise FileValidationException(f"Invalid file format: {detected_type}")

        # 3. Create document record in DB
        doc_record = DocumentRepository.create(
            db=self.db,
            session_id=session_id,
            filename=safe_filename,
            content_type=detected_type,
            file_size=file_size,
            status="pending"
        )

        try:
            # 4. Extract text
            if detected_type == "application/pdf":
                pages_data = self.extract_text_from_pdf(content_bytes)
            else:
                pages_data = self.extract_text_from_txt(content_bytes)

            if not pages_data:
                DocumentRepository.update_status(self.db, doc_record.id, "failed", "EMPTY_CONTENT")
                raise FileValidationException("Document contains no readable text.")

            # 5. Chunk text
            raw_chunks: List[Dict[str, Any]] = []
            chunk_texts_for_embedding: List[str] = []
            chunk_counter = 0

            for page_num, text in pages_data:
                splits = self.chunk_text(
                    text,
                    chunk_size=settings.RAG_CHUNK_SIZE,
                    chunk_overlap=settings.RAG_CHUNK_OVERLAP
                )
                for split in splits:
                    raw_chunks.append({
                        "document_id": doc_record.id,
                        "chunk_index": chunk_counter,
                        "chunk_text": split,
                        "page_number": page_num
                    })
                    chunk_texts_for_embedding.append(split)
                    chunk_counter += 1

            if not raw_chunks:
                DocumentRepository.update_status(self.db, doc_record.id, "failed", "NO_CHUNKS_GENERATED")
                raise FileValidationException("Failed to extract any text chunks from the document.")

            # 6. Generate embeddings
            embeddings = await self.embedding_provider.get_embeddings(chunk_texts_for_embedding)
            for idx, emb in enumerate(embeddings):
                raw_chunks[idx]["embedding"] = emb

            # 7. Persist chunks
            DocumentRepository.add_chunks(self.db, doc_record.id, raw_chunks)
            DocumentRepository.update_status(self.db, doc_record.id, "indexed")
            
            # Fetch refreshed
            updated = DocumentRepository.get_by_id_and_session(self.db, doc_record.id, session_id)
            res = DocumentResponse.model_validate(updated)
            res.chunks_count = len(raw_chunks)
            return res

        except Exception as e:
            logger.error(f"Failed to ingest document {safe_filename}: {e}")
            DocumentRepository.update_status(self.db, doc_record.id, "failed", "PROCESSING_ERROR")
            if isinstance(e, FileValidationException):
                raise
            raise FileValidationException(f"Failed to process document: {str(e)}")

    def list_documents(self, session_id: str) -> DocumentListResponse:
        docs = DocumentRepository.list_by_session(self.db, session_id=session_id)
        doc_responses = []
        for d in docs:
            r = DocumentResponse.model_validate(d)
            r.chunks_count = len(d.chunks)
            doc_responses.append(r)
        return DocumentListResponse(documents=doc_responses, total=len(doc_responses))

    def delete_document(self, document_id: str, session_id: str) -> bool:
        deleted = DocumentRepository.delete(self.db, document_id=document_id, session_id=session_id)
        if not deleted:
            raise ResourceNotFoundException("Document", document_id)
        return True
