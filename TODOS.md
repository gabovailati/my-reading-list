# TODOS

Deferred items from the engineering review of the reading list app design.
Each item was considered during `/plan-eng-review` and explicitly deferred from MVP scope.

---

## T1 — Pagination for GET /items

**What:** Add cursor-based or page-number pagination to `GET /items` (e.g. `GET /items?status=unread&page=2&per_page=50`).

**Why:** The current unbounded list is fine at personal-tool scale (tens to hundreds of items), but HTMX swaps the entire list on every toggle — this degrades noticeably at 500+ items.

**Pros:** Keeps the UI snappy as the list grows; enables infinite-scroll or next/prev UX.

**Cons:** Adds LIMIT/OFFSET logic to `db.py:list_items` and HTMX pagination fragments to the template; marginal complexity for early usage volume.

**Context:** The review accepted unbounded list as an explicit MVP scope decision (D8). When the list grows, pagination is a ~2h change: add `LIMIT`/`OFFSET` to `list_items` in `db.py`, add prev/next HTMX fragment partials to the template.

**Depends on:** Nothing — additive to existing `GET /items`.

---

## T2 — Alembic migrations

**What:** Add Alembic for database schema migration management, replacing the current "ALTER TABLE for nullable additions / file-drop for breaking changes" approach.

**Why:** The current approach works for MVP but breaks down when: (a) production data can't be dropped, (b) multiple breaking changes pile up, or (c) multi-user lands and needs coordinated migrations. Alembic gives versioned, reversible migrations with an audit trail.

**Pros:** Safe schema evolution with production data; rollback support; industry-standard pattern.

**Cons:** Adds `alembic/` tree and `alembic.ini`; `alembic upgrade head` must run on deploy; slight ops overhead.

**Context:** Explicitly deferred: "no Alembic for MVP." The cross-model tension resolution (tension #3) added `ALTER TABLE ADD COLUMN` for nullable additions, which buys more runway before Alembic is needed. Add when the schema stabilizes post-MVP (after labels + URL metadata land).

**Depends on:** Schema stabilization — after labels and URL metadata columns land.

---

## T3 — URL metadata extraction (trafilatura)

**What:** When a URL is added via the bot, extract its title and description using `trafilatura` (async-safe wrapper, 2-second timeout, fallback to raw URL on failure). Store result in `items.title`.

**Why:** Without extraction, `title` shows the raw URL (e.g. `https://example.com/very-long-slug`). Extracted titles make the reading list actually readable at a glance.

**Pros:** Transforms the app from a link dump into a real reading list; high user-visible value.

**Cons:** Adds `trafilatura` dependency; network call on every URL capture (mitigated by 2s timeout + fallback); some sites block scrapers.

**Context:** Explicitly listed as post-MVP in the design doc. Library choice (`trafilatura`) is already recorded in the plan. Run synchronously inside `POST /items` handler (FastAPI runs it in a thread pool via `asyncio.to_thread`); fall back to raw URL on timeout or error.

**Depends on:** Nothing — additive to `POST /items` handler.

---

## T4 — Labels (#tag syntax)

**What:** Add a `labels` TEXT column (comma-separated for MVP, junction table post-multi-user) to `items`. Bot parses `#tag` syntax in messages on capture. Add `GET /items?label=foo` filter to the API and UI.

**Why:** Allows organizing the reading list by topic (e.g. `#gstack`, `#work`, `#ai`) — the key organizational feature described in the original problem statement.

**Pros:** Unlocks topic-based filtering; aligns with the "organized reading list" goal; natural Telegram UX (hashtags are familiar).

**Cons:** Adds parsing logic to the bot handler; adds a filter parameter to `list_items`; schema migration needed (ALTER TABLE).

**Context:** Explicitly post-MVP. The labels column is added via `ALTER TABLE items ADD COLUMN labels TEXT` (no data loss — per cross-model tension #3 resolution). Bot handler strips `#tags` from message text and stores them separately.

**Depends on:** T2 (Alembic) is recommended before adding labels — the schema change is simple but it's a good first migration to validate the Alembic setup.

---

## T5 — AI organization / auto-tagging

**What:** Auto-categorize items using an LLM API (low-cost Claude model, e.g. Haiku — verify current model ID at time of implementation) on capture or on-demand.

**Why:** Reduces manual labeling effort; could suggest labels, group related items, or flag items of unusual interest.

**Pros:** Aligns with the original "experiment with AI" goal; high novelty value for a gstack/Conductor experiment.

**Cons:** Adds LLM API cost (minimal with Haiku but non-zero); requires prompt design and eval; potential latency on capture.

**Context:** Explicitly post-MVP. The design originally mentioned this as "AI-assisted organization." Add after the label system (T4) is in place — auto-tagging is most useful when there's a label taxonomy to suggest into.

**Depends on:** T4 (Labels) — auto-tagging needs a label system to write into.
