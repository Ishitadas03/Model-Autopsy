"""Dataset and model catalog schemas for Model Autopsy platform."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field

from model_autopsy.schemas.base import SchemaBase
from model_autopsy.schemas.enums import TaskType


class DatasetFeatureSchema(SchemaBase):
    """Schema representing an individual feature in a dataset."""

    name: str = Field(description="Name of the feature.")
    type: Literal["numeric", "categorical", "boolean"] = Field(
        description="Feature data type classification."
    )
    missing_count: int = Field(
        default=0,
        alias="missingCount",
        ge=0,
        description="Count of missing or null values in this feature.",
    )


class DatasetSchema(SchemaBase):
    """Schema representing a benchmark or uploaded dataset."""

    id: str = Field(description="Unique dataset identifier.")
    name: str = Field(description="Human-readable dataset title.")
    description: str = Field(description="Detailed dataset description.")
    sample_count: int = Field(
        alias="sampleCount",
        gt=0,
        description="Total number of instances in the dataset.",
    )
    feature_count: int = Field(
        alias="featureCount",
        gt=0,
        description="Total number of features in the dataset.",
    )
    class_count: Optional[int] = Field(
        default=None,
        alias="classCount",
        gt=0,
        description="Number of target classes for classification tasks.",
    )
    task_type: TaskType = Field(
        alias="taskType",
        description="Primary machine learning task type.",
    )
    is_custom: bool = Field(
        default=False,
        alias="isCustom",
        description="Whether the dataset was uploaded by a user.",
    )
    features: List[DatasetFeatureSchema] = Field(
        default_factory=list,
        description="Ordered list of feature specifications.",
    )


class ModelAdapterSchema(SchemaBase):
    """Schema representing an estimator or architecture adapter."""

    id: str = Field(description="Unique model adapter identifier.")
    name: str = Field(description="Human-readable model name.")
    framework: Literal["scikit-learn"] = Field(
        default="scikit-learn",
        description="Underlying ML framework.",
    )
    task_types: List[TaskType] = Field(
        alias="taskTypes",
        description="Supported ML task types.",
    )
    predict_proba: bool = Field(
        alias="predictProba",
        description="Whether the adapter supports probability estimation.",
    )
    description: str = Field(description="Overview of model architecture and inductive biases.")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default or active hyperparameters for the estimator.",
    )
