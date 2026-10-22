from unittest.mock import AsyncMock, MagicMock

import pytest

from src.backend.core.bus.recovery import PendingQuarantineStorage


@pytest.mark.asyncio
async def test_scan_advances_past_ineligible_and_failed_entries():
    client = AsyncMock()
    client.xpending_range.side_effect = [
        [{"message_id": "1-0"}, {"message_id": "2-0"}],
        [{"message_id": "3-0"}],
    ]
    client.eval.side_effect = [0, RuntimeError("write failed"), 1]
    delegate = AsyncMock()
    delegate.read_events.return_value = [("4-0", {"type": "new"})]
    storage = PendingQuarantineStorage(client, delegate, min_idle_ms=100, scan_count=2)

    for _ in range(2):
        assert await storage.read_events("events", "group", "worker", 10, None) == [("4-0", {"type": "new"})]

    assert client.xpending_range.call_args_list[1].kwargs["min"] == "(2-0"
    assert client.eval.call_count == 3


@pytest.mark.parametrize("idle,count", [(0, 1), (-1, 1), (1, 0)])
def test_recovery_limits_must_be_positive(idle, count):
    with pytest.raises(ValueError):
        PendingQuarantineStorage(AsyncMock(), AsyncMock(), min_idle_ms=idle, scan_count=count)


@pytest.mark.parametrize("field", ["stream_pending_min_idle_ms", "stream_pending_scan_count"])
def test_settings_reject_zero_limits(field):
    from src.backend.config.settings import BackendSettings

    with pytest.raises(ValueError):
        BackendSettings(**{field: 0})


@pytest.mark.parametrize("groups", [None, ["character"]])
def test_actual_container_runtimes_install_recovery(groups, monkeypatch):
    from fastapi import FastAPI

    from src.backend.config.settings import BackendSettings
    from src.backend.core.containers import redis as container

    config = BackendSettings(
        stream_enabled_groups=groups, stream_consumer_group="chosen", stream_pending_min_idle_ms=123
    )
    monkeypatch.setattr(container, "settings", config)
    app = FastAPI()
    app.state.redis_client = MagicMock()
    runtimes = container.RedisContainer()._build_stream_runtimes(app)
    assert len(runtimes) == (1 if groups else len(container.EVENT_ROUTER_GROUPS))
    for runtime in runtimes:
        assert isinstance(runtime.processor.storage, PendingQuarantineStorage)
        assert runtime.processor.storage.min_idle_ms == 123
        assert runtime.processor.storage.delegate is runtime.consumer


@pytest.mark.asyncio
async def test_helper_installs_recovery(monkeypatch):
    from fastapi import FastAPI

    from src.backend.core import lifespan
    from src.backend.core.bus.recovery import GameStreamRuntime

    monkeypatch.setattr(GameStreamRuntime, "start", AsyncMock())
    app = FastAPI()
    app.state.redis_client = MagicMock()
    await lifespan.start_event_bus(app)
    assert isinstance(app.state.stream_runtime.processor.storage, PendingQuarantineStorage)


@pytest.mark.asyncio
async def test_chat_runtime_installs_recovery(monkeypatch):
    from fastapi import FastAPI

    from src.backend.chat.core import lifespan
    from src.backend.core.bus.recovery import GameStreamRuntime

    client = AsyncMock()
    monkeypatch.setattr(lifespan.aioredis, "from_url", lambda *args, **kwargs: client)
    monkeypatch.setattr(GameStreamRuntime, "start", AsyncMock())
    monkeypatch.setattr(GameStreamRuntime, "stop", AsyncMock())
    app = FastAPI()
    async with lifespan.lifespan(app):
        assert isinstance(app.state.stream_runtime.processor.storage, PendingQuarantineStorage)
