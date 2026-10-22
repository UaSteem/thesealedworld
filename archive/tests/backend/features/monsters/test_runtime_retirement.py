from __future__ import annotations

import asyncio

import pytest

from src.backend.features.monsters.catalog.materialization.clan_factory import ClanFactory
from src.backend.features.monsters.catalog.materialization.generation_builder import MonsterClanGenerationBuilder
from src.backend.features.monsters.catalog.services.generated_rebuild_service import MonsterGeneratedRebuildService
from src.backend.features.monsters.encounters.services.habitat_clan_pool_materialization_service import (
    HabitatClanPoolMaterializationService,
)
from src.backend.features.monsters.encounters.services.monster_group_service import MonsterGroupService
from src.backend.features.monsters.runtime_retirement import LegacyMonsterRuntimeRetired


class ForbiddenIO:
    def __getattr__(self, name):
        raise AssertionError(f"Retired runtime touched dependency: {name}")


def test_world_and_rift_group_requests_fail_before_dependencies():
    service = object.__new__(MonsterGroupService)
    service.location_context = ForbiddenIO()
    service.repository = ForbiddenIO()
    for request in (
        service.prepare_monster_group("loc", 100),
        service.prepare_monster_group_for_scope(
            scope_type="rift", scope_id="old", budget=100, tier=1, danger=0, biome_id="forest", loc_id="loc"
        ),
    ):
        with pytest.raises(LegacyMonsterRuntimeRetired):
            asyncio.run(request)


def test_materialization_entrypoints_fail_before_dependencies():
    from src.backend.features.monsters.catalog.services.encounter_monster_service import EncounterMonsterService

    encounter = EncounterMonsterService(ForbiddenIO(), ForbiddenIO())
    factory = ClanFactory(ForbiddenIO())
    builder = object.__new__(MonsterClanGenerationBuilder)
    materializer = HabitatClanPoolMaterializationService(repository=ForbiddenIO(), factory=ForbiddenIO())
    rebuild = object.__new__(MonsterGeneratedRebuildService)
    for request in (
        factory.build_clan_template(
            family_id="wolf_pack", context=None, context_hash="x", identity_hash="x", normalized_tags=()
        ),
        builder.generate_clan_template(None),
        materializer.ensure_scope_pool(None),
        materializer.ensure_scope_pools(iter(())),
        rebuild.apply(None),
        encounter.ensure_clan_for_context(None, "wolf_pack"),
        encounter.prune_generated_clans_for_zone_contexts({}),
    ):
        with pytest.raises(LegacyMonsterRuntimeRetired):
            asyncio.run(request)


def test_rebuild_http_dependency_and_cli_reject_without_database(monkeypatch):
    from fastapi import HTTPException

    from src.backend.features.monsters.api.router import get_monster_generated_rebuild_service
    from src.backend.features.monsters.scripts import rebuild_generated

    def forbidden_session(*args, **kwargs):
        raise AssertionError("Database must not be opened")

    monkeypatch.setattr(rebuild_generated, "get_manual_session_context", forbidden_session)
    with pytest.raises(HTTPException) as exc:
        get_monster_generated_rebuild_service()
    assert exc.value.status_code == 410
    with pytest.raises(LegacyMonsterRuntimeRetired):
        rebuild_generated.main()
    with pytest.raises(LegacyMonsterRuntimeRetired):
        asyncio.run(rebuild_generated.async_main())


def test_event_replies_with_retirement_without_database(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from src.backend.features.monsters import events

    def forbidden_session(*args, **kwargs):
        raise AssertionError("Database must not be opened")

    bus = SimpleNamespace(publish=AsyncMock(), publish_reply=AsyncMock())
    monkeypatch.setattr(events, "_app", SimpleNamespace(state=SimpleNamespace(events=bus)))
    monkeypatch.setattr(events, "get_manual_session_context", forbidden_session)
    asyncio.run(events.on_group_prepare_requested({"correlation_id": "retired-test"}))
    assert bus.publish.await_args.args[0] == events.MonsterEvents.GROUP_PREPARE_FAILED
    ack = bus.publish_reply.await_args.args[1]
    assert ack["status"] == "error"
    assert ack["code"] == "legacy_monster_runtime_retired"


def test_retired_rebuild_constructor_never_creates_item_or_document_services(monkeypatch):
    from src.backend.features.monsters.catalog.services import generated_rebuild_service as rebuild

    def forbidden(*args, **kwargs):
        raise AssertionError("No item or document service should be constructed")

    monkeypatch.setattr(rebuild, "ItemGenerationService", forbidden)
    monkeypatch.setattr(rebuild, "GeneratedMonsterActorRepository", forbidden)
    with pytest.raises(LegacyMonsterRuntimeRetired):
        rebuild.MonsterGeneratedRebuildService(session=ForbiddenIO())


def test_rebuild_routes_return_gone_before_db_dependency():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from src.backend.core.database import get_db
    from src.backend.features.monsters.api.access import require_monster_catalog_read, require_monster_catalog_write
    from src.backend.features.monsters.api.router import router

    def forbidden_db():
        raise AssertionError("Retired HTTP endpoints must not open a DB session")

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = forbidden_db
    app.dependency_overrides[require_monster_catalog_read] = lambda: "test-reader"
    app.dependency_overrides[require_monster_catalog_write] = lambda: "test-writer"
    with TestClient(app) as client:
        for operation in ("plan", "apply"):
            response = client.post(f"/api/admin/monsters/generated/rebuild/{operation}", json={})
            assert response.status_code == 410
            assert response.json()["detail"]["code"] == "legacy_monster_runtime_retired"
        response = client.get("/api/admin/monsters/catalog/bootstrap")
        assert response.status_code == 200
        assert response.headers["ETag"]


def test_world_bootstrap_keeps_world_and_rift_catalog_without_monster_materialization(monkeypatch):
    from contextlib import asynccontextmanager
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from src.backend.core.containers import game

    session = SimpleNamespace(commit=AsyncMock())

    @asynccontextmanager
    async def session_context():
        yield session

    def forbidden(*args, **kwargs):
        raise AssertionError("Retired population/template service must not be constructed")

    world_bootstrap = SimpleNamespace(bootstrap=AsyncMock(return_value=7))
    rift_bootstrap = SimpleNamespace(sync_fixtures=AsyncMock(return_value=SimpleNamespace(settings=2, nodes=9)))
    monkeypatch.setattr(game, "get_manual_session_context", session_context)
    for name in (
        "WorldRepository",
        "WorldDataIntegration",
        "WorldLocationIntegration",
        "WorldCacheService",
        "AIGenerationTaskRepository",
        "GenerationAIService",
        "LLMWorldGenerator",
        "RiftResourceLoader",
        "RiftSettingRepository",
        "RiftNodePoolRepository",
        "RiftCatalogDocumentRepository",
    ):
        monkeypatch.setattr(game, name, lambda *args, **kwargs: SimpleNamespace())
    monkeypatch.setattr(game, "build_generation_ai_registry", lambda **kwargs: SimpleNamespace())
    monkeypatch.setattr(game, "WorldBootstrapService", lambda **kwargs: world_bootstrap)
    monkeypatch.setattr(game, "RiftCatalogBootstrapService", lambda **kwargs: rift_bootstrap)
    monkeypatch.setattr(game, "get_mongo_provider", lambda: SimpleNamespace(database=lambda: object()))
    for name in (
        "EncounterMonsterService",
        "ClanFactory",
        "MonsterClanGenerationBuilder",
        "HabitatClanPoolMaterializationService",
        "RiftPopulationBootstrapService",
    ):
        monkeypatch.setattr(game, name, forbidden, raising=False)
    monkeypatch.setattr(game.settings, "bootstrap_content_materialization_enabled", True)
    container = game.GameFeatureContainer()
    monkeypatch.setattr(container, "_schedule_bootstrap_generation_ai", AsyncMock(return_value=0))
    app = SimpleNamespace(state=SimpleNamespace(world_locations=object()))
    asyncio.run(container._bootstrap_world(app))
    world_bootstrap.bootstrap.assert_awaited_once()
    rift_bootstrap.sync_fixtures.assert_awaited_once()
    assert app.state.world_cache_loaded_count == 7
    assert app.state.rift_catalog_settings == 2
    assert app.state.monster_population_clans == 0
    assert app.state.rift_population_clans == 0
    assert app.state.rift_population_bindings == {}
    session.commit.assert_awaited_once()
