"""Model Autopsy FastAPI Application."""
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

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

    # The free Render web instance has no separate always-on worker.
    # Spawn one durable polling task ONLY when the current DB schema is ready.
    database_ready = False
    worker_shutdown = None
    worker_task = None
    try:
        await asyncio.wait_for(init_db(), timeout=10.0)
        database_ready = True
        logger.info("Database initialized and schema checked")
    except Exception as e:
        logger.error("Database not ready; experiment worker will not start: %s", e)

    app.state.embedded_worker_task = None
    if settings.JOB_EXECUTION_MODE == "embedded":
        if database_ready:
            from app.workers.experiment_worker import serve_jobs
            worker_shutdown = asyncio.Event()
            worker_task = asyncio.create_task(
                serve_jobs(worker_shutdown),
                name="embedded-durable-ml-queue",
            )
            app.state.embedded_worker_task = worker_task
            logger.warning(
                "Embedded free-tier worker active: jobs may be interrupted "
                "by Render spin-down or instance restart"
            )
        else:
            logger.error("Embedded worker disabled until database migrations complete")

    try:
        yield
    finally:
        # Stop claiming jobs before the process shuts down. A cancellation
        # terminates the child process; status remains durable in PostgreSQL.
        if worker_shutdown is not None:
            worker_shutdown.set()
        if worker_task is not None:
            try:
                await asyncio.wait_for(worker_task, timeout=8.0)
            except asyncio.TimeoutError:
                worker_task.cancel()
                await asyncio.gather(worker_task, return_exceptions=True)
            except asyncio.CancelledError:
                worker_task.cancel()
                await asyncio.gather(worker_task, return_exceptions=True)

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