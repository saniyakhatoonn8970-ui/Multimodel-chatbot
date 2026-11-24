from typing import Generator
from fastapi import Header, Depends
from sqlalchemy.orm import Session

from backend.app.core.exceptions import SessionUnauthorizedException
from backend.app.core.security import is_valid_session_id
from backend.app.db.session import get_db


def get_current_session_id(x_session_id: str = Header(None, alias="X-Session-ID")) -> str:
    """
    Extract and validate the anonymous session token from the X-Session-ID HTTP header.
    Rejects malformed, empty, or missing session identifiers.
    """
    if not x_session_id or not is_valid_session_id(x_session_id):
        raise SessionUnauthorizedException(
            "Missing or invalid X-Session-ID header. An opaque 32-64 character hexadecimal session token is required."
        )
    return x_session_id
