"""Read-only Studio consumer checks for the Monsters encounter contract."""

import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.studio.features.cabinet.modules.content_ops.cabinet as content_ops
from fastapi_cabinet import include_cabinet
from src.studio.integrations.backend_api.catalog_monsters import (
    CatalogMonstersApi,
    EncounterContract,
    EncounterSelectionResult,
)

METADATA = {
    "version": 4,
    "profile_override_example": {
        "id": "test",
        "budget": {"base_points": 80, "gs_bonus_max": 10, "gs_threshold": 35, "gs_step_size": 5, "gs_points_per_step": 5},
        "variants": [{"id": "veteran", "core": {"veteran": 1, "elite": 0, "boss": 0}}],
        "min_members": 2,
        "max_members": 8,
    },
    "encounter_types": [{"id": "ordinary", "name": "Обычная встреча"}],
    "location_tiers": list(range(8)),
    "families": [{"id": "goblin_tribe", "name": "Гоблины"}],
    "difficulties": [{"id": "normal", "name": "Средняя"}, {"id": "hard", "name": "Тяжёлая"}],
    "party_modes": [
        {"id": "solo", "name": "Соло", "available": True},
        {"id": "group", "name": "Группа", "available": False},
    ],
}
RESULT = {
    "status": "prepared",
    "order": {},
    "profile": METADATA["profile_override_example"],
    "profile_source": "builtin",
    "admission": {"location_tier": 1, "roles": [{"role": "minion", "min_tier": 1, "max_tier": 1}]},
    "configurations": [
        {
            "id": "goblin.normal",
            "family_id": "goblin_tribe",
            "encounter_type": "ordinary",
            "difficulty": "normal",
            "party_mode": "solo",
            "count": {"min_count": 2, "max_count": 5},
            "roles": [{"role": "minion", "min_count": 1, "max_count": 5}],
            "allow_repeated_members": True,
            "same_clan": True,
            "profile_source": "builtin",
            "profile_id": "solo.ordinary.normal",
            "variant_id": "minions",
            "budget_base": 20,
            "budget_bonus": 5,
            "budget_effective": 25,
            "gs_threshold": 35, "gs_step_size": 5, "gs_steps": 1,
            "gs_points_per_step": 5, "gs_bonus_max": 10, "gs_cap_reached": False,
        }
    ],
    "candidates": [
        {
            "member_id": "goblin.sneak",
            "family_id": "goblin_tribe",
            "clan_id": "base",
            "variant_id": "sneak",
            "role": "minion",
            "tier": 1,
            "name": "Лазутчик",
            "assembly_cost": 10,
        }
    ],
    "excluded": [
        {
            "member_id": "missing",
            "tier": 1,
            "issues": [{"code": "unknown_skill", "path": "skills", "message": "Навык отсутствует"}],
        }
    ],
    "reasons": [],
    "stages": [{"name": "admission", "status": "completed", "detail": "Правила допуска применены"}],
}


SELECTED = {
    "status": "selected",
    "preparation": RESULT,
    "selection": {
        "status": "selected",
        "assembly_input": {"configuration": RESULT["configurations"][0]},
        "members": RESULT["candidates"] * 2,
    },
    "reasons": [],
    "attempts": [{"configuration_id": "goblin.normal", "clan_id": "base", "feasible": True, "reasons": []}],
    "selection_strategy": "point_budget",
    "profile_source": "builtin",
    "profile_id": "solo.ordinary.normal",
    "variant_id": "minions",
    "budget_base": 20,
    "budget_bonus": 5,
    "budget_effective": 25,
    "budget_spent": 20,
    "budget_remaining": 5,
}


POOL = {
    "mode": "relative_gs", "reference_gs": 36.326, "player_gs_ratio": 0.8, "scaled_points": 20,
    "base_points": 20, "bonus_points": 5, "effective_points": 25,
    "gs_threshold": 35, "gs_step_size": 5, "gs_steps": 1,
    "gs_points_per_step": 5, "gs_bonus_max": 10, "gs_cap_reached": False,
}
SENIOR_POOL = {**POOL, "mode": "fixed", "base_points": 0, "bonus_points": 0, "effective_points": 0,
               "gs_points_per_step": 0, "gs_bonus_max": 0}
METADATA["version"] = 6
METADATA["profile_override_example"].pop("budget")
METADATA["profile_override_example"].pop("variants")
METADATA["profile_override_example"].update(
    minions=POOL, seniors=SENIOR_POOL,
    roles=[{"role": "minion", "min_count": 1, "max_count": 5}],
)
RESULT["configurations"][0].update(minions=POOL, seniors=SENIOR_POOL)
SELECTED.update(
    minions={**POOL, "spent_points": 20, "remaining_points": 5},
    seniors={**SENIOR_POOL, "spent_points": 0, "remaining_points": 0},
)


@pytest.mark.asyncio
async def test_encounter_client_uses_selected_source_get_and_exact_external_order():
    calls = []
    order = {
        "encounter_type": "ordinary",
        "difficulty": "hard",
        "party_mode": "solo",
        "player_gear_score": 125.5,
        "location_tier": 1,
        "family_ids": ["goblin_tribe"],
        "seed": 42,
    }

    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        assert request.url.host == "selected-backend"
        assert request.headers["X-Service-Key"] == "local-inspection"
        if request.url.path.endswith("/contract"):
            return httpx.Response(200, json=METADATA)
        assert json.loads(request.url.params["order"]) == order
        assert request.url.path.endswith("/select")
        return httpx.Response(200, json=SELECTED)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api = CatalogMonstersApi(
            client,
            "http://selected-backend",
            internal_service_key="local-inspection",
            internal_service_header="X-Service-Key",
        )
        assert (await api.get_encounter_contract()).families[0].name == "Гоблины"
        assert (await api.select_encounter(order)).selection.members[0].name == "Лазутчик"
    assert len(calls) == 2


@pytest.mark.parametrize("failure", [None, "rejected", "missing_gs", "invalid", "offline", "validation"])
def test_encounter_page_previews_and_surfaces_errors_without_writes(monkeypatch, failure):
    calls = []

    class Api:
        async def get_encounter_contract(self):
            if failure == "offline":
                raise httpx.ConnectError("private connection detail")
            return EncounterContract.model_validate(METADATA)

        async def select_encounter(self, order):
            calls.append(order)
            if failure == "validation":
                request = httpx.Request("GET", "http://backend/preview")
                raise httpx.HTTPStatusError(
                    "private response", request=request, response=httpx.Response(422, request=request)
                )
            if failure in {"rejected", "missing_gs"}:
                return EncounterSelectionResult.model_validate(
                    {
                        "status": "rejected",
                        "preparation": RESULT,
                        "selection": None,
                        "reasons": [
                            {
                                "code": "constraints_unsatisfiable",
                                "path": "selection",
                                "message": "Требуется GS игрока" if failure == "missing_gs" else "Нет допустимого состава",
                                "member_ids": [],
                            }
                        ],
                        "attempts": [
                            {"configuration_id": "goblin.normal", "clan_id": "base", "feasible": False, "reasons": []}
                        ],
                    }
                )
            return EncounterSelectionResult.model_validate(SELECTED)

    monkeypatch.setattr(content_ops, "_api", lambda request: Api())
    app = FastAPI()
    include_cabinet(app, modules=("src.studio.features.cabinet.modules.content_ops.cabinet",), mount_path="/admin")
    with TestClient(app) as client:
        response = client.get(
            "/admin/content-ops/monster-encounter",
            params={
                "run": "1",
                "location_tier": "bad" if failure == "invalid" else "1",
                "family_ids": "goblin_tribe",
                "required_tags": "forest, melee",
                "seed": "42",
            },
        )
        assert response.status_code == 200
        assert "Проверка заказа монстров" in response.text
        assert "private" not in response.text
        assert 'name="required_tags"' not in response.text
        assert 'name="excluded_tags"' not in response.text
        if failure != "offline":
            assert 'name="difficulty"' in response.text
            assert 'name="party_mode"' in response.text
            assert 'name="player_gear_score"' in response.text
        assert client.post("/admin/content-ops/monster-encounter").status_code in (404, 405)
        if failure is None:
            assert "Лазутчик" in response.text
            assert "Навык отсутствует" in response.text
            assert "2–5 бойцов" in response.text
            assert "Отряд собран" in response.text
            assert "2 бойцов" in response.text
            assert "Проверенные конфигурации" in response.text
            assert "Пул миньонов" in response.text
            assert "Пул старших" in response.text
            assert "Очки между пулами не переносятся" in response.text
            assert "порог GS" in response.text
            assert "GS на ступень" in response.text
            assert "достигнутая ступень" in response.text
            assert "Эталон GS" in response.text
            assert "Отношение GS" in response.text
            assert "Масштабированная база" in response.text
            assert "потолок бонуса" in response.text
            assert "Потрачено: 20" in response.text
            assert "Применённый профиль: встроенный" in response.text
            assert "остаток: 5" in response.text
            assert "Целевой GS:" not in response.text
            assert 'name="profile_source"' in response.text
            assert 'name="profile_override"' in response.text
            assert 'type="checkbox" name="family_ids"' not in response.text
            assert calls[0] == {
                "encounter_type": "ordinary",
                "difficulty": "normal",
                "party_mode": "solo",
                "location_tier": 1,
                "family_ids": ["goblin_tribe"],
                "seed": 42,
            }
        elif failure == "missing_gs":
            assert "Требуется GS игрока" in response.text
            assert "Отряд не собран" in response.text
            assert "player_gear_score" not in calls[0]
        elif failure == "rejected":
            assert "Нет допустимого состава" in response.text
            assert "Отряд не собран" in response.text
        else:
            assert 'role="alert"' in response.text


def test_source_client_keeps_key_server_side(monkeypatch):
    monkeypatch.setattr(content_ops, "studio_settings", SimpleNamespace(monster_catalog_read_key="local-key"))
    clients = []
    monkeypatch.setattr(content_ops, "CatalogMonstersApi", lambda **kwargs: clients.append(kwargs))
    for kind in ("local", "prod"):
        request = SimpleNamespace(
            state=SimpleNamespace(source=SimpleNamespace(kind=kind, api_base=f"http://{kind}")),
            app=SimpleNamespace(state=SimpleNamespace(backend_http_client=object())),
        )
        content_ops._api(request)
    assert clients[0]["internal_service_key"] == "local-key"
    assert clients[1]["internal_service_key"] is None
    assert clients[1]["base_url"] == "http://prod"


@pytest.mark.parametrize("gear_score", ["-1", "nan", "inf", "bad"])
def test_encounter_page_rejects_invalid_gs_before_backend_selection(monkeypatch, gear_score):
    class Api:
        async def get_encounter_contract(self):
            return EncounterContract.model_validate(METADATA)

        async def select_encounter(self, order):
            pytest.fail("Invalid GS must not reach backend")

    monkeypatch.setattr(content_ops, "_api", lambda request: Api())
    app = FastAPI()
    include_cabinet(app, modules=("src.studio.features.cabinet.modules.content_ops.cabinet",), mount_path="/admin")
    with TestClient(app) as client:
        response = client.get(
            "/admin/content-ops/monster-encounter",
            params={"run": "1", "player_gear_score": gear_score, "family_ids": "goblin_tribe"},
        )
    assert response.status_code == 200
    assert 'role="alert"' in response.text
    assert "конечное неотрицательное" in response.text


def test_encounter_page_forwards_group_and_displays_domain_refusal(monkeypatch):
    class Api:
        async def get_encounter_contract(self):
            return EncounterContract.model_validate(METADATA)

        async def select_encounter(self, order):
            assert order["party_mode"] == "group"
            assert order["difficulty"] == "hard"
            assert order["player_gear_score"] == 101.5
            return EncounterSelectionResult.model_validate(
                {
                    "status": "rejected",
                    "preparation": RESULT,
                    "reasons": [
                        {
                            "code": "party_mode_unavailable",
                            "path": "party_mode",
                            "message": "Групповой профиль пока не разработан",
                        }
                    ],
                }
            )

    monkeypatch.setattr(content_ops, "_api", lambda request: Api())
    app = FastAPI()
    include_cabinet(app, modules=("src.studio.features.cabinet.modules.content_ops.cabinet",), mount_path="/admin")
    with TestClient(app) as client:
        response = client.get(
            "/admin/content-ops/monster-encounter",
            params={
                "run": "1",
                "party_mode": "group",
                "difficulty": "hard",
                "player_gear_score": "101.5",
                "family_ids": "goblin_tribe",
            },
        )
    assert "Групповой профиль пока не разработан" in response.text
    assert "Отряд не собран" in response.text
    assert 'value="group" selected' in response.text


@pytest.mark.parametrize("source", ["builtin", "external"])
def test_encounter_override_is_forwarded_whole_only_when_external(monkeypatch, source):
    calls = []

    class Api:
        async def get_encounter_contract(self):
            return EncounterContract.model_validate(METADATA)

        async def select_encounter(self, order):
            calls.append(order)
            return EncounterSelectionResult.model_validate(SELECTED)

    monkeypatch.setattr(content_ops, "_api", lambda request: Api())
    app = FastAPI()
    include_cabinet(app, modules=("src.studio.features.cabinet.modules.content_ops.cabinet",), mount_path="/admin")
    override = METADATA["profile_override_example"]
    with TestClient(app) as client:
        response = client.get(
            "/admin/content-ops/monster-encounter",
            params={
                "run": "1",
                "family_ids": "goblin_tribe",
                "profile_source": source,
                "profile_override": json.dumps(override),
            },
        )
    assert response.status_code == 200
    assert len(calls) == 1
    if source == "external":
        assert calls[0]["profile_override"] == override
    else:
        assert "profile_override" not in calls[0]


@pytest.mark.parametrize("override", ["{broken", "[]", "null", '"text"'])
def test_encounter_external_invalid_json_never_reaches_selection(monkeypatch, override):
    class Api:
        async def get_encounter_contract(self):
            return EncounterContract.model_validate(METADATA)

        async def select_encounter(self, order):
            pytest.fail("Invalid external profile must not reach selection")

    monkeypatch.setattr(content_ops, "_api", lambda request: Api())
    app = FastAPI()
    include_cabinet(app, modules=("src.studio.features.cabinet.modules.content_ops.cabinet",), mount_path="/admin")
    with TestClient(app) as client:
        response = client.get(
            "/admin/content-ops/monster-encounter",
            params={
                "run": "1",
                "family_ids": "goblin_tribe",
                "profile_source": "external",
                "profile_override": override,
            },
        )
    assert response.status_code == 200
    assert 'role="alert"' in response.text


@pytest.mark.parametrize("families", [[], ["goblin_tribe", "rat_swarm"]])
def test_encounter_requires_exactly_one_family_before_selection(monkeypatch, families):
    class Api:
        async def get_encounter_contract(self):
            return EncounterContract.model_validate(METADATA)

        async def select_encounter(self, order):
            pytest.fail("Invalid family count must not reach selection")

    monkeypatch.setattr(content_ops, "_api", lambda request: Api())
    app = FastAPI()
    include_cabinet(app, modules=("src.studio.features.cabinet.modules.content_ops.cabinet",), mount_path="/admin")
    with TestClient(app) as client:
        response = client.get("/admin/content-ops/monster-encounter", params={"run": "1", "family_ids": families})
    assert response.status_code == 200
    assert 'role="alert"' in response.text
    assert "ровно одну семью" in response.text
