"""Observable contracts for intent ownership and strike-local execution."""

from __future__ import annotations

import pytest

from src.backend.features.combat.dto import (
    ActiveEffectDTO,
    ActorLoadoutDTO,
    ActorMetaDTO,
    ActorRawDTO,
    ActorSnapshot,
    BattleContext,
    BattleMeta,
    CombatActionDTO,
    CombatMoveDTO,
    ExchangePayload,
)
from src.backend.features.combat.integrations import CombatCatalogIntegrator
from src.backend.features.combat.runtime.engine.execution import StrikeExecution
from src.backend.features.combat.runtime.engine.pipeline import CombatPipeline
from src.backend.features.combat.runtime.engine.resolver import CombatResolver
from src.backend.features.combat.runtime.processors.executor import CombatExecutor


def actor(actor_id: str, team: str, *, dual: bool = False) -> ActorSnapshot:
    layout = {"main_hand": "skill_swords"}
    if dual:
        layout.update(off_hand="skill_swords", tactical_style="skill_dual_wield")
    return ActorSnapshot(
        meta=ActorMetaDTO(
            id=actor_id,
            name=actor_id,
            type="player" if team == "a" else "monster",
            team=team,
            hp=1000,
            max_hp=1000,
            stamina=100,
            max_stamina=100,
        ),
        raw=ActorRawDTO(
            modifiers={
                key: {"base": value, "source": {}, "temp": {}}
                for key, value in {
                    "main_hand_damage_base": 3.0,
                    "off_hand_damage_base": 2.0,
                    "main_hand_accuracy": 1.0,
                    "off_hand_accuracy": 1.0,
                }.items()
            }
        ),
        loadout=ActorLoadoutDTO(layout=layout),
    )


def move(owner: str, target: str, feint: str | None = None) -> CombatMoveDTO:
    return CombatMoveDTO(
        move_id=f"move-{owner}",
        char_id=owner,
        strategy="exchange",
        payload=ExchangePayload(target_id=target, feint_id=feint),
    )


def battle(*actors: ActorSnapshot) -> BattleContext:
    return BattleContext(
        session_id="execution-contract",
        actors={a.char_id: a for a in actors},
        meta=BattleMeta(
            active=1,
            step_counter=0,
            active_actors_count=len(actors),
            teams={team: [a.char_id for a in actors if a.meta.team == team] for team in ("a", "b")},
            actors_info={a.char_id: a.meta.type for a in actors},
            battle_type="arena",
            location_id="arena",
        ),
    )


@pytest.fixture
def deterministic_resolver(monkeypatch):
    """Keep real resolver/effects; choose only the random outcome flags."""
    resolve = CombatResolver.resolve_exchange

    def resolve_hit(source, target, ctx):
        ctx.flags.force.hit = True
        ctx.stages.check_evasion = False
        ctx.stages.check_parry = False
        ctx.stages.check_block = False
        ctx.stages.check_crit = False
        return resolve(source, target, ctx)

    monkeypatch.setattr(CombatResolver, "resolve_exchange", staticmethod(resolve_hit))


@pytest.mark.unit
@pytest.mark.parametrize(
    ("feint", "effect", "cost"),
    [
        ("second_breath", "prep_second_breath", 15),
        ("foresight_parry", "prep_foresight_parry", 9),
        ("wind_dance", "prep_counter_cap_on_dodge", 15),
        ("broken_step", "prep_dual_broken_step", 9),
    ],
)
async def test_partner_offhand_never_activates_players_self_preparation(deterministic_resolver, feint, effect, cost):
    player, monster = actor("1", "a", dual=True), actor("monster", "b", dual=True)
    ctx = battle(player, monster)
    await CombatExecutor()._handle_exchange(
        ctx,
        CombatActionDTO(action_type="exchange", move=move("1", "monster", feint), partner_move=move("monster", "1")),
    )
    results = [task["result"] for task in ctx.pending_result_support_tasks]
    casts = [(r["source_id"], e["action_id"]) for r in results for e in r["events"] if e["type"] == "CAST"]
    assert casts == [("1", feint)]
    assert [e.effect_id for e in player.statuses.effects] == [effect]
    assert monster.statuses.effects == []
    assert sum(int(r["resource_changes"].get("stamina", {}).get("cost", "0")) for r in results) == -cost
    assert set(player.meta.feints.cooldowns) == {feint}
    assert monster.meta.feints.cooldowns == {}
    assert (ctx.meta.step_counter, player.meta.exchange_counter, monster.meta.exchange_counter) == (1, 1, 1)
    assert {task["global_turn"] for task in ctx.pending_result_support_tasks} == {1}
    assert [r["action_facts"]["execution"]["origin"] for r in results] == ["primary", "primary", "offhand", "offhand"]
    assert [r["feint_activation"]["state"] for r in results if r["feint_activation"]] == ["activated"]
    assert {entry["global_turn"] for entry in ctx.pending_logs} == {1}
    strike_logs = [entry for entry in ctx.pending_logs if "execution" in entry]
    assert {entry["wave"] for entry in strike_logs} == {1, 2}
    primary_ids = {r["action_facts"]["execution"]["strike_id"] for r in results[:2]}
    for entry in strike_logs:
        if entry["execution"]["origin"] == "offhand":
            assert entry["execution"]["parent_id"] in primary_ids
            assert ".off_hand." in entry["template"]["key"]


@pytest.mark.unit
async def test_pipeline_rejects_foreign_intent_before_effects_or_cost():
    player, monster = actor("1", "a"), actor("monster", "b")
    with pytest.raises(ValueError, match="owner"):
        await CombatPipeline().calculate(monster, player, move("1", "monster", "second_breath"))
    assert monster.statuses.effects == []
    assert monster.meta.stamina == 100


@pytest.mark.unit
@pytest.mark.parametrize(("forced", "swapped"), [(False, False), (False, True), (True, False)])
async def test_real_prepared_counter_uses_reactor_ownership_without_feint_activation(monkeypatch, forced, swapped):
    player, monster = actor("1", "a"), actor("monster", "b")
    monster.statuses.effects.append(
        ActiveEffectDTO(
            uid="own-riposte",
            effect_id="prep_perfect_riposte",
            source_id="monster",
            expire_at_exchange=99,
            params={"heal_max_hp_ratio": 0.12, "heal_min": 6},
        )
    )
    monster.meta.hp = 700
    resolve = CombatResolver.resolve_exchange

    def resolve_parry(source, target, ctx):
        ctx.flags.force.hit = True
        ctx.stages.check_evasion = False
        ctx.stages.check_block = False
        ctx.stages.check_crit = False
        if ctx.result.target_id == "monster" and not ctx.result.is_counter:
            ctx.flags.force.parry = True
        else:
            ctx.stages.check_parry = False
        return resolve(source, target, ctx)

    monkeypatch.setattr(CombatResolver, "resolve_exchange", staticmethod(resolve_parry))
    ctx = battle(player, monster)
    player_move, monster_move = move("1", "monster", "second_breath"), move("monster", "1")
    await CombatExecutor()._handle_exchange(
        ctx,
        CombatActionDTO(
            action_type="exchange",
            move=monster_move if swapped else player_move,
            partner_move=player_move if swapped else (None if forced else monster_move),
            is_forced=forced,
        ),
    )
    results = [task["result"] for task in ctx.pending_result_support_tasks]
    assert [(r["source_id"], e["action_id"]) for r in results for e in r["events"] if e["type"] == "CAST"] == [
        ("1", "second_breath")
    ]
    counter = [r for r in results if r["action_facts"]["execution"]["origin"] == "counter"]
    assert len(counter) == 1
    assert (counter[0]["source_id"], counter[0]["target_id"]) == ("monster", "1")
    assert counter[0]["action_facts"]["execution"]["owner_id"] == "monster"
    assert monster.meta.hp == 820
    assert monster.statuses.effects == []
    assert (ctx.meta.step_counter, player.meta.exchange_counter, monster.meta.exchange_counter) == (1, 1, 1)


@pytest.mark.unit
async def test_aoe_projects_hit_effects_for_both_owners_without_reactivation(monkeypatch, deterministic_resolver):
    # Exercise real catalog mechanics with a compound prep + hit feint, without
    # changing the production catalog or replacing the pipeline/effect service.
    get_entry = CombatCatalogIntegrator.get_feint_catalog_entry
    entry = get_entry("sword_cross_arc").model_copy(deep=True)
    entry.technical.preparation_effects = [{"id": "prep_second_breath", "target_actor": "source"}]
    entry.technical.effects = [{"id": "dot_bleed", "target_actor": "target"}]
    monkeypatch.setattr(
        CombatCatalogIntegrator,
        "get_feint_catalog_entry",
        staticmethod(lambda key: entry if key == "sword_cross_arc" else get_entry(key)),
    )
    from src.backend.features.combat.runtime.engine.math_core import MathCore

    monkeypatch.setattr(MathCore, "roll_chance", staticmethod(lambda chance: (0.0, chance > 0)))
    player, ally, monster, other = actor("1", "a"), actor("ally", "a"), actor("monster", "b"), actor("other", "b")
    ctx = battle(player, ally, monster, other)
    await CombatExecutor()._handle_exchange(
        ctx,
        CombatActionDTO(
            action_type="exchange",
            move=move("1", "monster", "sword_cross_arc"),
            partner_move=move("monster", "1", "sword_cross_arc"),
        ),
    )
    results = [task["result"] for task in ctx.pending_result_support_tasks]
    assert [(r["source_id"], r["target_id"]) for r in results] == [
        ("1", "monster"),
        ("monster", "1"),
        ("1", "other"),
        ("monster", "ally"),
    ]
    assert sum(e["type"] == "CAST" for r in results for e in r["events"]) == 2
    for owner in (player, monster):
        assert sum(e.effect_id == "prep_second_breath" for e in owner.statuses.effects) == 1
        assert set(owner.meta.feints.cooldowns) == {"sword_cross_arc"}
    for target in (ally, other):
        assert [e.effect_id for e in target.statuses.effects] == ["dot_bleed"]
    for task in ctx.pending_result_support_tasks:
        result = task["result"]
        assert task["action"]["move"]["payload"]["target_id"] == result["target_id"]
        if result["action_facts"]["execution"]["origin"] == "secondary":
            assert result["feint_activation"] is None
            assert "cost" not in result["resource_changes"].get("stamina", {})
            assert all(app["effect_id"] != "prep_second_breath" for app in result["status_applications"])
    assert (ctx.meta.step_counter, player.meta.exchange_counter, monster.meta.exchange_counter) == (1, 1, 1)
    assert (ally.meta.exchange_counter, other.meta.exchange_counter) == (0, 0)


@pytest.mark.unit
@pytest.mark.parametrize("block", ["resource", "forbidden"])
async def test_rejected_activation_never_grants_free_aoe_projection(deterministic_resolver, block):
    player, monster, other = actor("1", "a"), actor("monster", "b"), actor("other", "b")
    if block == "resource":
        player.meta.stamina = 0
    else:
        player.statuses.effects.append(
            ActiveEffectDTO(
                uid="no-feints",
                effect_id="concussed_no_feints",
                source_id="monster",
                expire_at_exchange=99,
                control=CombatCatalogIntegrator.get_effect_catalog_entry("concussed_no_feints").technical.control_logic,
            )
        )
    ctx = battle(player, monster, other)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster", "sword_cross_arc"), is_forced=True)
    )
    results = [task["result"] for task in ctx.pending_result_support_tasks]
    assert len(results) == 1
    assert results[0]["feint_activation"]["state"] == "rejected"
    assert not any(event["type"] == "CAST" for event in results[0]["events"])
    assert player.meta.feints.cooldowns == {}
    assert other.meta.hp == 1000


@pytest.mark.unit
async def test_typed_boundary_revalidates_mutated_intent_owner():
    player, monster = actor("1", "a"), actor("monster", "b")
    selected = move("1", "monster", "second_breath")
    strike = StrikeExecution.primary(selected, monster.char_id)
    selected.char_id = "monster"
    with pytest.raises(ValueError, match="owner"):
        await CombatPipeline().calculate(player, monster, strike)


@pytest.mark.unit
@pytest.mark.parametrize("origin", ["primary", "offhand", "counter"])
async def test_typed_origin_overrides_contradictory_branch_modifiers(deterministic_resolver, origin):
    player, monster = actor("1", "a"), actor("monster", "b")
    primary = StrikeExecution.primary(move("1", "monster", "second_breath"), monster.char_id)
    strike = (
        primary if origin == "primary" else primary.child(origin, owner_id=player.char_id, target_id=monster.char_id)
    )
    result = await CombatPipeline().calculate(
        player,
        monster,
        strike,
        external_mods={
            "hand": "off",
            "source_type": "off_hand",
            "is_counter_attack": True,
            "feint_role": "secondary",
            "pay_cost": False,
            "generate_feints": False,
        },
    )
    assert result.hand == ("off_hand" if origin == "offhand" else "main_hand")
    assert result.is_counter is (origin == "counter")
    assert bool(result.feint_activation) is (origin == "primary")
    if origin == "primary":
        assert result.resource_changes["stamina"]["cost"] == "-15"
