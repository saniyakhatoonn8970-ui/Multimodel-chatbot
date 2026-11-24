from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from backend.app.db.models.conversation import Conversation
from backend.app.db.models.message import Message


class ConversationRepository:
    @staticmethod
    def create(db: Session, session_id: str, title: Optional[str] = None) -> Conversation:
        conv = Conversation(
            session_id=session_id,
            title=title or "New Conversation"
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def get_by_id_and_session(db: Session, conversation_id: str, session_id: str) -> Optional[Conversation]:
        """Fetch conversation strictly verifying ownership by session_id."""
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.session_id == session_id
        )
        return db.scalar(stmt)

    @staticmethod
    def list_by_session(db: Session, session_id: str, limit: int = 50, offset: int = 0) -> List[Conversation]:
        stmt = select(Conversation).where(
            Conversation.session_id == session_id
        ).order_by(desc(Conversation.updated_at)).limit(limit).offset(offset)
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_by_session(db: Session, session_id: str) -> int:
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        return len(list(db.scalars(stmt).all()))

    @staticmethod
    def delete(db: Session, conversation_id: str, session_id: str) -> bool:
        conv = ConversationRepository.get_by_id_and_session(db, conversation_id, session_id)
        if not conv:
            return False
        db.delete(conv)
        db.commit()
        return True

    @staticmethod
    def update_title(db: Session, conversation_id: str, session_id: str, new_title: str) -> Optional[Conversation]:
        conv = ConversationRepository.get_by_id_and_session(db, conversation_id, session_id)
        if not conv:
            return None
        conv.title = new_title
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: str,
        role: str,
        content: str,
        input_modality: str = "text",
        output_modality: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            input_modality=input_modality,
            output_modality=output_modality,
            message_metadata=metadata or {}
        )
        db.add(msg)
        
        # Update parent conversation updated_at
        conv = db.get(Conversation, conversation_id)
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
            
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def get_messages(
        db: Session, conversation_id: str, session_id: str, limit: Optional[int] = None
    ) -> List[Message]:
        conv = ConversationRepository.get_by_id_and_session(db, conversation_id, session_id)
        if not conv:
            return []
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        if limit:
            stmt = stmt.limit(limit)
        return list(db.scalars(stmt).all())
