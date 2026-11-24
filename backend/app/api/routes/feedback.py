from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_session_id
from backend.app.core.exceptions import ResourceNotFoundException
from backend.app.db.session import get_db
from backend.app.repositories.feedback_repo import FeedbackRepository
from backend.app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def record_feedback(
    payload: FeedbackCreate,
    session_id: str = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """
    Record helpful / unhelpful feedback for an assistant response.
    Enforces that the message belongs to the caller's session.
    """
    is_authorized = FeedbackRepository.verify_message_session(
        db=db, message_id=payload.message_id, session_id=session_id
    )
    if not is_authorized:
        raise ResourceNotFoundException("Message", payload.message_id)

    fb = FeedbackRepository.create(
        db=db,
        message_id=payload.message_id,
        feedback_type=payload.feedback_type,
        comment=payload.comment
    )
    return FeedbackResponse.model_validate(fb)
