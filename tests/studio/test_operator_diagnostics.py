from types import SimpleNamespace

import httpx
import pytest

from src.studio.features.cabinet.modules.combat import cabinet
from src.studio.settings import StudioSettings


@pytest.mark.parametrize("kind", ["local", "prod"])
async def test_diagnostic_client_uses_selected_source_read_key(kind):
    settings = StudioSettings(
        _env_file=None, local_operator_read_key="local-reader", prod_operator_read_key="prod-reader"
    )
    source = settings.sources()[kind]
    seen = []

    def backend(request):
        seen.append(request)
        return httpx.Response(200, json={"count": 1})

    async with httpx.AsyncClient(transport=httpx.MockTransport(backend)) as client:
        request = SimpleNamespace(
            state=SimpleNamespace(source=source), app=SimpleNamespace(state=SimpleNamespace(backend_http_client=client))
        )
        assert await cabinet._get_summary_data(request) == {"count": 1}
    assert seen[0].headers["X-Operator-Key"] == f"{kind}-reader"
    assert "X-Internal-Service-Key" not in seen[0].headers
    assert str(seen[0].url).startswith(source.api_base)
    assert source.operator_read_key not in repr(source)


async def test_unconfigured_source_does_not_fall_back_to_site_key():
    source = StudioSettings(_env_file=None, local_operator_read_key="").sources()["local"]
    seen = []

    def backend(request):
        seen.append(request)
        return httpx.Response(403, json={"detail": "Operator read access required"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(backend)) as client:
        request = SimpleNamespace(
            state=SimpleNamespace(source=source), app=SimpleNamespace(state=SimpleNamespace(backend_http_client=client))
        )
        assert await cabinet._get_summary_data(request) == {}
    assert "X-Operator-Key" not in seen[0].headers
    assert "X-Internal-Service-Key" not in seen[0].headers


@pytest.mark.parametrize("domain", ["combat", "scenario", "exploration"])
@pytest.mark.parametrize("status,rows,next_cursor", [(200, [], "17:0"), (200, [], None), (403, [], None)])
async def test_session_table_distinguishes_sample_continuation_and_unavailable(domain, status, rows, next_cursor):
    from importlib import import_module

    module = import_module(f"src.studio.features.cabinet.modules.{domain}.cabinet")
    source = StudioSettings(_env_file=None, local_operator_read_key="local-reader").sources()["local"]
    seen = []

    def backend(request):
        seen.append(request)
        return httpx.Response(status, json=rows, headers={"X-Next-Cursor": next_cursor} if next_cursor else {})

    async with httpx.AsyncClient(transport=httpx.MockTransport(backend)) as client:
        request = SimpleNamespace(
            state=SimpleNamespace(source=source), app=SimpleNamespace(state=SimpleNamespace(backend_http_client=client))
        )
        table = await module._sessions_provider(request)
    assert len(seen) == 1
    assert seen[0].headers["X-Operator-Key"] == "local-reader"
    assert seen[0].url.params["limit"] == "100"
    if status == 403:
        assert "недоступны" in table.title
    else:
        assert "Выборка" in table.title
        assert ("есть продолжение" in table.title) == bool(next_cursor)
