"""API v1 router."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    health,
    experiments,
    datasets,
    models,
    failures,
    artifacts,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["Experiments"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(failures.router, prefix="/experiments", tags=["Failures"])
api_router.include_router(artifacts.router, prefix="/experiments", tags=["Artifacts"])