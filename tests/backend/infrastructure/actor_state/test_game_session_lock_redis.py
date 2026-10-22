"""Opt-in adapter checks against an explicitly selected disposable Redis."""

import asyncio
import os
from typing import Annotated
from uuid import uuid4

import httpx
import pytest
from codex_platform.redis_service import RedisService
from fastapi import Depends, FastAPI
from redis.asyncio import Redis

from src.backend.core.auth import User, get_current_user
from src.backend.core.game_auth import create_game_token_pair
from src.backend.features.game_lobby.api.router import router
from src.backend.infrastructure.redis.managers import build_redis_managers


@pytest.mark.external
@pytest.mark.integration
async def test_real_redis_logout_refresh_races_and_captured_http_credentials(monkeypatch):
    url = os.environ.get("TEST_REDIS_URL")
    if not url:
        pytest.skip("requires explicitly provided disposable TEST_REDIS_URL")
    from src.backend.config.settings import settings

    service_key = "synthetic-internal-service-key"  # pragma: allowlist secret - synthetic test credential
    monkeypatch.setattr(settings, "frontend_internal_service_key", service_key)
    monkeypatch.setattr(settings, "secret_key", "synthetic-session-signing-key")
    raw = Redis.from_url(url, decode_responses=True)
    manager = build_redis_managers(RedisService(raw)).game_session_lock
    character_id = uuid4().int % (10**15)
    key = manager.build_key(character_id)
    pair = create_game_token_pair(user_id=uuid4(), character_id=character_id, session_id="session-A")
    app = FastAPI()
    app.state.game_session_lock = manager
    app.include_router(router)

    @app.get("/protected")
    async def protected(user: Annotated[User, Depends(get_current_user)]):
        return {"user_id": str(user.id)}

    try:
        # Whichever operation wins first, renewal never resurrects a deleted key.
        for _ in range(20):
            await manager.claim(character_id, "session-A")
            await asyncio.gather(
                manager.release_if_current(character_id, "session-A"),
                *(manager.touch_if_current(character_id, "session-A") for _ in range(8)),
            )
            assert await manager.current(character_id) is None
        # Neither stale logout nor stale renewal may delete/replace a newer login.
        for _ in range(20):
            await manager.claim(character_id, "session-A")
            await asyncio.gather(
                manager.claim(character_id, "session-B"),
                manager.release_if_current(character_id, "session-A"),
                manager.touch_if_current(character_id, "session-A"),
            )
            assert await manager.current(character_id) == "session-B"

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as anonymous:
            response = await anonymous.post("/game-lobby/logout-token", json={"token": pair.refresh_token})
            assert response.status_code == 403
            assert await manager.current(character_id) == "session-B"

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Internal-Service-Key": service_key},
        ) as client:
            # A stale signed credential cannot revoke the replacement session.
            response = await client.post("/game-lobby/logout-token", json={"token": pair.refresh_token})
            assert response.status_code == 200
            assert response.json() == {"revoked": False}
            assert await manager.current(character_id) == "session-B"

            await manager.claim(character_id, "session-A")
            assert (
                await client.get("/protected", headers={"Authorization": f"Bearer {pair.access_token}"})
            ).status_code == 200
            response = await client.post("/game-lobby/logout-token", json={"token": pair.refresh_token})
            assert response.status_code == 200 and response.json() == {"revoked": True}
            assert (
                await client.get("/protected", headers={"Authorization": f"Bearer {pair.access_token}"})
            ).status_code == 409
            response = await client.post("/game-lobby/refresh-token", json={"refresh_token": pair.refresh_token})
            assert response.status_code == 409
            assert await manager.current(character_id) is None
    finally:
        await raw.delete(key)
        await raw.aclose()
