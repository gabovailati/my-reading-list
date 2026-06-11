import pytest
import pytest_asyncio
from db import create_engine, init_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    eng = create_engine(TEST_DB_URL)
    await init_db(eng)
    yield eng
    await eng.dispose()
