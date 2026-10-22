import base64
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from src.studio.features.sources.redis_readonly import ReadOnlyRedis
from src.studio.security import StudioAccessMiddleware, guard_source_request, selected_source
from src.studio.settings import StudioSettings

TOKEN = "synthetic-studio-access-password"  # pragma: allowlist secret


def auth():
    return {"Authorization": "Basic " + base64.b64encode(("studio:" + TOKEN).encode()).decode()}


@pytest.mark.parametrize("password,status", [("", 503), (TOKEN, 401)])
async def test_studio_requires_configured_identity(password, status):
    app = FastAPI()
    app.add_middleware(StudioAccessMiddleware, settings=StudioSettings(_env_file=None, studio_access_token=password))

    @app.get("/")
    def home():
        return {"ok": True}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost") as client:
        assert (await client.get("/")).status_code == status


async def test_authenticated_host_and_csrf_boundaries():
    app = FastAPI()
    app.add_middleware(StudioAccessMiddleware, settings=StudioSettings(_env_file=None, studio_access_token=TOKEN))

    @app.post("/studio/source")
    def source():
        return {"ok": True}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost", headers=auth()
    ) as client:
        assert (await client.post("/studio/source")).status_code == 403
        assert (await client.post("/studio/source", headers={"Origin": "http://evil.test"})).status_code == 403
        assert (await client.post("/studio/source", headers={"Origin": "http://localhost"})).status_code == 200
        assert (
            await client.post("/studio/source", headers={"Host": "evil.test", "Origin": "http://evil.test"})
        ).status_code == 403


@pytest.mark.parametrize("kind", ["local", "prod"])
async def test_selected_http_readonly_and_explicit_local_compute(kind):
    source = StudioSettings(_env_file=None).sources()[kind]
    handle = selected_source.set(source)
    try:
        await guard_source_request(httpx.Request("GET", source.api_base + "/api/report"))
        for target in ["/api/mutate", "/api/admin/combat-ai/simulation-runs/clear"]:
            with pytest.raises(PermissionError):
                await guard_source_request(httpx.Request("POST", source.api_base + target))
        request = httpx.Request("POST", source.api_base + "/api/admin/combat-ai/simulation-runs/train-battle")
        if kind == "local":
            await guard_source_request(request)
        else:
            with pytest.raises(PermissionError):
                await guard_source_request(request)
        with pytest.raises(PermissionError):
            await guard_source_request(httpx.Request("GET", "http://evil.test/api/report"))
    finally:
        selected_source.reset(handle)


async def test_redis_wrapper_denies_mutation_before_client():
    calls = []

    async def execute(*args, **kwargs):
        calls.append(args)
        return '{"ok": true}' if args[0] == "JSON.GET" else "value"

    client = ReadOnlyRedis(SimpleNamespace(execute_command=execute))
    assert await client.get("key") == "value"
    assert await client.json().get("key") == {"ok": True}
    for command in ["SET", "EVAL", "DEL", "JSON.SET", "CONFIG"]:
        with pytest.raises(PermissionError):
            await client.execute_command(command, "key", "value")
    with pytest.raises(AttributeError):
        client.pipeline()
    assert [row[0] for row in calls] == ["GET", "JSON.GET"]


@pytest.mark.parametrize(
    "fallback,cookie,expected", [("local", "prod", 403), ("prod", "local", 200), ("prod", "invalid", 403)]
)
async def test_selected_source_gate_uses_cookie_before_fallback(fallback, cookie, expected):
    app = FastAPI()
    settings = StudioSettings(_env_file=None, studio_access_token=TOKEN, studio_source=fallback)
    app.add_middleware(StudioAccessMiddleware, settings=settings)

    @app.post("/admin/action")
    async def action():
        return {"ok": True}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost", headers=auth()
    ) as client:
        response = await client.post(
            "/admin/action", headers={"Origin": "http://localhost", "Cookie": "studio_source=" + cookie}
        )
        assert response.status_code == expected


async def test_unbound_http_transport_denies_even_reads():
    with pytest.raises(PermissionError):
        await guard_source_request(httpx.Request("GET", "http://localhost/api/report"))


async def test_postgres_reads_use_readonly_transaction_and_no_raw_execute():
    from contextlib import asynccontextmanager

    from src.studio.features.sources.postgres_readonly import ReadOnlyPostgresPool

    modes = []
    queries = []

    class Connection:
        @asynccontextmanager
        async def transaction(self, **kwargs):
            modes.append(kwargs)
            yield

        async def fetch(self, query, *args, **kwargs):
            queries.append(query)
            return [1]

    class Pool:
        @asynccontextmanager
        async def acquire(self):
            yield Connection()

    wrapped = ReadOnlyPostgresPool(Pool())
    async with wrapped.acquire() as connection:
        assert await connection.fetch("SELECT 1") == [1]
        for query in ["UPDATE data SET value=1", "SET transaction_read_only=off", "SELECT 1; DELETE FROM data", ""]:
            with pytest.raises(PermissionError):
                await connection.fetch(query)
        with pytest.raises(AttributeError):
            connection.execute("DELETE FROM data")
    assert modes == [{"readonly": True}]
    assert queries == ["SELECT 1"]


async def test_postgres_registry_enables_server_readonly(monkeypatch):
    import asyncpg

    from src.studio.features.sources.postgres_readonly import PostgresPoolRegistry

    calls = []

    async def create_pool(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(asyncpg, "create_pool", create_pool)
    registry = PostgresPoolRegistry()
    for kind in ["local", "prod"]:
        await registry.get(StudioSettings(_env_file=None).sources()[kind])
    assert len(calls) == 2
    assert all(call["server_settings"] == {"default_transaction_read_only": "on"} for call in calls)
