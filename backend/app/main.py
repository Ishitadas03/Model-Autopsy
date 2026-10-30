"""Model Autopsy FastAPI Application."""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.database import close_db, init_db
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.logging import (
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
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down Model Autopsy API")
    await close_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Model Autopsy: ML Model Robustness Testing & Failure Boundary Detection API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_request_context(request_id=request_id)

        # Add request ID to response headers
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        clear_request_context()
        return response

    # Scientific invariants middleware - inject caveats on boundary/sensitivity fields
    @app.middleware("http")
    async def scientific_invariants_middleware(request: Request, call_next):
        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                import json
                body_bytes = b""
                async for chunk in response.body_iterator:
                    body_bytes += chunk if isinstance(chunk, bytes) else chunk.encode("utf-8")

                body = json.loads(body_bytes.decode("utf-8"))
                body = _inject_scientific_caveats(body)

                headers = dict(response.headers)
                headers.pop("content-length", None)
                return JSONResponse(
                    content=body,
                    status_code=response.status_code,
                    headers=headers,
                )
            except Exception:
                # If we can't parse/modify, return original
                pass

        return response

    # Register exception handlers
    register_exception_handlers(app)

    # Include API router
    app.include_router(api_router, prefix="/api")

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