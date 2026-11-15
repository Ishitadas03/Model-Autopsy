"""Health check and storage observability endpoints."""

import asyncio
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
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


@router.get("/ready", response_model=dict)
async def readiness() -> JSONResponse:
    """Deployment gate: only ready with migrated DB, auth config, and durable R2."""
    checks = {"database": False, "authentication": False, "r2_storage": False}
    try:
        from app.core.database import async_session_factory
        async with async_session_factory() as session:
            version = (await session.execute(text("SELECT version_num FROM alembic_version"))).scalar_one_or_none()
            checks["database"] = version == "003_durable_jobs"
    except Exception:
        pass

    checks["authentication"] = (
        settings.APP_ENV != "production"
        or (settings.AUTH_REQUIRED and bool(settings.SUPABASE_URL))
    )
    if settings.APP_ENV == "production":
        try:
            access = await asyncio.wait_for(
                asyncio.to_thread(storage_service.check_bucket_access), timeout=6
            )
            checks["r2_storage"] = (
                settings.STORAGE_PROVIDER == "r2"
                and storage_service.is_configured()
                and bool(access.get("accessible"))
            )
        except Exception:
            checks["r2_storage"] = False
    else:
        checks["r2_storage"] = True

    ready = all(checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ready" if ready else "not_ready", "checks": checks},
        headers={"Cache-Control": "no-store"},
    )


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

    }
