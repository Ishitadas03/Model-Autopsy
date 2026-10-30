"""Health check endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_session

router = APIRouter()


@router.get("/health", response_model=dict)
async def health_check(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    """Check backend service availability and mode."""
    # Check database connectivity
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "mode": "live",
        "version": settings.APP_VERSION,
        "database": db_status,
    }