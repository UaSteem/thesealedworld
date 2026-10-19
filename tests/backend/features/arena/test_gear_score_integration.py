from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from tests.backend.features.arena.test_arena_service import FakeStore

from src.backend.features.arena.integrations import arena_integration as module
from src.backend.features.arena.integrations.arena_integration import ArenaIntegration
from src.backend.features.arena.integrations.session_integration import ArenaSessionIntegration
from src.backend.features.arena.integrations.stream_client import ArenaStreamClient


def integration(session=None):
    sessions = None
    if session is not None:

        async def patch(_char_id, fields):
            for path, value in fields.items():
                session.setdefault("metrics", {})[path.rsplit(".", 1)[-1]] = value

        sessions = SimpleNamespace(
            get_session=AsyncMock(return_value=session),
            get_sessions_batch=AsyncMock(return_value={1: session}),
            patch_fields=AsyncMock(side_effect=patch),
        )
    calculator = Mock()
    calculator.calculate_breakdown_from_active_character.return_value = {"total": 35.79}
    stream = SimpleNamespace(request_gear_scores=AsyncMock(return_value={1: 35.79}))
    return ArenaIntegration(
        session_manager=Mock(),
        stream_client=stream,
        character_sessions=sessions,
        gear_score_calculator=calculator,
    )


@pytest.mark.asyncio
async def test_legacy_cache_recalculates_once_and_retains_float():
    session = {"metrics": {"gear_score": 100}}
    arena = integration(session)
    assert await arena.fetch_gear_score(1) == 36
    assert await arena.fetch_gear_scores([1]) == {1: 36}
    arena.gear_score_calculator.calculate_breakdown_from_active_character.assert_called_once_with(session)
    assert session["metrics"]["gear_score"] == 35.79
    assert session["metrics"]["gear_score_version"] == module.GEAR_SCORE_VERSION
    assert session["metrics"]["gear_score_breakdown"] == {"total": 35.79}


@pytest.mark.asyncio
async def test_current_cache_preserves_rounding_without_recalculation():
    arena = integration({"metrics": {"gear_score": 35.79, "gear_score_version": module.GEAR_SCORE_VERSION}})
    assert await arena.fetch_gear_score(1) == 36
    assert await arena.fetch_gear_scores([1]) == {1: 36}
    arena.gear_score_calculator.calculate_breakdown_from_active_character.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("score", [float("nan"), float("inf"), -1, "35.79", True])
async def test_invalid_current_cache_is_recalculated(score):
    arena = integration({"metrics": {"gear_score": score, "gear_score_version": module.GEAR_SCORE_VERSION}})
    assert await arena.fetch_gear_score(1) == 36
    arena.gear_score_calculator.calculate_breakdown_from_active_character.assert_called_once()


@pytest.mark.asyncio
async def test_event_transport_keeps_float_and_arena_rounds_without_session():
    events = SimpleNamespace(request=AsyncMock(return_value={"status": "ok", "gear_scores": json.dumps({"1": 35.79})}))
    stream = ArenaStreamClient(events)
    assert await stream.request_gear_scores([1]) == {1: 35.79}
    arena = integration()
    arena.stream_client = stream
    assert await arena.fetch_gear_score(1) == 36
    assert await arena.fetch_gear_scores([1]) == {1: 36}


@pytest.mark.asyncio
async def test_missing_session_falls_back_to_events_and_missing_score_still_errors():
    arena = integration({})
    arena.character_sessions.get_session.return_value = None
    arena.character_sessions.get_sessions_batch.return_value = {}
    assert await arena.fetch_gear_score(1) == 36
    assert await arena.fetch_gear_scores([1]) == {1: 36}
    arena.stream_client.request_gear_scores.return_value = {}
    with pytest.raises(RuntimeError, match="unavailable"):
        await arena.fetch_gear_score(1)


@pytest.mark.asyncio
async def test_live_queue_uses_current_score_and_keeps_fifteen_percent_bounds():
    arena = integration({"metrics": {"gear_score": 100}})
    store = FakeStore()
    store.claim_opponent = AsyncMock(return_value=None)
    session = ArenaSessionIntegration(store, gear_scores=arena)
    assert await session.join_queue(1, "duel") == 36
    assert store.requests[1].gs == 36
    await session.find_opponent(1, "duel")
    store.claim_opponent.assert_awaited_once_with("duel", 1, 36 * 0.85, 36 * 1.15)


@pytest.mark.asyncio
async def test_live_queue_unavailable_score_does_not_enqueue_default():
    arena = integration()
    arena.stream_client.request_gear_scores.return_value = {}
    store = FakeStore()
    session = ArenaSessionIntegration(store, gear_scores=arena)
    with pytest.raises(RuntimeError, match="unavailable"):
        await session.join_queue(1, "duel")
    assert store.requests == {}


def test_app_dependency_connects_real_score_provider(monkeypatch):
    from src.backend.features.arena import dependencies

    store = Mock()
    monkeypatch.setattr(dependencies, "ArenaSessionManager", Mock(return_value=store))
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                redis=Mock(),
                events=Mock(),
                character_sessions=Mock(),
            )
        )
    )
    service = dependencies.get_arena_service(request, Mock())
    provider = service.session.gear_scores
    assert isinstance(provider, ArenaIntegration)
    assert provider.character_sessions is request.app.state.character_sessions
    assert provider.stream_client.events is request.app.state.events
