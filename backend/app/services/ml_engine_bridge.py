"""Bridge service to execute ML engine experiment scripts."""

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProgressData:
    """Parsed progress data from ML engine output."""

    def __init__(
        self,
        progress: int,
        stage: str,
        seed: Optional[int] = None,
        severity: Optional[float] = None,
        message: Optional[str] = None,
        seed_index: int = 0,
        severity_index: int = 0,
    ):
        self.progress = progress
        self.stage = stage
        self.seed = seed
        self.severity = severity
        self.message = message
        self.seed_index = seed_index
        self.severity_index = severity_index


class MLEngineBridge:
    """Bridge to execute ML engine experiment scripts asynchronously."""

    def __init__(self):
        self.scripts_dir = settings.SCRIPTS_BASE_DIR
        self.configs_dir = settings.CONFIGS_BASE_DIR
        self.artifacts_dir = settings.ARTIFACTS_BASE_DIR
        self.ml_engine_path = settings.ML_ENGINE_PATH
        self._running_processes: Dict[str, asyncio.subprocess.Process] = {}

    def _get_script_path(self, experiment_type: str, dataset_id: Optional[str] = None) -> Path:
        """Get the script path for an experiment type."""
        if dataset_id:
            ds_clean = str(dataset_id).strip().lower()
            if ds_clean not in ("iris", "iris-dataset", "fisher-iris", "german-credit", "german_credit"):
                generic_script = self.scripts_dir / "run_generic.py"
                if generic_script.exists():
                    return generic_script

        script_map = {
            "e001": "run_e001.py",
            "e002": "run_e002.py",
            "e003": "run_e003.py",
            "e004": "run_e004.py",
            "e005": "run_e005.py",
            "e006": "run_e006.py",
            "generic": "run_generic.py",
        }
        script_name = script_map.get(experiment_type.lower())
        if not script_name:
            script_name = "run_generic.py" if (self.scripts_dir / "run_generic.py").exists() else "run_e001.py"
        return self.scripts_dir / script_name

    def _generate_config_yaml(self, request_data: Dict[str, Any], output_dir: Path) -> Path:
        """Generate YAML config file for the experiment."""
        import yaml

        seeds = request_data.get("seeds", [42, 123, 456, 789, 1011])
        severity_levels = request_data.get("severity_levels", [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3])

        config = {
            "experiment": {
                "name": request_data.get("experiment_id", "custom_experiment"),
                "task_type": request_data.get("task_type", "classification"),
                "model": {
                    "name": request_data.get("model_name", "RandomForestClassifier"),
                    "type": request_data.get("model_type", "sklearn_rf"),
                    "hyperparameters": request_data.get("hyperparameters", {"n_estimators": 100, "random_state": 42}),
                },
                "dataset": {
                    "name": request_data.get("dataset_name", "Iris Dataset"),
                    "id": request_data.get("dataset_id", "iris"),
                    "path": request_data.get("dataset_path"),
                    "storage_key": request_data.get("dataset_storage_key"),
                    "sha256": request_data.get("dataset_sha256"),
                    "target_column": request_data.get("target_column") or request_data.get("target_name"),
                    "test_size": request_data.get("test_size", 0.20),
                },
                "stress_test": {
                    "perturbation_family": request_data.get("perturbation_family", "gaussian_noise"),
                    "severity_levels": severity_levels,
                    "stress_mode": request_data.get("stress_mode", "incremental"),
                    "target_features": request_data.get("target_features", []),
                },
                "evaluation": {
                    "metric": request_data.get("evaluation_metric", "f1"),
                    "failure_threshold": request_data.get("failure_threshold", 0.8),
                },
                "seeds": seeds,
                "reproducibility": {
                    "save_artifacts": True,
                    "artifact_dir": str(output_dir),
                },
            }
        }

        config_path = output_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        return config_path

    async def run_experiment(
        self,
        experiment_id: str,
        experiment_type: str,
        request_data: Dict[str, Any],
        progress_callback=None,
    ) -> Dict[str, Any]:
        """Run an ML engine experiment asynchronously."""
        # UI-configured jobs always use the manifest-driven generic runner.
        # Canonical E001-E006 research scripts are reserved for explicit CLI runs;
        # they do not necessarily honor selected model/target/severity settings.
        script_path = (
            self.scripts_dir / "run_generic.py"
            if request_data.get("use_generic")
            else self._get_script_path(experiment_type, request_data.get("dataset_id"))
        )

        # Create output directory
        output_dir = self.artifacts_dir / experiment_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate config
        config_path = self._generate_config_yaml(request_data, output_dir)

        # Build command based on script expectations
        seeds = request_data.get("seeds", [42, 123, 456, 789, 1011])
        cmd = [
            sys.executable,
            str(script_path),
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
        ]

        if script_path.name == "run_generic.py":
            cmd.append("--seeds")
            cmd.extend([str(s) for s in seeds])
        elif experiment_type.lower() == "e001":
            if len(seeds) > 1:
                cmd.append("--multi-seed")
            else:
                cmd.extend(["--seed", str(seeds[0])])
        else:
            cmd.append("--seeds")
            cmd.extend([str(s) for s in seeds])

        # Set up environment with ML engine in path
        env = os.environ.copy()
        ml_src = str(self.ml_engine_path / "src")
        env["PYTHONPATH"] = f"{ml_src}{os.pathsep}{env.get('PYTHONPATH', '')}"

        logger.info(
            "Starting experiment",
            experiment_id=experiment_id,
            experiment_type=experiment_type,
            cmd=" ".join(cmd),
        )

        # Run subprocess
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(self.ml_engine_path),
        )

        self._running_processes[experiment_id] = proc

        # Drain stderr concurrently. Otherwise stderr pipe backpressure can
        # deadlock the child before stdout finishes. Retain only the final 16 KiB.
        stderr_tail = bytearray()

        async def drain_stderr() -> None:
            while True:
                chunk = await proc.stderr.read(4096)
                if not chunk:
                    break
                stderr_tail.extend(chunk)
                if len(stderr_tail) > 16384:
                    del stderr_tail[:-16384]

        stderr_task = asyncio.create_task(drain_stderr())

        try:
            async for line in proc.stdout:
                line_str = line.decode("utf-8", errors="replace").strip()
                if line_str:
                    progress_data = self._parse_progress_line(line_str)
                    if progress_data and progress_callback:
                        await progress_callback(progress_data)
            await proc.wait()
            await stderr_task

            if proc.returncode != 0:
                stderr = stderr_tail.decode("utf-8", errors="replace")
                logger.error(
                    "Experiment subprocess failed",
                    experiment_id=experiment_id,
                    returncode=proc.returncode,
                    stderr=stderr,
                )
                raise RuntimeError(f"Experiment subprocess exited with code {proc.returncode}")

            artifacts = self._collect_artifacts(experiment_id, output_dir, seeds)
            results = self._parse_results(output_dir, seeds, request_data)
            logger.info("Experiment completed", experiment_id=experiment_id)
            return {
                "artifacts": artifacts,
                "results": results,
                "output_dir": str(output_dir),
            }
        finally:
            if proc.returncode is None:
                proc.kill()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    logger.error("Subprocess did not reap after kill", experiment_id=experiment_id)
            if not stderr_task.done():
                stderr_task.cancel()
            await asyncio.gather(stderr_task, return_exceptions=True)
            self._running_processes.pop(experiment_id, None)

    def _parse_progress_line(self, line: str) -> Optional[ProgressData]:
        """Parse progress from ML engine output line."""
        # Look for JSON progress lines
        match = re.search(r"(\{.*\})", line)
        if match:
            try:
                data = json.loads(match.group(1))
                if "progress" in data or "stage" in data:
                    return ProgressData(
                        progress=int(data.get("progress", 0)),
                        stage=data.get("stage", "evaluating"),
                        seed=data.get("seed"),
                        severity=data.get("severity"),
                        message=data.get("message"),
                    )
            except Exception:
                pass

        # Text based parsing
        pct_match = re.search(r"(\d+)%", line)
        if pct_match:
            return ProgressData(progress=int(pct_match.group(1)), stage="running")

        if "Severity" in line:
            sev_match = re.search(r"Severity\s+([\d.]+)", line)
            if sev_match:
                return ProgressData(
                    progress=50,
                    stage="stress_eval",
                    severity=float(sev_match.group(1)),
                )

        return None

    def _collect_artifacts(
        self, experiment_id: str, output_dir: Path, seeds: List[int]
    ) -> List[Dict[str, Any]]:
        """Collect generated artifacts recursively."""
        artifacts = []

        if not output_dir.exists():
            return artifacts

        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(self.artifacts_dir)
                seed = None
                for part in file_path.parts:
                    if part.startswith("seed_"):
                        try:
                            seed = int(part.replace("seed_", ""))
                        except ValueError:
                            pass

                artifacts.append({
                    "type": self._get_artifact_type(file_path.name),
                    "seed": seed,
                    "file_path": str(rel_path).replace("\\", "/"),
                    "file_name": file_path.name,
                    "file_size": file_path.stat().st_size,
                })

        return artifacts

    def _get_artifact_type(self, filename: str) -> str:
        """Determine artifact type enum string from filename."""
        lower = filename.lower()
        if lower.endswith(".json") and ("manifest" in lower):
            return "manifest_json"
        elif lower.endswith(".json") and ("reproducibility" in lower):
            return "reproducibility_json"
        elif lower.endswith(".json"):
            return "results_json"
        elif lower.endswith(".csv"):
            return "curves_csv"
        elif lower.endswith(".md"):
            return "report_md"
        return "results_json"

    def _parse_results(
        self, output_dir: Path, seeds: List[int], request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalize measured experiment results; never substitute demo measurements."""
        candidates = (
            "aggregate_results.json",
            "aggregate_comparison.json",
            "results.json",
            "failure_patterns_summary.json",
            "metrics.json",
        )
        data = None
        for filename in candidates:
            path = output_dir / filename
            if path.is_file():
                try:
                    with path.open("r", encoding="utf-8") as handle:
                        candidate = json.load(handle)
                except (OSError, ValueError) as exc:
                    raise ValueError(f"Invalid experiment results artifact {filename}: {exc}") from exc
                if not isinstance(candidate, dict):
                    raise ValueError(f"Experiment results artifact {filename} must be a JSON object")
                data = candidate
                break
        if data is None:
            raise ValueError(f"Experiment produced no readable results artifact in {output_dir}")

        target_data = data
        if isinstance(data.get("models"), dict):
            models = data["models"]
            if len(models) != 1:
                raise ValueError("Ambiguous multi-model results: explicit model selection required")
            target_data = next(iter(models.values()))
        if isinstance(target_data.get("corruptions"), dict):
            corruptions = target_data["corruptions"]
            if len(corruptions) != 1:
                raise ValueError("Ambiguous multi-corruption results: explicit protocol selection required")
            target_data = next(iter(corruptions.values()))
        if not isinstance(target_data, dict):
            raise ValueError("Experiment results have an invalid model/protocol structure")

        def measured(value: Any) -> Optional[float]:
            if isinstance(value, dict):
                value = value.get("mean")
            if value is None:
                return None
            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric metric in experiment results: {value!r}") from exc
            if not __import__("math").isfinite(number):
                raise ValueError("Experiment results contain a non-finite metric")
            return number

        baseline_metrics = target_data.get("baseline_metrics") or {}
        if not isinstance(baseline_metrics, dict):
            raise ValueError("baseline_metrics must be an object")
        metric_name = str(target_data.get("metric") or request_data.get("evaluation_metric") or "f1").lower()
        normalized_baseline = {
            str(key): measured(value)
            for key, value in baseline_metrics.items()
            if measured(value) is not None
        }
        baseline_f1 = measured(target_data.get("baseline_macro_f1"))
        if baseline_f1 is None:
            baseline_f1 = measured(baseline_metrics.get("macro_f1", baseline_metrics.get("f1")))
        baseline_accuracy = measured(target_data.get("baseline_accuracy"))
        if baseline_accuracy is None:
            baseline_accuracy = measured(baseline_metrics.get("accuracy"))
        if baseline_f1 is None and isinstance(target_data.get("per_seed_results"), dict):
            per_seed_values = [
                measured(value.get("baseline_macro_f1"))
                for value in target_data["per_seed_results"].values()
                if isinstance(value, dict)
            ]
            available = [v for v in per_seed_values if v is not None]
            if available:
                baseline_f1 = sum(available) / len(available)

        raw_curve = target_data.get("severity_aggregates")
        if raw_curve is None:
            raw_curve = target_data.get("severity_results")
        if raw_curve is None:
            raw_curve = target_data.get("curve_data")
        if not isinstance(raw_curve, list) or not raw_curve:
            raise ValueError("Experiment has no measured severity curve; refusing synthetic results")

        curve_data = []
        for point in raw_curve:
            if not isinstance(point, dict):
                raise ValueError("Severity curve contains an invalid point")
            severity = measured(point.get("severity", point.get("noiseLevel")))
            f1_score = measured(point.get("macro_f1", point.get("mean_macro_f1", point.get("f1"))))
            accuracy = measured(point.get("accuracy", point.get("mean_accuracy")))
            score = measured(point.get("score"))
            if score is None and isinstance(point.get("metrics"), dict):
                score = measured(point["metrics"].get(metric_name))
            if severity is None or (f1_score is None and accuracy is None and score is None):
                raise ValueError("Severity curve point is missing measured severity or metric")
            curve_data.append({
                "noiseLevel": severity,
                "severity": severity,
                "score": score if score is not None else (f1_score if f1_score is not None else accuracy),
                "f1": f1_score,
                "accuracy": accuracy,
                "baseline": baseline_f1,
                "threshold": request_data.get("failure_threshold"),
            })

        # Aggregated experiments may only provide the actual zero-severity evaluation.
        # Derive the baseline from that measured point, never from a fabricated constant.
        if baseline_f1 is None:
            zero = next((p for p in curve_data if p["severity"] == 0.0 and p["f1"] is not None), None)
            if zero is not None:
                baseline_f1 = zero["f1"]
        if baseline_accuracy is None:
            zero = next((p for p in curve_data if p["severity"] == 0.0 and p["accuracy"] is not None), None)
            if zero is not None:
                baseline_accuracy = zero["accuracy"]
        baseline_metric = normalized_baseline.get(metric_name)
        if baseline_metric is None:
            baseline_metric = baseline_f1 if metric_name == "f1" else baseline_accuracy
        if baseline_f1 is None and baseline_accuracy is None and baseline_metric is None:
            raise ValueError("Experiment has no measured baseline; refusing synthetic metrics")
        if baseline_metric is not None:
            normalized_baseline.setdefault(metric_name, baseline_metric)
        if baseline_f1 is not None:
            normalized_baseline.setdefault("f1", baseline_f1)
        if baseline_accuracy is not None:
            normalized_baseline.setdefault("accuracy", baseline_accuracy)
        for point in curve_data:
            point["baseline"] = baseline_metric

        feature_vulns = target_data.get("feature_vulnerabilities") or []
        failed_samples = target_data.get("failed_samples") or []
        if not isinstance(feature_vulns, list) or not isinstance(failed_samples, list):
            raise ValueError("Feature vulnerabilities and failed samples must be arrays")

        worst_f1 = measured(target_data.get("worst_case_macro_f1"))
        worst_accuracy = measured(target_data.get("worst_case_accuracy"))
        if worst_f1 is None:
            measured_f1 = [p["f1"] for p in curve_data if p["f1"] is not None]
            worst_f1 = min(measured_f1) if measured_f1 else None
        if worst_accuracy is None:
            measured_accuracy = [p["accuracy"] for p in curve_data if p["accuracy"] is not None]
            worst_accuracy = min(measured_accuracy) if measured_accuracy else None

        worst_severity = measured(target_data.get("worst_case_severity"))
        if worst_severity is None and any(p["f1"] is not None for p in curve_data):
            worst_point = min(
                (p for p in curve_data if p["f1"] is not None),
                key=lambda p: p["f1"],
            )
            worst_severity = worst_point["severity"]

        observed_boundary = target_data.get(
            "observed_boundary",
            target_data.get(
                "observed_failure_boundary", target_data.get("mean_observed_boundary")
            ),
        )

        raw_worst = target_data.get("worst_case_metrics") or {}
        if not isinstance(raw_worst, dict):
            raise ValueError("worst_case_metrics must be an object")
        normalized_worst = {
            str(key): measured(value)
            for key, value in raw_worst.items()
            if measured(value) is not None
        }
        if worst_f1 is not None:
            normalized_worst.setdefault("f1", worst_f1)
        if worst_accuracy is not None:
            normalized_worst.setdefault("accuracy", worst_accuracy)
        if metric_name not in normalized_worst:
            values = [p for p in curve_data if p["score"] is not None]
            if values:
                lower_better = metric_name in {"mae", "rmse", "mse", "loss"}
                extreme = max(values, key=lambda v: v["score"]) if lower_better else min(values, key=lambda v: v["score"])
                normalized_worst[metric_name] = extreme["score"]
                if worst_severity is None:
                    worst_severity = extreme["severity"]

        return {
            "metric": metric_name,
            "baseline_metrics": normalized_baseline,
            "worst_case_metrics": normalized_worst,
            "baseline_macro_f1": baseline_f1,
            "baseline_accuracy": baseline_accuracy,
            "worst_case_macro_f1": worst_f1,
            "worst_case_accuracy": worst_accuracy,
            "worst_case_severity": worst_severity,
            "observed_boundary": observed_boundary,
            "curve_data": curve_data,
            "feature_vulnerabilities": feature_vulns,
            "statistical_validation": target_data.get("statistical_validation"),
            "failed_samples_count": len(failed_samples),
            "failed_samples": failed_samples,
        }

    async def cancel_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Cancel a running experiment subprocess."""
        proc = self._running_processes.get(experiment_id)
        if proc and proc.returncode is None:
            pid = proc.pid
            try:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                return {"confirmed_stopped": True, "terminated_pid": pid}
            except Exception as e:
                logger.warning(f"Error terminating subprocess for {experiment_id}: {e}")
                return {"confirmed_stopped": False, "terminated_pid": pid}
        return {"confirmed_stopped": True, "terminated_pid": None}


# Singleton instance
ml_engine_bridge = MLEngineBridge()
