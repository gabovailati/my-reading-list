import pytest
from db import create_item, list_items, update_item, delete_item

USER = "default"


@pytest.mark.asyncio
async def test_create_item_with_url(engine):
    item = await create_item(engine, USER, "https://example.com", None)
    assert item["url"] == "https://example.com"
    assert item["note"] is None
    assert item["read"] is False
    assert item["read_at"] is None
    assert item["user_id"] == USER
    assert item["id"]
    assert item["created_at"]


@pytest.mark.asyncio
async def test_create_item_with_note_only(engine):
    item = await create_item(engine, USER, None, "Have a look at Gstack")
    assert item["url"] is None
    assert item["note"] == "Have a look at Gstack"
    assert item["read"] is False


@pytest.mark.asyncio
async def test_create_item_with_url_and_note(engine):
    item = await create_item(engine, USER, "https://example.com", "interesting")
    assert item["url"] == "https://example.com"
    assert item["note"] == "interesting"


@pytest.mark.asyncio
async def test_duplicate_urls_allowed(engine):
    item1 = await create_item(engine, USER, "https://example.com", None)
    item2 = await create_item(engine, USER, "https://example.com", None)
    assert item1["id"] != item2["id"]


@pytest.mark.asyncio
async def test_list_items_unread_filter(engine):
    await create_item(engine, USER, "https://a.com", None)
    await create_item(engine, USER, "https://b.com", None)
    unread = await list_items(engine, USER, "unread")
    assert len(unread) == 2
    assert all(not item["read"] for item in unread)


@pytest.mark.asyncio
async def test_list_items_done_filter(engine):
    item = await create_item(engine, USER, "https://a.com", None)
    await update_item(engine, USER, item["id"], read=True)
    done = await list_items(engine, USER, "done")
    assert len(done) == 1
    assert done[0]["read"] is True


@pytest.mark.asyncio
async def test_list_items_empty(engine):
    result = await list_items(engine, USER, "unread")
    assert result == []


@pytest.mark.asyncio
async def test_list_items_sorted_newest_first(engine):
    item1 = await create_item(engine, USER, "https://first.com", None)
    item2 = await create_item(engine, USER, "https://second.com", None)
    unread = await list_items(engine, USER, "unread")
    # newest first — item2 was created after item1
    assert unread[0]["id"] == item2["id"]
    assert unread[1]["id"] == item1["id"]


@pytest.mark.asyncio
async def test_update_item_mark_read(engine):
    item = await create_item(engine, USER, "https://example.com", None)
    updated = await update_item(engine, USER, item["id"], read=True)
    assert updated["read"] is True
    assert updated["read_at"] is not None


@pytest.mark.asyncio
async def test_update_item_mark_unread(engine):
    item = await create_item(engine, USER, "https://example.com", None)
    await update_item(engine, USER, item["id"], read=True)
    updated = await update_item(engine, USER, item["id"], read=False)
    assert updated["read"] is False
    assert updated["read_at"] is None


@pytest.mark.asyncio
async def test_update_item_not_found(engine):
    result = await update_item(engine, USER, "nonexistent-id", read=True)
    assert result is None


@pytest.mark.asyncio
async def test_update_item_wrong_user(engine):
    item = await create_item(engine, USER, "https://example.com", None)
    result = await update_item(engine, "other-user", item["id"], read=True)
    assert result is None


@pytest.mark.asyncio
async def test_delete_item_success(engine):
    item = await create_item(engine, USER, "https://example.com", None)
    deleted = await delete_item(engine, USER, item["id"])
    assert deleted is True
    remaining = await list_items(engine, USER, "unread")
    assert len(remaining) == 0


@pytest.mark.asyncio
async def test_delete_item_not_found(engine):
    result = await delete_item(engine, USER, "nonexistent-id")
    assert result is False


@pytest.mark.asyncio
async def test_delete_item_wrong_user(engine):
    item = await create_item(engine, USER, "https://example.com", None)
    result = await delete_item(engine, "other-user", item["id"])
    assert result is False
    # item still exists for original user
    remaining = await list_items(engine, USER, "unread")
    assert len(remaining) == 1


@pytest.mark.asyncio
async def test_wal_mode():
    # WAL mode only applies to file-based SQLite; :memory: always returns 'memory'.
    # Use a temp file to verify the event listener fires correctly.
    import tempfile, os
    from sqlalchemy import text
    from db import create_engine, init_db

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        file_engine = create_engine(f"sqlite+aiosqlite:///{db_path}")
        await init_db(file_engine)
        async with file_engine.connect() as conn:
            result = await conn.execute(text("PRAGMA journal_mode"))
            mode = result.scalar()
        await file_engine.dispose()
        assert mode == "wal"
    finally:
        os.unlink(db_path)
