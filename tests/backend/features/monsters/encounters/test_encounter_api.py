import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.config.settings import settings
from src.backend.core.database import get_db
from src.backend.features.monsters.api.dependencies import get_cached_monster_selection_service
from src.backend.features.monsters.api.router import router
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "frontend_internal_service_key", "test-read-secret")
    app = FastAPI()
    app.include_router(router)

    def forbidden_database():
        pytest.fail("Encounter preparation must not access the database")

    class LocalSelection:
        async def select(self, order):
            return MonsterEncounterSelectionService().select(order), "test"

    app.dependency_overrides[get_cached_monster_selection_service] = lambda: LocalSelection()
    app.dependency_overrides[get_db] = forbidden_database
    return TestClient(app, headers={"X-Internal-Service-Key": "test-read-secret"})


def order(**changes):
    return {"encounter_type": "ordinary", "location_tier": 0, "family_ids": ["goblin_tribe"], "seed": 42, "player_gear_score": 36.326, **changes}


def test_contract_advertises_domain_choices_without_system_families(client):
    response = client.get("/api/admin/monsters/encounters/contract")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 6
    assert {item["id"] for item in data["difficulties"]} == {"easy", "normal", "hard"}
    assert {item["id"]: item["available"] for item in data["party_modes"]} == {"solo": True, "group": False}
    assert {item["id"] for item in data["encounter_types"]} == {"ordinary", "patrol", "guard", "leader"}
    assert {"minions", "seniors", "roles"} <= data["profile_override_example"].keys()
    assert data["location_tiers"] == list(range(8))
    assert {item["id"] for item in data["families"]} == {
        "goblin_tribe",
        "wolf_pack",
        "rat_swarm",
        "bandit_gang",
        "golem_foundry",
    }


def test_preview_prepares_pool_not_selected_squad_and_is_repeatable(client):
    response = client.get("/api/admin/monsters/encounters/preview", params={"order": json.dumps(order())})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "prepared"
    assert data["configurations"] and data["candidates"]
    assert "members" not in data
    assert all(candidate["tier"] == 0 for candidate in data["candidates"])
    assert data == client.get("/api/admin/monsters/encounters/preview", params={"order": json.dumps(order())}).json()


@pytest.mark.parametrize(
    "value",
    [
        "{",
        json.dumps(order(count={"min_count": 3, "max_count": 5})),
        json.dumps(order(location_tier=True)),
        json.dumps(order(seed=None)),
        json.dumps(order(required_tags=[])),
        json.dumps(order(excluded_tags=["beast"])),
    ],
)
def test_invalid_external_order_is_422(client, value):
    assert client.get("/api/admin/monsters/encounters/preview", params={"order": value}).status_code == 422


def test_semantic_rejection_is_typed_successful_inspection(client):
    data = client.get(
        "/api/admin/monsters/encounters/preview", params={"order": json.dumps(order(encounter_type="missing"))}
    ).json()
    assert data["status"] == "rejected"
    assert data["reasons"][0]["code"] == "unknown_encounter_type"


@pytest.mark.parametrize("path", ["contract", "preview", "select"])
def test_encounter_inspection_is_protected_and_readonly(client, path):
    url = "/api/admin/monsters/encounters/" + path
    assert client.get(url, headers={"X-Internal-Service-Key": "wrong"}).status_code == 403
    assert client.post(url, json=order()).status_code == 405


def test_selected_squad_is_repeatable_ready_and_satisfies_internal_contract(client):
    from src.backend.features.monsters.encounters.dto.result import MonsterEncounterSelectionDTO

    url = "/api/admin/monsters/encounters/select"
    params = {"order": json.dumps(order())}
    response = client.get(url, params=params)
    assert response.status_code == 200
    result = MonsterEncounterSelectionDTO.model_validate(response.json())
    assert result.status == "selected"
    assert result.selection.members
    assert all(member in result.preparation.candidates for member in result.selection.members)
    assert response.json() == client.get(url, params=params).json()


def test_selection_rejections_and_bad_orders_remain_readonly(client):
    url = "/api/admin/monsters/encounters/select"
    assert client.get(url, params={"order": "{"}).status_code == 422
    data = client.get(url, params={"order": json.dumps(order(location_tier=7))}).json()
    assert data["status"] == "rejected"
    assert data["selection"] is None
    assert data["reasons"][0]["code"] == "no_ready_candidates"


@pytest.mark.parametrize("difficulty", ["easy", "normal", "hard"])
def test_selection_cannot_escape_requested_difficulty(client, difficulty):
    data = client.get(
        "/api/admin/monsters/encounters/select",
        params={"order": json.dumps(order(difficulty=difficulty, party_mode="solo", player_gear_score=1000000.0))},
    ).json()
    assert data["status"] == "selected"
    config = data["selection"]["assembly_input"]["configuration"]
    assert config["difficulty"] == difficulty
    assert config["party_mode"] == "solo"


def test_group_has_explicit_refusal_without_solo_fallback(client):
    data = client.get(
        "/api/admin/monsters/encounters/select", params={"order": json.dumps(order(party_mode="group"))}
    ).json()
    assert data["status"] == "rejected"
    assert data["selection"] is None
    assert data["reasons"][0]["code"] == "group_profile_unavailable"


@pytest.mark.parametrize("families", [[], ["rat_swarm", "goblin_tribe"]])
def test_order_requires_exactly_one_family(client, families):
    assert (
        client.get(
            "/api/admin/monsters/encounters/select", params={"order": json.dumps(order(family_ids=families))}
        ).status_code
        == 422
    )


def test_external_profile_replaces_builtin_and_spends_points(client):
    override = {
        "id": "studio.test.veteran",
        "minions": {"base_points": 30},
        "seniors": {"base_points": 23},
        "roles": [
            {"role": "minion", "min_count": 2, "max_count": 3},
            {"role": "veteran", "min_count": 1, "max_count": 1},
        ],
        "min_members": 2,
        "max_members": 4,
    }
    response = client.get(
        "/api/admin/monsters/encounters/select", params={"order": json.dumps(order(profile_override=override))}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "selected"
    assert data["profile_source"] == "external"
    assert data["profile_id"] == "studio.test.veteran"
    assert data["variant_id"] == "ranks"
    assert sum(m["role"] == "veteran" for m in data["selection"]["members"]) == 1
    assert all(m["role"] in {"minion", "veteran"} for m in data["selection"]["members"])
    assert data["budget_spent"] == sum(m["assembly_cost"] for m in data["selection"]["members"])
    assert data["budget_remaining"] == 53 - data["budget_spent"]
    assert data["minions"]["spent_points"] == sum(m["assembly_cost"] for m in data["selection"]["members"] if m["role"] == "minion")
    assert data["minions"]["spent_points"] <= 30
    assert data["seniors"]["spent_points"] == 23


def test_fifth_family_small_squad_is_selected_from_ready_golems(client):
    response = client.get(
        "/api/admin/monsters/encounters/select",
        params={
            "order": json.dumps(
                order(
                    family_ids=["golem_foundry"],
                    location_tier=2,
                    difficulty="easy",
                    profile_override={
                        "id": "test.golems",
                        "minions": {"base_points": 80},
                        "seniors": {"base_points": 0},
                        "roles": [{"role": "minion", "min_count": 2, "max_count": 2}],
                        "min_members": 2,
                        "max_members": 2,
                    },
                )
            ),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "selected"
    assert len(data["selection"]["members"]) == 2
    assert all(
        member["family_id"] == "golem_foundry" and member["role"] == "minion" for member in data["selection"]["members"]
    )
    assert data["budget_spent"] == sum(m["assembly_cost"] for m in data["selection"]["members"])
    assert 26 <= data["budget_spent"] <= 32
    assert all(m["tier"] == 2 for m in data["selection"]["members"])


def test_relative_builtin_requires_player_gs(client):
    data = client.get("/api/admin/monsters/encounters/select", params={"order": json.dumps(order(player_gear_score=None))}).json()
    assert data["status"] == "rejected"
    assert data["reasons"][0]["code"] == "player_gear_score_required"
