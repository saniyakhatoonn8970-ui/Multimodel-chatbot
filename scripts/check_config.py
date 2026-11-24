import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.db.session import check_db_connection


def main():
    print("=" * 60)
    print(" MindBridge AI - Environment & Configuration Checker")
    print("=" * 60)

    print(f"App Name:        {settings.APP_NAME}")
    print(f"Environment:     {settings.ENVIRONMENT}")
    print(f"Host:Port:       {settings.HOST}:{settings.PORT}")
    print(f"Frontend URL:    {settings.FRONTEND_URL}")
    print(f"Allowed Origins: {settings.cors_origins}")
    print("-" * 60)

    # Database
    db_target = settings.DATABASE_URL
    masked_db = db_target.split("@")[-1] if "@" in db_target else db_target
    print(f"Configured Database: {masked_db}")
    db_status = check_db_connection()
    if db_status:
        print("Database Status:     [SUCCESS] Connected to database.")
    else:
        print("Database Status:     [WARNING] Could not connect to primary database.")
        if settings.ALLOW_SQLITE_DEV_FALLBACK:
            print("                     SQLite fallback is enabled for local development.")
        else:
            print("                     Check that MySQL Server is running and credentials are valid.")

    print("-" * 60)
    # Providers
    print("Provider Configurations:")
    print(f"  - LLM:        {settings.LLM_PROVIDER} ({settings.LLM_MODEL}) [{'KEY CONFIGURED' if settings.LLM_API_KEY else 'NO KEY / OFFLINE'}]")
    print(f"  - Embeddings: {settings.EMBEDDING_PROVIDER} ({settings.EMBEDDING_MODEL}) [{'KEY CONFIGURED' if settings.EMBEDDING_API_KEY else 'NO KEY / OFFLINE'}]")
    print(f"  - Vision:     {settings.VISION_PROVIDER} ({settings.VISION_MODEL}) [{'KEY CONFIGURED' if settings.VISION_API_KEY else 'NO KEY / OFFLINE'}]")
    print(f"  - STT:        {settings.STT_PROVIDER} ({settings.STT_MODEL}) [{'KEY CONFIGURED' if settings.STT_API_KEY else 'NO KEY / OFFLINE'}]")
    print(f"  - TTS:        {settings.TTS_PROVIDER} ({settings.TTS_MODEL}) [{'KEY CONFIGURED' if settings.TTS_API_KEY else 'NO KEY / OFFLINE'}]")

    print("-" * 60)
    print("RAG & Safety Settings:")
    print(f"  - Chunk Size / Overlap: {settings.RAG_CHUNK_SIZE} / {settings.RAG_CHUNK_OVERLAP}")
    print(f"  - Top-K Chunks:         {settings.RAG_TOP_K}")
    print(f"  - Relevance Threshold:  {settings.RAG_RELEVANCE_THRESHOLD}")
    print(f"  - Max Doc Size (MB):    {settings.MAX_DOCUMENT_SIZE_MB}")
    print(f"  - Max PDF Pages:        {settings.MAX_PDF_PAGES}")
    print(f"  - Crisis Lifeline:      {settings.CRISIS_HELPLINE_US}")
    print("=" * 60)
    print("Configuration check complete.")


if __name__ == "__main__":
    main()
