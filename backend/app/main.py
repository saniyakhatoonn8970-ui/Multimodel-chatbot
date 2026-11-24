from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.exceptions import MindBridgeException
from backend.app.core.logging import logger
from backend.app.api.routes import (
    health,
    conversations,
    chat,
    documents,
    audio,
    feedback
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} in '{settings.ENVIRONMENT}' environment...")
    logger.info(f"Configured CORS origins: {settings.cors_origins}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Secure Multimodal Conversational AI Assistant with RAG & Safety Guardrails",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Restrict CORS to configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Session-ID", "Authorization"],
)


@app.exception_handler(MindBridgeException)
async def mindbridge_exception_handler(request: Request, exc: MindBridgeException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "code": exc.error_code,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log internal error without exposing stack trace or secrets to client
    logger.error(f"Unhandled exception during {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected server error occurred. Please try again later.",
            "code": "INTERNAL_SERVER_ERROR"
        }
    )


# Register routes
app.include_router(health.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(audio.router)
app.include_router(feedback.router)


@app.get("/", include_in_schema=False)
def root():
    """Friendly landing endpoint so opening http://127.0.0.1:8000 in browser shows status & instructions."""
    return {
        "service": settings.APP_NAME,
        "status": "online",
        "version": "1.0.0",
        "api_documentation": "/docs",
        "health_check": "/health",
        "frontend_ui": f"{settings.FRONTEND_URL} (Run: python scripts/run_dev.py frontend)",
        "message": "FastAPI backend is running successfully. Open the Streamlit frontend to chat!"
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
