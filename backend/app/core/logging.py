"""Structured logging configuration for Model Autopsy API."""
import logging
import logging.config
from typing import Any, Dict, Optional

from pydantic import BaseModel


class RequestContext(BaseModel):
    """Container for request-specific context data."""
    request_id: str
    path: str
    method: str


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Adapter to inject request context into log records."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        request_context = getattr(self, "_request_context", None)
        if request_context:
            extra = {
                "request_id": request_context.request_id,
                "path": request_context.path,
                "method": request_context.method,
            }
            kwargs.setdefault("extra", {})
            kwargs["extra"].update(extra)
        return msg, kwargs


def setup_logging() -> None:
    """Configure structured JSON logging for the application."""
    logging.config.dictConfig({
        "version": 1,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(asctime)s [%(levelname)s] [%(name)s] [%(request_id)s] %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": "INFO",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    })


class RequestContextFilter(logging.Filter):
    """Filter that injects request context into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        context = get_request_context()
        record.request_id = context.request_id if context else "-"
        record.path = context.path if context else "-"
        record.method = context.method if context else "-"
        return True


def clear_request_context() -> None:
    """Clear the current request context."""
    global _request_context
    _request_context = None


def set_request_context(request_id: str, path: str = "", method: str = "") -> None:
    """Set the current request context for logging."""
    global _request_context
    _request_context = RequestContext(request_id=request_id, path=path, method=method)


def get_logger(name: str = "") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# Request context management for FastAPI middleware
_request_context: Optional[RequestContext] = None


def init_request_context(request_id: str, path: str = "", method: str = "") -> None:
    """Initialize request context."""
    global _request_context
    _request_context = RequestContext(request_id=request_id, path=path, method=method)


def get_request_context() -> Optional[RequestContext]:
    """Get current request context."""
    return _request_context