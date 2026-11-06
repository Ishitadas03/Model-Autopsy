"""Health check and storage observability endpoints."""

import asyncio
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.core.config import settings
    from app.core.database import get_session
    from app.services.storage_service import storage_service
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.database import get_session
    from backend.app.services.storage_service import storage_service

router = APIRouter()


@router.get("/health", response_model=dict)
async def health_check(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    """Check backend service availability, database connectivity, and storage status."""
    db_status = "ok"
    try:
        await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=4.0)
    except Exception:
        db_status = "error"

    storage_info = {
        "active_provider": storage_service.active_provider,
        "is_r2_configured": storage_service.is_configured(),
        "bucket_name": storage_service.bucket_name,
    }

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "mode": "live",
        "version": settings.APP_VERSION,
        "database": db_status,
        "storage": storage_info,
    }


@router.get("/storage/status", response_model=dict)
async def storage_status() -> dict:
    """Detailed Cloudflare R2 and local storage status verification."""
    access_check = storage_service.check_bucket_access()
    return {
        "active_provider": storage_service.active_provider,
        "is_r2_configured": storage_service.is_configured(),
        "bucket_name": storage_service.bucket_name,
        "bucket_accessible": access_check.get("accessible", False),
        "access_details": access_check,
        "local_datasets_dir": str(storage_service.get_local_path("datasets")),
        "local_artifacts_dir": str(storage_service.get_local_path("experiments")),
    }
