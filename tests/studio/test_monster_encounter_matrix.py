from __future__ import annotations

import asyncio
import math
from types import SimpleNamespace

from src.studio.features.cabinet.modules.content_ops.cabinet import _encounter_profile_matrix


def test_matrix_uses_builtin_same_order_and_cap_rounding_with_bounded_concurrency():
    calls = []
    active = 0
    peak = 0

    class Api:
        async def select_encounter(self, order):
            nonlocal active, peak
            calls.append(order)
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0)
            active -= 1
            config = SimpleNamespace(
                minions=SimpleNamespace(mode="relative_gs", reference_gs=66.664, base_points=30, gs_threshold=35, gs_step_size=5, gs_points_per_step=0, gs_bonus_max=10),
                seniors=SimpleNamespace(mode="fixed", gs_threshold=40, gs_step_size=10, gs_points_per_step=10, gs_bonus_max=25),
            )
            return SimpleNamespace(preparation=SimpleNamespace(configurations=[config], profile=None))

    rows = asyncio.run(_encounter_profile_matrix(Api(), family_id="rat_swarm", location_tier=2, seed=13, reference_gs=66.664))
    assert len(rows) == 12
    assert len(calls) == 24
    assert peak <= 4
    assert all(order["family_ids"] == ["rat_swarm"] for order in calls)
    assert all(order["location_tier"] == 2 and order["seed"] == 13 for order in calls)
    assert all(order["party_mode"] == "solo" and "profile_override" not in order for order in calls)
    assert all("player_gear_score" in order for order in calls)
    assert {order["player_gear_score"] for order in calls if "player_gear_score" in order} == {66.664, math.nextafter(66.664 * 40 / 30, math.inf)}
    assert {(row["encounter_type"], row["difficulty"]) for row in rows} == {
        (kind, difficulty)
        for kind in ("ordinary", "patrol", "guard", "leader")
        for difficulty in ("easy", "normal", "hard")
    }


def test_matrix_keeps_refusals_and_reads_profile_when_no_configuration():
    class Api:
        async def select_encounter(self, order):
            return SimpleNamespace(
                status="rejected",
                reasons=[SimpleNamespace(message="Слишком дорогая семья")],
                preparation=SimpleNamespace(
                    configurations=[],
                    profile={
                        "minions": {
                            "mode": "relative_gs", "reference_gs": 36.326, "base_points": 30,
                            "gs_threshold": 35,
                            "gs_step_size": 5,
                            "gs_points_per_step": 5,
                            "gs_bonus_max": 15,
                        },
                        "seniors": {"mode": "fixed", "gs_threshold": 35, "gs_step_size": 5, "gs_points_per_step": 0, "gs_bonus_max": 0}
                    },
                ),
            )

    rows = asyncio.run(_encounter_profile_matrix(Api(), family_id="golem_foundry", location_tier=0, seed=13, reference_gs=36.326))
    assert all(row["base"].status == "rejected" and row["cap"].status == "rejected" for row in rows)
    assert all(row["cap_gs"] >= 54.489 for row in rows)
    assert all("error" not in row for row in rows)


def test_matrix_page_renders_both_rosters_and_refusals(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from fastapi_cabinet import include_cabinet
    from src.studio.features.cabinet.modules.content_ops import cabinet

    class Api:
        async def get_encounter_contract(self):
            return SimpleNamespace(
                version=6,
                reference_player_gs_by_tier={0: 36.326}, provisional_reference_tiers=[6, 7],
                profile_override_example={},
                families=[SimpleNamespace(id="goblin_tribe", name="Гоблины")],
                location_tiers=[0],
                encounter_types=[
                    SimpleNamespace(id=kind, name=kind) for kind in ("ordinary", "patrol", "guard", "leader")
                ],
                difficulties=[SimpleNamespace(id=value, name=value) for value in ("easy", "normal", "hard")],
                party_modes=[SimpleNamespace(id="solo", name="Соло", available=True)],
            )

        async def select_encounter(self, order):
            pool = SimpleNamespace(mode="fixed", base_points=45, bonus_points=0, effective_points=45,
                                   spent_points=15, remaining_points=30, gs_threshold=35, gs_step_size=5,
                                   gs_steps=0, gs_points_per_step=5, gs_bonus_max=15, gs_cap_reached=False)
            config = SimpleNamespace(minions=pool, seniors=pool)
            member = SimpleNamespace(name="Лазутчик", role="minion", tier=0)
            return SimpleNamespace(
                preparation=SimpleNamespace(configurations=[config], profile=None, reasons=[]),
                selection=None if order["encounter_type"] == "leader" else SimpleNamespace(members=[member]),
                reasons=[SimpleNamespace(message="Не хватает очков на ядро")],
                minions=pool, seniors=pool,
                budget_base=45,
                budget_effective=60 if "player_gear_score" in order else 45,
                budget_spent=15,
            )

    monkeypatch.setattr(cabinet, "_api", lambda request: Api())
    app = FastAPI()
    include_cabinet(app, modules=("src.studio.features.cabinet.modules.content_ops.cabinet",), mount_path="/admin")
    with TestClient(app) as client:
        response = client.get(
            "/admin/content-ops/monster-encounter",
            params={
                "compare_profiles": "1",
                "family_ids": "goblin_tribe",
                "location_tier": "0",
                "seed": "13",
            },
        )
    assert response.status_code == 200
    assert "Все соло-профили: эталон и потолок бонуса" in response.text
    assert "Лазутчик" in response.text
    assert "Не хватает очков на ядро" in response.text
    assert "Внешний тестовый профиль здесь не применяется" in response.text
    assert "Миньоны" in response.text
    assert "Старшие" in response.text
    assert "Потолок обоих пулов" in response.text
