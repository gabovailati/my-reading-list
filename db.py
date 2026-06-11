import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    select,
    update,
    delete,
    insert,
    event,
)
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

metadata = MetaData()

items = Table(
    "items",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("url", String, nullable=True),
    Column("title", String, nullable=True),
    Column("note", String, nullable=True),
    Column("read", Boolean, nullable=False, default=False),
    Column("read_at", DateTime, nullable=True),
    Column("created_at", DateTime, nullable=False),
)


def create_engine(database_url: str) -> AsyncEngine:
    engine = create_async_engine(database_url)

    @event.listens_for(engine.sync_engine, "connect")
    def set_wal_mode(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")

    return engine


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


def _row_to_dict(row) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "url": row.url,
        "title": row.title,
        "note": row.note,
        "read": row.read,
        "read_at": row.read_at.isoformat() if row.read_at else None,
        "created_at": row.created_at.isoformat(),
    }


async def create_item(
    engine: AsyncEngine,
    user_id: str,
    url: str | None,
    note: str | None,
) -> dict:
    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with engine.begin() as conn:
        await conn.execute(
            insert(items).values(
                id=item_id,
                user_id=user_id,
                url=url,
                title=None,
                note=note,
                read=False,
                read_at=None,
                created_at=now,
            )
        )
        result = await conn.execute(select(items).where(items.c.id == item_id))
        row = result.fetchone()
    return _row_to_dict(row)


async def list_items(
    engine: AsyncEngine,
    user_id: str,
    status: str = "unread",
) -> list[dict]:
    is_read = status == "done"
    async with engine.connect() as conn:
        result = await conn.execute(
            select(items)
            .where(items.c.user_id == user_id)
            .where(items.c.read == is_read)
            .order_by(items.c.created_at.desc())
        )
        rows = result.fetchall()
    return [_row_to_dict(r) for r in rows]


async def update_item(
    engine: AsyncEngine,
    user_id: str,
    item_id: str,
    read: bool,
) -> dict | None:
    read_at = datetime.now(timezone.utc).replace(tzinfo=None) if read else None
    async with engine.begin() as conn:
        await conn.execute(
            update(items)
            .where(items.c.id == item_id)
            .where(items.c.user_id == user_id)
            .values(read=read, read_at=read_at)
        )
        result = await conn.execute(
            select(items)
            .where(items.c.id == item_id)
            .where(items.c.user_id == user_id)
        )
        row = result.fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


async def delete_item(
    engine: AsyncEngine,
    user_id: str,
    item_id: str,
) -> bool:
    async with engine.begin() as conn:
        result = await conn.execute(
            delete(items)
            .where(items.c.id == item_id)
            .where(items.c.user_id == user_id)
        )
    return result.rowcount > 0
