from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.features.combat.api import analytics_router, internal_router
from src.backend.features.combat.dependencies import get_combat_analytics_dashboard_service
from src.backend.features.exploration.api.internal_router import router as exploration_router
from src.backend.features.scenario.api.internal_router import router as scenario_router


@pytest.fixture
def access_client(monkeypatch):
    # Patch the module object imported by the new policy, without reading .env.
    import src.backend.config.settings as config

    monkeypatch.setattr(
        config,
        "settings",
        SimpleNamespace(
            operator_read_key="test-operator-reader",
            operator_write_key="test-operator-writer",
            frontend_internal_service_key="test-site-service",  # pragma: allowlist secret - synthetic test credential
            site_to_game_service_key="test-site-service",  # pragma: allowlist secret - synthetic test credential
        ),
    )
    app = FastAPI()
    for router in (internal_router.router, exploration_router, scenario_router, analytics_router.router):
        app.include_router(router)
    service = SimpleNamespace(combat_summary=AsyncMock(return_value={"count": 7}))
    app.dependency_overrides[get_combat_analytics_dashboard_service] = lambda: service
    return TestClient(app), service


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/internal/combat/sessions"),
        ("GET", "/api/internal/combat/sessions/private-session"),
        ("GET", "/api/internal/scenario/sessions"),
        ("GET", "/api/internal/exploration/sessions"),
        ("GET", "/api/game/combat/analytics/filters"),
        ("GET", "/api/game/combat/analytics/rollups"),
        ("GET", "/api/game/combat/analytics/drilldown"),
        ("GET", "/api/game/combat/analytics/combat-summary"),
        ("GET", "/api/game/combat/analytics/debug/raw/private-combat"),
        ("POST", "/api/game/combat/analytics/backfill"),
    ],
)
@pytest.mark.parametrize("headers", [{}, {"X-Internal-Service-Key": "test-site-service"}, {"X-Operator-Key": "wrong"}])
def test_diagnostics_deny_before_storage(access_client, method, path, headers):
    client, service = access_client
    # No Redis/database fixture: denial must happen before any storage work.
    response = client.request(method, path, headers=headers)
    assert response.status_code == 403
    service.combat_summary.assert_not_awaited()


@pytest.mark.parametrize("key", ["test-operator-reader", "test-operator-writer"])
def test_reader_and_writer_can_read_summary(access_client, key):
    client, service = access_client
    response = client.get("/api/game/combat/analytics/combat-summary", headers={"X-Operator-Key": key})
    assert response.status_code == 200
    assert response.json() == {"count": 7}
    service.combat_summary.assert_awaited_once()


def test_reader_cannot_backfill(access_client):
    client, _ = access_client
    response = client.post("/api/game/combat/analytics/backfill", headers={"X-Operator-Key": "test-operator-reader"})
    assert response.status_code == 403


@pytest.mark.parametrize(
    "read,write,key",
    [
        ("", "", "test-operator-reader"),
        ("dev-reader", "", "dev-reader"),
        ("change-me-reader", "", "change-me-reader"),
        ("test-site-service", "test-site-service", "test-site-service"),
        (" test-operator-reader", "", " test-operator-reader"),
    ],
)
def test_invalid_operator_config_fails_closed(access_client, read, write, key):
    from src.backend.config import settings as config

    config.settings.operator_read_key = read
    config.settings.operator_write_key = write
    client, _ = access_client
    response = client.get("/api/game/combat/analytics/combat-summary", headers={"X-Operator-Key": key})
    assert response.status_code == 403


def test_equal_read_write_keys_do_not_escalate_reader(access_client):
    from src.backend.config import settings as config

    config.settings.operator_write_key = config.settings.operator_read_key
    client, _ = access_client
    response = client.post("/api/game/combat/analytics/backfill", headers={"X-Operator-Key": "test-operator-reader"})
    assert response.status_code == 403


def test_writer_can_backfill(access_client, monkeypatch):
    from src.backend.core.database import get_db

    client, _ = access_client

    async def db():
        yield object()

    client.app.dependency_overrides[get_db] = db
    rows = AsyncMock(return_value=[])
    monkeypatch.setattr(
        analytics_router, "CombatFinalizationRepository", lambda session: SimpleNamespace(get_all_for_backfill=rows)
    )
    monkeypatch.setattr(analytics_router, "get_mongo_provider", lambda: SimpleNamespace(database=lambda: object()))
    monkeypatch.setattr(analytics_router, "CombatDocumentRepository", lambda database: object())
    response = client.post("/api/game/combat/analytics/backfill", headers={"X-Operator-Key": "test-operator-writer"})
    assert response.status_code == 200
    assert response.json() == {"processed": 0, "skipped": 0, "errors": 0}
    rows.assert_awaited_once_with(limit=500)


@pytest.mark.parametrize("domain", ["combat", "scenario", "exploration"])
def test_authorized_session_page_contract(access_client, monkeypatch, domain):
    client, _ = access_client
    client.app.state.redis = object()
    if domain == "combat":
        module, manager_name = internal_router, "CombatSessionManager"
    else:
        from importlib import import_module

        module = import_module(f"src.backend.features.{domain}.api.internal_router")
        manager_name = "ScenarioSessionManager" if domain == "scenario" else "ExplorationEncounterRuntimeManager"
    page = AsyncMock(return_value=([], "17:0"))
    monkeypatch.setattr(module, manager_name, lambda redis: SimpleNamespace(list_session_page=page))
    response = client.get(
        f"/api/internal/{domain}/sessions?cursor=5:2&limit=7", headers={"X-Operator-Key": "test-operator-reader"}
    )
    assert response.status_code == 200
    assert response.json() == []
    assert response.headers["X-Next-Cursor"] == "17:0"
    page.assert_awaited_once_with(cursor="5:2", limit=7)
    for query in ("limit=0", "limit=101", "cursor=invalid"):
        response = client.get(
            f"/api/internal/{domain}/sessions?{query}", headers={"X-Operator-Key": "test-operator-reader"}
        )
        assert response.status_code == 422
    assert page.await_count == 1


def test_session_detail_uses_allowlist(access_client, monkeypatch):
    client, _ = access_client
    client.app.state.redis = object()
    meta = AsyncMock(return_value={"status": "active", "active": "1", "future_private_field": "hidden"})
    monkeypatch.setattr(internal_router, "CombatSessionManager", lambda redis: SimpleNamespace(get_meta=meta))
    response = client.get("/api/internal/combat/sessions/known", headers={"X-Operator-Key": "test-operator-reader"})
    assert response.status_code == 200
    assert response.json() == {"session_id": "known", "status": "active", "active": "1"}
