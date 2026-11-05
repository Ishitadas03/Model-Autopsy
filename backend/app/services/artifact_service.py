"""Artifact service for managing experiment artifacts."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi import Response
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse

from app.core.config import settings
from app.core.exceptions import ArtifactNotFoundError
from app.core.logging import get_logger
from app.models.artifact import ArtifactManifest, ArtifactType
from app.repositories.artifact import ArtifactRepository
from app.repositories.experiment import ExperimentRepository

logger = get_logger(__name__)


class ArtifactService:
    """Service for managing and serving experiment artifacts."""

    def __init__(self, session):
        self.session = session
        self.artifact_repo = ArtifactRepository(session)
        self.exp_repo = ExperimentRepository(session)

    async def get_e003_artifact(self, format: str) -> Union[Dict[str, Any], Response]:
        """Get E003 canonical experiment artifact in specified format."""
        e003_dir = settings.ARTIFACTS_BASE_DIR / "E003"

        format_str = str(format).lower()
        if format_str in ("json", "application/json"):
            return await self._serve_json(e003_dir)
        elif format_str in ("csv", "text/csv"):
            return await self._serve_csv(e003_dir)
        elif format_str in ("markdown", "md", "text/markdown"):
            return await self._serve_markdown(e003_dir)
        else:
            raise ArtifactNotFoundError(f"Format {format} not supported for E003")

    async def get_artifact(
        self,
        experiment_id: UUID,
        artifact_type: str,
        seed: Optional[int],
        format: str,
    ) -> Union[Dict[str, Any], Response]:
        """Get experiment artifact by type."""
        try:
            artifact_type_enum = ArtifactType(artifact_type)
        except ValueError:
            raise ArtifactNotFoundError(f"Unknown artifact type: {artifact_type}")

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

        format_str = str(format).lower()
        if format_str == "json" and file_path.suffix == ".json":
            return await self._serve_json_file(file_path)
        elif format_str == "csv" and file_path.suffix == ".csv":
            return await self._serve_csv_file(file_path)
        elif format_str in ("markdown", "md") and file_path.suffix == ".md":
            return await self._serve_markdown_file(file_path)
        else:
            return FileResponse(
                path=file_path,
                filename=manifest.file_name,
                media_type=manifest.mime_type,
            )

    async def _serve_json(self, directory: Path) -> Dict[str, Any]:
        """Serve JSON artifact from directory."""
        if not directory.exists():
            raise ArtifactNotFoundError(f"Artifacts directory {directory} not found")

        # Priority search patterns for canonical E003 / experiment JSON artifacts
        for pattern in [
            "aggregate_comparison.json",
            "aggregate_results.json",
            "results.json",
            "*comparison*.json",
            "*results*.json",
            "*.json",
        ]:
            files = list(directory.glob(pattern))
            if files:
                with open(files[0], "r", encoding="utf-8") as f:
                    return json.load(f)

        # Fallback to subdirectories
        for f in directory.rglob("*.json"):
            with open(f, "r", encoding="utf-8") as json_f:
                return json.load(json_f)

        raise ArtifactNotFoundError(f"No JSON results found in {directory}")

    async def _serve_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Serve JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def _serve_csv(self, directory: Path) -> Response:
        """Serve CSV artifact from directory."""
        if not directory.exists():
            raise ArtifactNotFoundError(f"Artifacts directory {directory} not found")

        for pattern in [
            "aggregate_comparison.csv",
            "aggregate_results.csv",
            "curves.csv",
            "*curves*.csv",
            "*comparison*.csv",
            "*.csv",
        ]:
            files = list(directory.glob(pattern))
            if files:
                content = files[0].read_bytes()
                return Response(
                    content=content,
                    media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{files[0].name}"'},
                )

        for f in directory.rglob("*.csv"):
            content = f.read_bytes()
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{f.name}"'},
            )

        raise ArtifactNotFoundError(f"No CSV curves found in {directory}")

    async def _serve_csv_file(self, file_path: Path) -> Response:
        """Serve CSV file."""
        content = file_path.read_bytes()
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'},
        )

    async def _serve_markdown(self, directory: Path) -> Response:
        """Serve Markdown artifact from directory."""
        if not directory.exists():
            raise ArtifactNotFoundError(f"Artifacts directory {directory} not found")

        for pattern in ["report.md", "*report*.md", "*.md"]:
            files = list(directory.glob(pattern))
            if files:
                content = files[0].read_bytes()
                return Response(
                    content=content,
                    media_type="text/markdown",
                    headers={"Content-Disposition": f'attachment; filename="{files[0].name}"'},
                )

        for f in directory.rglob("*.md"):
            content = f.read_bytes()
            return Response(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{f.name}"'},
            )

        raise ArtifactNotFoundError(f"No Markdown report found in {directory}")

    async def _serve_markdown_file(self, file_path: Path) -> Response:
        """Serve Markdown file."""
        content = file_path.read_bytes()
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'},
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
