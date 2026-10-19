from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest
from starlette.requests import Request
from starlette.responses import Response

from src.frontend.core.middleware import SiteAnalyticsMiddleware
from src.frontend.features.cabinet.modules.site_analytics import cabinet as site_analytics


class _SessionContext:
    def __init__(self, session: object) -> None:
        self.session = session

    async def __aenter__(self) -> object:
        return self.session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.mark.unit
async def test_site_analytics_middleware_counts_current_lobby_route() -> None:
    request = _request_for_path("/game-lobby")
    middleware = SiteAnalyticsMiddleware(app=SimpleNamespace())

    await middleware.dispatch(request, _ok_response)

    assert request.app.state.site_analytics["visits"] == 1
    assert request.app.state.site_analytics["lobby_visits"] == 1
    assert "game_joins" not in request.app.state.site_analytics


@pytest.mark.unit
async def test_site_analytics_middleware_counts_current_game_enter_route() -> None:
    request = _request_for_path("/game-lobby/enter", method="POST")
    middleware = SiteAnalyticsMiddleware(app=SimpleNamespace())

    await middleware.dispatch(request, _ok_response)

    assert request.app.state.site_analytics["game_joins"] == 1
    assert "lobby_visits" not in request.app.state.site_analytics


@pytest.mark.unit
async def test_site_analytics_middleware_does_not_count_removed_legacy_event_paths() -> None:
    request = _request_for_path("/lobby")
    middleware = SiteAnalyticsMiddleware(app=SimpleNamespace())

    await middleware.dispatch(request, _ok_response)

    assert request.app.state.site_analytics["visits"] == 1
    assert "lobby_visits" not in request.app.state.site_analytics


@pytest.mark.unit
async def test_registrations_provider_counts_site_users(monkeypatch) -> None:
    class FakeUserRepository:
        def __init__(self, session: object) -> None:
            self.session = session

        async def count_all(self) -> int:
            return 8

    monkeypatch.setattr(site_analytics, "get_session_context", lambda: _SessionContext(object()), raising=False)
    monkeypatch.setattr(site_analytics, "UserRepository", FakeUserRepository, raising=False)

    metric = await site_analytics._registrations_provider(_provider_request())

    assert metric.key == "registrations"
    assert metric.value == "8"
    assert metric.subtitle == "site.auth_users"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("provider_name", "key", "title"),
    [
        ("_active_combats_provider", "active_combats", "Активных боёв"),
        ("_active_scenarios_provider", "active_scenarios", "Активных сценариев"),
        ("_active_travels_provider", "active_travels", "Активных путешествий"),
    ],
)
async def test_active_sessions_provider_defers_to_studio_without_http_requests(provider_name, key, title) -> None:
    requests = []

    def record_request(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=[])

    async with httpx.AsyncClient(transport=httpx.MockTransport(record_request)) as client:
        request = _provider_request()
        request.app.state.backend_http_client = client

        metric = await getattr(site_analytics, provider_name)(request)

    assert metric.key == key
    assert metric.title == title
    assert metric.value == "—"
    assert metric.subtitle == "Операторская диагностика доступна в Studio"
    assert requests == []


async def _ok_response(request: Request) -> Response:
    return Response("ok")


def _request_for_path(path: str, *, method: str = "GET") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "scheme": "http",
            "client": ("testclient", 50000),
            "app": SimpleNamespace(state=SimpleNamespace(site_analytics={})),
        }
    )


def _provider_request() -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(backend_http_client=object(), site_analytics={})))
