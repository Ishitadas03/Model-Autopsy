"""Baseline evaluation service for Model Autopsy."""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
)
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.svm import SVC, SVR
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from app.core.logging import get_logger
from app.repositories.dataset import DatasetRepository
from app.services.preprocessing import prepare_holdout
from app.services.model_limits import validate_model_params
from app.services.dataset_loader import load_registered_csv

logger = get_logger(__name__)


class BaselineEvaluationRequest(BaseModel):
    """Request schema for evaluating a model baseline."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    dataset_id: str = Field(alias="datasetId")
    model_id: str = Field(default="random-forest-classifier", alias="modelId")
    task_type: Optional[str] = Field(default=None, alias="taskType")
    test_size: float = Field(default=0.2, alias="testSize")
    seed: int = Field(default=42)
    target_name: Optional[str] = Field(default=None, alias="targetName")
    model_params: Dict[str, Any] = Field(default_factory=dict, alias="modelParams")


class BaselineEvaluationResponse(BaseModel):
    """Response schema for baseline evaluation."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    dataset_id: str = Field(alias="datasetId")
    model_id: str = Field(alias="modelId")
    task_type: str = Field(alias="taskType")
    sample_count: int = Field(alias="sampleCount")
    train_count: int = Field(alias="trainCount")
    test_count: int = Field(alias="testCount")
    target_name: str = Field(alias="targetName")
    feature_names: List[str] = Field(alias="featureNames")
    metrics: Dict[str, Any]


class BaselineService:
    """Service to train and evaluate reproducible baseline models."""

    async def evaluate_baseline(
        self, request: BaselineEvaluationRequest, session: AsyncSession
    ) -> BaselineEvaluationResponse:
        """Execute true hold-out baseline training and evaluation."""
        logger.info(
            "Evaluating baseline",
            dataset_id=request.dataset_id,
            model_id=request.model_id,
            task_type=request.task_type,
            seed=request.seed,
        )

        # 1. Load dataset DataFrame
        df, detected_target, inferred_task = await self._load_dataframe(
            request.dataset_id, request.target_name, session
        )

        return await asyncio.to_thread(self._evaluate_dataframe, request, df, detected_target, inferred_task)

    def _evaluate_dataframe(
        self, request: BaselineEvaluationRequest, df: pd.DataFrame,
        detected_target: str, inferred_task: str,
    ) -> BaselineEvaluationResponse:
        # Training must not block queue heartbeats and other ASGI requests.
        if request.task_type and request.task_type != inferred_task:
            raise ValueError("Task type must match the registered dataset")
        if request.target_name and request.target_name != detected_target:
            raise ValueError("Target must match the registered dataset")
        # Resolve target and task type
        target_col = request.target_name if request.target_name and request.target_name in df.columns else detected_target
        task_type = (request.task_type or inferred_task or "classification").lower()
        is_classification = task_type == "classification"

        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' does not exist in dataset '{request.dataset_id}'")

        X_raw = df.drop(columns=[target_col])
        feature_names = list(X_raw.columns)

        if len(feature_names) == 0:
            raise ValueError(f"Dataset has no feature columns after removing target column '{target_col}'")

        if task_type not in ("classification", "regression"):
            raise ValueError(f"Unsupported task type '{task_type}'")
        # Split first; impute and encode features using training samples only.
        test_size = float(request.test_size)
        seed = int(request.seed)
        X_train, X_test, y_train, y_test, classes, feature_names = prepare_holdout(
            df, target_col, task_type, test_size, seed,
        )

        # 5. Instantiate model adapter
        model = self._instantiate_model(
            model_id=request.model_id,
            is_classification=is_classification,
            seed=seed,
            params=request.model_params,
        )

        # 6. Fit and evaluate
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        # 7. Compute metrics
        metrics: Dict[str, Any] = {}
        if is_classification:
            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
            rec = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
            f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
            cm = confusion_matrix(y_test, y_pred).tolist()

            metrics = {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4),
                "confusion_matrix": cm,
                "classes": classes,
            }
        else:
            mae = float(mean_absolute_error(y_test, y_pred))
            mse = float(mean_squared_error(y_test, y_pred))
            rmse = float(np.sqrt(mse))
            r2 = float(r2_score(y_test, y_pred))

            metrics = {
                "mae": round(mae, 4),
                "mse": round(mse, 4),
                "rmse": round(rmse, 4),
                "r2": round(r2, 4),
            }

        return BaselineEvaluationResponse(
            datasetId=request.dataset_id,
            modelId=request.model_id,
            taskType=task_type,
            sampleCount=len(df),
            trainCount=len(X_train),
            testCount=len(X_test),
            targetName=target_col,
            featureNames=feature_names,
            metrics=metrics,
        )

    async def _load_dataframe(
        self, dataset_id: str, target_name: Optional[str], session: AsyncSession
    ) -> Tuple[pd.DataFrame, str, str]:
        """Load DataFrame from built-in benchmarks or storage."""
        clean_id = dataset_id.lower().strip()

        if clean_id in ("iris", "iris-dataset", "fisher-iris"):
            from sklearn.datasets import load_iris
            raw_iris = load_iris(as_frame=True)
            df = raw_iris.frame
            return df, "target", "classification"

        # Check database
        repo = DatasetRepository(session)
        db_ds = await repo.get_by_dataset_id(dataset_id)

        target_col = (db_ds.target_name if db_ds else None) or "target"
        task_type = (db_ds.task_type if db_ds else None) or "classification"

        metadata = db_ds.metadata_ if db_ds and db_ds.metadata_ else {}
        df = await asyncio.to_thread(
            load_registered_csv, dataset_id,
            metadata.get("storage_key"), metadata.get("sha256"),
        )
        return df, target_col, task_type

    def _instantiate_model(
        self, model_id: str, is_classification: bool, seed: int, params: Dict[str, Any]
    ) -> Any:
        """Use only bounded supported hyperparameters; no arbitrary fallback."""
        task = "classification" if is_classification else "regression"
        p = validate_model_params(model_id, task, params)
        m_id = model_id.lower()

        if is_classification:
            if "random" in m_id or "rf" in m_id:
                return RandomForestClassifier(
                    n_estimators=p.get("n_estimators", 100),
                    max_depth=p.get("max_depth"),
                    min_samples_split=p.get("min_samples_split", 2),
                    random_state=seed,
                )
            if "logistic" in m_id or "lr" in m_id:
                return LogisticRegression(
                    C=p.get("C", 1.0), max_iter=p.get("max_iter", 500),
                    penalty=p.get("penalty", "l2"),
                    solver=p.get("solver", "lbfgs"),
                    random_state=seed,
                )
            if "gradient" in m_id or "gb" in m_id:
                return GradientBoostingClassifier(
                    n_estimators=p.get("n_estimators", 100),
                    learning_rate=p.get("learning_rate", 0.1),
                    max_depth=p.get("max_depth", 3),
                    random_state=seed,
                )
            if "svm" in m_id or "svc" in m_id:
                return SVC(
                    C=p.get("C", 1.0), kernel=p.get("kernel", "rbf"),
                    gamma=p.get("gamma", "scale"),
                    probability=True, random_state=seed,
                )
        else:
            if "random" in m_id or "rf" in m_id:
                return RandomForestRegressor(
                    n_estimators=p.get("n_estimators", 100),
                    max_depth=p.get("max_depth"),
                    min_samples_split=p.get("min_samples_split", 2),
                    random_state=seed,
                )
            if "gradient" in m_id or "gb" in m_id:
                return GradientBoostingRegressor(
                    n_estimators=p.get("n_estimators", 100),
                    learning_rate=p.get("learning_rate", 0.1),
                    max_depth=p.get("max_depth", 3),
                    random_state=seed,
                )
            if "ridge" in m_id:
                return Ridge(alpha=p.get("alpha", 1.0), random_state=seed)
            if "svr" in m_id or "svm" in m_id:
                return SVR(
                    C=p.get("C", 1.0), kernel=p.get("kernel", "rbf"),
                    gamma=p.get("gamma", "scale"),
                )
            if "linear" in m_id:
                return LinearRegression(fit_intercept=p.get("fit_intercept", True))

        raise ValueError(f"Unsupported model adapter: {model_id}")


baseline_service = BaselineService()
