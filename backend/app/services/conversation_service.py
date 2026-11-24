from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.core.exceptions import ResourceNotFoundException
from backend.app.db.models.conversation import Conversation
from backend.app.repositories.conversation_repo import ConversationRepository
from backend.app.schemas.conversation import (
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse
)
from backend.app.schemas.message import MessageResponse


class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, session_id: str, title: Optional[str] = None) -> ConversationResponse:
        conv = ConversationRepository.create(self.db, session_id=session_id, title=title)
        return ConversationResponse.model_validate(conv)

    def list_conversations(self, session_id: str, limit: int = 50, offset: int = 0) -> ConversationListResponse:
        convs = ConversationRepository.list_by_session(self.db, session_id=session_id, limit=limit, offset=offset)
        total = ConversationRepository.count_by_session(self.db, session_id=session_id)
        return ConversationListResponse(
            conversations=[ConversationResponse.model_validate(c) for c in convs],
            total=total
        )

    def get_conversation_detail(self, conversation_id: str, session_id: str) -> ConversationDetailResponse:
        conv = ConversationRepository.get_by_id_and_session(self.db, conversation_id=conversation_id, session_id=session_id)
        if not conv:
            raise ResourceNotFoundException("Conversation", conversation_id)
        
        messages = ConversationRepository.get_messages(self.db, conversation_id=conversation_id, session_id=session_id)
        return ConversationDetailResponse(
            id=conv.id,
            session_id=conv.session_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=[MessageResponse.model_validate(m) for m in messages]
        )

    def delete_conversation(self, conversation_id: str, session_id: str) -> bool:
        deleted = ConversationRepository.delete(self.db, conversation_id=conversation_id, session_id=session_id)
        if not deleted:
            raise ResourceNotFoundException("Conversation", conversation_id)
        return True
