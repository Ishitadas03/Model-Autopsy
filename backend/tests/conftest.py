"""Pytest configuration and fixtures."""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import Base, get_session
from app.main import create_app
from app.models import (  # noqa: F401
    experiment,
    dataset,
    model_adapter,
    failure_sample,
    artifact,
)


# Test database URL (use SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    # Clean up test database file
    test_db = Path("./test.db")
    if test_db.exists():
        test_db.unlink()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with dependency override."""
    app = create_app()

    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
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