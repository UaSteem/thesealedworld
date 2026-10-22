"""Studio operator access and selected-source transport policy."""

from __future__ import annotations

import base64
import binascii
import secrets
from contextvars import ContextVar
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    import httpx
    from starlette.requests import Request

    from src.studio.settings import Source, StudioSettings

selected_source: ContextVar[Source | None] = ContextVar("studio_selected_source", default=None)
_LOCAL_COMPUTE = frozenset(
    {
        "/api/admin/combat-ai/simulation-runs/demo",
        "/api/admin/combat-ai/simulation-runs/live-demo",
        "/api/admin/combat-ai/simulation-runs/live-demo-batch",
        "/api/admin/combat-ai/simulation-runs/family-pressure",
        "/api/admin/combat-ai/simulation-runs/family-pressure-batch",
        "/api/admin/combat-ai/simulation-runs/train-synthetic",
        "/api/admin/combat-ai/simulation-runs/train-battle",
    }
)


class StudioAccessMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, settings: StudioSettings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next):
        configured = self.settings.studio_access_token
        if not configured:
            return JSONResponse(
                {"detail": "Configure STUDIO_ACCESS_TOKEN before opening Studio (Basic username: studio)."},
                status_code=503,
            )
        hostname = urlsplit(str(request.url)).hostname
        if hostname not in self.settings.studio_allowed_hosts:
            return JSONResponse({"detail": "Studio host denied"}, status_code=403)
        supplied = request.headers.get("Authorization", "")
        try:
            scheme, encoded = supplied.split(" ", 1)
            user, password = base64.b64decode(encoded, validate=True).decode().split(":", 1)
            valid = (
                scheme.lower() == "basic"
                and user == "studio"
                and secrets.compare_digest(password.encode(), configured.encode())
            )
        except (ValueError, UnicodeError, binascii.Error):
            valid = False
        if not valid:
            return JSONResponse(
                {"detail": "Studio authentication required"},
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Studio"'},
            )
        origin = request.headers.get("Origin")
        expected = str(request.url.replace(path="", query="", fragment="")).rstrip("/")
        if (origin and origin != expected) or (request.method not in {"GET", "HEAD", "OPTIONS"} and origin != expected):
            return JSONResponse({"detail": "Studio origin denied"}, status_code=403)
        if request.method not in {"GET", "HEAD", "OPTIONS"} and request.url.path != "/studio/source":
            kind = request.cookies.get("studio_source")
            if kind not in {"local", "prod"}:
                kind = self.settings.studio_source
            if kind != "local":
                return JSONResponse({"detail": "Selected source is read-only"}, status_code=403)
        return await call_next(request)


async def guard_source_request(request: httpx.Request) -> None:
    source = selected_source.get()
    if source is None:
        raise PermissionError("Studio HTTP request has no selected source")
    destination = urlsplit(str(request.url))
    base = urlsplit(source.api_base)
    prefix = base.path.rstrip("/")
    if (destination.scheme, destination.netloc) != (base.scheme, base.netloc) or not (
        destination.path == prefix or destination.path.startswith(prefix + "/")
    ):
        raise PermissionError("Studio destination differs from selected source")
    if request.method in {"GET", "HEAD"}:
        return
    path = destination.path[len(prefix) :]
    if source.kind == "local" and request.method == "POST" and path in _LOCAL_COMPUTE:
        return
    raise PermissionError("Selected-source mutation denied")
