"""Bridge service to execute ML engine experiment scripts."""

import asyncio
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

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
    ):
        self.progress = progress
        self.stage = stage
        self.seed = seed
        self.severity = severity
        self.message = message


class MLEngineBridge:
    """Bridge to execute ML engine experiment scripts asynchronously."""

    def __init__(self):
        self.scripts_dir = settings.SCRIPTS_BASE_DIR
        self.configs_dir = settings.CONFIGS_BASE_DIR
        self.artifacts_dir = settings.ARTIFACTS_BASE_DIR
        self.ml_engine_path = settings.ML_ENGINE_PATH

    def _get_script_path(self, experiment_type: str) -> Path:
        """Get the script path for an experiment type."""
        script_map = {
            "e001": "run_e001.py",
            "e002": "run_e002.py",
            "e003": "run_e003.py",
            "e004": "run_e004.py",
        }
        script_name = script_map.get(experiment_type.lower())
        if not script_name:
            raise ValueError(f"Unknown experiment type: {experiment_type}")
        return self.scripts_dir / script_name

    def _generate_config_yaml(self, request_data: Dict[str, Any], output_dir: Path) -> Path:
        """Generate YAML config file for the experiment."""
        import yaml

        config = {
            "experiment": {
                "name": request_data.get("experiment_id", "custom_experiment"),
                "model": {
                    "name": request_data.get("model_name"),
                    "type": request_data.get("model_type", "sklearn_rf"),
                    "hyperparameters": request_data.get("hyperparameters", {}),
                },
                "dataset": {
                    "name": request_data.get("dataset_name"),
                    "id": request_data.get("dataset_id"),
                    "path": request_data.get("dataset_path"),
                },
                "stress_test": {
                    "perturbation_family": request_data.get("perturbation_family"),
                    "severity_levels": request_data.get("severity_levels", [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]),
                    "stress_mode": request_data.get("stress_mode", "incremental"),
                },
                "evaluation": {
                    "metric": request_data.get("evaluation_metric", "macro_f1"),
                    "failure_threshold": request_data.get("failure_threshold", 0.8),
                },
                "seeds": request_data.get("seeds", [42, 123, 456, 789, 1011]),
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
        """
        Run an ML engine experiment asynchronously.

        Args:
            experiment_id: Unique experiment identifier
            experiment_type: Type of experiment (e001, e002, e003, e004)
            request_data: Experiment configuration
            progress_callback: Async callback(progress: ProgressData)

        Returns:
            Dictionary with experiment results and artifact paths
        """
        script_path = self._get_script_path(experiment_type)

        # Create output directory
        output_dir = self.artifacts_dir / experiment_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate config
        config_path = self._generate_config_yaml(request_data, output_dir)

        # Build command
        seeds = request_data.get("seeds", [42, 123, 456, 789, 1011])
        cmd = [
            "python",
            str(script_path),
            "--config",
            str(config_path),
            "--seeds",
            ",".join(map(str, seeds)),
            "--output-dir",
            str(output_dir),
        ]

        # Set up environment with ML engine in path
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{self.ml_engine_path}/src:{env.get('PYTHONPATH', '')}"

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
            cwd=self.ml_engine_path,
        )

        # Track progress
        current_progress = 0
        current_seed_idx = 0
        current_severity_idx = 0
        total_seeds = len(seeds)
        total_severities = len(request_data.get("severity_levels", [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]))

        # Read stdout line by line for progress
        async for line in proc.stdout:
            line = line.decode("utf-8").strip()
            if line:
                progress_data = self._parse_progress_line(line)
                if progress_data:
                    current_progress = progress_data.progress
                    if progress_data.seed is not None:
                        try:
                            current_seed_idx = seeds.index(progress_data.seed)
                        except ValueError:
                            pass
                    if progress_data.severity is not None:
                        severities = request_data.get("severity_levels", [])
                        try:
                            current_severity_idx = severities.index(progress_data.severity)
                        except ValueError:
                            pass

                    if progress_callback:
                        await progress_callback(ProgressData(
                            progress=current_progress,
                            stage=progress_data.stage,
                            seed=progress_data.seed,
                            severity=progress_data.severity,
                            message=progress_data.message,
                        ))

        # Wait for completion
        await proc.wait()

        if proc.returncode != 0:
            stderr = ""
            async for line in proc.stderr:
                stderr += line.decode("utf-8")
            logger.error(
                "Experiment failed",
                experiment_id=experiment_id,
                returncode=proc.returncode,
                stderr=stderr,
            )
            raise RuntimeError(f"Experiment failed with return code {proc.returncode}: {stderr}")

        # Collect artifacts
        artifacts = self._collect_artifacts(experiment_id, output_dir, seeds)

        # Parse results
        results = self._parse_results(output_dir, seeds)

        logger.info("Experiment completed", experiment_id=experiment_id)

        return {
            "artifacts": artifacts,
            "results": results,
            "output_dir": str(output_dir),
        }

    def _parse_progress_line(self, line: str) -> Optional[ProgressData]:
        """Parse progress from ML engine output line."""
        # Look for JSON progress lines
        try:
            if line.startswith("{"):
                data = json.loads(line)
                if "progress" in data:
                    return ProgressData(
                        progress=data.get("progress", 0),
                        stage=data.get("stage", "unknown"),
                        seed=data.get("seed"),
                        severity=data.get("severity"),
                        message=data.get("message"),
                    )
        except json.JSONDecodeError:
            pass

        # Look for text-based progress patterns
        patterns = [
            r"Progress:\s*(\d+)%",
            r"Running seed\s+(\d+)",
            r"Severity\s+([\d.]+)",
            r"Stage:\s*(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return ProgressData(
                    progress=int(match.group(1)) if match.group(1).isdigit() else 0,
                    stage="running",
                )

        return None

    def _collect_artifacts(
        self, experiment_id: str, output_dir: Path, seeds: List[int]
    ) -> List[Dict[str, Any]]:
        """Collect generated artifacts."""
        artifacts = []

        # Per-seed artifacts
        for seed in seeds:
            seed_dir = output_dir / f"seed_{seed}"
            if seed_dir.exists():
                for artifact_file in seed_dir.glob("*"):
                    if artifact_file.is_file():
                        artifacts.append({
                            "type": self._get_artifact_type(artifact_file.name),
                            "seed": seed,
                            "file_path": str(artifact_file.relative_to(self.artifacts_dir)),
                            "file_name": artifact_file.name,
                            "file_size": artifact_file.stat().st_size,
                        })

        # Aggregated artifacts
        for artifact_file in output_dir.glob("*"):
            if artifact_file.is_file() and not artifact_file.name.startswith("seed_"):
                artifacts.append({
                    "type": self._get_artifact_type(artifact_file.name),
                    "seed": None,
                    "file_path": str(artifact_file.relative_to(self.artifacts_dir)),
                    "file_name": artifact_file.name,
                    "file_size": artifact_file.stat().st_size,
                })

        return artifacts

    def _get_artifact_type(self, filename: str) -> str:
        """Determine artifact type from filename."""
        if filename.endswith(".json") and "result" in filename:
            return "results_json"
        elif filename.endswith(".csv") and "curve" in filename:
            return "curves_csv"
        elif filename.endswith(".md") and "report" in filename:
            return "report_md"
        elif filename.endswith(".json") and "manifest" in filename:
            return "manifest_json"
        elif filename.endswith(".json") and "reproducibility" in filename:
            return "reproducibility_json"
        return "unknown"

    def _parse_results(self, output_dir: Path, seeds: List[int]) -> Dict[str, Any]:
        """Parse experiment results from output directory."""
        import yaml

        # Try to load aggregated results
        results_file = output_dir / "results.yaml"
        if results_file.exists():
            with open(results_file) as f:
                return yaml.safe_load(f)

        # Try JSON
        results_file = output_dir / "results.json"
        if results_file.exists():
            with open(results_file) as f:
                return json.load(f)

        # Fallback: try to load from first seed
        for seed in seeds:
            seed_dir = output_dir / f"seed_{seed}"
            result_file = seed_dir / "results.json"
            if result_file.exists():
                with open(result_file) as f:
                    return json.load(f)

        return {}

    async def cancel_experiment(self, experiment_id: str) -> bool:
        """Cancel a running experiment (best effort)."""
        # In a full implementation, we would track running processes
        # For now, we just mark as cancelled in the database
        logger.info("Cancel requested", experiment_id=experiment_id)
        return True


# Singleton instance
ml_engine_bridge = MLEngineBridge()