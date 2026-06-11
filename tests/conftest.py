import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from db import create_engine, init_db
from main import create_app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    eng = create_engine(TEST_DB_URL)
    await init_db(eng)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def client():
    app = create_app(database_url=TEST_DB_URL)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c
