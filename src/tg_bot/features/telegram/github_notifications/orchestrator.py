import asyncio
import hashlib
import hmac
import json
import re
from typing import Any

from aiohttp import web
from loguru import logger as log

from tg_bot.features.telegram.delivery.topics import TOPICS, topic_view
from tg_bot.infrastructure.redis.github_deliveries import DeliveryLease

from .events import Notification, notification_for

WEBHOOK_PATH = "/webhooks/github"
PROCESSING_TIMEOUT = 8


class GitHubNotificationsOrchestrator:
    def __init__(self, container: Any) -> None:
        self.container = container
        self.runner: web.AppRunner | None = None

    def create_app(self) -> web.Application:
        app = web.Application(client_max_size=1024 * 1024)
        app.router.add_post(WEBHOOK_PATH, self.handle)
        return app

    async def startup(self, **_: Any) -> None:
        settings = self.container.settings
        if not settings.github_webhook_enabled or self.runner:
            return
        if not settings.github_webhook_secret.get_secret_value().strip() or self.container.redis_client is None:
            raise RuntimeError("GitHub webhook requires secret and Redis")
        runner = web.AppRunner(self.create_app(), shutdown_timeout=9)
        try:
            await runner.setup()
            site = web.TCPSite(runner, settings.github_webhook_host, settings.github_webhook_port)
            await site.start()
        except BaseException:
            await runner.cleanup()
            raise
        self.runner = runner
        log.info("GitHubWebhookStarted")

    async def shutdown(self, **_: Any) -> None:
        if self.runner:
            runner, self.runner = self.runner, None
            await runner.cleanup()

    async def handle(self, request: web.Request) -> web.Response:
        settings = self.container.settings
        secret = settings.github_webhook_secret.get_secret_value()
        if not settings.github_webhook_enabled or not secret.strip():
            raise web.HTTPServiceUnavailable()
        body = await request.read()
        signature = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not re.fullmatch(r"sha256=[0-9a-f]{64}", signature) or not hmac.compare_digest(signature, expected):
            raise web.HTTPUnauthorized()
        delivery_id = request.headers.get("X-GitHub-Delivery", "")
        if not re.fullmatch(r"[\w-]{1,128}", delivery_id):
            raise web.HTTPBadRequest(text="Missing or invalid delivery ID")
        event = request.headers.get("X-GitHub-Event", "")
        try:
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise ValueError("Expected JSON object")
            if event == "ping":
                return web.Response(text="pong")
            notification = notification_for(event, payload, settings.github_repositories, settings.github_branches)
        except (ValueError, TypeError, OverflowError):
            raise web.HTTPBadRequest(text="Invalid GitHub payload") from None
        if notification is None:
            return web.Response(status=202, text="ignored")
        try:
            # GitHub times out at 10s; include Redis, Telegram and commit in budget.
            async with asyncio.timeout(PROCESSING_TIMEOUT):
                return await self.deliver(delivery_id, notification)
        except Exception as exc:
            log.bind(error_type=type(exc).__name__).warning("GitHubDeliveryFailed")
            raise web.HTTPServiceUnavailable(headers={"Retry-After": "1"}) from None

    async def deliver(self, delivery_id: str, notification: Notification) -> web.Response:
        settings = self.container.settings
        chat_id = settings.telegram_dev_chat_id
        namespace = f"{chat_id}:{TOPICS[notification.topic]}"
        lease = DeliveryLease(self.container.redis_client, namespace, delivery_id, notification.entity)
        claimed = await lease.claim()
        # A normal overlapping PR lifecycle delivery should wait for the first
        # update, then edit its stored ID. The outer timeout bounds contention.
        while claimed == 0:
            await asyncio.sleep(0.05)
            claimed = await lease.claim()
        if claimed == 2:
            return web.Response(text="duplicate")
        try:
            old = await lease.entity_state() if notification.entity else {}
            if old.get("version", 0) > notification.version or (old.get("merged") and not notification.merged):
                await lease.commit()
                return web.Response(text="stale")
            if not await lease.owns():
                raise RuntimeError("Delivery lease lost before send")
            view = topic_view(chat_id, notification.topic, notification.text)
            message_id = await self.container.get_feature("delivery").send_notification(view, old.get("message_id"))
            await lease.commit(
                message_id if notification.entity else None,
                notification.version,
                notification.merged,
            )
            return web.Response(text="delivered")
        finally:
            # Keep release bounded too; failing release expires by TTL. Never
            # release another worker's token or turn failed sends into done.
            try:
                async with asyncio.timeout(0.25):
                    await lease.release()
            except Exception as exc:
                log.bind(error_type=type(exc).__name__).warning("GitHubDeliveryLeaseReleaseFailed")
