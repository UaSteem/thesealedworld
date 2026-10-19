from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI, HTTPException, Request
from starlette.responses import PlainTextResponse

from src.frontend import app as frontend
from src.frontend.features.auth.services import auth_service as auth

CANARY = "SYNTHETIC_APP_URL_CANARY"


def capture_logger(monkeypatch, module):
    logger = MagicMock()
    logger.bind.return_value = logger
    logger.opt.return_value = logger
    monkeypatch.setattr(module, "logger", logger)
    return logger


@pytest.mark.parametrize(
    "failure,expected", [("unknown", 404), ("backend_status", 502), ("backend_request", 503), ("server", 500)]
)
async def test_http_error_log_producers_never_include_raw_urls_tokens_or_exception_messages(
    monkeypatch, failure, expected
):
    logs = capture_logger(monkeypatch, frontend)

    async def render(*args, **kwargs):
        return PlainTextResponse("safe page", status_code=kwargs["status_code"])

    monkeypatch.setattr(frontend, "get_ui_renderer", lambda request: SimpleNamespace(render=render))
    app = FastAPI()
    app.add_exception_handler(404, frontend.not_found_handler)
    app.add_exception_handler(httpx.HTTPStatusError, frontend.backend_http_status_handler)
    app.add_exception_handler(httpx.RequestError, frontend.backend_request_error_handler)
    app.add_exception_handler(500, frontend.server_error_handler)

    @app.get("/failure/{token}")
    async def fail(token: str):
        request = httpx.Request("GET", f"http://backend/private/{token}?secret={CANARY}")
        if failure == "backend_status":
            response = httpx.Response(503, request=request)
            raise httpx.HTTPStatusError(CANARY, request=request, response=response)
        if failure == "backend_request":
            raise httpx.ConnectError(CANARY, request=request)
        raise RuntimeError(CANARY)

    path = "/unknown/" if failure == "unknown" else "/failure/"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        response = await client.get(f"{path}{CANARY}?token={CANARY}")
    assert response.status_code == expected
    if failure == "server":
        # Production logging sanitizes the attached exception while retaining frames.
        assert CANARY not in repr(logs.bind.call_args_list)
        assert isinstance(logs.opt.call_args.kwargs["exception"], RuntimeError)
    else:
        assert CANARY not in repr(logs.mock_calls)
    fields = [call.kwargs for call in logs.bind.call_args_list]
    assert fields and fields[0]["method"] == "GET"
    assert fields[0]["route_template"] == ("<unmatched>" if failure == "unknown" else "/failure/{token}")


async def test_auth_guard_before_routing_does_not_log_raw_path(monkeypatch):
    logs = capture_logger(monkeypatch, auth)
    service = auth.FrontendAuthService(auth_service=object())
    monkeypatch.setattr(service, "get_current_user", AsyncMock(return_value=None))
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": f"/account/{CANARY}",
            "query_string": f"token={CANARY}".encode(),
            "headers": [],
        }
    )
    with pytest.raises(HTTPException) as exc:
        await service.require_current_user(request)
    assert exc.value.status_code == 303
    assert logs.bind.call_args_list[0].kwargs["route_template"] == "<unmatched>"
    assert CANARY not in repr(logs.mock_calls)


async def test_auth_token_rejection_logs_type_without_token_text(monkeypatch):
    logs = capture_logger(monkeypatch, auth)
    service = auth.FrontendAuthService(auth_service=object())

    def reject_token(token):
        raise ValueError(CANARY)

    monkeypatch.setattr(auth, "decode_access_token", reject_token)
    monkeypatch.setattr(service, "_refresh_from_request", AsyncMock(return_value=None))
    request = Request({"type": "http", "method": "GET", "path": "/account", "query_string": b"", "headers": []})
    assert await service._current_user_or_refresh(request, CANARY) is None
    assert logs.bind.call_args_list[0].kwargs["error_type"] == "ValueError"
    assert CANARY not in repr(logs.mock_calls)


def test_real_server_error_handler_with_production_logging_retains_safe_trace():
    import json
    import subprocess
    import sys

    script = r"""
import asyncio
import sys
sys.path.insert(0, "src")
from types import SimpleNamespace
import httpx
from fastapi import FastAPI
from starlette.responses import PlainTextResponse
from src.frontend import app as frontend
from src.shared.infrastructure.logging_config import setup_logging
setup_logging(SimpleNamespace(debug=False, log_level_console='INFO'), 'frontend-privacy')
async def render(*args, **kwargs):
    return PlainTextResponse('safe page', status_code=kwargs['status_code'])
frontend.get_ui_renderer = lambda request: SimpleNamespace(render=render)
app = FastAPI()
app.add_exception_handler(500, frontend.server_error_handler)
@app.get('/failure/{token}')
async def fail(token: str):
    raise RuntimeError(token + '?raw_query=PRODUCTION_URL_TOKEN_CANARY')
async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url='http://test') as client:
        assert (await client.get('/failure/PRODUCTION_URL_TOKEN_CANARY?secret=PRODUCTION_URL_TOKEN_CANARY')).status_code == 500
print('PRIVACY_LOG_START')
asyncio.run(run())
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    wire = result.stdout.split("PRIVACY_LOG_START", 1)[1]
    assert "PRODUCTION_URL_TOKEN_CANARY" not in wire
    record = next(
        json.loads(line)["record"]
        for line in wire.splitlines()
        if line.startswith("{") and "FrontendServerError" in line
    )
    assert record["extra"]["route_template"] == "/failure/{token}"
    assert record["extra"]["method"] == "GET"
    assert record["extra"]["status"] == 500
    assert record["extra"]["error_type"] == "RuntimeError"
    assert record["extra"]["error_trace"]
