"""Bounded authentication lifetime and frame budgets for one realtime socket."""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections.abc import Callable
from typing import Any

from fastapi import WebSocketDisconnect

SESSION_POLL_SECONDS = 1.0
STORAGE_TIMEOUT_SECONDS = 2.0
MAX_FRAME_BYTES = 16 * 1024
FRAME_RATE = 20.0
FRAME_BURST = 40.0


class SessionGuard:
    """All outbound adapters share this socket so revocation cannot bypass policy.

    The frame limit applies after ASGI receive; the server still owns wire limits.
    A successful Redis read is the authorization point for each operation, not an
    atomic transaction with subsequent network delivery.
    """

    def __init__(self, socket: Any, lock: Any, character_id: int, session_id: str, expires_at: float):
        self._socket = socket
        self._lock = lock
        self._character_id = character_id
        self._session_id = session_id
        self._expires_at = expires_at
        self._closed_code: int | None = None
        self._detach: Callable[[], None] = lambda: None
        self._tokens = FRAME_BURST
        self._last_frame_at = time.monotonic()
        self._pending_sends: set[asyncio.Task[Any]] = set()

    @property
    def closed(self) -> bool:
        return self._closed_code is not None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._socket, name)

    def on_disconnect(self, callback: Callable[[], None]) -> None:
        self._detach = callback

    def _raise_if_closed(self) -> None:
        if self._closed_code is not None:
            raise WebSocketDisconnect(self._closed_code)

    async def ensure_current(self) -> None:
        self._raise_if_closed()
        if time.time() >= self._expires_at:
            await self.close(4001, "access token expired")
            raise WebSocketDisconnect(4001)
        try:
            current = await asyncio.wait_for(self._lock.current(self._character_id), STORAGE_TIMEOUT_SECONDS)
        except Exception:
            current = None
        self._raise_if_closed()
        if current != self._session_id:
            await self.close(4003, "stale session")
            raise WebSocketDisconnect(4003)
        # Expiry may have passed while awaiting storage.
        if time.time() >= self._expires_at:
            await self.close(4001, "access token expired")
            raise WebSocketDisconnect(4001)

    async def accept(self) -> None:
        await self._socket.accept()
        await self.ensure_current()

    async def close(self, code: int = 1000, reason: str = "") -> None:
        if self._closed_code is not None:
            return
        self._closed_code = code
        self._detach()
        for pending in self._pending_sends:
            pending.cancel()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(self._socket.close(code=code, reason=reason), STORAGE_TIMEOUT_SECONDS)

    async def send_text(self, data: str) -> None:
        await self.ensure_current()
        pending = asyncio.create_task(self._socket.send_text(data))
        self._pending_sends.add(pending)
        try:
            await asyncio.wait_for(pending, STORAGE_TIMEOUT_SECONDS)
        except asyncio.CancelledError:
            self._raise_if_closed()
            raise
        except TimeoutError:
            await self.close(1011, "delivery unavailable")
            raise WebSocketDisconnect(1011) from None
        finally:
            self._pending_sends.discard(pending)

    async def receive_text(self) -> str:
        try:
            raw = await self._socket.receive_text()
        except KeyError:
            await self.close(1003, "text frames required")
            raise WebSocketDisconnect(1003) from None
        await self.ensure_current()
        if len(raw.encode("utf-8")) > MAX_FRAME_BYTES:
            await self.close(1009, "frame too large")
            raise WebSocketDisconnect(1009)
        now = time.monotonic()
        self._tokens = min(FRAME_BURST, self._tokens + (now - self._last_frame_at) * FRAME_RATE)
        self._last_frame_at = now
        if self._tokens < 1:
            await self.close(1008, "frame rate exceeded")
            raise WebSocketDisconnect(1008)
        self._tokens -= 1
        return raw

    async def monitor(self, owner: asyncio.Task[Any]) -> None:
        try:
            while self._closed_code is None:
                await asyncio.sleep(max(0, min(SESSION_POLL_SECONDS, self._expires_at - time.time())))
                await self.ensure_current()
        except WebSocketDisconnect:
            pass
        finally:
            if self._closed_code is not None and not owner.done():
                owner.cancel()
