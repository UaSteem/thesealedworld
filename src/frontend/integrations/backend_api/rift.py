"""Explicit failure boundary for callers of the retired node Rift runtime."""

from typing import Any

from fastapi import HTTPException

from src.frontend.integrations.backend_api.base import BaseApiClient


class BackendRiftApi(BaseApiClient):
    async def _retired(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise HTTPException(status_code=410, detail="Legacy node Rift has been retired")

    view = _retired
    travel_start = _retired
    travel_tick = _retired
    action = _retired
    complete = _retired
    leave = _retired
