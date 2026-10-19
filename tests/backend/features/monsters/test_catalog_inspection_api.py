import hashlib
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.config.settings import settings
from src.backend.core.database import get_db
from src.backend.features.monsters.api.router import router
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.inspection.services.catalog_view_service import CatalogMonsterViewService


@pytest.fixture
def catalog_client(monkeypatch):
    monkeypatch.setattr(settings, "frontend_internal_service_key", "test-read-secret")
    app = FastAPI()
    app.include_router(router)

    def forbidden_database():
        raise AssertionError("Catalog inspection must not access database")

    app.dependency_overrides[get_db] = forbidden_database
    return TestClient(app, headers={"X-Internal-Service-Key": "test-read-secret"})


def test_catalog_inspection_returns_authored_clans_without_database(catalog_client):
    response = catalog_client.get("/api/admin/monsters/catalog")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 6
    assert sum(c["member_count"] for c in data["items"]) == 63
    assert all(c["clan_id"].endswith(".base") for c in data["items"])
    assert not any("created_at" in c or "unique_hash" in c for c in data["items"])
    member = data["items"][0]["members"][0]
    expected = get_catalog().members[member["member_id"]]
    assert member["base_stats"] == dict(expected.base_stats)
    assert member["skills"] == list(expected.skills)
    assert member["fixed_loadout"] == dict(expected.fixed_loadout)


def test_catalog_summary_counts_missing_member_art(catalog_client):
    assert catalog_client.get("/api/admin/monsters/catalog/summary").json() == {
        "families": 6, "clans": 6, "members": 63, "missing_images": 16,
    }
    assert catalog_client.get("/api/admin/monsters/catalog/summary?family_id=goblin_tribe").json() == {
        "families": 1, "clans": 1, "members": 12, "missing_images": 0,
    }


def test_stone_golems_are_inspectable_with_prepared_natural_equipment(catalog_client):
    response = catalog_client.get("/api/admin/monsters/catalog?clan_id=golem_foundry.base")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    clan = data["items"][0]
    assert clan["member_count"] == 12
    assert {member["role"] for member in clan["members"]} == {"minion", "veteran", "elite", "boss"}
    gear = catalog_client.get("/api/admin/monsters/catalog/equipment", params={
        "member_id": "golem_foundry.base.stone_worker", "tier": 2,
    })
    assert gear.status_code == 200
    assert "Каменный" in response.text


def test_catalog_filters_members_and_paginates_without_database(catalog_client):
    filtered = catalog_client.get("/api/admin/monsters/catalog?family_id=goblin_tribe&role=boss").json()
    assert filtered["pagination"]["total"] == 1
    assert all(m["role"] == "boss" for m in filtered["items"][0]["members"])
    page = catalog_client.get("/api/admin/monsters/catalog?offset=1&limit=2&include_members=false").json()
    assert len(page["items"]) == 2
    assert page["pagination"]["has_more"] is True
    assert all(not c["members"] and c["member_count"] for c in page["items"])
    assert catalog_client.get("/api/admin/monsters/catalog?clan_id=unknown").json()["items"] == []


@pytest.mark.parametrize("path", ["/catalog", "/catalog/summary"])
def test_catalog_inspection_requires_read_credentials(catalog_client, path):
    response = catalog_client.get("/api/admin/monsters" + path, headers={"X-Internal-Service-Key": "wrong"})
    assert response.status_code == 403


def test_published_local_images_are_byte_identical_to_sources():
    service = CatalogMonsterViewService()
    for clan in service.list_catalog(limit=100).items:
        for member in clan.members:
            if member.image is None:
                continue
            assert member.image.image_url.startswith("/static/images/monsters/catalog/")
            published = Path("src/frontend") / member.image.image_url.lstrip("/")
            assert published.is_file()
            assert hashlib.sha256(published.read_bytes()).digest() == hashlib.sha256(
                Path(member.image.source_path).read_bytes()
            ).digest()
