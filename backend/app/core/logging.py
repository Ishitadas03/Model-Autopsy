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


# Request context management for FastAPI middleware
_request_context: Optional[RequestContext] = None


def get_request_context() -> Optional[RequestContext]:
    """Get current request context."""
    return _request_context


def set_request_context(request_id: str, path: str = "", method: str = "") -> None:
    """Set the current request context for logging."""
    global _request_context
    _request_context = RequestContext(request_id=request_id, path=path, method=method)


def clear_request_context() -> None:
    """Clear the current request context."""
    global _request_context
    _request_context = None


def init_request_context(request_id: str, path: str = "", method: str = "") -> None:
    """Initialize request context."""
    set_request_context(request_id, path, method)


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Adapter to inject request context and arbitrary kwargs into extra."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        extra = dict(kwargs.get("extra") or {})
        standard_kwargs = {"exc_info", "stack_info", "stacklevel", "extra"}
        custom_kwargs = {k: v for k, v in list(kwargs.items()) if k not in standard_kwargs}
        for k in custom_kwargs:
            kwargs.pop(k, None)
        extra.update(custom_kwargs)

        request_context = get_request_context()
        if request_context:
            extra["request_id"] = request_context.request_id
            extra["path"] = request_context.path
            extra["method"] = request_context.method

        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging() -> None:
    """Configure structured JSON logging for the application."""
    formatter_cls = "pythonjsonlogger.jsonlogger.JsonFormatter"
    try:
        import pythonjsonlogger.jsonlogger  # noqa: F401
    except ImportError:
        formatter_cls = "pythonjsonlogger.json.JsonFormatter"

    logging.config.dictConfig({
        "version": 1,
        "formatters": {
            "json": {
                "()": formatter_cls,
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
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    })


class RequestContextFilter(logging.Filter):
    """Filter to ensure request_id is always present in log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def get_logger(name: str = "") -> StructuredLoggerAdapter:
    """Get a structured logger instance."""
    return StructuredLoggerAdapter(logging.getLogger(name), {})
