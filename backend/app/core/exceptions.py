"""Custom exceptions and error handlers."""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelAutopsyException(Exception):
    """Base exception for Model Autopsy application."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ExperimentNotFoundError(ModelAutopsyException):
    """Raised when experiment is not found."""

    def __init__(self, experiment_id: str):
        super().__init__(
            message=f"Experiment '{experiment_id}' not found",
            error_code="EXPERIMENT_NOT_FOUND",
            details={"experiment_id": experiment_id},
        )


class ExperimentAlreadyRunningError(ModelAutopsyException):
    """Raised when trying to start an already running experiment."""

    def __init__(self, experiment_id: str):
        super().__init__(
            message=f"Experiment '{experiment_id}' is already running",
            error_code="EXPERIMENT_ALREADY_RUNNING",
            details={"experiment_id": experiment_id},
        )


class ExperimentExecutionError(ModelAutopsyException):
    """Raised when experiment execution fails."""

    def __init__(self, experiment_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Experiment '{experiment_id}' execution failed: {reason}",
            error_code="EXPERIMENT_EXECUTION_FAILED",
            details={"experiment_id": experiment_id, "reason": reason, **(details or {})},
        )


class InvalidExperimentConfigError(ModelAutopsyException):
    """Raised when experiment configuration is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_EXPERIMENT_CONFIG",
            details=details or {},
        )


class ArtifactNotFoundError(ModelAutopsyException):
    """Raised when artifact is not found."""

    def __init__(self, artifact_id: str):
        super().__init__(
            message=f"Artifact '{artifact_id}' not found",
            error_code="ARTIFACT_NOT_FOUND",
            details={"artifact_id": artifact_id},
        )


class DatabaseError(ModelAutopsyException):
    """Raised when database operation fails."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={"original_error": str(original_error)} if original_error else {},
        )


class ConcurrencyLimitError(ModelAutopsyException):
    """Raised when max concurrent experiments limit is reached."""

    def __init__(self, max_concurrent: int):
        super().__init__(
            message=f"Maximum concurrent experiments limit ({max_concurrent}) reached",
            error_code="CONCURRENCY_LIMIT_EXCEEDED",
            details={"max_concurrent": max_concurrent},
        )


# HTTP Exception handlers
def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with FastAPI app."""

    @app.exception_handler(ModelAutopsyException)
    async def model_autopsy_exception_handler(
        request: Request, exc: ModelAutopsyException
    ) -> JSONResponse:
        logger.error(
            "Application error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(ExperimentNotFoundError)
    async def experiment_not_found_handler(
        request: Request, exc: ExperimentNotFoundError
    ) -> JSONResponse:
        logger.warning("Experiment not found", experiment_id=exc.details.get("experiment_id"))
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(ExperimentAlreadyRunningError)
    async def experiment_already_running_handler(
        request: Request, exc: ExperimentAlreadyRunningError
    ) -> JSONResponse:
        logger.warning("Experiment already running", experiment_id=exc.details.get("experiment_id"))
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(InvalidExperimentConfigError)
    async def invalid_experiment_config_handler(
        request: Request, exc: InvalidExperimentConfigError
    ) -> JSONResponse:
        logger.warning("Invalid experiment config", details=exc.details)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(ArtifactNotFoundError)
    async def artifact_not_found_handler(
        request: Request, exc: ArtifactNotFoundError
    ) -> JSONResponse:
        logger.warning("Artifact not found", artifact_id=exc.details.get("artifact_id"))
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(ConcurrencyLimitError)
    async def concurrency_limit_handler(
        request: Request, exc: ConcurrencyLimitError
    ) -> JSONResponse:
        logger.warning("Concurrency limit exceeded", max_concurrent=exc.details.get("max_concurrent"))
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        logger.warning("Validation error", errors=exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": exc.errors()},
                }
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        logger.error("Database integrity error", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "INTEGRITY_ERROR",
                    "message": "Database constraint violation",
                    "details": {"constraint": str(exc.orig) if exc.orig else "unknown"},
                }
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.error("Database error", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "Database operation failed",
                    "details": {},
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": {},
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                }
            },
        )