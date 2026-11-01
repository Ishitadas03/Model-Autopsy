"""Pytest configuration and fixtures."""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add project root and backend to path
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
ml_engine_src = project_root / "ml_engine" / "src"

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(ml_engine_src))
sys.path.insert(0, str(backend_dir))

from backend.app.core.config import settings
from backend.app.core.database import Base, get_session
from backend.app.main import create_app
from backend.app.models import (  # noqa: F401
    experiment,
    dataset,
    model_adapter,
    failure_sample,
    artifact,
)


# Test database URL (use SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    test_db = Path("./test.db")
    if test_db.exists():
        try:
            test_db.unlink()
        except OSError:
            pass


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with dependency override."""
    from backend.app.main import app

    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def seed_datasets(test_session):
    """Seed default datasets."""
    from backend.app.repositories.dataset import DatasetRepository

    repo = DatasetRepository(test_session)
    await repo.seed_default_datasets()
    await test_session.commit()


@pytest.fixture
async def seed_models(test_session, seed_datasets):
    """Seed default model adapters."""
    from backend.app.repositories.model_adapter import ModelAdapterRepository

    repo = ModelAdapterRepository(test_session)
    await repo.seed_default_adapters()
    await test_session.commit()


@pytest.fixture
async def seed_experiment(test_session, seed_datasets, seed_models):
    """Seed a sample experiment with runs, results, and failed samples."""
    from backend.app.models.experiment import Experiment, ExperimentRun, ExperimentResult, ExperimentStatus, TaskType, StressType, StressMode
    from backend.app.models.failure_sample import FailedSample

    exp = Experiment(
        experiment_id="EXP-0241",
        model_name="RandomForest-v2 (Credit)",
        dataset_name="German Credit Benchmark",
        dataset_id="german-credit",
        task_type=TaskType.CLASSIFICATION,
        perturbation_family=StressType.GAUSSIAN_NOISE,
        noise_type="Gaussian Noise",
        evaluation_metric="f1",
        failure_threshold=0.80,
        seed=42,
        stress_mode=StressMode.INCREMENTAL,
        severity_levels=[0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
        seeds=[42, 123],
        config_yaml="experiment:\n  name: EXP-0241\n",
        status=ExperimentStatus.COMPLETED,
        progress_percent=100,
    )
    test_session.add(exp)
    await test_session.flush()

    run1 = ExperimentRun(
        experiment_id=exp.id,
        seed=42,
        run_index=0,
        status=ExperimentStatus.COMPLETED,
        progress_percent=100,
    )
    run2 = ExperimentRun(
        experiment_id=exp.id,
        seed=123,
        run_index=1,
        status=ExperimentStatus.COMPLETED,
        progress_percent=100,
    )
    test_session.add_all([run1, run2])

    curve_data = [
        {"noiseLevel": 0.0, "score": 0.958},
        {"noiseLevel": 0.05, "score": 0.932},
        {"noiseLevel": 0.10, "score": 0.885},
        {"noiseLevel": 0.15, "score": 0.841},
        {"noiseLevel": 0.20, "score": 0.824},
        {"noiseLevel": 0.25, "score": 0.768},
        {"noiseLevel": 0.30, "score": 0.712},
    ]

    vulns = [
        {"feature": "Credit Score", "drop": 0.284, "rank": 1, "caveat": "Empirical sensitivity — not a causal explanation."},
        {"feature": "Income", "drop": 0.192, "rank": 2, "caveat": "Empirical sensitivity — not a causal explanation."},
        {"feature": "Age", "drop": 0.115, "rank": 3, "caveat": "Empirical sensitivity — not a causal explanation."},
        {"feature": "Loan Amount", "drop": 0.083, "rank": 4, "caveat": "Empirical sensitivity — not a causal explanation."},
    ]

    result = ExperimentResult(
        experiment_id=exp.id,
        baseline_macro_f1=0.958,
        baseline_accuracy=0.958,
        worst_case_macro_f1=0.712,
        worst_case_accuracy=0.712,
        observed_boundary=0.231,
        failed_samples_count=25,
        curve_data=curve_data,
        feature_vulnerabilities=vulns,
        statistical_validation={"numSeeds": 2, "mean": 0.712, "std": 0.012, "ci95": 0.015},
    )
    test_session.add(result)

    # Add 25 failed samples for pagination and filtering tests
    for i in range(25):
        sample = FailedSample(
            experiment_id=exp.id,
            sample_index=i + 1,
            sample_id=f"samp-{101 + i}",
            true_label="Legitimate" if i % 2 == 0 else "Fraud",
            predicted_label="Fraud" if i % 2 == 0 else "Legitimate",
            confidence=0.874,
            noise_level=0.20,
            seed=42,
            features_clean={"Income": 65000, "Credit Score": 720, "Age": 34, "Loan Amount": 12000},
            features_stressed={"Income": 58200, "Credit Score": 580, "Age": 34, "Loan Amount": 12000},
            feature_diffs={"Income": -6800, "Credit Score": -140, "Age": 0, "Loan Amount": 0},
        )
        test_session.add(sample)

    await test_session.commit()
    return exp