import httpx
import pytest
from fastapi import FastAPI
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

from src.shared.infrastructure import metrics_middleware as middleware
from src.shared.infrastructure.log_middleware import LogContextMiddleware

CANARY = "SYNTHETIC_URL_TOKEN_CANARY"


@pytest.fixture
def metrics(monkeypatch):
    registry = CollectorRegistry()
    total = Counter("http_requests", "requests", ["service", "method", "path_template", "status"], registry=registry)
    duration = Histogram(
        "http_request_duration_seconds", "duration", ["service", "method", "path_template"], registry=registry
    )
    inflight = Gauge("http_requests_in_flight", "inflight", ["service"], registry=registry)
    monkeypatch.setattr(middleware, "HTTP_REQUESTS_TOTAL", total)
    monkeypatch.setattr(middleware, "HTTP_REQUEST_DURATION", duration)
    monkeypatch.setattr(middleware, "HTTP_REQUESTS_IN_FLIGHT", inflight)
    return registry, total, duration, inflight


async def test_metrics_use_routed_templates_and_bounded_unknown_paths_on_success_and_error(metrics):
    from prometheus_client import generate_latest

    registry, total, duration, inflight = metrics
    app = FastAPI()
    app.add_middleware(middleware.PrometheusMiddleware, service_name="privacy")

    @app.get("/verify/{token}")
    async def verify(token: str):
        return {"ok": True}

    @app.get("/failure/{token}")
    async def failure(token: str):
        raise RuntimeError(token)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        for token in (CANARY, "SECOND_IDENTIFIER"):
            assert (await client.get(f"/verify/{token}?token={CANARY}")).status_code == 200
        for index in range(25):
            assert (await client.get(f"/unknown/{CANARY}/{index}?secret={CANARY}")).status_code == 404
        assert (await client.get(f"/failure/{CANARY}")).status_code == 500
        assert (await client.request("CUSTOM_CANARY_METHOD", f"/verify/{CANARY}")).status_code == 405
    samples = [sample for sample in total.collect()[0].samples if sample.name.endswith("_total")]
    assert {(s.labels["path_template"], s.labels["method"], s.labels["status"]) for s in samples} == {
        ("/verify/{token}", "GET", "200"),
        ("<unmatched>", "GET", "404"),
        ("/failure/{token}", "GET", "500"),
        ("/verify/{token}", "OTHER", "405"),
    }
    assert len(samples) == 4
    assert sum(s.value for s in samples) == 29
    assert inflight.labels(service="privacy")._value.get() == 0
    timing = [s for s in duration.collect()[0].samples if s.name.endswith("_count")]
    assert sum(s.value for s in timing) == 29
    wire = generate_latest(registry).decode()
    assert CANARY not in wire and "SECOND_IDENTIFIER" not in wire and "CUSTOM_CANARY_METHOD" not in wire


async def test_transport_log_context_does_not_copy_url_character_identifiers():
    from codex_core.common.log_context import get_log_context

    app = FastAPI()
    app.add_middleware(LogContextMiddleware)

    @app.get("/characters/{char_id}")
    async def character(char_id: str):
        context = get_log_context()
        assert "char_id" not in context and "character_id" not in context
        return {"has_request_id": bool(context.get("request_id"))}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/characters/{CANARY}")
    assert response.status_code == 200
    assert response.json() == {"has_request_id": True}
    assert response.headers["X-Request-ID"]
