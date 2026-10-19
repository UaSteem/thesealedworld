import io
import json
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from loguru import logger

from src.shared.infrastructure.logging_config import setup_logging


@pytest.fixture
def production_logs(monkeypatch):
    original_add = logger.add
    stdout = io.StringIO()
    handlers = logging.getLogger().handlers[:]

    def synchronous_sink(*args, **kwargs):
        # Exercise actual sink serialization without Windows multiprocessing queues.
        kwargs["enqueue"] = False
        if args and hasattr(args[0], "write"):
            args = (stdout, *args[1:])
        if hasattr(kwargs.get("sink"), "write"):
            kwargs["sink"] = stdout
        return original_add(*args, **kwargs)

    monkeypatch.setattr(logger, "add", synchronous_sink)
    settings = SimpleNamespace(debug=False, log_level_console="DEBUG")
    setup_logging(settings, "privacy-test")
    collected = []
    logger.add(collected.append, serialize=True)
    yield collected, stdout
    logger.remove()
    logger.configure(patcher=None)
    logging.getLogger().handlers = handlers


def _records(production_logs):
    collected, stdout = production_logs
    return stdout.getvalue(), "".join(collected)


def test_production_exception_keeps_event_trace_and_type_without_private_values(production_logs):
    private_local = "CANARY_LOCAL_PRIVATE"
    try:
        raise RuntimeError("CANARY_SMTP_PASSWORD player-canary@example.test CANARY_BODY_PRIVATE")
    except RuntimeError:
        logger.bind(
            correlation_id="trace-canary",
            request_id="request-canary",
            email="player-canary@example.test",
            body="CANARY_BODY_PRIVATE",
            password="CANARY_SMTP_PASSWORD",  # pragma: allowlist secret - synthetic test credential
            error=private_local,
        ).exception("EmailDeliveryFailed")
    for output in _records(production_logs):
        assert "CANARY_" not in output
        assert "player-canary@example.test" not in output
        record = json.loads(output)["record"]
        assert record["message"] == "EmailDeliveryFailed"
        assert record["extra"]["correlation_id"] == "trace-canary"
        assert record["extra"]["request_id"] == "request-canary"
        assert record["extra"]["service"] == "privacy-test"
        assert record["name"] == __name__
        assert record["function"] == "test_production_exception_keeps_event_trace_and_type_without_private_values"
        assert record["extra"]["error_type"] == "RuntimeError"
        assert "test_production_exception" in str(record["extra"]["error_trace"])


@pytest.mark.asyncio
async def test_email_success_and_smtp_failure_do_not_log_recipient_or_message(production_logs, monkeypatch):
    from src.frontend.features.email.services.email_service import EmailService

    send = AsyncMock()
    monkeypatch.setattr("src.frontend.features.email.services.email_service.aiosmtplib.send", send)
    service = EmailService(
        smtp_host="smtp.example.test",
        smtp_port=587,
        smtp_start_tls=True,
        smtp_user="sender-canary@example.test",
        smtp_password="CANARY_SMTP_PASSWORD",  # pragma: allowlist secret - synthetic test credential
        email_from="sender-canary@example.test",
    )
    await service.send(
        to="player-canary@example.test", subject="CANARY_SUBJECT_PRIVATE", body_html="CANARY_BODY_PRIVATE"
    )
    send.side_effect = RuntimeError("CANARY_SMTP_PASSWORD player-canary@example.test CANARY_BODY_PRIVATE")
    with pytest.raises(RuntimeError):
        await service.send(
            to="player-canary@example.test", subject="CANARY_SUBJECT_PRIVATE", body_html="CANARY_BODY_PRIVATE"
        )
    for output in _records(production_logs):
        assert "canary@example.test" not in output
        assert "CANARY_" not in output
        assert "EmailSent" in output


def test_unstructured_library_exception_message_is_not_forwarded(production_logs):
    import logging

    try:
        raise ValueError("CANARY_BODY_PRIVATE")
    except ValueError:
        logging.getLogger("smtp").exception("SMTP rejected player-canary@example.test CANARY_BODY_PRIVATE")
    for output in _records(production_logs):
        assert "CANARY_" not in output
        assert "player-canary@example.test" not in output
        assert "ValueError" in output


def test_production_redacts_sensitive_fields_and_unstructured_access_logs(production_logs):
    sensitive = {
        field: "CANARY_PRIVATE"
        for field in ("url", "backend_url", "uri", "path", "query_string", "dsn", "bearer", "error_message", "response")
    }
    logger.bind(**sensitive, route_template="/account/verify/{token}", method="GET").warning("BackendRejected")
    logging.getLogger("uvicorn.access").info('127.0.0.1 "GET /verify?token=CANARY_PRIVATE HTTP/1.1" 200')
    for output in _records(production_logs):
        assert "CANARY_PRIVATE" not in output
        assert "/account/verify/{token}" in output
        assert "BackendRejected" in output


@pytest.mark.asyncio
async def test_email_fallback_callers_preserve_failure_event_without_pii(production_logs):
    from src.frontend.features.account.services.account_service import AccountService
    from src.frontend.features.cabinet.modules.messaging.bridge import SiteMessagingBridge

    service = SimpleNamespace(
        send_template=AsyncMock(side_effect=RuntimeError("CANARY_PRIVATE player-canary@example.test"))
    )
    await AccountService(email_service=service)._notify_application_submitted("player-canary@example.test")
    await SiteMessagingBridge(email_service=service)._notify_status_change(
        email="player-canary@example.test", approved=True
    )
    for output in _records(production_logs):
        assert "CANARY_PRIVATE" not in output
        assert "player-canary@example.test" not in output
        assert "TesterApplicationEmailDeliveryFailed" in output
        assert "TesterStatusEmailDeliveryFailed" in output
        assert "RuntimeError" in output
