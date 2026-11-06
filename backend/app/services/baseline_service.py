"""Baseline evaluation service for Model Autopsy."""

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
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
from app.services.storage_service import storage_service

logger = get_logger(__name__)


class BaselineEvaluationRequest(BaseModel):
    """Request schema for evaluating a model baseline."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    dataset_id: str = Field(alias="datasetId")
    model_id: str = Field(default="random-forest-classifier", alias="modelId")
    task_type: Optional[str] = Field(default="classification", alias="taskType")
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

        # Resolve target and task type
        target_col = request.target_name if request.target_name and request.target_name in df.columns else detected_target
        task_type = (request.task_type or inferred_task or "classification").lower()
        is_classification = task_type == "classification"

        if target_col not in df.columns:
            target_col = df.columns[-1]

        y_raw = df[target_col]
        X_raw = df.drop(columns=[target_col])
        feature_names = list(X_raw.columns)

        if len(feature_names) == 0:
            raise ValueError(f"Dataset has no feature columns after removing target column '{target_col}'")

        # 2. Preprocess feature columns
        numeric_cols = list(X_raw.select_dtypes(include=[np.number]).columns)
        categorical_cols = [c for c in feature_names if c not in numeric_cols]

        X_processed = pd.DataFrame(index=X_raw.index)

        # Handle numeric features
        if numeric_cols:
            num_imputer = SimpleImputer(strategy="median")
            X_num = num_imputer.fit_transform(X_raw[numeric_cols])
            for i, col in enumerate(numeric_cols):
                X_processed[col] = X_num[:, i]

        # Handle categorical features via one-hot or frequency encoding
        if categorical_cols:
            cat_imputer = SimpleImputer(strategy="most_frequent")
            X_cat = cat_imputer.fit_transform(X_raw[categorical_cols])
            for i, col in enumerate(categorical_cols):
                le = LabelEncoder()
                X_processed[col] = le.fit_transform(X_cat[:, i].astype(str))

        # 3. Preprocess target
        if is_classification:
            le_target = LabelEncoder()
            y_processed = le_target.fit_transform(y_raw.astype(str))
            classes = [str(c) for c in le_target.classes_]
        else:
            y_processed = pd.to_numeric(y_raw, errors="coerce").fillna(0.0).values.astype(np.float64)
            classes = []

        X_mat = X_processed.values.astype(np.float64)
        y_vec = y_processed

        # 4. Stratified or random hold-out split
        test_size = max(0.05, min(0.50, float(request.test_size)))
        seed = int(request.seed)

        stratify = None
        if is_classification and len(classes) > 1:
            # Check minimum class count for stratification
            _, class_counts = np.unique(y_vec, return_counts=True)
            if np.all(class_counts >= 2):
                stratify = y_vec

        X_train, X_test, y_train, y_test = train_test_split(
            X_mat,
            y_vec,
            test_size=test_size,
            random_state=seed,
            stratify=stratify,
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

        target_col = target_name or (db_ds.target_name if db_ds else None) or "target"
        task_type = (db_ds.task_type if db_ds else None) or "classification"

        # Try storage service
        object_key = f"datasets/{dataset_id}/data.csv"
        raw_bytes = storage_service.get_object(object_key)

        if raw_bytes is None and db_ds and db_ds.metadata_:
            storage_key = db_ds.metadata_.get("storage_key")
            if storage_key:
                raw_bytes = storage_service.get_object(storage_key)

        if raw_bytes is not None:
            df = pd.read_csv(io.BytesIO(raw_bytes))
            return df, target_col, task_type

        # Check local filesystem fallback paths
        local_candidates = [
            Path(f"data/datasets/{dataset_id}/data.csv"),
            Path(f"data/{dataset_id}.csv"),
            Path(f"datasets/{dataset_id}.csv"),
        ]
        for p in local_candidates:
            if p.exists():
                df = pd.read_csv(p)
                return df, target_col, task_type

        # Fallback to Iris if synthetic demo
        from sklearn.datasets import load_iris
        raw_iris = load_iris(as_frame=True)
        return raw_iris.frame, "target", "classification"

    def _instantiate_model(
        self, model_id: str, is_classification: bool, seed: int, params: Dict[str, Any]
    ) -> Any:
        """Instantiate scikit-learn model with parameters."""
        m_id = model_id.lower()

        if is_classification:
            if "random" in m_id or "rf" in m_id:
                n_est = int(params.get("n_estimators", 100))
                max_d = int(params["max_depth"]) if params.get("max_depth") else None
                return RandomForestClassifier(n_estimators=n_est, max_depth=max_d, random_state=seed)
            if "logistic" in m_id or "lr" in m_id:
                c_val = float(params.get("C", 1.0))
                return LogisticRegression(C=c_val, max_iter=500, random_state=seed)
            if "gradient" in m_id or "gb" in m_id:
                n_est = int(params.get("n_estimators", 100))
                lr = float(params.get("learning_rate", 0.1))
                return GradientBoostingClassifier(n_estimators=n_est, learning_rate=lr, random_state=seed)
            if "svm" in m_id or "svc" in m_id:
                c_val = float(params.get("C", 1.0))
                return SVC(C=c_val, probability=True, random_state=seed)
            return RandomForestClassifier(n_estimators=100, random_state=seed)
        else:
            if "random" in m_id or "rf" in m_id:
                return RandomForestRegressor(n_estimators=100, random_state=seed)
            if "gradient" in m_id or "gb" in m_id:
                return GradientBoostingRegressor(n_estimators=100, random_state=seed)
            if "ridge" in m_id:
                alpha = float(params.get("alpha", 1.0))
                return Ridge(alpha=alpha, random_state=seed)
            if "svm" in m_id or "svr" in m_id:
                return SVR()
            return LinearRegression()


baseline_service = BaselineService()
