# my-reading-list

A personal reading list app with a Telegram bot interface. Save URLs and notes from Telegram, view and manage them through a web UI.

**Version:** 0.1.0.0 — service layer + FastAPI foundation  
**Status:** Foundation shipped, router implementation in progress (Issue #4), Telegram bot in progress (Issue #5)

---

## Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI (async) |
| Database | SQLite via SQLAlchemy Core + aiosqlite |
| Bot | python-telegram-bot v21 |
| Templates | Jinja2 |
| Server | Uvicorn |

---

## Setup

```bash
pip install -r requirements.txt
```

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./data/reading_list.db` | SQLAlchemy async DB URL |
| `BASIC_AUTH_USERNAME` | No | `admin` | HTTP Basic Auth username |
| `BASIC_AUTH_PASSWORD` | No | *(unset = no auth)* | HTTP Basic Auth password. When unset, auth is skipped entirely (passwordless local dev). |
| `BOT_MODE` | No | `polling` | Telegram bot mode: `polling` or `webhook` |

Create a `.env` file to set them locally:

```
DATABASE_URL=sqlite+aiosqlite:///./data/reading_list.db
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=secret
```

---

## Run

```bash
uvicorn main:app --reload
```

The app creates the `data/` directory and initializes the database on first startup.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/items` | Add a reading list item |
| GET | `/items` | List items (`?status=unread` or `?status=done`) |
| PATCH | `/items/{id}` | Mark an item read or unread |
| DELETE | `/items/{id}` | Remove an item |
| POST | `/telegram/webhook` | Telegram webhook endpoint (no auth required) |

All routes except `/telegram/webhook` require HTTP Basic Auth when `BASIC_AUTH_PASSWORD` is set.

---

## Database

`db.py` is the shared service layer. It uses SQLAlchemy Core (not ORM) with async execution via `aiosqlite`.

- WAL mode is enabled on every connection (better concurrent read/write)
- All items are scoped by `user_id` (ready for multi-user; MVP uses `"default"`)
- Duplicate URLs are allowed
- Marking an item read sets `read_at`; toggling back to unread clears it

Schema:

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT (UUID) | Primary key |
| `user_id` | TEXT | Scope key |
| `url` | TEXT | Nullable |
| `title` | TEXT | Nullable; populated by URL extraction (T3, post-MVP) |
| `note` | TEXT | Nullable |
| `read` | BOOLEAN | Default false |
| `read_at` | DATETIME | Set on mark-read, cleared on mark-unread |
| `created_at` | DATETIME | UTC, set on creation |

---

## Tests

```bash
pytest
```

24 tests covering:
- Service layer: create, list (with status filter), update read state, delete, WAL mode, user isolation, sort order
- Auth middleware: no password (passthrough), missing credentials, valid credentials, wrong password, webhook bypass

---

## Deferred work

See [TODOS.md](TODOS.md) for the full backlog of explicitly deferred items (pagination, Alembic migrations, URL metadata extraction, labels, AI tagging, composite index).
