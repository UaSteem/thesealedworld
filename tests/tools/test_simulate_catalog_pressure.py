"""Independent clones, real resolver, and team aggregation for pressure diagnostics."""

import asyncio
import random
from copy import deepcopy
from types import SimpleNamespace

from tools.monsters import simulate_catalog_pressure as pressure


def test_pressure_roster_has_independent_identical_monsters_and_alternates_player_order():
    inputs = pressure.build_reference_inputs("goblin_tribe.base.goblin_spearman", 5)
    before = deepcopy(inputs)
    actors, ids = pressure.build_roster(inputs, monsters=3, swapped=False)
    assert len({str(actor.meta.id) for actor in actors}) == 4
    assert min(str(actor.meta.id) for actor in actors) == ids["player"][0]
    assert all(actor.meta.team == "monster" for actor in actors[1:])
    assert actors[1].raw == actors[2].raw == actors[3].raw
    assert actors[1].skills == inputs["monster"]["skills"]
    actors[1].raw.attributes.clear()
    assert actors[2].raw.attributes
    assert inputs == before
    swapped, swapped_ids = pressure.build_roster(inputs, monsters=3, swapped=True)
    assert max(str(actor.meta.id) for actor in swapped) == swapped_ids["player"][0]


def test_pressure_real_resolver_is_deterministic_and_restores_random_state():
    inputs = pressure.build_reference_inputs("goblin_tribe.base.goblin_spearman", 5)
    state = random.getstate()
    first, sample = asyncio.run(pressure.run_pressure_batch(inputs, monsters=2, battles=2, seed=21, max_rounds=2))
    assert random.getstate() == state
    second, _ = asyncio.run(pressure.run_pressure_batch(inputs, monsters=2, battles=2, seed=21, max_rounds=2))
    assert first == second
    assert len(first["fights"]) == 2
    assert sum(first["wins"].values()) == 2
    assert sample["resolver_results"]
    assert all(fight["rounds"] <= 2 for fight in first["fights"])
    for fight in first["fights"]:
        assert len(fight["actor_ids"]["monster"]) == 2
        assert fight["remaining_hp"]["monster"] == sum(
            fight["remaining_hp_by_actor"][actor_id] for actor_id in fight["actor_ids"]["monster"]
        )


def test_pressure_death_facts_override_positive_corpse_hp_and_aggregate_clone_metrics(monkeypatch):
    class Simulator:
        async def run(self, state):
            actors = list(state.ctx.actors.values())
            actors[0].meta.hp = 2
            actors[0].meta.is_dead = True
            telemetry = state.telemetry
            telemetry.damage_by_actor = {str(actors[1].meta.id): 5, str(actors[2].meta.id): 7}
            telemetry.deaths = [str(actors[0].meta.id)]
            return SimpleNamespace(
                winner="monster",
                rounds_completed=1,
                completion_reason="victory",
                telemetry=telemetry,
                final_hp_by_actor={str(actor.meta.id): actor.meta.hp for actor in actors},
            )

    monkeypatch.setattr(pressure, "InMemoryCombatSimulator", Simulator)
    inputs = pressure.build_reference_inputs("goblin_tribe.base.goblin_spearman", 5)
    report, _ = asyncio.run(pressure.run_pressure_batch(inputs, monsters=2, battles=1, seed=1, max_rounds=1))
    assert report["wins"] == {"player": 0, "monster": 1, "draw": 0}
    assert report["mean_deaths"] == {"player": 1, "monster": 0}
    assert report["mean_remaining_hp"]["player"] == 2
    assert report["telemetry_totals"]["monster"]["damage"] == 12
