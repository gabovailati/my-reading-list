# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0.0] - 2026-06-11

### Added

- **Shared database service layer** (`db.py`) — async SQLAlchemy Core engine with WAL mode, full CRUD for reading list items (`create_item`, `list_items`, `update_item`, `delete_item`). Items are scoped by `user_id` from day one. Duplicate URLs are allowed. Marking an item read sets `read_at`; toggling back to unread clears it.

- **FastAPI application factory** (`main.py`) — `create_app(database_url)` factory for test isolation. Async lifespan context initialises the database on startup and disposes the engine on shutdown (including on startup failure). Data directory is created automatically for file-based SQLite.

- **HTTP Basic Auth middleware** — protects all routes with `BASIC_AUTH_PASSWORD` / `BASIC_AUTH_USERNAME` env vars. Timing-safe comparison via `hmac.compare_digest`. `/telegram/webhook` is explicitly exempt (Telegram secret token validation comes in a future release). Auth is a no-op when the env var is unset, enabling passwordless local dev.

- **Router stubs** for `POST /items`, `GET /items`, `PATCH /items/{id}`, `DELETE /items/{id}`, and `POST /telegram/webhook` — mount cleanly so the app boots; full implementation in the next PR.

- **Test suite** — 24 tests covering all service layer operations (create, list with status filter, update read state, delete, WAL mode, user isolation, sort order) and all auth middleware branches (no password, missing creds, valid creds, wrong password, webhook bypass).
