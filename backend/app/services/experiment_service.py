"""Experiment service for managing experiment lifecycle."""

import asyncio
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import Base
from backend.app.core.exceptions import (
    ConcurrencyLimitError,
    ExperimentAlreadyRunningError,
    ExperimentExecutionError,
    ExperimentNotFoundError,
    InvalidExperimentConfigError,
)
from backend.app.core.logging import get_logger
from backend.app.models.experiment import (
    Experiment,
    ExperimentRun,
    ExperimentResult,
    ExperimentStatus,
    StressMode,
    StressType,
    TaskType,
)
from backend.app.models.failure_sample import FailedSample
from backend.app.models.artifact import ArtifactManifest, ArtifactReference, ArtifactType
from backend.app.repositories.experiment import ExperimentRepository, ExperimentRunRepository, ExperimentResultRepository
from backend.app.repositories.failure_sample import FailureSampleRepository
from backend.app.repositories.artifact import ArtifactRepository
from backend.app.services.ml_engine_bridge import ml_engine_bridge, ProgressData
from backend.app.schemas import ExperimentRunRequest

logger = get_logger(__name__)


class ExperimentService:
    """Service for managing experiment lifecycle."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.exp_repo = ExperimentRepository(session)
        self.run_repo = ExperimentRunRepository(session)
        self.result_repo = ExperimentResultRepository(session)
        self.fail_repo = FailureSampleRepository(session)
        self.artifact_repo = ArtifactRepository(session)
        self._running_experiments: Dict[str, asyncio.Task] = {}

    async def create_experiment(self, request: ExperimentRunRequest) -> Experiment:
        """Create and queue a new experiment."""
        # Check concurrency limit
        running = await self.exp_repo.get_running_experiments()
        if len(running) >= settings.MAX_CONCURRENT_EXPERIMENTS:
            raise ConcurrencyLimitError(settings.MAX_CONCURRENT_EXPERIMENTS)

        # Generate experiment ID
        experiment_id = await self.exp_repo.get_next_experiment_id()

        # Determine experiment type from perturbation family
        experiment_type = self._get_experiment_type(request.perturbationFamily)

        # Build severity levels
        severity_levels = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
        seeds = request.seeds or settings.DEFAULT_SEEDS

        # Generate config YAML
        config_yaml = self._generate_config_yaml(request, experiment_id, severity_levels, seeds)

        # Create experiment record
        experiment = await self.exp_repo.create(
            experiment_id=experiment_id,
            model_name=request.modelName,
            dataset_name=request.datasetName,
            dataset_id=request.datasetId,
            task_type=TaskType(request.taskType),
            perturbation_family=StressType(request.perturbationFamily),
            noise_type=request.noiseType,
            evaluation_metric=request.evaluationMetric,
            failure_threshold=request.failureThreshold,
            seed=request.seed,
            stress_mode=StressMode(request.stressMode) if request.stressMode else StressMode.INCREMENTAL,
            severity_levels=severity_levels,
            seeds=seeds,
            config_yaml=config_yaml,
            status=ExperimentStatus.QUEUED,
        )

        # Create experiment runs for each seed
        for i, seed in enumerate(seeds):
            await self.run_repo.create(
                experiment_id=experiment.id,
                seed=seed,
                run_index=i,
                status=ExperimentStatus.QUEUED,
            )

        # Queue background execution
        task = asyncio.create_task(self._run_experiment_background(experiment.id, experiment_type, request))
        self._running_experiments[str(experiment.id)] = task

        logger.info(
            "Experiment created and queued",
            experiment_id=experiment_id,
            db_id=str(experiment.id),
        )

        return experiment

    def _get_experiment_type(self, perturbation_family: str) -> str:
        """Map perturbation family to experiment type."""
        mapping = {
            "gaussian_noise": "e001",
            "mcar_missingness": "e002",
            "outlier_contamination": "e003",
            "multi_corruption": "e002",  # E002 handles multiple
            "cross_model": "e003",
            "failure_patterns": "e004",
        }
        return mapping.get(perturbation_family, "e001")

    def _generate_config_yaml(
        self, request: ExperimentRunRequest, experiment_id: str, severity_levels: List[float], seeds: List[int]
    ) -> str:
        """Generate YAML config for the experiment."""
        import yaml

        config = {
            "experiment": {
                "name": experiment_id,
                "model": {
                    "name": request.modelName,
                    "type": "sklearn_rf",  # Default, would be determined from model adapter
                    "hyperparameters": {"n_estimators": 100, "random_state": request.seed},
                },
                "dataset": {
                    "name": request.datasetName,
                    "id": request.datasetId,
                },
                "stress_test": {
                    "perturbation_family": request.perturbationFamily,
                    "severity_levels": severity_levels,
                    "stress_mode": request.stressMode or "incremental",
                },
                "evaluation": {
                    "metric": request.evaluationMetric,
                    "failure_threshold": request.failureThreshold,
                },
                "seeds": seeds,
                "reproducibility": {
                    "save_artifacts": True,
                },
            }
        }

        return yaml.dump(config, default_flow_style=False)

    async def _run_experiment_background(
        self, experiment_db_id: uuid.UUID, experiment_type: str, request: ExperimentRunRequest
    ) -> None:
        """Background task to run experiment."""
        try:
            # Update status to running
            experiment = await self.exp_repo.get_by_id(experiment_db_id)
            if not experiment:
                logger.error("Experiment not found", experiment_db_id=str(experiment_db_id))
                return

            experiment.status = ExperimentStatus.RUNNING
            experiment.started_at = datetime.utcnow()
            experiment.progress_percent = 0
            await self.session.flush()

            # Update first run to running
            runs = await self.run_repo.get_by_experiment(experiment_db_id)
            if runs:
                runs[0].status = ExperimentStatus.RUNNING
                runs[0].started_at = datetime.utcnow()
                await self.session.flush()

            # Prepare request data for ML engine
            request_data = {
                "experiment_id": experiment.experiment_id,
                "model_name": request.modelName,
                "dataset_name": request.datasetName,
                "dataset_id": request.datasetId,
                "perturbation_family": request.perturbationFamily,
                "evaluation_metric": request.evaluationMetric,
                "failure_threshold": request.failureThreshold,
                "stress_mode": request.stressMode or "incremental",
                "severity_levels": experiment.severity_levels,
                "seeds": experiment.seeds,
            }

            # Progress callback
            async def progress_callback(progress: ProgressData):
                await self._update_progress(experiment_db_id, progress)

            # Run experiment
            result = await ml_engine_bridge.run_experiment(
                experiment_id=experiment.experiment_id,
                experiment_type=experiment_type,
                request_data=request_data,
                progress_callback=progress_callback,
            )

            # Process results
            await self._process_results(experiment_db_id, result)

            # Mark as completed
            experiment = await self.exp_repo.get_by_id(experiment_db_id)
            experiment.status = ExperimentStatus.COMPLETED
            experiment.completed_at = datetime.utcnow()
            experiment.progress_percent = 100
            await self.session.flush()

            # Mark all runs as completed
            for run in runs:
                run.status = ExperimentStatus.COMPLETED
                run.completed_at = datetime.utcnow()
                run.progress_percent = 100
            await self.session.flush()

            logger.info("Experiment completed", experiment_id=experiment.experiment_id)

        except asyncio.CancelledError:
            logger.info("Experiment cancelled", experiment_db_id=str(experiment_db_id))
            await self._mark_experiment_cancelled(experiment_db_id)
            raise
        except Exception as e:
            logger.exception("Experiment failed", experiment_db_id=str(experiment_db_id))
            await self._mark_experiment_failed(experiment_db_id, str(e))
            raise ExperimentExecutionError(
                experiment_id=str(experiment_db_id),
                reason=str(e),
            )
        finally:
            # Clean up running experiments tracking
            self._running_experiments.pop(str(experiment_db_id), None)

    async def _update_progress(self, experiment_db_id: uuid.UUID, progress: ProgressData) -> None:
        """Update experiment progress."""
        experiment = await self.exp_repo.get_by_id(experiment_db_id)
        if experiment:
            experiment.progress_percent = progress.progress
            experiment.current_seed_index = progress.seed_index if hasattr(progress, 'seed_index') else 0
            experiment.current_severity_index = progress.severity_index if hasattr(progress, 'severity_index') else 0
            await self.session.flush()

            # Update current run
            runs = await self.run_repo.get_by_experiment(experiment_db_id)
            if runs and progress.seed is not None:
                for run in runs:
                    if run.seed == progress.seed:
                        run.status = ExperimentStatus.RUNNING
                        run.progress_percent = progress.progress
                        run.current_severity = progress.severity
                        await self.session.flush()
                        break

    async def _process_results(
        self, experiment_db_id: uuid.UUID, result_data: Dict[str, Any]
    ) -> None:
        """Process and store experiment results."""
        experiment = await self.exp_repo.get_by_id(experiment_db_id)
        if not experiment:
            return

        results = result_data.get("results", {})
        artifacts = result_data.get("artifacts", [])

        # Create ExperimentResult
        exp_result = await self.result_repo.create(
            experiment_id=experiment_db_id,
            baseline_macro_f1=results.get("baseline_macro_f1"),
            baseline_accuracy=results.get("baseline_accuracy"),
            baseline_per_class=results.get("baseline_per_class"),
            worst_case_macro_f1=results.get("worst_case_macro_f1"),
            worst_case_accuracy=results.get("worst_case_accuracy"),
            worst_case_severity=results.get("worst_case_severity"),
            observed_boundary=results.get("observed_boundary"),
            curve_data=results.get("curve_data", []),
            feature_vulnerabilities=results.get("feature_vulnerabilities", []),
            metric_statistics=results.get("metric_statistics"),
            statistical_validation=results.get("statistical_validation"),
            failed_samples_count=results.get("failed_samples_count", 0),
            consensus_failures=results.get("consensus_failures"),
            error_persistence_rate=results.get("error_persistence_rate"),
        )

        # Store artifacts
        for artifact in artifacts:
            await self.artifact_repo.create(
                experiment_id=experiment_db_id,
                artifact_type=ArtifactType(artifact["type"]),
                seed=artifact.get("seed"),
                file_path=artifact["file_path"],
                file_name=artifact["file_name"],
                file_size_bytes=artifact["file_size"],
                content_hash=self._compute_hash(
                    settings.ARTIFACTS_BASE_DIR / artifact["file_path"]
                ),
                mime_type=self._get_mime_type(artifact["file_name"]),
            )

        # Store failed samples if available
        failed_samples = results.get("failed_samples", [])
        for sample in failed_samples:
            await self.fail_repo.create(
                experiment_id=experiment_db_id,
                sample_index=sample.get("sample_index", 0),
                sample_id=sample.get("sample_id", f"samp-{sample.get('sample_index', 0)}"),
                true_label=sample.get("true_label", ""),
                predicted_label=sample.get("predicted_label", ""),
                confidence=sample.get("confidence", 0.0),
                noise_level=sample.get("noise_level", 0.0),
                seed=sample.get("seed", 0),
                features_clean=sample.get("features_clean", {}),
                features_stressed=sample.get("features_stressed", {}),
                feature_diffs=sample.get("feature_diffs", {}),
            )

        await self.session.flush()

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        if not file_path.exists():
            return ""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename."""
        if filename.endswith(".json"):
            return "application/json"
        elif filename.endswith(".csv"):
            return "text/csv"
        elif filename.endswith(".md"):
            return "text/markdown"
        elif filename.endswith(".yaml") or filename.endswith(".yml"):
            return "application/x-yaml"
        return "application/octet-stream"

    async def _mark_experiment_cancelled(self, experiment_db_id: uuid.UUID) -> None:
        """Mark experiment as cancelled."""
        experiment = await self.exp_repo.get_by_id(experiment_db_id)
        if experiment:
            experiment.status = ExperimentStatus.CANCELLED
            experiment.completed_at = datetime.utcnow()
            await self.session.flush()

            runs = await self.run_repo.get_by_experiment(experiment_db_id)
            for run in runs:
                if run.status in [ExperimentStatus.QUEUED, ExperimentStatus.RUNNING]:
                    run.status = ExperimentStatus.CANCELLED
                    run.completed_at = datetime.utcnow()
            await self.session.flush()

    async def _mark_experiment_failed(self, experiment_db_id: uuid.UUID, error_message: str) -> None:
        """Mark experiment as failed."""
        experiment = await self.exp_repo.get_by_id(experiment_db_id)
        if experiment:
            experiment.status = ExperimentStatus.FAILED
            experiment.error_message = error_message
            experiment.completed_at = datetime.utcnow()
            await self.session.flush()

            runs = await self.run_repo.get_by_experiment(experiment_db_id)
            for run in runs:
                if run.status in [ExperimentStatus.QUEUED, ExperimentStatus.RUNNING]:
                    run.status = ExperimentStatus.FAILED
                    run.error_message = error_message
                    run.completed_at = datetime.utcnow()
            await self.session.flush()

    async def cancel_experiment(self, experiment_db_id: uuid.UUID) -> None:
        """Cancel a running experiment."""
        experiment = await self.exp_repo.get_by_id(experiment_db_id)
        if not experiment:
            raise ExperimentNotFoundError(str(experiment_db_id))

        if experiment.status not in [ExperimentStatus.QUEUED, ExperimentStatus.RUNNING]:
            raise ExperimentAlreadyRunningError(experiment.experiment_id)

        # Cancel background task
        task = self._running_experiments.get(str(experiment_db_id))
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Mark as cancelled
        await self._mark_experiment_cancelled(experiment_db_id)