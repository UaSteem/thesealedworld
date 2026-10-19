"""HTTP request context middleware for structured logging.

Injects ``request_id`` and a ``healthcheck`` marker into the
async-local log context so every log call within the request automatically
carries these fields.
"""

import uuid

from codex_core.common.log_context import clear_log_context, set_log_context
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_HEALTHCHECK_PATHS = frozenset({"/health", "/", "/metrics"})


class LogContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = uuid.uuid4().hex
        ctx: dict = {"request_id": request_id}

        if request.url.path in _HEALTHCHECK_PATHS:
            ctx["healthcheck"] = True

        set_log_context(**ctx)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_log_context()
