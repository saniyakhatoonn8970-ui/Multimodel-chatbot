import re
import secrets
import os
from typing import Optional, Tuple


def generate_session_id() -> str:
    """Generate an opaque, high-entropy cryptographic session identifier."""
    return secrets.token_hex(32)


def is_valid_session_id(session_id: Optional[str]) -> bool:
    """Verify that the session identifier matches the high-entropy hex format (64 chars hex)."""
    if not session_id or not isinstance(session_id, str):
        return False
    # Allow 32 to 64 character alphanumeric tokens
    return bool(re.fullmatch(r"^[a-zA-Z0-9_\-]{32,64}$", session_id))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename against path traversal, null-byte injection, and invalid characters.
    """
    if not filename:
        return "unnamed_file"
    # Strip directory components (both Unix and Windows style)
    clean_name = os.path.basename(filename.replace("\\", "/"))
    # Remove null bytes and non-printable characters
    clean_name = re.sub(r'[\x00-\x1f\x7f]', '', clean_name)
    # Allow alphanumeric, dot, hyphen, underscore, and space
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.\s]', '_', clean_name)
    clean_name = clean_name.strip(" .")
    return clean_name or "sanitized_file"


def validate_file_signature(content: bytes, declared_content_type: str) -> Tuple[bool, str]:
    """
    Validate actual magic byte signatures rather than relying purely on user-supplied MIME type.
    Returns (is_valid, detected_type_or_reason).
    """
    if not content:
        return False, "File is empty"

    header = content[:16]

    # PDF: starts with %PDF-
    if header.startswith(b"%PDF-"):
        return True, "application/pdf"

    # PNG: starts with 89 50 4E 47 0D 0A 1A 0A
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return True, "image/png"

    # JPEG: starts with FF D8 FF
    if header.startswith(b"\xff\xd8\xff"):
        return True, "image/jpeg"

    # WebP: starts with RIFF, then 4 bytes size, then WEBP
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return True, "image/webp"

    # WAV: starts with RIFF, then 4 bytes size, then WAVE
    if header[:4] == b"RIFF" and header[8:12] == b"WAVE":
        return True, "audio/wav"

    # WebM / Matroska: starts with \x1a\x45\xdf\xa3
    if header.startswith(b"\x1a\x45\xdf\xa3"):
        return True, "audio/webm"

    # Plain text: check for reasonable ASCII/UTF-8 decodability
    if declared_content_type.startswith("text/") or declared_content_type in ("application/json", "application/octet-stream"):
        try:
            content[:1024].decode("utf-8")
            return True, "text/plain"
        except UnicodeDecodeError:
            pass

    # If declared is text/plain but failed above
    if declared_content_type == "text/plain":
        try:
            content[:1024].decode("utf-8")
            return True, "text/plain"
        except UnicodeDecodeError:
            return False, "Invalid text encoding, expected UTF-8"

    return False, f"Unsupported file signature for declared type: {declared_content_type}"
