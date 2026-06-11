import base64

import pytest
from httpx import ASGITransport, AsyncClient

from main import create_app


def _basic_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


@pytest.fixture
def app_with_auth(monkeypatch):
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "secret")
    monkeypatch.setenv("BASIC_AUTH_USERNAME", "admin")
    application = create_app()

    from fastapi.responses import JSONResponse

    @application.get("/items")
    async def items():
        return JSONResponse([])

    @application.post("/telegram/webhook")
    async def webhook():
        return JSONResponse({"ok": True})

    return application


@pytest.fixture
def app_no_auth(monkeypatch):
    monkeypatch.delenv("BASIC_AUTH_PASSWORD", raising=False)
    application = create_app()

    from fastapi.responses import JSONResponse

    @application.get("/items")
    async def items():
        return JSONResponse([])

    return application


@pytest.mark.anyio
async def test_no_password_env_passes_all_routes(app_no_auth):
    async with AsyncClient(
        transport=ASGITransport(app=app_no_auth), base_url="http://test"
    ) as client:
        resp = await client.get("/items")
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_valid_credentials_returns_200(app_with_auth):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_auth), base_url="http://test"
    ) as client:
        resp = await client.get("/items", headers={"Authorization": _basic_header("admin", "secret")})
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_missing_credentials_returns_401(app_with_auth):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_auth), base_url="http://test"
    ) as client:
        resp = await client.get("/items")
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") == 'Basic realm="Reading List"'


@pytest.mark.anyio
async def test_wrong_password_returns_401(app_with_auth):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_auth), base_url="http://test"
    ) as client:
        resp = await client.get("/items", headers={"Authorization": _basic_header("admin", "wrong")})
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") == 'Basic realm="Reading List"'


@pytest.mark.anyio
async def test_wrong_username_returns_401(app_with_auth):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_auth), base_url="http://test"
    ) as client:
        resp = await client.get("/items", headers={"Authorization": _basic_header("wronguser", "secret")})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_telegram_webhook_bypasses_auth(app_with_auth):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_auth), base_url="http://test"
    ) as client:
        resp = await client.post("/telegram/webhook")
    assert resp.status_code == 200
