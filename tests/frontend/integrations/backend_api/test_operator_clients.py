from types import SimpleNamespace

import httpx
import pytest

from src.frontend.integrations.backend_api.combat_ai_testing import CombatAiTestingApi
from src.frontend.integrations.backend_api.game_config import GameConfigApi
from src.studio.features.cabinet.modules.combat_ai_testing.cabinet import _api as simulation_api
from src.studio.settings import StudioSettings


@pytest.mark.parametrize("api_type", [GameConfigApi, CombatAiTestingApi])
async def test_operator_client_uses_method_specific_key_without_service_fallback(api_type):
    seen = []
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: seen.append(request) or httpx.Response(200, json={}))
    ) as client:
        api = api_type(
            client=client,
            base_url="http://backend.test",
            operator_read_key="reader",
            operator_write_key="writer",  # pragma: allowlist secret
        )  # pragma: allowlist secret
        await api._request("GET", "/read")
        await api._request("POST", "/write")
    assert [request.headers.get("X-Operator-Key") for request in seen] == ["reader", "writer"]
    assert all("X-Internal-Service-Key" not in request.headers for request in seen)


@pytest.mark.parametrize("kind", ["local", "prod"])
async def test_studio_selected_source_simulation_capabilities(kind):
    source = StudioSettings(
        _env_file=None,
        local_operator_read_key="local-reader",  # pragma: allowlist secret
        prod_operator_read_key="prod-reader",  # pragma: allowlist secret
        local_operator_write_key="local-writer",  # pragma: allowlist secret
    ).sources()[kind]  # pragma: allowlist secret
    seen = []
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: seen.append(request) or httpx.Response(200, json={"runs": []}))
    ) as client:
        request = SimpleNamespace(
            state=SimpleNamespace(source=source), app=SimpleNamespace(state=SimpleNamespace(backend_http_client=client))
        )
        api = simulation_api(request)
        assert await api.list_runs() == []
        if kind == "prod":
            with pytest.raises(httpx.HTTPStatusError) as exc:
                await api.clear_runs()
            assert exc.value.response.status_code == 403
            assert len(seen) == 1
        else:
            assert await api.clear_runs() == 0
            assert seen[1].headers["X-Operator-Key"] == "local-writer"
    assert seen[0].headers["X-Operator-Key"] == f"{kind}-reader"
    assert all(str(item.url).startswith(source.api_base) for item in seen)
    assert "local-writer" not in repr(source)


@pytest.mark.parametrize("role,expected", [("anonymous", 303), ("user", 303), ("superuser", 200)])
async def test_frontend_config_credentials_stay_behind_superuser_boundary(monkeypatch, role, expected):
    from fastapi import FastAPI, Request

    from src.frontend.features.cabinet.middleware.admin_auth import AdminAuthMiddleware
    from src.frontend.features.cabinet.modules.game_settings import cabinet

    monkeypatch.setattr(cabinet.settings, "backend_operator_read_key", "admin-reader")  # pragma: allowlist secret
    monkeypatch.setattr(cabinet.settings, "backend_operator_write_key", "admin-writer")  # pragma: allowlist secret
    seen = []
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: seen.append(request) or httpx.Response(200, json=[]))
    ) as backend:
        app = FastAPI()
        app.state.backend_http_client = backend
        app.add_middleware(AdminAuthMiddleware)

        @app.middleware("http")
        async def trusted_identity_fixture(request, call_next):
            request.state.user = None if role == "anonymous" else SimpleNamespace(is_superuser=role == "superuser")
            return await call_next(request)

        @app.get("/admin/config")
        async def config_page(request: Request):
            widget = await cabinet._config_provider("test", "Config", "combat", "/admin/config")(request)
            return {"count": len(widget.entries)}

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://site.test") as frontend:
            response = await frontend.get("/admin/config")
    assert response.status_code == expected
    assert len(seen) == (1 if role == "superuser" else 0)
    if seen:
        assert seen[0].headers["X-Operator-Key"] == "admin-reader"
        assert "X-Internal-Service-Key" not in seen[0].headers
    assert "admin-reader" not in response.text and "admin-writer" not in response.text


async def test_operator_client_does_not_inherit_ordinary_frontend_key():
    seen = []
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: seen.append(request) or httpx.Response(200, json=[]))
    ) as client:
        api = GameConfigApi(client=client, base_url="http://backend.test")
        await api.list_namespace("combat")
    assert "X-Operator-Key" not in seen[0].headers
    assert "X-Internal-Service-Key" not in seen[0].headers
