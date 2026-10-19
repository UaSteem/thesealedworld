import asyncio
import os
import time
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.testclient import TestClient

from src.backend.chat.services.connection_manager import ChatConnectionManager
from src.backend.realtime.api import ws as ws_module
from src.backend.realtime.services.connection_manager import RealtimeConnectionManager


@pytest.fixture
def socket_app(monkeypatch):
    monkeypatch.setattr("src.backend.realtime.services.session_guard.SESSION_POLL_SECONDS", 0.05)
    app = FastAPI()
    app.include_router(ws_module.router)
    lock = SimpleNamespace(session="session", failed=False)

    async def current(_character_id):
        if lock.failed:
            raise RuntimeError("storage unavailable")
        return lock.session

    lock.current = current
    app.state.game_session_lock = lock
    app.state.realtime_manager = RealtimeConnectionManager()
    app.state.chat_manager = ChatConnectionManager()
    app.state.redis = SimpleNamespace()
    app.state.chat_sessions = SimpleNamespace(get_state=AsyncMock(return_value={}))
    claims = SimpleNamespace(sub=uuid.uuid4(), character_id=42, session_id="session", exp=time.time() + 30)
    monkeypatch.setattr(ws_module, "decode_game_access_token", lambda _: claims)
    monkeypatch.setattr(ws_module.settings, "realtime_allowed_origins", ["https://play.example.test"])
    return app, lock, claims


def connect(client, suffix=""):
    return client.websocket_connect("/ws/realtime?token=test" + suffix, headers={"Origin": "https://play.example.test"})


@pytest.mark.parametrize("failure,code", [("replace", 4003), ("logout", 4003), ("expiry", 4001), ("storage", 4003)])
def test_idle_socket_closes_when_authority_is_lost(socket_app, failure, code):
    app, lock, claims = socket_app
    if failure == "expiry":
        claims.exp = time.time() + 0.1
    with TestClient(app) as client, connect(client) as socket:
        if failure == "replace":
            lock.session = "replacement"
        elif failure == "logout":
            lock.session = None
        elif failure == "expiry":
            pass
        else:
            lock.failed = True
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()
        assert closed.value.code == code
    assert app.state.realtime_manager.active_count == 0
    assert not app.state.chat_manager._by_ws


def test_query_character_cannot_bootstrap_another_identity(socket_app):
    app, _, _ = socket_app
    with TestClient(app) as client, connect(client, "&char_id=999") as socket:
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()
        assert closed.value.code == 4001
    assert not app.state.chat_manager._by_ws


@pytest.mark.parametrize("delivery", ["notice", "chat", "incoming"])
def test_revocation_is_checked_on_each_delivery_before_monitor(socket_app, monkeypatch, delivery):
    app, lock, _ = socket_app
    monkeypatch.setattr("src.backend.realtime.services.session_guard.SESSION_POLL_SECONDS", 100)
    handle = AsyncMock()
    monkeypatch.setattr(ws_module.ChatBridge, "handle_chat_send", handle)
    with TestClient(app) as client, connect(client) as socket:
        lock.session = "replacement"
        if delivery == "incoming":
            socket.send_json({"type": "chat.send", "payload": {"channel": "global", "content": "rejected"}})
        elif delivery == "notice":

            async def send():
                assert not await app.state.realtime_manager.send_to_character(42, {"type": "private.notice"})

            client.portal.call(send)
        else:
            client.portal.call(app.state.chat_manager.broadcast_topic, "chat:global", {"content": "private"})
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()
        assert closed.value.code == 4003
        handle.assert_not_awaited()
        assert not app.state.chat_manager._by_ws
    assert app.state.realtime_manager.active_count == 0


@pytest.mark.parametrize("kind,code", [("size", 1009), ("rate", 1008), ("binary", 1003)])
def test_websocket_transport_budget(socket_app, monkeypatch, kind, code):
    app, _, _ = socket_app
    monkeypatch.setattr("src.backend.realtime.services.session_guard.FRAME_RATE", 0)
    monkeypatch.setattr("src.backend.realtime.services.session_guard.FRAME_BURST", 2)
    with TestClient(app) as client, connect(client) as socket:
        if kind == "size":
            socket.send_text("ж" * 9000)
        elif kind == "binary":
            socket.send_bytes(b"not a text frame")
        else:
            for _ in range(3):
                socket.send_json({"type": "pong"})
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()
        assert closed.value.code == code
    assert not app.state.chat_manager._by_ws


def test_absent_lock_fails_closed(socket_app):
    app, _, _ = socket_app
    del app.state.game_session_lock
    with TestClient(app) as client, connect(client) as socket:
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()
        assert closed.value.code == 4003
    assert app.state.realtime_manager.active_count == 0


def test_slow_session_store_fails_closed_and_background_tasks_are_cleaned(socket_app, monkeypatch):
    app, lock, _ = socket_app
    monkeypatch.setattr("src.backend.realtime.services.session_guard.STORAGE_TIMEOUT_SECONDS", 0.02)
    with TestClient(app) as client:
        with connect(client) as socket:

            async def unavailable(_character_id):
                await asyncio.Event().wait()

            lock.current = unavailable
            with pytest.raises(WebSocketDisconnect) as closed:
                socket.receive_json()
            assert closed.value.code == 4003

        async def remaining_tasks():
            await asyncio.sleep(0)
            return [task.get_name() for task in asyncio.all_tasks() if task.get_name().startswith("realtime-")]

        assert client.portal.call(remaining_tasks) == []
        assert app.state.realtime_manager.active_count == 0


def test_revoke_while_outbound_delivery_is_waiting_cancels_send(socket_app):
    app, lock, _ = socket_app
    with TestClient(app) as client, connect(client) as socket:
        entry = app.state.realtime_manager.get(42)
        guard = entry.ws
        started = asyncio.Event()
        cancelled = asyncio.Event()
        original = guard._socket.send_text

        async def blocked_send(_data):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        async def race():
            guard._socket.send_text = blocked_send
            delivery = asyncio.create_task(app.state.realtime_manager.send_to_character(42, {"type": "private.notice"}))
            await started.wait()
            lock.session = "replacement"
            assert not await delivery
            assert cancelled.is_set()
            assert not guard._pending_sends
            guard._socket.send_text = original

        client.portal.call(race)
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()
        assert closed.value.code == 4003
        assert not app.state.chat_manager._by_ws


@pytest.mark.skipif(not os.environ.get("TEST_REALTIME_REDIS_URL"), reason="Requires disposable TEST_REALTIME_REDIS_URL")
@pytest.mark.parametrize("action", ["replacement", "logout"])
def test_real_redis_session_revocation_closes_actual_asgi_socket(socket_app, monkeypatch, action):
    from codex_platform.redis_service import RedisService
    from redis.asyncio import Redis

    from src.backend.core.game_auth import (
        create_game_access_token,
        create_game_refresh_token,
        decode_game_access_token,
        require_internal_service_key,
    )
    from src.backend.features.game_lobby.api.router import router as lobby_router
    from src.backend.infrastructure.actor_state.managers.game_session_lock import GameSessionLockManager

    app, _, claims = socket_app
    redis = Redis.from_url(os.environ["TEST_REALTIME_REDIS_URL"], decode_responses=True)
    manager = GameSessionLockManager(RedisService(redis), ttl_seconds=60)
    character_id = uuid.uuid4().int & ((1 << 62) - 1)
    session_id = uuid.uuid4().hex
    monkeypatch.setattr(ws_module.settings, "secret_key", "synthetic-ws-session-signing-key")
    monkeypatch.setattr(ws_module, "decode_game_access_token", decode_game_access_token)
    token = create_game_access_token(user_id=claims.sub, character_id=character_id, session_id=session_id)
    app.state.game_session_lock = manager
    app.include_router(lobby_router)
    app.dependency_overrides[require_internal_service_key] = lambda: object()
    with TestClient(app) as client:
        try:
            client.portal.call(manager.claim, character_id, session_id)
            with client.websocket_connect(
                "/ws/realtime?token=" + token, headers={"Origin": "https://play.example.test"}
            ) as socket:
                if action == "replacement":
                    client.portal.call(manager.claim, character_id, "new-session")
                else:
                    refresh = create_game_refresh_token(
                        user_id=claims.sub, character_id=character_id, session_id=session_id
                    )
                    response = client.post("/game-lobby/logout-token", json={"token": refresh})
                    assert response.status_code == 200
                    assert response.json() == {"revoked": True}
                with pytest.raises(WebSocketDisconnect) as closed:
                    socket.receive_json()
                assert closed.value.code == 4003
            assert app.state.realtime_manager.active_count == 0
        finally:
            client.portal.call(redis.delete, manager.build_key(character_id))
            client.portal.call(redis.aclose)
