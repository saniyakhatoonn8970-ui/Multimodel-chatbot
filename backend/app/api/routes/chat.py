from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_session_id
from backend.app.core.exceptions import ValidationException
from backend.app.db.session import get_db
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.chat_service import ChatService
from backend.app.services.multimodal_service import MultimodalService

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_message(
    payload: ChatRequest,
    session_id: str = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """
    Standard text conversational endpoint with RAG retrieval and optional audio synthesis.
    """
    chat_service = ChatService(db)
    return await chat_service.handle_chat_message(
        conversation_id=payload.conversation_id,
        session_id=session_id,
        user_text=payload.message,
        use_rag=payload.use_rag,
        rag_only=payload.rag_only,
        enable_audio_response=payload.enable_audio_response,
        input_modality="text"
    )


@router.post("/multimodal", response_model=ChatResponse)
async def chat_multimodal(
    conversation_id: str = Form(...),
    message: Optional[str] = Form(""),
    use_rag: bool = Form(True),
    rag_only: bool = Form(False),
    enable_audio_response: bool = Form(False),
    image_file: Optional[UploadFile] = File(None),
    session_id: str = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """
    Multimodal conversation endpoint supporting image inspection and text query.
    """
    if not message and not image_file:
        raise ValidationException("Either a text message or an image file must be provided.")

    chat_service = ChatService(db)

    # If image is attached, process through vision provider directly
    if image_file:
        user_display_text = message.strip() if message else f"Please analyze this uploaded image ({image_file.filename})."
        img_bytes = await image_file.read()
        content_type = image_file.content_type or "image/jpeg"
        multimodal_service = MultimodalService()
        
        vision_analysis = await multimodal_service.process_image(
            image_bytes=img_bytes,
            content_type=content_type,
            user_prompt=user_display_text
        )

        return await chat_service.handle_chat_message(
            conversation_id=conversation_id,
            session_id=session_id,
            user_text=user_display_text,
            use_rag=False,
            rag_only=False,
            enable_audio_response=enable_audio_response,
            input_modality="image",
            override_response=vision_analysis,
            extra_metadata={"attached_image": image_file.filename}
        )

    return await chat_service.handle_chat_message(
        conversation_id=conversation_id,
        session_id=session_id,
        user_text=message.strip(),
        use_rag=use_rag,
        rag_only=rag_only,
        enable_audio_response=enable_audio_response,
        input_modality="text"
    )
