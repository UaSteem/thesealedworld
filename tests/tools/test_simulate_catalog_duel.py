"""The diagnostic must preserve Studio builds and execute the real resolver."""

import asyncio
import random
from copy import deepcopy

import pytest
from tools.monsters.simulate_catalog_duel import build_actor, build_reference_inputs, run_batch


@pytest.mark.parametrize(
    "member_id",
    (
        "goblin_tribe.base.goblin_spearman",
        "wolf_pack.base.alpha_prime",
        "rat_swarm.base.rat_king",
        "bandit_gang.base.bandit_thug",
    ),
)
def test_simulation_builds_monster_without_inspection_calculation(monkeypatch, member_id):
    from src.backend.features.monsters.inspection.services.catalog_view_service import CatalogMonsterViewService
    from src.backend.features.monsters.inspection.services.equipment_stats_service import MonsterEquipmentStatsService

    studio = CatalogMonsterViewService().equipment(member_id=member_id, tier=3).stats_preview.technical

    def forbidden(*args, **kwargs):
        raise AssertionError("Simulation must obtain the monster from instances")

    monkeypatch.setattr(MonsterEquipmentStatsService, "preview", forbidden)
    inputs = build_reference_inputs(member_id, 3)
    assert inputs["monster"]["raw"] == studio["equipped_trace"]["raw"]
    assert inputs["monster"]["loadout"] == studio["equipped_trace"]["loadout"]
    assert inputs["monster"]["skills"] == studio["skills"]
    assert inputs["monster"]["preview_values"] == studio["equipped"]


def test_actor_uses_studio_raw_skills_and_loadout_without_mutating_inputs():
    inputs = build_reference_inputs("goblin_tribe.base.goblin_spearman", 5)
    before = deepcopy(inputs)
    for kind in ("player", "monster"):
        source = inputs[kind]
        actor = build_actor(source, actor_id=kind, team=kind, kind=kind)
        assert actor.skills == source["skills"]
        assert actor.loadout.layout == source["loadout"]["layout"]
        assert actor.loadout.known_abilities == source["loadout"].get("known_abilities", [])
        assert actor.meta.hp == round(source["preview_values"]["hp"])
        assert actor.stats.mods.main_hand_damage_base == source["preview_values"]["main_hand_damage_base"]
        if kind == "monster":
            assert actor.meta.role == "veteran"
    assert inputs == before
    assert len(inputs["player"]["equipment"]) == 16
    assert len(inputs["monster"]["equipment"]["items"]) == 4


def test_batch_real_resolver_is_seeded_bounded_and_restores_random_state():
    inputs = build_reference_inputs("goblin_tribe.base.goblin_spearman", 5)
    state = random.getstate()
    first, log = asyncio.run(run_batch(inputs, battles=2, seed=500, max_rounds=2))
    assert random.getstate() == state
    second, _ = asyncio.run(run_batch(inputs, battles=2, seed=500, max_rounds=2))
    assert first["fights"] == second["fights"]
    assert len(first["fights"]) == 2
    assert all(fight["rounds"] <= 2 for fight in first["fights"])
    assert first["fights"][0]["actor_ids"] != first["fights"][1]["actor_ids"]
    assert log["resolver_results"]
    assert log["telemetry"]["round_events"]
    assert log["telemetry"]["hit_count"] + log["telemetry"]["miss_count"] > 0
