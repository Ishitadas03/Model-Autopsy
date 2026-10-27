"""Artifact reference and reproducibility manifest schemas."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field

from model_autopsy.schemas.base import SchemaBase


class ArtifactReferenceSchema(SchemaBase):
    """Metadata reference to a persisted scientific artifact."""

    key: str = Field(description="Logical identifier for the artifact (e.g. 'aggregate_csv').")
    filename: str = Field(description="Basename of the file (e.g. 'aggregate_comparison.csv').")
    relative_path: str = Field(
        alias="relativePath",
        description="Path relative to the experiment artifact directory.",
    )
    format: Literal["json", "csv", "png", "markdown", "text"] = Field(
        description="Serialization file format."
    )
    size_bytes: int = Field(alias="sizeBytes", ge=0, description="File size on disk in bytes.")


class EnvironmentMetadataSchema(SchemaBase):
    """Execution software and hardware runtime environment."""

    python_version: str = Field(description="Python interpreter version.")
    platform: str = Field(description="Operating system platform details.")
    os_system: Optional[str] = Field(default=None, description="OS name.")
    architecture: Optional[str] = Field(default=None, description="Machine architecture.")
    package_versions: Dict[str, str] = Field(
        default_factory=dict,
        description="Exact package versions for core dependencies.",
    )


class ArtifactManifestSchema(SchemaBase):
    """Machine-readable reproducibility manifest matching canonical manifest.json."""

    experiment_id: str = Field(description="Unique experiment ID.")
    protocol_version: str = Field(description="Protocol specification version.")
    timestamp_utc: str = Field(description="ISO 8601 UTC execution timestamp.")
    git_commit_hash: Optional[str] = Field(
        default=None,
        description="Git commit SHA-1 at execution time.",
    )
    environment: EnvironmentMetadataSchema = Field(
        description="Software environment and package versions."
    )
    dataset_metadata: Dict[str, Any] = Field(
        description="Dataset summary, partition shapes, and SHA-256 fingerprint."
    )
    models_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Model architecture and hyperparameter configurations.",
    )
    seeds_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="PRNG seeds evaluated.",
    )
    evaluation_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Thresholds and metric configurations.",
    )
    tested_models: Optional[List[str]] = Field(
        default=None,
        description="List of tested model identifiers.",
    )
    tested_corruptions: Optional[List[str]] = Field(
        default=None,
        description="List of tested corruption identifiers.",
    )
    artifacts: List[ArtifactReferenceSchema] = Field(
        default_factory=list,
        description="Indexed list of generated artifact files.",
    )
