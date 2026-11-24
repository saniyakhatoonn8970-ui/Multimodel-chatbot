from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    chunk_text: str
    page_number: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    session_id: str
    filename: str
    content_type: str
    file_size: int
    processing_status: str
    error_code: Optional[str] = None
    chunks_count: Optional[int] = 0
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
