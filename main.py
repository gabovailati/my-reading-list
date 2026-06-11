import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import create_engine, init_db
from routers import items as items_router
from routers import webhook as webhook_router


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/reading_list.db")


def create_app(database_url: str | None = None) -> FastAPI:
    db_url = database_url or get_database_url()
    engine = create_engine(db_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Ensure data directory exists for file-based databases
        if "/:memory:" not in db_url and ":memory:" not in db_url:
            import pathlib
            db_path = db_url.replace("sqlite+aiosqlite:///", "")
            pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        await init_db(engine)

        # Bot startup — implemented in Issue #5 (bot.py)
        bot_app = None
        try:
            from bot import create_bot_app, start_bot, stop_bot  # noqa: PLC0415
            bot_mode = os.getenv("BOT_MODE", "polling")
            bot_app = create_bot_app(mode=bot_mode)
            await start_bot(bot_app, mode=bot_mode)
        except ImportError:
            pass  # bot.py not yet implemented

        app.state.engine = engine
        yield

        if bot_app is not None:
            try:
                from bot import stop_bot  # noqa: PLC0415
                await stop_bot(bot_app, mode=os.getenv("BOT_MODE", "polling"))
            except ImportError:
                pass

        await engine.dispose()

    app = FastAPI(lifespan=lifespan)

    # Auth middleware
    password = os.getenv("BASIC_AUTH_PASSWORD")

    @app.middleware("http")
    async def basic_auth_middleware(request: Request, call_next):
        if request.url.path == "/telegram/webhook":
            return await call_next(request)
        if not password:
            return await call_next(request)
        import base64
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return Response(
                "Unauthorized", status_code=401,
                headers={"WWW-Authenticate": "Basic realm=\"reading-list\""},
            )
        try:
            decoded = base64.b64decode(auth_header[6:]).decode()
            username, _, provided_password = decoded.partition(":")
        except Exception:
            return Response(
                "Unauthorized", status_code=401,
                headers={"WWW-Authenticate": "Basic realm=\"reading-list\""},
            )
        expected_username = os.getenv("BASIC_AUTH_USERNAME", "admin")
        if username != expected_username or provided_password != password:
            return Response(
                "Unauthorized", status_code=401,
                headers={"WWW-Authenticate": "Basic realm=\"reading-list\""},
            )
        return await call_next(request)

    app.include_router(items_router.router)
    app.include_router(webhook_router.router)

    return app


def get_current_user() -> str:
    """Returns the current user ID. Returns 'default' for MVP; swap point for multi-user."""
    return "default"


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
