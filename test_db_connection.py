import asyncio
from sqlalchemy import create_async_engine

# Use hardcoded connection string for testing since environment variable isn't set
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/model_autopsy"

engine = create_async_engine(DATABASE_URL)

async def test_connection():
    async with engine.connect() as conn:
        await conn.execute(asyncio.text('SELECT 1'))
    print('Database connection successful')

asyncio.run(test_connection())