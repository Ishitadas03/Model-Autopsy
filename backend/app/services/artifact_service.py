"""Artifact service for managing experiment artifacts."""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi.responses import FileResponse, StreamingResponse

from backend.app.core.config import settings
from backend.app.core.exceptions import ArtifactNotFoundError
from backend.app.core.logging import get_logger
from backend.app.models.artifact import ArtifactManifest, ArtifactType
from backend.app.repositories.artifact import ArtifactRepository
from backend.app.repositories.experiment import ExperimentRepository

logger = get_logger(__name__)


class ArtifactService:
    """Service for managing and serving experiment artifacts."""

    def __init__(self, session):
        self.session = session
        self.artifact_repo = ArtifactRepository(session)
        self.exp_repo = ExperimentRepository(session)

    async def get_e003_artifact(self, format: str) -> Union[Dict[str, Any], StreamingResponse, FileResponse]:
        """Get E003 canonical experiment artifact in specified format."""
        # E003 is a special canonical experiment - look for it in artifacts
        # For now, serve from the pre-generated artifacts directory
        e003_dir = settings.ARTIFACTS_BASE_DIR / "E003"

        if format == "json":
            return await self._serve_json(e003_dir)
        elif format == "csv":
            return await self._serve_csv(e003_dir)
        elif format == "markdown":
            return await self._serve_markdown(e003_dir)
        else:
            raise ArtifactNotFoundError(f"Format {format} not supported for E003")

    async def get_artifact(
        self,
        experiment_id: UUID,
        artifact_type: str,
        seed: Optional[int],
        format: str,
    ) -> Union[Dict[str, Any], StreamingResponse, FileResponse]:
        """Get experiment artifact by type."""
        # Find artifact manifest
        artifact_type_enum = ArtifactType(artifact_type)
        manifest = await self.artifact_repo.get_by_experiment_and_type(
            experiment_id, artifact_type_enum, seed
        )

        if not manifest:
            raise ArtifactNotFoundError(
                f"Artifact {artifact_type} for experiment {experiment_id} (seed={seed}) not found"
            )

        file_path = settings.ARTIFACTS_BASE_DIR / manifest.file_path

        if not file_path.exists():
            raise ArtifactNotFoundError(f"Artifact file not found: {file_path}")

        if format == "json" and file_path.suffix == ".json":
            return await self._serve_json_file(file_path)
        elif format == "csv" and file_path.suffix == ".csv":
            return await self._serve_csv_file(file_path)
        elif format == "markdown" and file_path.suffix == ".md":
            return await self._serve_markdown_file(file_path)
        else:
            # Default: serve file directly
            return FileResponse(
                path=file_path,
                filename=manifest.file_name,
                media_type=manifest.mime_type,
            )

    async def _serve_json(self, directory: Path) -> Dict[str, Any]:
        """Serve JSON artifact from directory."""
        # Look for results.json or aggregated results
        for pattern in ["results.json", "*_results.json", "aggregated_results.json"]:
            files = list(directory.glob(pattern))
            if files:
                with open(files[0]) as f:
                    return json.load(f)

        # Fallback: look in seed subdirectories
        for seed_dir in directory.glob("seed_*"):
            result_file = seed_dir / "results.json"
            if result_file.exists():
                with open(result_file) as f:
                    return json.load(f)

        raise ArtifactNotFoundError(f"No JSON results found in {directory}")

    async def _serve_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Serve JSON file."""
        with open(file_path) as f:
            return json.load(f)

    async def _serve_csv(self, directory: Path) -> StreamingResponse:
        """Serve CSV artifact from directory."""
        for pattern in ["curves.csv", "*_curves.csv", "robustness_curves.csv"]:
            files = list(directory.glob(pattern))
            if files:
                return StreamingResponse(
                    iter([files[0].read_bytes()]),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={files[0].name}"},
                )

        # Fallback
        for seed_dir in directory.glob("seed_*"):
            csv_file = seed_dir / "curves.csv"
            if csv_file.exists():
                return StreamingResponse(
                    iter([csv_file.read_bytes()]),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={csv_file.name}"},
                )

        raise ArtifactNotFoundError(f"No CSV curves found in {directory}")

    async def _serve_csv_file(self, file_path: Path) -> StreamingResponse:
        """Serve CSV file."""
        return StreamingResponse(
            iter([file_path.read_bytes()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={file_path.name}"},
        )

    async def _serve_markdown(self, directory: Path) -> StreamingResponse:
        """Serve Markdown artifact from directory."""
        for pattern in ["report.md", "*_report.md"]:
            files = list(directory.glob(pattern))
            if files:
                return StreamingResponse(
                    iter([files[0].read_bytes()]),
                    media_type="text/markdown",
                    headers={"Content-Disposition": f"attachment; filename={files[0].name}"},
                )

        # Fallback
        for seed_dir in directory.glob("seed_*"):
            md_file = seed_dir / "report.md"
            if md_file.exists():
                return StreamingResponse(
                    iter([md_file.read_bytes()]),
                    media_type="text/markdown",
                    headers={"Content-Disposition": f"attachment; filename={md_file.name}"},
                )

        raise ArtifactNotFoundError(f"No Markdown report found in {directory}")

    async def _serve_markdown_file(self, file_path: Path) -> StreamingResponse:
        """Serve Markdown file."""
        return StreamingResponse(
            iter([file_path.read_bytes()]),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={file_path.name}"},
        )

    async def list_artifacts(self, experiment_id: UUID) -> List[Dict[str, Any]]:
        """List all artifacts for an experiment."""
        manifests = await self.artifact_repo.get_by_experiment(experiment_id)
        return [
            {
                "id": str(m.id),
                "type": m.artifact_type.value,
                "seed": m.seed,
                "file_name": m.file_name,
                "file_size": m.file_size_bytes,
                "mime_type": m.mime_type,
                "created_at": m.created_at.isoformat() + "Z",
            }
            for m in manifests
        ]