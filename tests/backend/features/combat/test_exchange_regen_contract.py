"""AG-02: passive regeneration belongs to exchange finalization."""

from __future__ import annotations

import pytest

from src.backend.features.combat.dto import ActiveEffectDTO, CombatActionDTO
from src.backend.features.combat.runtime.engine.mechanics_service import MechanicsService
from src.backend.features.combat.runtime.engine.resolver import CombatResolver
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine
from src.backend.features.combat.runtime.processors.executor import CombatExecutor
from src.backend.features.combat.runtime.support.analytics_builder import CombatAnalyticsFactBuilder
from src.backend.features.combat.runtime.support.dto import CombatResultSupportTaskDTO
from tests.backend.features.combat.test_exchange_execution_contract import actor, battle, move


def regenerating(actor_id, team, **kwargs):
    snapshot = actor(actor_id, team, **kwargs)
    snapshot.meta.hp = 500
    snapshot.meta.stamina = 40
    snapshot.raw.modifiers.update(
        {
            "hp_regen": {"base": 7.0, "source": {}, "temp": {}},
            "stamina_regen": {"base": 3.0, "source": {}, "temp": {}},
        }
    )
    return snapshot


def regen_results(ctx):
    return [
        task["result"]
        for task in ctx.pending_result_support_tasks
        if task["result"]["action_facts"].get("phase") == "exchange_finalize"
    ]


@pytest.fixture
def deterministic(monkeypatch):
    resolve = CombatResolver.resolve_exchange

    def hit(source, target, ctx):
        ctx.flags.force.hit = True
        ctx.stages.check_evasion = False
        ctx.stages.check_parry = False
        ctx.stages.check_block = False
        ctx.stages.check_crit = False
        return resolve(source, target, ctx)

    monkeypatch.setattr(CombatResolver, "resolve_exchange", staticmethod(hit))


@pytest.mark.unit
async def test_forced_defender_without_intent_regenerates_and_fact_only_result_is_logged(deterministic):
    source, target = regenerating("1", "a"), regenerating("2", "b")
    ctx = battle(source, target)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "2"), is_forced=True)
    )
    (final,) = regen_results(ctx)
    assert final["events"] == []
    assert [(f["actor_id"], f["owner"], f["resource"], f["delta"]) for f in final["resource_facts"]] == [
        ("1", "source", "hp", 7),
        ("1", "source", "stamina", 3),
        ("2", "target", "hp", 7),
        ("2", "target", "stamina", 3),
    ]
    assert all(f["reason"] == "combat_regen" for f in final["resource_facts"])
    assert source.meta.hp == 507
    assert source.meta.stamina == target.meta.stamina == 43
    (entry,) = [e for e in ctx.pending_logs if e["kind"] == "combat_regen"]
    assert {r["resource"] for r in entry["resources"]} == {"hp", "stamina"}
    assert {r["actor_id"] for r in entry["resources"]} == {"1", "2"}
    assert entry["global_turn"] == 1
    assert {task["global_turn"] for task in ctx.pending_result_support_tasks} == {1}
    assert source.meta.exchange_counter == target.meta.exchange_counter == 1
    payload = CombatResultSupportTaskDTO.model_validate(ctx.pending_result_support_tasks[-1])
    analytics = CombatAnalyticsFactBuilder.build_result_fact_from_support_payload(payload)
    assert {(f[0], f[2], f[3], f[4]) for f in analytics["rf"]} == {
        ("1", "hp", "combat_regen", 7),
        ("1", "stamina", "combat_regen", 3),
        ("2", "hp", "combat_regen", 7),
        ("2", "stamina", "combat_regen", 3),
    }


@pytest.mark.unit
async def test_primary_offhand_counter_and_secondary_regenerate_only_main_pair_once(monkeypatch, deterministic):
    source, target, extra = regenerating("1", "a", dual=True), regenerating("2", "b", dual=True), regenerating("3", "b")
    resolve = CombatResolver.resolve_exchange

    def counter(source_stats, target_stats, pipeline_ctx):
        resolve(source_stats, target_stats, pipeline_ctx)
        if (
            pipeline_ctx.result.source_id == "1"
            and pipeline_ctx.result.action_facts["execution"]["origin"] == "primary"
        ):
            pipeline_ctx.result.chain_events.trigger_counter_attack = True

    monkeypatch.setattr(CombatResolver, "resolve_exchange", staticmethod(counter))
    ctx = battle(source, target, extra)
    executor = CombatExecutor()
    commits = []
    commit = executor.pipeline.mechanics_service.apply_exchange_results

    def capture(*args, **kwargs):
        commit(*args, **kwargs)
        commits.append((source.meta.hp, target.meta.hp, source.meta.stamina, target.meta.stamina))

    monkeypatch.setattr(executor.pipeline.mechanics_service, "apply_exchange_results", capture)
    await executor._handle_exchange(
        ctx,
        CombatActionDTO(action_type="exchange", move=move("1", "2", "sword_cross_arc"), partner_move=move("2", "1")),
    )
    strikes = [
        task["result"] for task in ctx.pending_result_support_tasks if "execution" in task["result"]["action_facts"]
    ]
    assert {r["action_facts"]["execution"]["origin"] for r in strikes} == {"primary", "offhand", "counter", "secondary"}
    assert all("combat_regen" not in changes for r in strikes for changes in r["resource_changes"].values())
    (final,) = regen_results(ctx)
    assert len(final["resource_facts"]) == 4
    assert (source.meta.hp, target.meta.hp, source.meta.stamina, target.meta.stamina) == tuple(
        value + delta for value, delta in zip(commits[-1], (7, 7, 3, 3), strict=True)
    )
    assert extra.meta.stamina == 40
    assert extra.meta.exchange_counter == 0
    assert not any(f["actor_id"] == "3" for f in final["resource_facts"])


@pytest.mark.unit
@pytest.mark.parametrize("death_wave", ["primary", "offhand"])
async def test_death_before_finalize_never_regenerates(monkeypatch, deterministic, death_wave):
    source, target = regenerating("1", "a", dual=True), regenerating("2", "b")
    source.meta.hp = 1 if death_wave == "primary" else 500
    resolve = CombatResolver.resolve_exchange

    def lethal(source_stats, target_stats, pipeline_ctx):
        resolve(source_stats, target_stats, pipeline_ctx)
        r = pipeline_ctx.result
        if death_wave == "primary" and r.source_id == "2":
            r.damage_final = 5000
        elif death_wave == "offhand" and r.hand == "off_hand":
            r.reflected_damage = 5000

    monkeypatch.setattr(CombatResolver, "resolve_exchange", staticmethod(lethal))
    ctx = battle(source, target)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "2"), partner_move=move("2", "1"))
    )
    strikes = [
        task["result"] for task in ctx.pending_result_support_tasks if "execution" in task["result"]["action_facts"]
    ]
    if death_wave == "offhand":
        assert any(r["hand"] == "off_hand" and r["reflected_damage"] == 5000 for r in strikes)
    assert not source.is_alive
    assert source.meta.hp == 0
    assert all(f["actor_id"] != "1" for r in regen_results(ctx) for f in r["resource_facts"])


@pytest.mark.unit
async def test_unidirectional_does_not_regenerate(deterministic):
    source, target = regenerating("1", "a"), regenerating("2", "b")
    ctx = battle(source, target)
    await CombatExecutor()._handle_unidirectional(ctx, CombatActionDTO(action_type="instant", move=move("1", "2")))
    assert source.meta.hp == 500
    assert source.meta.stamina == target.meta.stamina == 40
    assert not regen_results(ctx)
    assert not any(
        f["reason"] == "combat_regen" for t in ctx.pending_result_support_tasks for f in t["result"]["resource_facts"]
    )


@pytest.mark.unit
async def test_expiring_active_modifier_is_used_before_cleanup(deterministic):
    source, target = regenerating("1", "a"), regenerating("2", "b")
    source.raw.modifiers["hp_regen"]["temp"]["regen-buff"] = "+5"
    source.statuses.effects.append(
        ActiveEffectDTO(
            uid="regen-buff",
            effect_id="test-regen",
            source_id="1",
            expire_at_exchange=1,
            modified_keys=["hp_regen"],
            modified_sources={"hp_regen": ["regen-buff"]},
        )
    )
    ctx = battle(source, target)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "2"), is_forced=True)
    )
    (final,) = regen_results(ctx)
    assert next(f["delta"] for f in final["resource_facts"] if f["actor_id"] == "1" and f["resource"] == "hp") == 12
    assert source.raw.modifiers["hp_regen"]["temp"] == {}
    assert source.statuses.effects == []


@pytest.mark.unit
def test_regen_refreshes_dirty_stats_and_records_actual_clamped_deltas():
    source, target = regenerating("1", "a"), regenerating("2", "b")
    StatsEngine.ensure_stats(source)
    source.raw.modifiers["hp_regen"]["base"] = 12
    source.dirty_stats.add("hp_regen")
    source.meta.hp = 999
    source.meta.stamina = 99
    target.meta.is_dead = True
    result = MechanicsService().apply_exchange_regen(source, target)
    assert source.stats.mods.hp_regen == 12
    assert source.dirty_stats == set()
    assert [(f.resource, f.before, f.after, f.max, f.delta) for f in result.resource_facts] == [
        ("hp", 999, 1000, 1000, 1),
        ("stamina", 99, 100, 100, 1),
    ]


@pytest.mark.unit
@pytest.mark.parametrize("hp_regen,stamina_regen", [(0, 0), (-5, -3), (0.1, 0.9)])
def test_regen_uses_existing_rounding_and_positive_deltas_only(hp_regen, stamina_regen):
    source, target = regenerating("1", "a"), regenerating("2", "b")
    source.raw.modifiers["hp_regen"]["base"] = hp_regen
    source.raw.modifiers["stamina_regen"]["base"] = stamina_regen
    target.meta.is_dead = True
    result = MechanicsService().apply_exchange_regen(source, target)
    assert [f.delta for f in result.resource_facts] == ([1, 1] if hp_regen > 0 else [])
