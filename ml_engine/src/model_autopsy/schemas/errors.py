"""Structured API error responses and validation error representations."""

from datetime import datetime, timezone
from typing import Any, List, Optional, Union
from pydantic import Field

from model_autopsy.schemas.base import SchemaBase


class ValidationErrorItem(SchemaBase):
    """Field-specific parameter validation failure detail."""

    loc: List[Union[str, int]] = Field(description="JSON pointer path to invalid field.")
    msg: str = Field(description="Descriptive reason why validation failed.")
    type: str = Field(description="Validation error type identifier.")
    input: Optional[Any] = Field(default=None, description="Supplied invalid input value.")


class ApiErrorResponse(SchemaBase):
    """Canonical error envelope returned for non-2xx API responses."""

    error: str = Field(description="High-level category or summary of the error.")
    code: str = Field(
        description="Machine-readable structured error code (e.g. 'NOT_FOUND', 'VALIDATION_ERROR')."
    )
    detail: Optional[str] = Field(
        default=None,
        description="Detailed contextual message explaining the failure.",
    )
    validation_errors: Optional[List[ValidationErrorItem]] = Field(
        default=None,
        alias="validationErrors",
        description="Detailed list of field-level validation errors, if applicable.",
    )
    experiment_id: Optional[str] = Field(
        default=None,
        alias="experimentId",
        description="Associated experiment identifier, if applicable.",
    )
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        alias="timestampUtc",
        description="UTC ISO timestamp when error was generated.",
    )
