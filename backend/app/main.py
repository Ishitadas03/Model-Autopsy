"""Model Autopsy FastAPI Application."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import (
    RequestContextFilter,
    clear_request_context,
    get_logger,
    set_request_context,
    setup_logging,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger.info("Starting Model Autopsy API", version=settings.APP_VERSION)

    # Initialize database
    try:
        await asyncio.wait_for(init_db(), timeout=1.5)
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization deferred (database not ready): {e}")

    yield

    # Shutdown
    logger.info("Shutting down Model Autopsy API")
    try:
        await asyncio.wait_for(close_db(), timeout=1.0)
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")


class ScientificJSONResponse(JSONResponse):
    """Custom JSONResponse that automatically enforces scientific invariants on all responses."""

    def render(self, content: Any) -> bytes:
        if isinstance(content, (dict, list)):
            content = _inject_scientific_caveats(content)
        return super().render(content)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Model Autopsy: ML Model Robustness Testing & Failure Boundary Detection API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ScientificJSONResponse,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=settings.CORS_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_request_context(request_id=request_id)

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        clear_request_context()
        return response

    # Register exception handlers
    register_exception_handlers(app)

    # Include API router
    app.include_router(api_router, prefix="/api")
    app.include_router(api_router, prefix="/api/v1")

    # Direct health check for Render and external monitors
    @app.get("/health", tags=["Health"])
    async def direct_health():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "app": settings.APP_NAME,
        }

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


def _inject_scientific_caveats(data: dict) -> dict:
    """Recursively inject scientific caveats and enforce scientific invariants."""
    if not isinstance(data, dict):
        if isinstance(data, list):
            return [_inject_scientific_caveats(item) for item in data]
        return data

    FORBIDDEN_FIELDS = {
        "robustness_score",
        "robustnessScore",
        "overall_score",
        "overallScore",
        "letter_grade",
        "letterGrade",
        "subjective_rating",
        "subjectiveRating",
    }

    result = {}
    for key, value in data.items():
        # Invariant 3: NO aggregate robustness score, letter grade, or subjective rating
        if key in FORBIDDEN_FIELDS:
            continue

        # Invariant 1: Boundary metric responses MUST include: 'Observed failure boundary under the specified experimental configuration.'
        if key in ("observed_boundary", "observedBoundary", "failure_boundary", "boundary"):
            result[key] = value
            result["observed_boundary_caveat"] = "Observed failure boundary under the specified experimental configuration."
            result["observedBoundaryLabel"] = "Observed failure boundary under the specified experimental configuration."
        # Invariant 2: Feature sensitivity responses MUST include caveat: 'Empirical sensitivity — not a causal explanation.'
        elif key in ("feature_vulnerabilities", "featureVulnerabilities", "feature_sensitivities", "sensitivities"):
            if isinstance(value, list):
                result[key] = [
                    {**item, "caveat": "Empirical sensitivity — not a causal explanation."}
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        elif key in ("most_vulnerable_feature", "mostVulnerableFeature"):
            if isinstance(value, dict):
                vuln = dict(value)
                vuln["caveat"] = "Empirical sensitivity — not a causal explanation."
                result[key] = vuln
            else:
                result[key] = value
        # Recurse into nested dicts
        elif isinstance(value, dict):
            result[key] = _inject_scientific_caveats(value)
        elif isinstance(value, list):
            result[key] = [_inject_scientific_caveats(item) for item in value]
        else:
            result[key] = value

    return result


app = create_app()