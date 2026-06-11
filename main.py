import base64
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response


def _valid_basic_auth(credentials: str, username: str, password: str) -> bool:
    if not credentials.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(credentials[6:]).decode("utf-8")
        user, pwd = decoded.split(":", 1)
        return user == username and pwd == password
    except Exception:
        return False


def create_app(database_url: str = "sqlite+aiosqlite:///data/reading_list.db") -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # DB startup and bot init wired here in Issues #1/#2/#5
        yield

    app = FastAPI(lifespan=lifespan)

    @app.middleware("http")
    async def basic_auth_middleware(request: Request, call_next):
        if request.url.path == "/telegram/webhook":
            return await call_next(request)
        password = os.getenv("BASIC_AUTH_PASSWORD")
        if not password:
            return await call_next(request)
        credentials = request.headers.get("Authorization", "")
        if not _valid_basic_auth(
            credentials,
            os.getenv("BASIC_AUTH_USERNAME", "admin"),
            password,
        ):
            return Response(
                "Unauthorized",
                status_code=401,
                headers={"WWW-Authenticate": "Basic"},
            )
        return await call_next(request)

    # Routers mounted in Issues #4/#5
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
