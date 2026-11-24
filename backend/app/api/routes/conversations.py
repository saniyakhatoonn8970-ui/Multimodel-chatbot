from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_session_id
from backend.app.db.session import get_db
from backend.app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse
)
from backend.app.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    session_id: str = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """Create a new conversation associated with the caller's anonymous session token."""
    service = ConversationService(db)
    return service.create_conversation(session_id=session_id, title=payload.title)


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session_id: str = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """List all conversations strictly owned by the caller's anonymous session token."""
    service = ConversationService(db)
    return service.list_conversations(session_id=session_id, limit=limit, offset=offset)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    session_id: str = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """Retrieve full details and message history for an authorized conversation."""
    service = ConversationService(db)
    return service.get_conversation_detail(conversation_id=conversation_id, session_id=session_id)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    session_id: str = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """Permanently delete an authorized conversation and all its associated messages."""
    service = ConversationService(db)
    service.delete_conversation(conversation_id=conversation_id, session_id=session_id)
    return None
