"""Custom domain exceptions and FastAPI exception handlers."""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class DomainException(Exception):
    """Base domain exception."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(DomainException):
    """Resource not found exception."""

    pass


class JobNotFoundError(NotFoundError):
    """Job not found in database."""

    def __init__(self, job_id: str):
        super().__init__(f"Job with ID '{job_id}' was not found.", {"job_id": job_id})


class CertificateNotFoundError(NotFoundError):
    """Certificate not found in database or disk."""

    def __init__(self, certificate_id: str):
        super().__init__(
            f"Certificate with ID '{certificate_id}' was not found.",
            {"certificate_id": certificate_id},
        )


class CertificateNotReadyError(DomainException):
    """Certificate requested is not yet in COMPLETED state."""

    def __init__(self, certificate_id: str, status: str):
        super().__init__(
            f"Certificate '{certificate_id}' is not ready for download (current status: {status}).",
            {"certificate_id": certificate_id, "status": status},
        )


class ValidationDomainError(DomainException):
    """Domain level validation failure."""

    pass


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Handle custom domain exceptions cleanly."""
    status_code = status.HTTP_400_BAD_REQUEST

    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, CertificateNotReadyError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, ValidationDomainError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.message,
            "details": exc.details,
        },
    )
