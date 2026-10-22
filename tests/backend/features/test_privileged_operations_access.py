from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from src.backend.core.database import get_db
from src.backend.features.combat.api.ai_simulation_router import router as simulation_router
from src.backend.features.game_config.api.router import router as config_router
from src.backend.features.generation_ai.api import router as generation_router

ROUTERS = (config_router, generation_router, simulation_router)
CASES = [
    (
        method,
        route.path.replace("{namespace}", "combat")
        .replace("{key}", "ROUND_TIME")
        .replace("{task_id}", "task")
        .replace("{run_id}", "run"),
    )
    for router in ROUTERS
    for route in router.routes
    if isinstance(route, APIRoute)
    for method in route.methods
]


@pytest.fixture
def client(monkeypatch):
    from src.backend.config import settings as config

    monkeypatch.setattr(
        config,
        "settings",
        SimpleNamespace(
            operator_read_key="ops-reader",  # pragma: allowlist secret
            operator_write_key="ops-writer",  # pragma: allowlist secret
            frontend_internal_service_key="ordinary-service",  # pragma: allowlist secret
            site_to_game_service_key="ordinary-service",  # pragma: allowlist secret
        ),
    )  # pragma: allowlist secret
    app = FastAPI()
    for router in ROUTERS:
        app.include_router(router)

    async def forbidden_db():
        raise AssertionError("Denied request reached database")

    app.dependency_overrides[get_db] = forbidden_db
    app.state.game_config = SimpleNamespace(list_all=AsyncMock(return_value={}), set=AsyncMock(return_value=True))
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("method,path", CASES)
@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-Internal-Service-Key": "ordinary-service"},
        {"X-Operator-Key": "ordinary-service"},
        {"Authorization": "Bearer game-or-site-token"},
    ],
)
def test_privileged_routes_deny_non_operator_before_storage(client, method, path, headers):
    response = client.request(method, path, headers=headers)
    assert response.status_code == 403
    client.app.state.game_config.list_all.assert_not_awaited()
    client.app.state.game_config.set.assert_not_awaited()


@pytest.mark.parametrize("method,path", [(method, path) for method, path in CASES if method != "GET"])
def test_read_capability_cannot_mutate(client, method, path):
    assert (
        client.request(method, path, headers={"X-Operator-Key": "ops-reader"}).status_code == 403
    )  # pragma: allowlist secret
    client.app.state.game_config.set.assert_not_awaited()


@pytest.mark.parametrize("key", ["ops-reader", "ops-writer"])  # pragma: allowlist secret
def test_operator_can_read_config(client, key):
    assert client.get("/api/internal/config", headers={"X-Operator-Key": key}).status_code == 200
    client.app.state.game_config.list_all.assert_awaited_once()


def test_writer_can_mutate_config(client):
    response = client.patch(
        "/api/internal/config/combat/ROUND_TIME", json={"value": "42"}, headers={"X-Operator-Key": "ops-writer"}
    )  # pragma: allowlist secret
    assert response.status_code == 200
    client.app.state.game_config.set.assert_awaited_once_with("combat", "ROUND_TIME", "42")


@pytest.mark.parametrize("key", ["ops-reader", "ops-writer"])  # pragma: allowlist secret
def test_operator_can_read_generation_task(client, key):
    from src.backend.features.generation_ai.api import get_generation_task_repository

    task = SimpleNamespace(
        id="task",
        task_type="news_cover_image",
        entity_type="news",
        entity_id="article",
        output_kind="image",
        status="pending",
        storage_key=None,
        generated_url=None,
        asset_hash=None,
        metadata_={},
        error={},
    )
    repository = SimpleNamespace(get=AsyncMock(return_value=task))
    client.app.dependency_overrides[get_generation_task_repository] = lambda: repository
    response = client.get("/api/admin/generation-ai/tasks/task", headers={"X-Operator-Key": key})
    assert response.status_code == 200
    assert response.json()["task_id"] == "task"
    repository.get.assert_awaited_once_with("task")


@pytest.mark.parametrize("key", ["ops-reader", "ops-writer"])  # pragma: allowlist secret
def test_operator_can_list_simulations(client, monkeypatch, key):
    from src.backend.features.combat.api import ai_simulation_router as module

    service = SimpleNamespace(list_recent=AsyncMock(return_value=[]))
    client.app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(module, "_service", lambda db: service)
    response = client.get("/api/admin/combat-ai/simulation-runs", headers={"X-Operator-Key": key})
    assert response.status_code == 200
    assert response.json() == {"runs": []}
    service.list_recent.assert_awaited_once_with(limit=50, run_kind=None)


def test_news_cover_generation_route_is_removed(client):
    assert (
        client.post(
            "/api/admin/generation-ai/news-covers", headers={"X-Operator-Key": "ops-writer"}, json={}
        ).status_code
        == 404
    )


def test_writer_can_create_simulation(client, monkeypatch):
    from src.backend.features.combat.api import ai_simulation_router as module

    db = SimpleNamespace(commit=AsyncMock())
    client.app.dependency_overrides[get_db] = lambda: db
    row = SimpleNamespace(
        id="new-run",
        run_kind="simulation",
        scenario_key="starter_presets_5v5",
        status="completed",
        policy_ref=None,
        seed=7,
        max_rounds=3,
        rounds_completed=3,
        winner=None,
        reward=None,
        telemetry={},
        metadata_={},
        report_text="",
        created_at=None,
    )
    service = SimpleNamespace(run_demo=AsyncMock(return_value=row))
    monkeypatch.setattr(module, "_service", lambda session: service)
    response = client.post(
        "/api/admin/combat-ai/simulation-runs/demo?seed=7&max_rounds=3", headers={"X-Operator-Key": "ops-writer"}
    )  # pragma: allowlist secret
    assert response.status_code == 200
    assert response.json()["id"] == "new-run"
    service.run_demo.assert_awaited_once_with(seed=7, max_rounds=3, scenario_key="starter_presets_5v5")
    db.commit.assert_awaited_once()
