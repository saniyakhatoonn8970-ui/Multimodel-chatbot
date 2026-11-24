from fastapi import HTTPException, status
from typing import Optional, Any, Dict


class MindBridgeException(Exception):
    """Base exception for MindBridge AI application."""
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class SessionUnauthorizedException(MindBridgeException):
    def __init__(self, message: str = "Invalid or unauthorized session"):
        super().__init__(message=message, error_code="UNAUTHORIZED_SESSION", status_code=status.HTTP_401_UNAUTHORIZED)


class ResourceNotFoundException(MindBridgeException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' was not found or access is unauthorized.",
            error_code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ValidationException(MindBridgeException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="VALIDATION_ERROR", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class FileValidationException(MindBridgeException):
    def __init__(self, message: str, error_code: str = "INVALID_FILE"):
        super().__init__(message=message, error_code=error_code, status_code=status.HTTP_400_BAD_REQUEST)


class ProviderException(MindBridgeException):
    def __init__(self, provider_type: str, message: str):
        super().__init__(
            message=f"Provider error ({provider_type}): {message}",
            error_code="PROVIDER_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"provider_type": provider_type}
        )


class RateLimitException(MindBridgeException):
    def __init__(self, message: str = "Too many requests. Please slow down."):
        super().__init__(message=message, error_code="RATE_LIMIT_EXCEEDED", status_code=status.HTTP_429_TOO_MANY_REQUESTS)
