import asyncio
import hashlib
import hmac
import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiohttp.test_utils import TestClient, TestServer
from redis.asyncio import Redis

from tg_bot.core.config import BotSettings
from tg_bot.features.telegram.delivery.orchestrator import DeliveryOrchestrator
from tg_bot.features.telegram.delivery.topics import TOPICS, topic_view
from tg_bot.features.telegram.github_notifications.events import notification_for
from tg_bot.features.telegram.github_notifications.orchestrator import GitHubNotificationsOrchestrator
from tg_bot.infrastructure.redis import github_deliveries as adapter

REPO = {"full_name": "CodexDLC/thesealedworld"}
SECRET = "local-test-webhook-secret"  # pragma: allowlist secret


def settings(**kwargs):
    return BotSettings(
        _env_file=None,
        BOT_TOKEN="123456:local-test-token",  # pragma: allowlist secret
        SECRET_KEY="test",  # pragma: allowlist secret
        **kwargs,
    )


def push(branch="develop"):
    return {
        "repository": REPO,
        "ref": f"refs/heads/{branch}",
        "commits": [{"id": "abcdef123", "message": "Implement feature"}],  # pragma: allowlist secret
    }


def pr(action="opened", number=42, updated="2026-10-29T11:00:00Z", merged=False):
    return {
        "repository": REPO,
        "action": action,
        "number": number,
        "pull_request": {
            "base": {"ref": "develop"},
            "title": "Feature",
            "state": "closed" if action == "closed" else "open",
            "merged": merged,
            "updated_at": updated,
        },
    }


class ModelRedis:
    """Unit model only: these tests do not establish real Redis Lua semantics."""

    def __init__(self):
        self.values = {}
        self.hashes = {}
        self.fail_commit = False

    async def eval(self, script, key_count, *args):
        keys, values = args[:key_count], args[key_count:]
        if script == adapter._CLAIM:
            if self.values.get(keys[0]) == "done":
                return 2
            if any(key in self.values for key in keys):
                return 0
            for key in keys:
                self.values[key] = values[0]
            return 1
        if script == adapter._OWNS:
            return int(all(self.values.get(key) == values[0] for key in keys))
        if script == adapter._COMMIT:
            if self.fail_commit:
                raise ConnectionError("Redis unavailable")
            if not all(self.values.get(key) == values[0] for key in keys[:2]):
                return 0
            if values[1]:
                self.hashes[keys[2]] = dict(message_id=int(values[1]), version=int(values[2]), merged=int(values[3]))
            self.values[keys[0]] = "done"
            del self.values[keys[1]]
            return 1
        if script == adapter._RELEASE:
            for key in keys:
                if self.values.get(key) == values[0]:
                    del self.values[key]
            return 1
        raise AssertionError("Unexpected script")

    async def hgetall(self, key):
        return dict(self.hashes.get(key, {}))


@pytest_asyncio.fixture
async def webhook():
    bot = SimpleNamespace(
        send_message=AsyncMock(return_value=SimpleNamespace(message_id=90)), edit_message_text=AsyncMock()
    )
    redis = ModelRedis()
    container = SimpleNamespace(
        settings=settings(GITHUB_WEBHOOK_ENABLED=True, GITHUB_WEBHOOK_SECRET=SECRET), redis_client=redis, bot=bot
    )
    delivery = DeliveryOrchestrator(container)
    container.get_feature = lambda key: delivery if key == "delivery" else None
    feature = GitHubNotificationsOrchestrator(container)
    async with TestClient(TestServer(feature.create_app())) as client:
        yield client, feature, bot, redis


async def post(client, payload, event="push", delivery="delivery-1", signature=None, raw=None):
    body = raw if raw is not None else json.dumps(payload).encode()
    digest = "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return await client.post(
        "/webhooks/github",
        data=body,
        headers={
            "X-GitHub-Event": event,
            "X-GitHub-Delivery": delivery,
            "X-Hub-Signature-256": digest if signature is None else signature,
        },
    )


@pytest.mark.asyncio
async def test_pr_open_then_merge_updates_same_entity_message(webhook):
    client, feature, bot, redis = webhook
    assert (await post(client, pr(), "pull_request", "open")).status == 200
    assert (
        await post(client, pr("closed", updated="2026-10-29T12:00:00Z", merged=True), "pull_request", "merge")
    ).status == 200
    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.kwargs["message_thread_id"] == 14
    assert bot.edit_message_text.await_args.kwargs["message_id"] == 90
    assert "merged" in bot.edit_message_text.await_args.kwargs["text"]
    state = next(iter(redis.hashes.values()))
    assert state["message_id"] == 90 and state["merged"] == 1
    # Delayed opened events cannot overwrite merged, even after dedupe TTL.
    assert (await post(client, pr(), "pull_request", "late-open")).status == 200
    assert bot.edit_message_text.await_count == 1
    assert (await post(client, pr(number=43), "pull_request", "other-pr")).status == 200
    assert bot.send_message.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("signature", ["", "sha1=bad", "sha256=" + "0" * 64])
async def test_invalid_hmac_has_no_side_effects(webhook, signature):
    client, _, bot, redis = webhook
    assert (await post(client, push(), signature=signature)).status == 401
    bot.send_message.assert_not_awaited()
    assert not redis.values


@pytest.mark.asyncio
async def test_signed_body_cannot_be_tampered(webhook):
    client, _, bot, _ = webhook
    signed = "sha256=" + hmac.new(SECRET.encode(), b"{}", hashlib.sha256).hexdigest()
    assert (await post(client, push(), signature=signed)).status == 401
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_and_distinct_push_are_append_only(webhook):
    client, _, bot, _ = webhook
    assert (await post(client, push())).status == 200
    assert await (await post(client, push())).text() == "duplicate"
    assert (await post(client, push(), delivery="delivery-2")).status == 200
    assert bot.send_message.await_count == 2
    assert all(
        call.kwargs["chat_id"] == -1004387822347 and call.kwargs["message_thread_id"] == 14
        for call in bot.send_message.await_args_list
    )
    bot.edit_message_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_failure_is_retryable_and_not_deduplicated(webhook):
    client, _, bot, _ = webhook
    bot.send_message.side_effect = [
        TelegramNetworkError(method=None, message="temporary"),
        SimpleNamespace(message_id=91),
    ]
    assert (await post(client, push())).status == 503
    assert (await post(client, push())).status == 200
    assert await (await post(client, push())).text() == "duplicate"
    assert bot.send_message.await_count == 2


@pytest.mark.asyncio
async def test_transient_pr_edit_does_not_append(webhook):
    client, _, bot, _ = webhook
    assert (await post(client, pr(), "pull_request", "open")).status == 200
    bot.edit_message_text.side_effect = TelegramNetworkError(method=None, message="temporary")
    merged = pr("closed", updated="2026-10-29T12:00:00Z", merged=True)
    assert (await post(client, merged, "pull_request", "merge")).status == 503
    bot.send_message.assert_awaited_once()
    bot.edit_message_text.side_effect = None
    assert (await post(client, merged, "pull_request", "merge")).status == 200
    assert bot.edit_message_text.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reason,appends,status",
    [
        ("Bad Request: message to edit not found", True, 200),
        ("Bad Request: message is not modified", False, 200),
        ("Bad Request: can't parse entities", False, 503),
    ],
)
async def test_edit_fallback_only_for_missing_messages(webhook, reason, appends, status):
    client, _, bot, _ = webhook
    await post(client, pr(), "pull_request", "open")
    bot.edit_message_text.side_effect = TelegramBadRequest(method=None, message=reason)
    assert (
        await post(client, pr("closed", updated="2026-10-29T12:00:00Z", merged=True), "pull_request", "merge")
    ).status == status
    assert bot.send_message.await_count == 1 + int(appends)


@pytest.mark.asyncio
async def test_commit_failure_never_acknowledged_success(webhook):
    client, _, bot, redis = webhook
    redis.fail_commit = True
    assert (await post(client, push())).status == 503
    assert not any(value == "done" for value in redis.values.values())
    redis.fail_commit = False
    assert (await post(client, push())).status == 200
    # Documented ambiguity: send succeeded before failed commit, so a duplicate is possible.
    assert bot.send_message.await_count == 2


@pytest.mark.asyncio
async def test_concurrent_pr_events_are_serialized(webhook):
    client, _, bot, _ = webhook
    entered, finish = asyncio.Event(), asyncio.Event()

    async def slow_send(**kwargs):
        entered.set()
        await finish.wait()
        return SimpleNamespace(message_id=90)

    bot.send_message.side_effect = slow_send
    first = asyncio.create_task(post(client, pr(), "pull_request", "open"))
    await asyncio.wait_for(entered.wait(), 2)
    second = asyncio.create_task(
        post(client, pr("closed", updated="2026-10-29T12:00:00Z", merged=True), "pull_request", "merge")
    )
    await asyncio.sleep(0.1)
    assert not second.done()
    finish.set()
    assert (await first).status == 200
    assert (await second).status == 200
    bot.send_message.assert_awaited_once()
    bot.edit_message_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_whole_processing_timeout_is_failure(webhook, monkeypatch):
    from tg_bot.features.telegram.github_notifications import orchestrator

    monkeypatch.setattr(orchestrator, "PROCESSING_TIMEOUT", 0.01)
    client, _, bot, _ = webhook
    bot.send_message.side_effect = lambda **kw: None

    async def slow_send(**kwargs):
        await asyncio.sleep(1)

    bot.send_message.side_effect = slow_send
    assert (await post(client, push())).status == 503


@pytest.mark.asyncio
async def test_invalid_payload_delivery_header_and_size(webhook):
    client, _, bot, _ = webhook
    assert (await post(client, {}, raw=b"[1]")).status == 400
    assert (await post(client, {}, raw=b"{")).status == 400
    assert (await post(client, push(), delivery="")).status == 400
    assert (await post(client, push(), raw=b"x" * (1024 * 1024 + 1))).status == 413
    assert (await post(client, {}, event="ping")).status == 200
    bot.send_message.assert_not_awaited()


@pytest.mark.parametrize(
    "payload",
    [
        {**push(), "repository": {"full_name": "another/repository"}},
        push("feature/private"),
        {**push(), "ref": "refs/tags/v1"},
        {**push(), "deleted": True},
    ],
)
def test_push_filters(payload):
    assert notification_for("push", payload, {"codexdlc/thesealedworld"}, {"develop", "main"}) is None


@pytest.mark.parametrize(
    "event,payload,topic",
    [
        (
            "workflow_run",
            {"action": "completed", "workflow_run": {"head_branch": "main", "conclusion": "failure", "name": "deploy"}},
            "deploy",
        ),
        (
            "check_run",
            {"action": "completed", "check_run": {"check_suite": {"head_branch": "develop"}, "conclusion": "success"}},
            "deploy",
        ),
        (
            "deployment_status",
            {
                "deployment": {"ref": "refs/heads/main", "environment": "prod"},
                "deployment_status": {"state": "success"},
            },
            "deploy",
        ),
        (
            "workflow_run",
            {"action": "requested", "workflow_run": {"head_branch": "main", "conclusion": "failure"}},
            None,
        ),
        (
            "workflow_run",
            {"action": "completed", "workflow_run": {"head_branch": "secret", "conclusion": "failure"}},
            None,
        ),
        (
            "check_run",
            {"action": "completed", "check_run": {"check_suite": {"head_branch": "main"}, "conclusion": "skipped"}},
            None,
        ),
        ("deployment_status", {"deployment": {"ref": "main"}, "deployment_status": {"state": "in_progress"}}, None),
        ("pull_request", {**pr(), "pull_request": {**pr()["pull_request"], "base": {"ref": "feature"}}}, None),
    ],
)
def test_event_filters_and_topic_mapping(event, payload, topic):
    notification = notification_for(
        event, {"repository": REPO, **payload}, {"codexdlc/thesealedworld"}, {"develop", "main"}
    )
    assert (notification.topic if notification else None) == topic
    if topic:
        assert topic_view(-1004387822347, topic, notification.text).message_thread_id == 16


def test_rendered_user_text_is_escaped_and_bounded():
    data = pr()
    data["pull_request"]["title"] = '<a href="evil">&' * 10000
    notice = notification_for("pull_request", data, {"codexdlc/thesealedworld"}, {"develop"})
    assert len(notice.text) < 4096
    assert '<a href="evil">' not in notice.text
    assert "&lt;a" in notice.text
    assert dict(tasks=3, game_design=5, lore=7, graphics=9, bugs=12, github=14, deploy=16) == TOPICS


def test_configuration_fails_closed():
    with pytest.raises(ValueError):
        settings(GITHUB_WEBHOOK_ENABLED=True)
    with pytest.raises(ValueError):
        settings(GITHUB_WEBHOOK_ENABLED=True, GITHUB_WEBHOOK_SECRET=SECRET, USE_REDIS=False)
    with pytest.raises(ValueError):
        settings(GITHUB_WEBHOOK_ENABLED=True, GITHUB_WEBHOOK_SECRET=SECRET, GITHUB_WEBHOOK_BRANCHES="")
    assert settings().github_webhook_enabled is False


@pytest.mark.asyncio
async def test_disabled_handler_is_fail_closed(webhook):
    client, feature, bot, _ = webhook
    feature.container.settings.github_webhook_enabled = False
    assert (await post(client, push())).status == 503
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_discovery_and_dispatcher_lifecycle(monkeypatch):
    from tg_bot.core.container import BotContainer
    from tg_bot.core.factory import build_bot

    config = settings(USE_REDIS=False, USE_REDIS_STREAMS=False)
    container = BotContainer(config)
    bot, dispatcher = build_bot(config, None, container)
    feature = container.get_feature("github_notifications")
    assert isinstance(container.get_feature("delivery"), DeliveryOrchestrator)
    assert feature.startup in [handler.callback for handler in dispatcher.startup.handlers]
    assert feature.shutdown in [handler.callback for handler in dispatcher.shutdown.handlers]
    # Real endpoint startup and cleanup with no Telegram network call.
    feature.container.settings.github_webhook_enabled = True
    from pydantic import SecretStr

    feature.container.settings.github_webhook_secret = SecretStr(SECRET)
    feature.container.settings.github_webhook_port = 0
    feature.container.settings.github_webhook_host = "127.0.0.1"
    feature.container.redis_client = ModelRedis()
    await dispatcher.emit_startup(bot=bot)
    assert feature.runner is not None
    await dispatcher.emit_shutdown(bot=bot)
    assert feature.runner is None
    await container.shutdown()
    await bot.session.close()


@pytest.mark.asyncio
async def test_real_redis_leases_ttl_fencing_and_entity_state():
    redis_url = os.environ.get("TG_BOT_TEST_REDIS_URL")
    if not redis_url:
        pytest.skip("Requires explicit isolated TG_BOT_TEST_REDIS_URL; no default Redis access")
    redis = Redis.from_url(redis_url, socket_timeout=2, socket_connect_timeout=2)
    namespace = "test:" + uuid4().hex
    first = adapter.DeliveryLease(redis, namespace, "delivery-1", "pr:repo:42")
    second = adapter.DeliveryLease(redis, namespace, "delivery-2", "pr:repo:42")
    keys = [first.delivery_key, second.delivery_key, first.entity_key, first.lock_key]
    try:
        assert await first.claim() == 1
        assert 0 < await redis.ttl(first.delivery_key) <= adapter.LEASE_SECONDS
        assert await second.claim() == 0
        await first.commit(42, 100, False)
        assert await first.claim() == 2
        assert 0 < await redis.ttl(first.delivery_key) <= adapter.DELIVERY_TTL
        assert await second.claim() == 1
        assert await second.entity_state() == dict(message_id=42, version=100, merged=0)
        # Expire only this test's lock. A stale owner cannot commit or release a new lease.
        await redis.pexpire(second.lock_key, 1)
        await asyncio.sleep(0.02)
        third = adapter.DeliveryLease(redis, namespace, "delivery-3", "pr:repo:42")
        keys.append(third.delivery_key)
        assert await third.claim() == 1
        assert not await second.owns()
        with pytest.raises(RuntimeError):
            await second.commit(999, 999, True)
        await second.release()
        assert await third.owns()
        await third.commit(42, 200, True)
        assert await third.entity_state() == dict(message_id=42, version=200, merged=1)
        assert 0 < await redis.ttl(third.entity_key) <= adapter.ENTITY_TTL
    finally:
        await redis.delete(*keys)
        await redis.aclose()
