# Model Autopsy Backend

FastAPI backend for the Model Autopsy ML robustness research platform.

## Features

- **REST API** matching frontend contract exactly
- **Async experiment execution** with progress tracking
- **ML Engine integration** for E001-E004 experiments
- **PostgreSQL** with async SQLAlchemy and Alembic migrations
- **Artifact management** for results, curves, and reports
- **Scientific invariant enforcement** (caveats on boundaries/sensitivities)

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 16 (or use Docker Compose)
- ML Engine installed (`pip install -e ../ml_engine`)

### Installation

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install ML engine in development mode
pip install -e ../ml_engine

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### Database Setup

```bash
# Start PostgreSQL (if using Docker Compose from project root)
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Seed default datasets and models
python -c "
import asyncio
from backend.app.core.database import init_db, async_session_factory
from backend.app.repositories.dataset import DatasetRepository
from backend.app.repositories.model_adapter import ModelAdapterRepository

async def seed():
    await init_db()
    async with async_session_factory() as session:
        await DatasetRepository(session).seed_default_datasets()
        await ModelAdapterRepository(session).seed_default_adapters()
        await session.commit()

asyncio.run(seed())
"
```

### Running the Server

```bash
# Development
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/model_autopsy` | Async PostgreSQL connection URL |
| `ML_ENGINE_PATH` | `../ml_engine` | Path to ML engine root directory |
| `ARTIFACTS_BASE_DIR` | `../artifacts/experiments` | Base directory for experiment artifacts |
| `CONFIGS_BASE_DIR` | `../configs/experiments` | Base directory for experiment YAML configs |
| `SCRIPTS_BASE_DIR` | `../scripts/experiments` | Base directory for experiment runner scripts |
| `MAX_CONCURRENT_EXPERIMENTS` | `2` | Maximum concurrent experiments |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Debug mode |

## API Endpoints

### Health
- `GET /api/health` - Service health check

### Experiments
- `GET /api/experiments` - List all experiments
- `GET /api/experiments/{id}` - Get experiment details
- `POST /api/experiments` - Create new experiment
- `POST /api/experiments/{id}/cancel` - Cancel running experiment
- `GET /api/experiments/{id}/progress` - Get experiment progress

### Datasets
- `GET /api/datasets` - List available datasets
- `GET /api/datasets/{id}` - Get dataset details

### Models
- `GET /api/models` - List model adapters
- `GET /api/models/{id}` - Get model adapter details

### Failures
- `GET /api/experiments/{id}/failures` - Get paginated failed samples

### Artifacts
- `GET /api/experiments/e003?format={json|csv|markdown}` - Get E003 canonical artifact
- `GET /api/experiments/{id}/artifacts/{type}` - Get experiment artifact

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=backend/app --cov-report=html

# Specific test file
pytest tests/test_health.py -v
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app factory
│   ├── core/                   # Core configuration
│   │   ├── config.py           # Pydantic settings
│   │   ├── database.py         # Async DB setup
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── logging.py          # Structured logging
│   ├── models/                 # SQLAlchemy models
│   ├── repositories/           # Data access layer
│   ├── services/               # Business logic
│   │   ├── experiment_service.py
│   │   ├── ml_engine_bridge.py
│   │   └── artifact_service.py
│   ├── api/v1/                 # API endpoints
│   │   ├── router.py
│   │   └── endpoints/
│   └── schemas/                # Pydantic schemas (re-exported from ml_engine)
├── alembic/                    # Database migrations
├── tests/                      # Test suite
├── requirements.txt
├── Dockerfile
├── pytest.ini
└── alembic.ini
```

## Scientific Invariants

The backend enforces the following scientific invariants on all responses:

1. **Boundary metrics** include caveat: *"Observed failure boundary under the specified experimental configuration."*
2. **Feature sensitivities** include caveat: *"Empirical sensitivity — not a causal explanation."*
3. **No aggregate robustness score**, letter grade, or subjective rating
4. **Metric polarity**: f1/accuracy/roc_auc = higher better; mae/mse/loss = lower better

## Docker

```bash
# Build
docker build -t model-autopsy-backend -f Dockerfile .

# Run
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e ML_ENGINE_PATH=/app/ml_engine \
  -e ARTIFACTS_BASE_DIR=/app/artifacts/experiments \
  model-autopsy-backend
```

## Development

### Adding a New Migration

```bash
# After modifying models
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

### Code Quality

```bash
# Type checking
mypy backend/app

# Linting
ruff check backend/app

# Format
ruff format backend/app
```