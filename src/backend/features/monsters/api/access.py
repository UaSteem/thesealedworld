from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Header

from src.backend.config.settings import settings
from src.backend.core.exceptions import PermissionDeniedException
from src.backend.core.game_auth import InternalServiceIdentity


def _read_keys() -> tuple[str, ...]:
    return tuple(
        key
        for key in (
            settings.monster_catalog_read_key,
            settings.frontend_internal_service_key or settings.site_to_game_service_key,
        )
        if key and not key.startswith(("dev-", "change-me-"))
    )


async def require_monster_catalog_read(
    service_key: Annotated[str | None, Header(alias="X-Internal-Service-Key")] = None,
) -> InternalServiceIdentity:
    configured = _read_keys()
    if not configured:
        raise PermissionDeniedException("Monster catalog service key is not configured")
    if not service_key or not any(secrets.compare_digest(service_key.encode(), key.encode()) for key in configured):
        raise PermissionDeniedException("Invalid monster catalog read key")
    return InternalServiceIdentity(name="monster-catalog-reader")


async def require_monster_catalog_write(
    write_key: Annotated[str | None, Header(alias="X-Monster-Catalog-Write-Key")] = None,
) -> None:
    configured = settings.monster_catalog_write_key
    if (
        not configured
        or configured.startswith(("dev-", "change-me-"))
        or any(secrets.compare_digest(configured.encode(), key.encode()) for key in _read_keys())
    ):
        raise PermissionDeniedException("Separate monster catalog write key is not configured")
    if not write_key or not secrets.compare_digest(write_key.encode(), configured.encode()):
        raise PermissionDeniedException("Invalid monster catalog write key")
