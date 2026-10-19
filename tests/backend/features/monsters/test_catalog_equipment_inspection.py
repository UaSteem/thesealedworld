import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.config.settings import settings
from src.backend.core.database import get_db
from src.backend.features.monsters.api.router import router
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.inspection.services.catalog_view_service import CatalogMonsterViewService


@pytest.fixture
def equipment_client(monkeypatch):
    monkeypatch.setattr(settings, "monster_catalog_read_key", "test-equipment-read-secret")
    app = FastAPI()
    app.include_router(router)

    def forbidden_database():
        raise AssertionError("Equipment inspection must not access database")

    app.dependency_overrides[get_db] = forbidden_database
    return TestClient(app, headers={"X-Internal-Service-Key": "test-equipment-read-secret"})


def test_all_prepared_goblin_tiers_have_items_and_unchanged_base_stats():
    service = CatalogMonsterViewService()
    members = [member for member in get_catalog().members.values() if member.family_id == "goblin_tribe"]
    assert len(members) == 12
    for member in members:
        for tier in range(member.min_tier, member.max_tier + 1):
            result = service.equipment(member_id=member.id, tier=tier)
            assert result.base_stats == dict(member.base_stats)
            assert result.stats_scaled is False
            assert result.available_tiers == list(range(member.min_tier, member.max_tier + 1))
            assert result.equipment_set_id == member.equipment_set_id
            assert result.items
            assert all(item.generation.rarity_tier == tier for item in result.items)


def test_equipment_endpoint_projects_complete_saved_items(equipment_client):
    response = equipment_client.get("/api/admin/monsters/catalog/equipment", params={
        "member_id": "goblin_tribe.base.goblin_sneak", "tier": 3,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == 3
    assert data["available_tiers"] == [0, 1, 2, 3, 4, 5]
    assert data["items"][0]["combat"]["power"] > 0
    assert "affixes" in data["items"][0]["generation"]


@pytest.mark.parametrize("member_id,tier,status", [
    ("unknown", 0, 404),
    ("goblin_tribe.base.goblin_sneak", 6, 422),
    ("goblin_tribe.base.goblin_sneak", -1, 422),
    ("goblin_tribe.base.goblin_sneak", 8, 422),
])
def test_equipment_endpoint_rejects_unknown_or_unavailable(equipment_client, member_id, tier, status):
    assert equipment_client.get("/api/admin/monsters/catalog/equipment", params={
        "member_id": member_id, "tier": tier,
    }).status_code == status


def test_golem_family_has_prepared_natural_equipment(equipment_client):
    member = next(member for member in get_catalog().members.values() if member.family_id not in {"goblin_tribe", "wolf_pack", "rat_swarm", "bandit_gang"})
    response = equipment_client.get("/api/admin/monsters/catalog/equipment", params={
        "member_id": member.id, "tier": member.min_tier,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["available_tiers"] == [2, 3, 4, 5]
    assert data["items"] and len(data["items"]) == len(data["item_cards"])
    assert all(item["generation"]["natural_key"] for item in data["items"])


@pytest.mark.parametrize("key", [None, "wrong-key"])
def test_equipment_endpoint_requires_catalog_read_access(equipment_client, key):
    equipment_client.headers.clear()
    headers = {"X-Internal-Service-Key": key} if key else {}
    response = equipment_client.get("/api/admin/monsters/catalog/equipment", params={
        "member_id": "goblin_tribe.base.goblin_sneak", "tier": 0,
    }, headers=headers)
    assert response.status_code == 403


def test_inspection_returns_independent_item_data():
    service = CatalogMonsterViewService()
    first = service.equipment(member_id="goblin_tribe.base.goblin_sneak", tier=0)
    first.items[0].combat.power = -999
    second = service.equipment(member_id="goblin_tribe.base.goblin_sneak", tier=0)
    assert second.items[0].combat.power >= 0


@pytest.mark.parametrize("tier", range(1, 6))
def test_wolf_prepared_tiers_have_natural_cards_and_beast_stats(tier, monkeypatch):
    from src.backend.features.items.services.generation_service import ItemGenerationService
    from src.backend.features.monsters.catalog.resources.equipment_mapping import get_natural_equipment_mapping

    def forbidden(*args, **kwargs):
        raise AssertionError("Inspection must only read prepared items")

    monkeypatch.setattr(ItemGenerationService, "generate_runtime_projections", forbidden)
    service = CatalogMonsterViewService()
    members = [member for member in get_catalog().members.values() if member.family_id == "wolf_pack"]
    assert len(members) == 11
    for member in members:
        original = dict(member.base_stats)
        view = service.equipment(member_id=member.id, tier=tier)
        assert view.available_tiers == list(range(1, 6))
        assert len(view.items) == len(view.item_cards) == (3 if member.role in {"minion", "veteran"} else 4)
        assert view.equipment_set_id == f"wolf_pack.{member.base_id}"
        assert view.base_stats == original == dict(member.base_stats)
        trace = view.stats_preview.technical["equipped_trace"]
        assert trace["raw"]["rules"]["attribute_profile"] == "monster:beast"
        assert view.stats_preview.technical["skills"] == {key: round(tier / 7, 4) for key in member.skills}
        for item, card in zip(view.items, view.item_cards, strict=True):
            mapping = get_natural_equipment_mapping(item.generation.natural_key)
            assert mapping is not None
            assert card.title == mapping.name_ru
            assert card.description == mapping.description_ru
            assert card.material_label == "Природное снаряжение"
            assert card.technical == item.model_dump(mode="json")
        assert view.stats_preview.technical["equipped"]["armor"] > view.stats_preview.technical["base"]["armor"]
        assert view.stats_preview.technical["equipped"]["main_hand_damage_base"] > 0


def test_wolf_equipment_endpoint_is_read_only_and_returns_complete_cards(equipment_client):
    response = equipment_client.get("/api/admin/monsters/catalog/equipment", params={
        "member_id": "wolf_pack.base.cub", "tier": 3,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == 3
    assert data["available_tiers"] == [1, 2, 3, 4, 5]
    assert len(data["items"]) == len(data["item_cards"]) == 3
    assert any("клыки" in card["title"].lower() for card in data["item_cards"])
    assert data["stats_preview"]["technical"]["equipped_trace"]["raw"]["rules"]["attribute_profile"] == "monster:beast"


@pytest.mark.parametrize("family_id,count,profile", [
    ("rat_swarm", 12, "monster:beast"),
    ("bandit_gang", 12, "monster:humanoid"),
])
def test_remaining_prepared_families_all_tiers_are_read_only(family_id, count, profile, monkeypatch):
    from src.backend.features.items.services.generation_service import ItemGenerationService
    from src.backend.features.monsters.catalog.resources.equipment_mapping import get_natural_equipment_mapping

    def forbidden(*args, **kwargs):
        raise AssertionError("Inspection must only read prepared items")

    monkeypatch.setattr(ItemGenerationService, "generate_runtime_projections", forbidden)
    service = CatalogMonsterViewService()
    members = [member for member in get_catalog().members.values() if member.family_id == family_id]
    assert len(members) == count
    for member in members:
        original = dict(member.base_stats)
        for tier in range(member.min_tier, member.max_tier + 1):
            view = service.equipment(member_id=member.id, tier=tier)
            assert view.base_stats == original == dict(member.base_stats)
            assert view.available_tiers == list(range(member.min_tier, member.max_tier + 1))
            assert len(view.items) == len(view.item_cards)
            assert len(view.items) == len([value for value in member.fixed_loadout.values() if value])
            assert view.stats_preview.technical["equipped_trace"]["raw"]["rules"]["attribute_profile"] == profile
            assert view.stats_preview.technical["skills"] == {key: round(tier / 7, 4) for key in member.skills}
            for item, card in zip(view.items, view.item_cards, strict=True):
                if family_id == "rat_swarm":
                    natural = get_natural_equipment_mapping(item.generation.natural_key)
                    assert natural is not None
                    assert card.title == natural.name_ru
                    assert card.description == natural.description_ru
                    assert card.material_label == "Природное снаряжение"
                else:
                    assert not item.generation.natural_key
                    assert card.material_label != "Природное снаряжение"
                assert card.technical == item.model_dump(mode="json")
            assert view.stats_preview.technical["equipped"]["armor"] > view.stats_preview.technical["base"]["armor"]


@pytest.mark.parametrize("member_id", ["rat_swarm.base.screecher", "rat_swarm.base.rat_brute",
                                     "bandit_gang.base.bandit_cutthroat"])
def test_remaining_equipment_endpoint_is_read_only(equipment_client, member_id):
    response = equipment_client.get("/api/admin/monsters/catalog/equipment", params={"member_id": member_id, "tier": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["available_tiers"] == list(range(1 if member_id.startswith("bandit_gang") else 0, 6))
    assert len(data["items"]) == len(data["item_cards"])
    slots = {item["slot"] for item in data["items"]}
    if member_id.endswith("screecher"):
        assert {"two_hand", "quiver"} <= slots
