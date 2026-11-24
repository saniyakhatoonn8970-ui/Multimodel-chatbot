from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.base import Base

def create_db_engine():
    target_url = settings.DATABASE_URL
    try:
        engine = create_engine(
            target_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Connected to primary database: {target_url.split('@')[-1] if '@' in target_url else target_url}")
        return engine
    except Exception as e:
        if settings.ALLOW_SQLITE_DEV_FALLBACK and settings.ENVIRONMENT == "development":
            logger.warning(
                f"Could not connect to MySQL at {target_url} ({e}). "
                f"Falling back to local SQLite for development: {settings.DEV_SQLITE_URL}"
            )
            fallback_engine = create_engine(
                settings.DEV_SQLITE_URL,
                connect_args={"check_same_thread": False},
                echo=False
            )
            # Create tables in dev fallback if not present
            Base.metadata.create_all(bind=fallback_engine)
            return fallback_engine
        else:
            logger.error(f"Failed to connect to database at {target_url}: {e}")
            raise


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency with guaranteed closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Check database connectivity without exposing connection details."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
