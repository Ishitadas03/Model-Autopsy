"""Structured logging configuration."""

import json
import logging
import sys
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger

from backend.app.core.config import settings


class StructuredLogger(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(
        self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = self.formatTime(record)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "name", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "timestamp",
            ]:
                log_record[key] = value


def setup_logging() -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.DEBUG:
        # Human-readable format for development
        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # JSON format for production
        console_formatter = StructuredLogger(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin to add logger property to classes."""

    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__module__ + "." + self.__class__.__name__)
        return self._logger


# Context variables for request tracking
import contextvars

request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)
experiment_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("experiment_id", default=None)


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.experiment_id = experiment_id_var.get()
        return True


def set_request_context(request_id: Optional[str] = None, experiment_id: Optional[str] = None) -> None:
    """Set request context for logging."""
    if request_id:
        request_id_var.set(request_id)
    if experiment_id:
        experiment_id_var.set(experiment_id)


def clear_request_context() -> None:
    """Clear request context."""
    request_id_var.set(None)
    experiment_id_var.set(None)