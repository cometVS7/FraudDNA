"""FraudDNA Centralized Domain Errors and Exception Handling.

Defines a lightweight, domain-driven exception hierarchy and centralized FastAPI
handlers that produce consistent, secure, and backwards-compatible JSON error responses.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_request_id

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Base exception for all FraudDNA business domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationDomainError(DomainError):
    """Raised when domain entities or input payloads fail validation constraints."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class NotFoundDomainError(DomainError):
    """Raised when a requested domain entity (transaction, customer, cluster) does not exist."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictDomainError(DomainError):
    """Raised on state conflict or idempotent resource collisions."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class DependencyDomainError(DomainError):
    """Raised when an external or downstream dependency fails or returns unexpected data."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="DEPENDENCY_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


class ServiceUnavailableDomainError(DomainError):
    """Raised when a required subsystem is offline or degraded."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


def create_error_response(
    message: str,
    code: str,
    status_code: int,
    details: Any = None,
) -> JSONResponse:
    """Construct structured, backwards-compatible JSON error response."""
    request_id = get_request_id()
    content: dict[str, Any] = {
        "detail": message,  # Preserves V1 string compatibility for tests and existing frontend
        "error": {
            "code": code,
            "message": message,
            "status": status_code,
            "request_id": request_id,
        },
    }
    if details is not None:
        content["error"]["details"] = jsonable_encoder(details)

    headers = {}
    if request_id:
        headers[settings.REQUEST_ID_HEADER] = request_id

    return JSONResponse(status_code=status_code, content=content, headers=headers)


async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    """Handle explicit domain exceptions."""
    logger.warning(
        f"Domain error [{exc.code}] ({exc.status_code}): {exc.message}",
        extra={"error_code": exc.code, "error_details": exc.details},
    )
    return create_error_response(
        message=exc.message,
        code=exc.code,
        status_code=exc.status_code,
        details=exc.details,
    )


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI / Pydantic schema validation failures."""
    errors = jsonable_encoder(exc.errors())
    first_msg = errors[0]["msg"] if errors else "Validation failed"
    logger.info(f"Request validation failure: {first_msg}")
    return create_error_response(
        message=first_msg,
        code="VALIDATION_ERROR",
        status_code=422,
        details=errors,
    )


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Safely catch unhandled internal exceptions without leaking stack traces."""
    logger.error(f"Unhandled internal server error: {exc}", exc_info=True)
    message = "An unexpected internal server error occurred."
    details = str(exc) if settings.DEBUG else None

    return create_error_response(
        message=message,
        code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers with the FastAPI application."""
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
