from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from codex_platform.streams.producer import StreamProducer

from tg_bot.features.telegram.community_feed.logic.orchestrator import CommunityFeedOrchestrator


@pytest.mark.asyncio
async def test_private_dev_group_is_excluded_from_public_community_feed(monkeypatch):
    publish = AsyncMock()
    monkeypatch.setattr(StreamProducer, "publish", publish)
    container = SimpleNamespace(
        settings=SimpleNamespace(telegram_dev_chat_id=-1004387822347, redis_stream_name="test"), redis_client=object()
    )
    message = SimpleNamespace(chat=SimpleNamespace(id=-1004387822347))
    feature = CommunityFeedOrchestrator(container)
    await feature.process_group_message(message, container)
    publish.assert_not_awaited()
    message = SimpleNamespace(
        chat=SimpleNamespace(id=-10042, username=None, title="Public"),
        text="A public community message",
        from_user=None,
        date=datetime.now(UTC),
        message_id=1,
    )
    await feature.process_group_message(message, container)
    publish.assert_awaited_once()
    assert publish.await_args.args[0] == "community.message.approved"
