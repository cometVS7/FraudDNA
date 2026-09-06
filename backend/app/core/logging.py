"""FraudDNA Production Structured Logging Foundation.

Provides contextual, structured logging with correlation IDs, transaction/investigation
context tracking via contextvars, sensitive data redaction, and dual console/JSON formatting.
"""

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variables for asynchronous request tracing
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)
_transaction_id_ctx: ContextVar[str | None] = ContextVar("transaction_id", default=None)
_investigation_id_ctx: ContextVar[str | None] = ContextVar("investigation_id", default=None)
_case_id_ctx: ContextVar[str | None] = ContextVar("case_id", default=None)

# Regular expressions for redaction of sensitive credentials and payment data
CARD_PAN_REGEX = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
BEARER_TOKEN_REGEX = re.compile(r"(Bearer\s+)[A-Za-z0-9_\-\.]+", re.IGNORECASE)
SECRET_ASSIGNMENT_REGEX = re.compile(
    r"(?i)\b(password|secret|api_key|token|auth_key)\s*[:=]\s*['\"]?([^'\"\s,;]+)['\"]?"
)


def sanitize_log_message(msg: str) -> str:
    """Sanitize sensitive patterns from raw log message strings."""
    if not isinstance(msg, str):
        return msg

    # Redact Authorization bearer tokens
    cleaned = BEARER_TOKEN_REGEX.sub(r"\1[REDACTED]", msg)

    # Redact secret / password assignments
    cleaned = SECRET_ASSIGNMENT_REGEX.sub(r"\1=[REDACTED]", cleaned)

    # Redact suspected payment card primary account numbers (keep first 4 and last 4)
    def _mask_pan(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19:
            return f"{digits[:4]}-****-****-{digits[-4:]}"
        return match.group(0)

    cleaned = CARD_PAN_REGEX.sub(_mask_pan, cleaned)
    return cleaned


def set_request_context(
    request_id: str | None = None,
    correlation_id: str | None = None,
    transaction_id: str | None = None,
    investigation_id: str | None = None,
    case_id: str | None = None,
) -> None:
    """Populate contextual tracking identifiers for the current task/coroutine."""
    if request_id is not None:
        _request_id_ctx.set(request_id)
    if correlation_id is not None:
        _correlation_id_ctx.set(correlation_id)
    if transaction_id is not None:
        _transaction_id_ctx.set(transaction_id)
    if investigation_id is not None:
        _investigation_id_ctx.set(investigation_id)
    if case_id is not None:
        _case_id_ctx.set(case_id)


def get_request_id() -> str | None:
    """Return active request ID from context."""
    return _request_id_ctx.get()


def get_correlation_id() -> str | None:
    """Return active correlation ID from context."""
    return _correlation_id_ctx.get() or _request_id_ctx.get()


def get_transaction_id() -> str | None:
    """Return active transaction ID from context."""
    return _transaction_id_ctx.get()


def get_investigation_id() -> str | None:
    """Return active investigation ID from context."""
    return _investigation_id_ctx.get()


def get_case_id() -> str | None:
    """Return active case ID from context."""
    return _case_id_ctx.get()


def clear_request_context() -> None:
    """Clear contextual tracking identifiers for the current task/coroutine."""
    _request_id_ctx.set(None)
    _correlation_id_ctx.set(None)
    _transaction_id_ctx.set(None)
    _investigation_id_ctx.set(None)
    _case_id_ctx.set(None)


class ContextFilter(logging.Filter):
    """Injects contextual tracking identifiers into LogRecord objects."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        record.correlation_id = get_correlation_id() or "-"
        record.transaction_id = get_transaction_id() or "-"
        record.investigation_id = get_investigation_id() or "-"
        record.case_id = get_case_id() or "-"

        # Sanitize message payload
        if isinstance(record.msg, str):
            record.msg = sanitize_log_message(record.msg)
        return True


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter with contextual tags and safe redaction."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
        req_id = getattr(record, "request_id", "-")
        tx_id = getattr(record, "transaction_id", "-")
        inv_id = getattr(record, "investigation_id", "-")

        context_parts = []
        if req_id != "-":
            context_parts.append(f"req={req_id}")
        if tx_id != "-":
            context_parts.append(f"tx={tx_id}")
        if inv_id != "-":
            context_parts.append(f"inv={inv_id}")

        context_str = f" [{', '.join(context_parts)}]" if context_parts else ""
        formatted_msg = super().format(record)
        return f"[{timestamp}] [{record.levelname:<7}] [{record.name}]{context_str} {formatted_msg}"


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for production log collection systems."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "correlation_id": getattr(record, "correlation_id", None),
            "transaction_id": getattr(record, "transaction_id", None),
            "investigation_id": getattr(record, "investigation_id", None),
            "case_id": getattr(record, "case_id", None),
        }

        # Filter out keys with None values
        filtered_entry = {k: v for k, v in log_entry.items() if v is not None and v != "-"}

        if record.exc_info:
            filtered_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(filtered_entry)


def setup_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    """Initialize structured logging for root and application loggers."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        new_handler: logging.Handler = logging.StreamHandler(sys.stdout)
        new_handler.setLevel(level)

        if log_format.lower() == "json":
            formatter: logging.Formatter = JSONFormatter()
        else:
            formatter = ConsoleFormatter("%(message)s")

        new_handler.setFormatter(formatter)
        new_handler.addFilter(ContextFilter())
        root_logger.addHandler(new_handler)
    else:
        for handler in root_logger.handlers:
            handler.setLevel(level)
            if not any(isinstance(f, ContextFilter) for f in handler.filters):
                handler.addFilter(ContextFilter())

    # Ensure uvicorn loggers adopt standard level without silencing errors
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("app").setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with contextual structured logging."""
    return logging.getLogger(name)
