"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_session

router = APIRouter()
print("HEALTH GET_SESSION ID:", id(get_session))


@router.get("/health", response_model=dict)
async def health_check(session: AsyncSession = Depends(get_session)) -> dict:
    """Check backend service availability and mode."""
    # Check database connectivity
    db_status = "ok"
    try:
        print("DEBUG HEALTH SESSION BIND:", getattr(session, "bind", None), session)
        await session.execute(text("SELECT 1"))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Health check DB error: {e}", exc_info=True)
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "mode": "live",
        "version": settings.APP_VERSION,
        "database": db_status,
    }