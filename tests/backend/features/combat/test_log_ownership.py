from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI, Request

from src.backend.core.auth import User, get_current_user
from src.backend.core.game_auth import create_game_access_token
from src.backend.features.combat.api.router import router
from src.backend.features.combat.dependencies import (
    get_combat_character_repository,
    get_combat_runtime_orchestrator,
)
from src.shared.schemas.combat import CombatLogDTO


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("authenticated", "scope_char_id", "owner", "expected"),
    [(False, None, True, 401), (True, 6, True, 403), (True, 5, False, 404), (True, 5, True, 200)],
)
async def test_logs_require_auth_scope_and_owner_before_read(authenticated, scope_char_id, owner, expected):
    app = FastAPI()
    app.include_router(router)
    user_id = uuid4()
    calls = []

    class Characters:
        async def get_by_id_and_user_id(self, char_id, requested_user_id):
            calls.append(("owner", char_id, requested_user_id))
            return object() if owner else None

    class Orchestrator:
        async def get_logs(self, char_id, **kwargs):
            calls.append(("logs", char_id, kwargs))
            return CombatLogDTO(session_id="battle-1", page=kwargs["page"], page_size=kwargs["page_size"])

    async def current_user(request: Request):
        request.state.game_token_claims = SimpleNamespace(sub=user_id, character_id=scope_char_id)
        return User(id=user_id)

    if authenticated:
        app.dependency_overrides[get_current_user] = current_user
    app.dependency_overrides[get_combat_character_repository] = Characters
    app.dependency_overrides[get_combat_runtime_orchestrator] = Orchestrator
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/game/combat/5/logs?page=2&page_size=8")
    assert response.status_code == expected
    reads = [call for call in calls if call[0] == "logs"]
    if expected == 200:
        assert calls == [("owner", 5, user_id), ("logs", 5, {"page": 2, "page_size": 8})]
        assert response.json()["session_id"] == "battle-1"
    else:
        assert not reads
    if expected in (401, 403):
        assert not calls


@pytest.mark.asyncio
async def test_logs_reject_signed_game_token_for_another_character():
    app = FastAPI()
    app.include_router(router)
    calls = []

    class Characters:
        async def get_by_id_and_user_id(self, *args):
            calls.append("ownership")
            return object()

    class Orchestrator:
        async def get_logs(self, *args, **kwargs):
            calls.append("logs")
            return CombatLogDTO()

    app.dependency_overrides[get_combat_character_repository] = Characters
    app.dependency_overrides[get_combat_runtime_orchestrator] = Orchestrator
    token = create_game_access_token(user_id=uuid4(), character_id=6, session_id="test-session")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/game/combat/5/logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert not calls
