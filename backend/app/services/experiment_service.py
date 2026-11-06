"""Experiment service for managing experiment lifecycle."""

import asyncio
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import session_context
from app.core.exceptions import (
    ConcurrencyLimitError,
    ExperimentAlreadyRunningError,
    ExperimentExecutionError,
    ExperimentNotFoundError,
    InvalidExperimentConfigError,
)
from app.core.logging import get_logger
from app.models.experiment import (
    Experiment,
    ExperimentRun,
    ExperimentResult,
    ExperimentStatus,
    StressMode,
    StressType,
    TaskType,
)
from app.models.failure_sample import FailedSample
from app.models.artifact import ArtifactManifest, ArtifactType
from app.repositories.experiment import (
    ExperimentRepository,
    ExperimentRunRepository,
    ExperimentResultRepository,
)
from app.repositories.failure_sample import FailureSampleRepository
from app.repositories.artifact import ArtifactRepository, ArtifactReferenceRepository
from app.services.ml_engine_bridge import ml_engine_bridge, ProgressData
from app.schemas import ExperimentRunRequest

logger = get_logger(__name__)


class ExperimentService:
    """Service for managing experiment lifecycle."""

    # Class-level background task registry across requests
    _active_tasks: Dict[str, asyncio.Task] = {}

    def __init__(self, session: AsyncSession):
        self.session = session
        self.exp_repo = ExperimentRepository(session)
        self.run_repo = ExperimentRunRepository(session)
        self.result_repo = ExperimentResultRepository(session)
        self.fail_repo = FailureSampleRepository(session)
        self.artifact_repo = ArtifactRepository(session)

    async def create_experiment(self, request: ExperimentRunRequest) -> Experiment:
        """Create and queue a new experiment."""
        # 1. Validate metric polarity and task compatibility
        self._validate_metric_polarity(request)

        # 2. Check concurrency limit
        running = await self.exp_repo.get_running_experiments()
        if len(running) >= settings.MAX_CONCURRENT_EXPERIMENTS:
            raise ConcurrencyLimitError(settings.MAX_CONCURRENT_EXPERIMENTS)

        # 3. Generate human-readable experiment ID (e.g., EXP-0001)
        experiment_id = await self.exp_repo.get_next_experiment_id()

        # 4. Extract parameters supporting both snake_case and camelCase
        model_name = request.model_name or request.model_id or "RandomForest-v2 (Credit)"
        dataset_name = request.dataset_name or request.dataset_id
        dataset_id = request.dataset_id
        pert_family = request.perturbation_family or "gaussian_noise"
        noise_type = request.noise_type or "Gaussian Noise"
        eval_metric = request.evaluation_metric or request.metric or "f1"
        threshold = float(request.failure_threshold if request.failure_threshold is not None else 0.80)
        seed = int(request.seed if request.seed is not None else 42)
        seeds = request.seeds or settings.DEFAULT_SEEDS
        stress_mode = request.stress_mode or "incremental"
        severity_levels = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]

        task_type_enum = self._to_task_type(request.task_type)
        pert_enum = self._to_stress_type(pert_family)
        mode_enum = self._to_stress_mode(stress_mode)

        experiment_type = self._get_experiment_type(pert_family)

        # Generate config YAML
        config_yaml = self._generate_config_yaml(
            experiment_id=experiment_id,
            model_name=model_name,
            dataset_name=dataset_name,
            dataset_id=dataset_id,
            perturbation_family=pert_family,
            evaluation_metric=eval_metric,
            failure_threshold=threshold,
            severity_levels=severity_levels,
            seeds=seeds,
            seed=seed,
            stress_mode=stress_mode,
        )

        # Create experiment record in database
        experiment = await self.exp_repo.create(
            experiment_id=experiment_id,
            model_name=model_name,
            dataset_name=dataset_name,
            dataset_id=dataset_id,
            task_type=task_type_enum,
            perturbation_family=pert_enum,
            noise_type=noise_type,
            evaluation_metric=eval_metric,
            failure_threshold=threshold,
            seed=seed,
            stress_mode=mode_enum,
            severity_levels=severity_levels,
            seeds=seeds,
            config_yaml=config_yaml,
            status=ExperimentStatus.QUEUED,
            progress_percent=0,
        )

        # Create per-seed runs
        for i, run_seed in enumerate(seeds):
            await self.run_repo.create(
                experiment_id=experiment.id,
                seed=run_seed,
                run_index=i,
                status=ExperimentStatus.QUEUED,
                progress_percent=0,
            )

        # Request data for ML engine bridge
        request_data = {
            "experiment_id": experiment_id,
            "model_name": model_name,
            "dataset_name": dataset_name,
            "dataset_id": dataset_id,
            "perturbation_family": pert_family,
            "evaluation_metric": eval_metric,
            "failure_threshold": threshold,
            "stress_mode": stress_mode,
            "severity_levels": severity_levels,
            "seeds": seeds,
        }

        # Spawn background execution task
        exp_db_id = experiment.id
        task = asyncio.create_task(
            self._run_experiment_background(exp_db_id, experiment_type, request_data)
        )
        ExperimentService._active_tasks[str(exp_db_id)] = task

        logger.info(
            "Experiment created and queued",
            experiment_id=experiment_id,
            db_id=str(exp_db_id),
        )

        return experiment

    def _validate_metric_polarity(self, request: ExperimentRunRequest) -> None:
        """Enforce metric polarity invariant:
        - Higher is better: f1, accuracy, precision, recall, roc_auc, pr_auc
        - Lower is better: mae, rmse, loss
        """
        metric = (request.evaluation_metric or request.metric or "f1").lower()
        task_type = (request.task_type or "classification").lower()

        higher_better = {"f1", "accuracy", "precision", "recall", "roc_auc", "pr_auc", "r2"}
        lower_better = {"mae", "rmse", "loss", "mse"}

        if task_type == "classification" and metric in {"mae", "rmse"}:
            raise InvalidExperimentConfigError(
                f"Metric '{metric}' is a regression metric and cannot be used for classification task."
            )

        if task_type == "regression" and metric in {"f1", "accuracy", "roc_auc", "pr_auc"}:
            raise InvalidExperimentConfigError(
                f"Metric '{metric}' is a classification metric and cannot be used for regression task."
            )

        # Verify failure threshold boundaries
        if metric in higher_better and request.failure_threshold is not None:
            if request.failure_threshold < 0.0 or request.failure_threshold > 1.0:
                raise InvalidExperimentConfigError(
                    f"Failure threshold for higher-is-better metric '{metric}' must be between 0.0 and 1.0."
                )

        if metric in lower_better and request.failure_threshold is not None:
            if request.failure_threshold < 0.0:
                raise InvalidExperimentConfigError(
                    f"Failure threshold for lower-is-better metric '{metric}' must be non-negative."
                )

    def _to_task_type(self, val: Optional[str]) -> TaskType:
        if not val:
            return TaskType.CLASSIFICATION
        try:
            return TaskType(val.lower())
        except (ValueError, AttributeError):
            return TaskType.CLASSIFICATION

    def _to_stress_type(self, val: Optional[str]) -> StressType:
        if not val:
            return StressType.GAUSSIAN_NOISE
        v = str(val).lower()
        if "missing" in v:
            return StressType.MISSINGNESS
        if "outlier" in v:
            return StressType.OUTLIERS
        if "poison" in v or "pattern" in v:
            return StressType.POISONING
        if "adversarial" in v or "vulnerab" in v:
            return StressType.ADVERSARIAL
        if "shift" in v or "covariate" in v:
            return StressType.COVARIATE_SHIFT
        try:
            return StressType(v)
        except (ValueError, AttributeError):
            return StressType.GAUSSIAN_NOISE

    def _to_stress_mode(self, val: Optional[str]) -> StressMode:
        if not val:
            return StressMode.INCREMENTAL
        try:
            return StressMode(val.lower())
        except (ValueError, AttributeError):
            return StressMode.INCREMENTAL

    def _get_experiment_type(self, perturbation_family: str) -> str:
        """Map perturbation family or experiment id to experiment runner script."""
        val = str(perturbation_family).lower()
        if val in ("e001", "e002", "e003", "e004", "e005", "e006"):
            return val
        mapping = {
            "gaussian_noise": "e001",
            "mcar_missingness": "e002",
            "missingness": "e002",
            "multi_corruption": "e002",
            "outlier_contamination": "e003",
            "outliers": "e003",
            "cross_model": "e003",
            "failure_patterns": "e004",
            "poisoning": "e004",
            "feature_vulnerability": "e005",
            "adversarial": "e005",
            "covariate_shift": "e006",
            "distribution_shift": "e006",
        }
        return mapping.get(val, "e001")

    def _generate_config_yaml(
        self,
        experiment_id: str,
        model_name: str,
        dataset_name: str,
        dataset_id: str,
        perturbation_family: str,
        evaluation_metric: str,
        failure_threshold: float,
        severity_levels: List[float],
        seeds: List[int],
        seed: int,
        stress_mode: str,
    ) -> str:
        """Generate YAML config for the experiment."""
        import yaml

        config = {
            "experiment": {
                "name": experiment_id,
                "model": {
                    "name": model_name,
                    "type": "sklearn_rf",
                    "hyperparameters": {"n_estimators": 100, "random_state": seed},
                },
                "dataset": {
                    "name": dataset_name,
                    "id": dataset_id,
                },
                "stress_test": {
                    "perturbation_family": perturbation_family,
                    "severity_levels": severity_levels,
                    "stress_mode": stress_mode,
                },
                "evaluation": {
                    "metric": evaluation_metric,
                    "failure_threshold": failure_threshold,
                },
                "seeds": seeds,
                "reproducibility": {
                    "save_artifacts": True,
                },
            }
        }

        return yaml.dump(config, default_flow_style=False)

    async def _run_experiment_background(
        self, experiment_db_id: uuid.UUID, experiment_type: str, request_data: Dict[str, Any]
    ) -> None:
        """Isolated background runner with dedicated database session."""
        try:
            async with session_context() as session:
                exp_repo = ExperimentRepository(session)
                run_repo = ExperimentRunRepository(session)

                experiment = await exp_repo.get_by_id(experiment_db_id)
                if not experiment:
                    return

                experiment.status = ExperimentStatus.RUNNING
                experiment.started_at = datetime.utcnow()
                experiment.progress_percent = 0
                await session.flush()

                runs = await run_repo.get_by_experiment(experiment_db_id)
                if runs:
                    runs[0].status = ExperimentStatus.RUNNING
                    runs[0].started_at = datetime.utcnow()
                    await session.flush()

            # Progress update callback
            async def progress_callback(progress: ProgressData):
                try:
                    async with session_context() as prog_session:
                        p_exp_repo = ExperimentRepository(prog_session)
                        p_run_repo = ExperimentRunRepository(prog_session)
                        p_exp = await p_exp_repo.get_by_id(experiment_db_id)
                        if p_exp:
                            p_exp.progress_percent = progress.progress
                            p_exp.current_seed_index = progress.seed_index
                            p_exp.current_severity_index = progress.severity_index
                            p_runs = await p_run_repo.get_by_experiment(experiment_db_id)
                            if p_runs and progress.seed is not None:
                                for r in p_runs:
                                    if r.seed == progress.seed:
                                        r.status = ExperimentStatus.RUNNING
                                        r.progress_percent = progress.progress
                                        r.current_severity = progress.severity
                                        break
                            await prog_session.flush()
                except Exception as ex:
                    logger.debug(f"Progress update non-critical error: {ex}")

            # Run ML engine script
            result_data = await ml_engine_bridge.run_experiment(
                experiment_id=request_data["experiment_id"],
                experiment_type=experiment_type,
                request_data=request_data,
                progress_callback=progress_callback,
            )

            # Store completed results, artifacts, and failed samples
            async with session_context() as finish_session:
                await self._process_and_save_results(finish_session, experiment_db_id, result_data)

                f_exp_repo = ExperimentRepository(finish_session)
                f_run_repo = ExperimentRunRepository(finish_session)

                f_exp = await f_exp_repo.get_by_id(experiment_db_id)
                if f_exp:
                    f_exp.status = ExperimentStatus.COMPLETED
                    f_exp.completed_at = datetime.utcnow()
                    f_exp.progress_percent = 100

                f_runs = await f_run_repo.get_by_experiment(experiment_db_id)
                for r in f_runs:
                    r.status = ExperimentStatus.COMPLETED
                    r.completed_at = datetime.utcnow()
                    r.progress_percent = 100

                await finish_session.flush()

            logger.info("Experiment run successfully completed", experiment_id=request_data["experiment_id"])

        except asyncio.CancelledError:
            logger.info("Experiment run cancelled in background", db_id=str(experiment_db_id))
            async with session_context() as cancel_session:
                await self._mark_experiment_cancelled(cancel_session, experiment_db_id)
            raise
        except Exception as e:
            logger.exception("Experiment run failed in background", db_id=str(experiment_db_id))
            async with session_context() as fail_session:
                await self._mark_experiment_failed(fail_session, experiment_db_id, str(e))
        finally:
            ExperimentService._active_tasks.pop(str(experiment_db_id), None)

    async def _process_and_save_results(
        self, session: AsyncSession, experiment_db_id: uuid.UUID, result_data: Dict[str, Any]
    ) -> None:
        """Process and store experiment results, artifacts, and failure samples."""
        exp_repo = ExperimentRepository(session)
        result_repo = ExperimentResultRepository(session)
        artifact_repo = ArtifactRepository(session)
        fail_repo = FailureSampleRepository(session)

        experiment = await exp_repo.get_by_id(experiment_db_id)
        if not experiment:
            return

        results = result_data.get("results", {})
        artifacts = result_data.get("artifacts", [])
        failed_samples = results.get("failed_samples", [])

        # Create or update ExperimentResult
        await result_repo.create(
            experiment_id=experiment_db_id,
            baseline_macro_f1=results.get("baseline_macro_f1"),
            baseline_accuracy=results.get("baseline_accuracy"),
            worst_case_macro_f1=results.get("worst_case_macro_f1"),
            worst_case_accuracy=results.get("worst_case_accuracy"),
            worst_case_severity=results.get("worst_case_severity"),
            observed_boundary=results.get("observed_boundary"),
            boundary_caveat="Observed failure boundary under the specified experimental configuration.",
            curve_data=results.get("curve_data", []),
            feature_vulnerabilities=results.get("feature_vulnerabilities", []),
            statistical_validation=results.get("statistical_validation"),
            failed_samples_count=len(failed_samples),
        )

        # Store artifacts in database
        for art in artifacts:
            file_path_obj = settings.ARTIFACTS_BASE_DIR / art["file_path"]
            content_hash = self._compute_hash(file_path_obj)
            art_type_str = art.get("type", "results_json")
            try:
                art_type_enum = ArtifactType(art_type_str)
            except ValueError:
                art_type_enum = ArtifactType.RESULTS_JSON

            mime_type = self._get_mime_type(art["file_name"])
            await artifact_repo.create(
                experiment_id=experiment_db_id,
                artifact_type=art_type_enum,
                seed=art.get("seed"),
                file_path=art["file_path"],
                file_name=art["file_name"],
                file_size_bytes=art["file_size"],
                content_hash=content_hash,
                mime_type=mime_type,
            )

            # Store artifact using unified storage_service (R2 with local fallback)
            try:
                try:
                    from app.services.storage_service import storage_service
                except ImportError:
                    from backend.app.services.storage_service import storage_service

                if file_path_obj.exists():
                    r2_key = f"experiments/{experiment.experiment_id}/{art['file_name']}"
                    upload_res = storage_service.store_file(file_path_obj, r2_key, mime_type)
                    ref_repo = ArtifactReferenceRepository(session)
                    await ref_repo.create(
                        manifest_id=manifest.id,
                        reference_type=upload_res.provider,
                        reference_url=upload_res.key,
                        metadata_={
                            "sha256": upload_res.sha256_hash,
                            "size_bytes": upload_res.size_bytes,
                            "etag": upload_res.etag,
                            "url": upload_res.url,
                        },
                    )
            except Exception as e:
                logger.warning(f"Storage replication error for {art.get('file_name')}: {e}")

        # Store failed samples
        for s in failed_samples:
            await fail_repo.create(
                experiment_id=experiment_db_id,
                sample_index=s.get("sample_index", 0),
                sample_id=s.get("sample_id", "samp-0"),
                true_label=str(s.get("true_label", "")),
                predicted_label=str(s.get("predicted_label", "")),
                confidence=float(s.get("confidence", 0.0)),
                noise_level=float(s.get("noise_level", 0.0)),
                seed=int(s.get("seed", 42)),
                features_clean=s.get("features_clean", {}),
                features_stressed=s.get("features_stressed", {}),
                feature_diffs=s.get("feature_diffs", {}),
            )

        await session.flush()

    def _compute_hash(self, file_path: Path) -> str:
        if not file_path.exists():
            return ""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_mime_type(self, filename: str) -> str:
        if filename.endswith(".json"):
            return "application/json"
        elif filename.endswith(".csv"):
            return "text/csv"
        elif filename.endswith(".md"):
            return "text/markdown"
        elif filename.endswith(".png"):
            return "image/png"
        return "application/octet-stream"

    async def _mark_experiment_cancelled(self, session: AsyncSession, experiment_db_id: uuid.UUID) -> None:
        exp_repo = ExperimentRepository(session)
        run_repo = ExperimentRunRepository(session)

        exp = await exp_repo.get_by_id(experiment_db_id)
        if exp:
            exp.status = ExperimentStatus.CANCELLED
            exp.completed_at = datetime.utcnow()

        runs = await run_repo.get_by_experiment(experiment_db_id)
        for r in runs:
            if r.status in [ExperimentStatus.QUEUED, ExperimentStatus.RUNNING]:
                r.status = ExperimentStatus.CANCELLED
                r.completed_at = datetime.utcnow()
        await session.flush()

    async def _mark_experiment_failed(
        self, session: AsyncSession, experiment_db_id: uuid.UUID, error_message: str
    ) -> None:
        exp_repo = ExperimentRepository(session)
        run_repo = ExperimentRunRepository(session)

        exp = await exp_repo.get_by_id(experiment_db_id)
        if exp:
            exp.status = ExperimentStatus.FAILED
            exp.error_message = error_message
            exp.completed_at = datetime.utcnow()

        runs = await run_repo.get_by_experiment(experiment_db_id)
        for r in runs:
            if r.status in [ExperimentStatus.QUEUED, ExperimentStatus.RUNNING]:
                r.status = ExperimentStatus.FAILED
                r.error_message = error_message
                r.completed_at = datetime.utcnow()
        await session.flush()

    async def cancel_experiment(self, experiment_db_id: uuid.UUID) -> Dict[str, Any]:
        """Cancel a running or queued experiment."""
        experiment = await self.exp_repo.get_by_id(experiment_db_id)
        if not experiment:
            raise ExperimentNotFoundError(str(experiment_db_id))

        # Cancel bridge subprocess if active
        bridge_res = await ml_engine_bridge.cancel_experiment(experiment.experiment_id)

        # Cancel async task if active
        task = ExperimentService._active_tasks.get(str(experiment_db_id))
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Update DB status
        await self._mark_experiment_cancelled(self.session, experiment_db_id)

        return {
            "success": True,
            "experimentId": experiment.experiment_id,
            "status": "cancelled",
            "terminatedPid": bridge_res.get("terminated_pid"),
            "confirmedStopped": bridge_res.get("confirmed_stopped", True),
        }
