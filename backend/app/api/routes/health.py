from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.core.security import generate_session_id
from backend.app.db.session import check_db_connection

router = APIRouter(tags=["Health & System"])


@router.get("/health")
def health_check():
    """
    Returns basic service health status without disclosing internal credentials, 
    connection strings, or sensitive application secrets.
    """
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_ok else "unreachable",
        "providers": {
            "llm": settings.LLM_PROVIDER,
            "embeddings": settings.EMBEDDING_PROVIDER,
            "vision": settings.VISION_PROVIDER,
            "stt": settings.STT_PROVIDER,
            "tts": settings.TTS_PROVIDER,
        }
    }


@router.get("/api/session/new")
def get_new_session():
    """
    Generate and issue a fresh opaque, high-entropy cryptographic session identifier.
    The client must attach this token as 'X-Session-ID' on subsequent requests.
    """
    session_id = generate_session_id()
    return {
        "session_id": session_id,
        "token_type": "Bearer",
        "usage": "Send in 'X-Session-ID' header"
    }
