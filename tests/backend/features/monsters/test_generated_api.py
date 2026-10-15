import uuid

import pytest

from src.backend.config.settings import settings
from src.backend.features.monsters.api.router import (
    get_generated_monster_view_service,
)
from src.backend.features.monsters.inspection.dto.generated_view import GeneratedMonstersResponseDTO


@pytest.fixture(autouse=True)
def catalog_credentials(monkeypatch, client):
    monkeypatch.setattr(settings, "frontend_internal_service_key", "test-read-secret")
    monkeypatch.setattr(settings, "monster_catalog_write_key", "test-write-secret")
    client.headers.update(
        {
            "X-Internal-Service-Key": "test-read-secret",
            "X-Monster-Catalog-Write-Key": "test-write-secret",
        }
    )


@pytest.mark.unit
def test_generated_monsters_route_returns_paginated_clans(client) -> None:
    class FakeService:
        async def list_generated(
            self,
            *,
            family_id=None,
            clan_id=None,
            role=None,
            include_members=True,
            light=False,
            limit=25,
            offset=0,
        ) -> GeneratedMonstersResponseDTO:
            assert family_id == "rat_swarm"
            assert clan_id is None
            assert role is None
            assert include_members is True
            assert light is True
            assert limit == 10
            assert offset == 20
            return GeneratedMonstersResponseDTO(
                items=[
                    {
                        "clan_id": str(uuid.uuid4()),
                        "family_id": "rat_swarm",
                        "tier": 1,
                        "zone_id": "zone-a",
                        "title": "Rats",
                        "name_ru": "Rats",
                        "description": "Rats",
                        "gear_score_summary": {"count": 1, "min": 7, "avg": 7.0, "max": 7, "total": 7},
                        "members": [
                            {
                                "member_id": str(uuid.uuid4()),
                                "monster_id": str(uuid.uuid4()),
                                "clan_id": str(uuid.uuid4()),
                                "variant_id": "sewer_rat",
                                "variant_key": "sewer_rat",
                                "member_hash": "hash",
                                "role": "minion",
                                "title": "Rat",
                                "member_tier": 1,
                                "min_tier": 1,
                                "max_tier": 1,
                                "mongo_actor_key": "actor:rat",
                                "name_ru": "Rat",
                                "short_description": "Rat",
                                "threat_rating": 7,
                                "gear_score": 7,
                            }
                        ],
                    }
                ],
                pagination={"limit": 10, "offset": 20, "total": 42, "has_more": True},
            )

    from src.backend.app import app

    app.dependency_overrides[get_generated_monster_view_service] = lambda: FakeService()
    try:
        response = client.get("/api/admin/monsters/generated?family_id=rat_swarm&light=true&limit=10&offset=20")
    finally:
        app.dependency_overrides.pop(get_generated_monster_view_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"] == {"limit": 10, "offset": 20, "total": 42, "has_more": True}
    assert payload["items"][0]["members"][0]["monster_id"]
    assert payload["items"][0]["members"][0]["variant_key"] == "sewer_rat"
    assert payload["items"][0]["members"][0]["gear_score"] == 7


@pytest.mark.unit
def test_generated_monsters_summary_route_returns_aggregate_counts(client) -> None:
    class FakeService:
        async def summary(self, *, family_id=None):
            assert family_id == "rat_swarm"
            return {"clans": 6, "members": 72, "missing_images": 1}

    from src.backend.app import app

    app.dependency_overrides[get_generated_monster_view_service] = lambda: FakeService()
    try:
        response = client.get("/api/admin/monsters/generated/summary?family_id=rat_swarm")
    finally:
        app.dependency_overrides.pop(get_generated_monster_view_service, None)

    assert response.status_code == 200
    assert response.json() == {"clans": 6, "members": 72, "missing_images": 1}


@pytest.mark.unit
def test_generated_monster_rebuild_plan_route_returns_gone(client) -> None:
    response = client.post("/api/admin/monsters/generated/rebuild/plan", json={})
    assert response.status_code == 410
    assert response.json()["detail"]["code"] == "legacy_monster_runtime_retired"


@pytest.mark.unit
def test_generated_monster_rebuild_apply_route_returns_gone(client) -> None:
    response = client.post("/api/admin/monsters/generated/rebuild/apply", json={})
    assert response.status_code == 410
    assert response.json()["detail"]["code"] == "legacy_monster_runtime_retired"


@pytest.mark.unit
@pytest.mark.parametrize(
    "path",
    [
        "/api/admin/monsters/generated/clans/example/regenerate-flavor",
        "/api/admin/monsters/generated/clans/example/regenerate-member-images",
        "/api/admin/monsters/generated/clans/regenerate-member-images",
        "/api/admin/monsters/generated/members/example/regenerate-image",
    ],
)
def test_monster_generation_routes_are_removed(client, path):
    assert client.post(path).status_code == 404
