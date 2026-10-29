from typing import Any

from aiogram.exceptions import TelegramBadRequest
from codex_bot.base import UnifiedViewDTO

from .media_sender import MediaSendResult, TelegramMediaSender


class DeliveryOrchestrator:
    """Feature-owned transport using the Bot and coordinate manager from codex_bot.

    ViewSender remains the personal/topic UI synchronizer. Notifications have
    explicit entity coordinates (or no previous message) and propagate failures.
    """

    def __init__(self, container: Any) -> None:
        self.container = container

    def _news_sender(self) -> TelegramMediaSender:
        return TelegramMediaSender(self.container.bot, self.container.view_sender.manager)

    async def publish_news(self, **kwargs: Any) -> MediaSendResult:
        return await self._news_sender().send_or_replace_html(**kwargs)

    async def unpublish_news(self, **kwargs: Any) -> None:
        await self._news_sender().delete(**kwargs)

    async def send_notification(self, view: UnifiedViewDTO, message_id: int | None = None) -> int:
        """Append unless an explicit entity message ID was supplied.

        Transient edit errors must reach the webhook so a retry updates the same
        message. Recreate only when Telegram confirms the message is uneditable.
        """
        if not view.chat_id or not view.content:
            raise ValueError("Notification requires chat_id and content")
        if message_id:
            try:
                await self.container.bot.edit_message_text(
                    chat_id=view.chat_id,
                    message_id=message_id,
                    text=view.content.text,
                    parse_mode="HTML",
                )
                return message_id
            except TelegramBadRequest as exc:
                reason = exc.message.lower()
                if "message is not modified" in reason:
                    return message_id
                if not any(
                    reason.endswith(item)
                    for item in ("message to edit not found", "message can't be edited", "message can not be edited")
                ):
                    raise
        sent = await self.container.bot.send_message(
            chat_id=view.chat_id,
            message_thread_id=view.message_thread_id,
            text=view.content.text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return int(sent.message_id)
