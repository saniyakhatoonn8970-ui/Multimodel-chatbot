from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_session_id
from backend.app.db.session import get_db
from backend.app.schemas.document import DocumentResponse, DocumentListResponse
from backend.app.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["Documents & RAG"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """
    Ingest, parse (PDF/TXT), chunk, generate embeddings, and index a knowledge document.
    """
    content_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"
    service = DocumentService(db)
    return await service.ingest_document(
        session_id=session_id,
        filename=file.filename or "uploaded_file",
        content_bytes=content_bytes,
        content_type=content_type
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    session_id: str = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """List all indexed documents associated with the caller's anonymous session."""
    service = DocumentService(db)
    return service.list_documents(session_id=session_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    session_id: str = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """Permanently delete an authorized document and its vector embeddings."""
    service = DocumentService(db)
    service.delete_document(document_id=document_id, session_id=session_id)
    return None
