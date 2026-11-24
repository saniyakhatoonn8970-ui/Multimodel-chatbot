from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.models.feedback import Feedback
from backend.app.db.models.message import Message
from backend.app.db.models.conversation import Conversation


class FeedbackRepository:
    @staticmethod
    def create(
        db: Session,
        message_id: str,
        feedback_type: str,
        comment: Optional[str] = None
    ) -> Feedback:
        fb = Feedback(
            message_id=message_id,
            feedback_type=feedback_type,
            comment=comment
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return fb

    @staticmethod
    def verify_message_session(db: Session, message_id: str, session_id: str) -> bool:
        """Verify that the message being reviewed belongs to the user's session."""
        stmt = (
            select(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Message.id == message_id,
                Conversation.session_id == session_id
            )
        )
        return db.scalar(stmt) is not None
