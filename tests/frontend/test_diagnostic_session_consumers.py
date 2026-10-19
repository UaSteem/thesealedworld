from types import SimpleNamespace

import httpx
import pytest

from src.frontend.features.cabinet.modules.site_analytics.cabinet import _active_sessions_metric
from src.frontend.integrations.backend_api.combat_sessions import CombatSessionsApi
from src.frontend.integrations.backend_api.exploration_sessions import ExplorationSessionsApi
from src.frontend.integrations.backend_api.scenario_sessions import ScenarioSessionsApi


@pytest.mark.parametrize("api_type", [CombatSessionsApi, ScenarioSessionsApi, ExplorationSessionsApi])
async def test_session_client_preserves_cursor_and_key_without_automatic_scan(api_type):
    seen = []

    def backend(request):
        seen.append(request)
        return httpx.Response(200, json=[{"session_id": "one"}], headers={"X-Next-Cursor": "51:2"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(backend)) as client:
        api = api_type(
            client=client,
            base_url="http://selected-source",
            internal_service_key="reader",  # pragma: allowlist secret - synthetic test credential
            internal_service_header="X-Operator-Key",
        )
        assert await api.list_page(cursor="31:0", limit=7) == ([{"session_id": "one"}], "51:2")
    assert len(seen) == 1
    assert dict(seen[0].url.params) == {"cursor": "31:0", "limit": "7"}
    assert seen[0].headers["X-Operator-Key"] == "reader"
    assert "X-Internal-Service-Key" not in seen[0].headers


async def test_site_metric_never_calls_operator_api_or_reports_false_zero():
    class ForbiddenApi:
        def __init__(self, **kwargs):
            raise AssertionError("Public frontend must not request operator diagnostics")

    metric = await _active_sessions_metric(SimpleNamespace(), api_cls=ForbiddenApi, key="combats", title="Бои")
    assert metric.value == "—"
    assert "Studio" in metric.subtitle
