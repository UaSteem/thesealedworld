from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from starlette.requests import Request

from src.frontend.config.settings import settings
from src.frontend.features.auth.routes.pages import logout
from src.frontend.game_features.session.token_state import GAME_REFRESH_COOKIE_NAME


def _request():
    request = Request(
        {
            "type": "http",
            "headers": [
                (b"cookie", (f"tbmmorpg_refresh_token=site-old; {GAME_REFRESH_COOKIE_NAME}=game-refresh").encode())
            ],
            "app": SimpleNamespace(state=SimpleNamespace(backend_http_client=None)),
        }
    )
    request.state.auth_tokens = SimpleNamespace(refresh_token="site-rotated")
    request.state.game_tokens = SimpleNamespace(access_token="pending-access")
    return request


@pytest.mark.unit
async def test_browser_logout_revokes_game_and_current_site_refresh_clears_all_cookies(monkeypatch):
    monkeypatch.setattr(settings, "auth_cookie_domain", ".example.test")
    api = SimpleNamespace(logout_token=AsyncMock())
    monkeypatch.setattr("src.frontend.features.auth.routes.pages.BackendGameLobbyApi", lambda **kwargs: api)
    auth = SimpleNamespace(refresh_cookie_name="tbmmorpg_refresh_token", logout=AsyncMock())
    request = _request()
    response = await logout(request, auth)
    assert response.status_code == 303
    api.logout_token.assert_awaited_once_with("game-refresh", token_type="game_refresh")
    auth.logout.assert_awaited_once_with("site-rotated")
    assert request.state.auth_tokens is None
    assert request.state.game_tokens is None
    cookies = response.headers.getlist("set-cookie")
    for name in (
        "tbmmorpg_access_token",
        "tbmmorpg_refresh_token",
        "tbmmorpg_game_access_token",
        "tbmmorpg_game_refresh_token",
        "tbmmorpg_active_character_id",
    ):
        matches = [cookie for cookie in cookies if cookie.startswith(f"{name}=")]
        assert any("Domain=.example.test" in cookie for cookie in matches)
        assert any("Domain=" not in cookie for cookie in matches)
        assert all("Max-Age=0" in cookie and "Path=/" in cookie for cookie in matches)


@pytest.mark.unit
async def test_browser_logout_unavailable_preserves_credentials_for_retry(monkeypatch):
    api = SimpleNamespace(logout_token=AsyncMock(side_effect=httpx.ConnectError("offline")))
    monkeypatch.setattr("src.frontend.features.auth.routes.pages.BackendGameLobbyApi", lambda **kwargs: api)
    auth = SimpleNamespace(refresh_cookie_name="tbmmorpg_refresh_token", logout=AsyncMock())
    request = _request()
    response = await logout(request, auth)
    assert response.status_code == 503
    assert "set-cookie" not in response.headers
    auth.logout.assert_not_awaited()
    assert request.state.auth_tokens is not None


@pytest.mark.unit
@pytest.mark.parametrize("refresh_status", [200, 401])
async def test_logout_also_revokes_access_when_refresh_is_stale_or_invalid(monkeypatch, refresh_status):
    rejected = httpx.HTTPStatusError(
        "invalid refresh",
        request=httpx.Request("POST", "http://test/logout"),
        response=httpx.Response(refresh_status),
    )
    api = SimpleNamespace(logout_token=AsyncMock(side_effect=[rejected if refresh_status == 401 else None, None]))
    monkeypatch.setattr("src.frontend.features.auth.routes.pages.BackendGameLobbyApi", lambda **kwargs: api)
    request = _request()
    request.cookies["tbmmorpg_game_access_token"] = "current-access"
    auth = SimpleNamespace(refresh_cookie_name="tbmmorpg_refresh_token", logout=AsyncMock())
    response = await logout(request, auth)
    assert response.status_code == 303
    assert api.logout_token.await_args_list[1].args == ("current-access",)
    assert api.logout_token.await_args_list[1].kwargs == {"token_type": "game_access"}
