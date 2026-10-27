"""Base schema configuration for Model Autopsy Pydantic models."""

from pydantic import BaseModel, ConfigDict


class SchemaBase(BaseModel):
    """Base Pydantic model with dataclass compatibility and population by name/alias."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        validate_assignment=True,
        extra="forbid",
    )
