from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import ResourceNotFoundException
from backend.app.core.logging import logger
from backend.app.prompts.system import BASE_SYSTEM_PROMPT
from backend.app.providers.llm import get_llm_provider
from backend.app.repositories.conversation_repo import ConversationRepository
from backend.app.schemas.chat import ChatResponse
from backend.app.schemas.message import MessageResponse, Citation
from backend.app.services.multimodal_service import MultimodalService
from backend.app.services.rag_service import RAGService
from backend.app.services.safety_service import SafetyService


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_provider = get_llm_provider()
        self.rag_service = RAGService(db)
        self.multimodal_service = MultimodalService()

    async def handle_chat_message(
        self,
        conversation_id: str,
        session_id: str,
        user_text: str,
        use_rag: bool = True,
        rag_only: bool = False,
        enable_audio_response: bool = False,
        input_modality: str = "text",
        override_response: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        # 1. Verify conversation ownership
        conv = ConversationRepository.get_by_id_and_session(self.db, conversation_id, session_id)
        if not conv:
            raise ResourceNotFoundException("Conversation", conversation_id)

        clean_text = user_text.strip()

        # 2. Safety and crisis evaluation
        is_diverted, safe_reply, rule = SafetyService.evaluate_input(clean_text)
        if is_diverted and safe_reply:
            user_msg = ConversationRepository.add_message(
                self.db,
                conversation_id=conversation_id,
                role="user",
                content=clean_text,
                input_modality=input_modality,
                metadata=extra_metadata
            )
            asst_msg = ConversationRepository.add_message(
                self.db,
                conversation_id=conversation_id,
                role="assistant",
                content=safe_reply,
                output_modality="text",
                metadata={"safety_rule": rule}
            )
            return ChatResponse(
                conversation_id=conversation_id,
                user_message=MessageResponse.model_validate(user_msg),
                assistant_message=MessageResponse.model_validate(asst_msg),
                citations=[],
                crisis_triggered=(rule == "CRISIS_SELF_HARM"),
                warning=f"Safety intervention triggered: {rule}" if rule != "CRISIS_SELF_HARM" else None
            )

        # 3. If an explicit response is provided (e.g. from vision analysis)
        citations: List[Citation] = []
        if override_response:
            response_text = override_response
        else:
            # RAG Retrieval if enabled
            prompt_for_llm = clean_text
            if use_rag:
                prompt_for_llm, citations = await self.rag_service.retrieve_context_and_build_prompt(
                    session_id=session_id,
                    user_query=clean_text,
                    rag_only=rag_only
                )

            # 4. Prepare conversation history
            history_msgs = ConversationRepository.get_messages(
                self.db,
                conversation_id=conversation_id,
                session_id=session_id,
                limit=settings.CONVERSATION_HISTORY_LIMIT
            )

            formatted_messages: List[Dict[str, str]] = []
            for m in history_msgs:
                if m.role in ("user", "assistant"):
                    formatted_messages.append({"role": m.role, "content": m.content})

            # Append current user prompt
            formatted_messages.append({"role": "user", "content": prompt_for_llm})

            # 5. Generate completion
            response_text = await self.llm_provider.generate_response(
                messages=formatted_messages,
                system_instruction=BASE_SYSTEM_PROMPT
            )

        # 6. Optional Audio response synthesis
        audio_b64: Optional[str] = None
        if enable_audio_response:
            try:
                synth_result = await self.multimodal_service.synthesize_speech(response_text)
                audio_b64 = synth_result.get("audio_base64")
            except Exception as e:
                logger.error(f"TTS synthesis failed: {e}")

        # 7. Persist messages to DB
        user_metadata = extra_metadata or {}
        user_msg = ConversationRepository.add_message(
            self.db,
            conversation_id=conversation_id,
            role="user",
            content=clean_text,
            input_modality=input_modality,
            metadata=user_metadata
        )

        msg_metadata: Dict[str, Any] = {}
        if citations:
            msg_metadata["citations"] = [c.model_dump() for c in citations]
        if enable_audio_response and audio_b64:
            msg_metadata["has_audio"] = True

        asst_msg = ConversationRepository.add_message(
            self.db,
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            input_modality=input_modality,
            output_modality="audio" if (enable_audio_response and audio_b64) else "text",
            metadata=msg_metadata
        )

        return ChatResponse(
            conversation_id=conversation_id,
            user_message=MessageResponse.model_validate(user_msg),
            assistant_message=MessageResponse.model_validate(asst_msg),
            citations=citations,
            audio_base64=audio_b64,
            crisis_triggered=False
        )
