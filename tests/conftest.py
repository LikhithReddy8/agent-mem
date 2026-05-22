import os
from pathlib import Path

# Set HF_HOME before any transformers/sentence_transformers imports
project_root = Path(__file__).parent.parent
hf_cache = project_root / ".cache" / "models"
hf_cache.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(hf_cache)

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_mem_test",
)


@pytest.fixture(scope="session")
async def test_engine():
    from api.db import Base
    import api.models  # noqa

    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db(test_engine):
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_engine):
    from api.main import app
    from api.db import get_db

    async def override_db():
        session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
