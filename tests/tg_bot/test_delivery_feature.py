from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tg_bot.features.redis.announcements.logic.orchestrator import AnnouncementsOrchestrator


@pytest.mark.asyncio
async def test_news_uses_discovered_delivery_feature_for_publish_and_unpublish():
    delivery = SimpleNamespace(publish_news=AsyncMock(), unpublish_news=AsyncMock())
    requested = []

    def get_feature(key):
        requested.append(key)
        return delivery

    container = SimpleNamespace(
        settings=SimpleNamespace(telegram_channel_id="-10042", domain_name="https://game.test"),
        get_feature=get_feature,
    )
    feature = AnnouncementsOrchestrator(container)
    await feature.process_news({"id": 42, "title": "News", "slug": "news"})
    await feature.process_news_unpublished({"id": 42})
    assert requested == ["delivery", "delivery"]
    assert delivery.publish_news.await_args.kwargs["session_key"] == "news:42"
    assert delivery.unpublish_news.await_args.kwargs == {"session_key": "news:42", "chat_id": "-10042"}
