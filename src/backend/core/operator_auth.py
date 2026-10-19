"""Separate read/write capabilities for operational diagnostics, never game JWTs."""

import secrets
from typing import Annotated

from fastapi import Header

from src.backend.config import settings as config
from src.backend.core.exceptions import PermissionDeniedException


def _keys() -> tuple[str, str]:
    settings = config.settings
    service_keys = (settings.frontend_internal_service_key, settings.site_to_game_service_key)

    def usable(key: str) -> str:
        if not key or key != key.strip() or key.startswith(("dev-", "change-me-")) or key in service_keys:
            return ""
        return key

    read = usable(settings.operator_read_key)
    write = usable(settings.operator_write_key)
    # A read capability must never become a write capability through misconfiguration.
    if write == read:
        write = ""
    return read, write


async def require_operator_read(
    key: Annotated[str | None, Header(alias="X-Operator-Key")] = None,
) -> None:
    allowed = tuple(value for value in _keys() if value)
    if not key or not any(secrets.compare_digest(key.encode(), value.encode()) for value in allowed):
        raise PermissionDeniedException("Operator read access required")


async def require_operator_write(
    key: Annotated[str | None, Header(alias="X-Operator-Key")] = None,
) -> None:
    _, write = _keys()
    if not write or not key or not secrets.compare_digest(key.encode(), write.encode()):
        raise PermissionDeniedException("Operator write access required")
