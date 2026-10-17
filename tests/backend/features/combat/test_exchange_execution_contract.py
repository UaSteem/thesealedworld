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
    InteractionResultDTO,
    PipelineContextDTO,
)
from src.backend.features.combat.integrations import CombatCatalogIntegrator
from src.backend.features.combat.runtime.engine.execution import StrikeExecution
from src.backend.features.combat.runtime.engine.mechanics_service import MechanicsService
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


def assert_exchange_gift(results, *owners):
    """Check actor state, award accounting and facts after the real commit."""
    for owner in owners:
        assert owner.meta.tokens.get("gift", 0) == 1
    for result in results:
        expected = int(
            result["action_facts"]["execution"]["origin"] == "primary"
            and result["skip_reason"] is None
            and not result["is_counter"]
        )
        assert result["tokens_awarded_attacker"].get("gift", 0) == expected
        facts = [fact for fact in result["token_facts"] if fact["token"] == "gift"]
        assert len(facts) == expected
        if facts:
            assert (facts[0]["amount"], facts[0]["reason"], facts[0]["tags"]) == (1, "exchange", ["exchange"])


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
    results = [
        task["result"] for task in ctx.pending_result_support_tasks if "execution" in task["result"]["action_facts"]
    ]
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
    assert_exchange_gift(results, player, monster)
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
    results = [
        task["result"] for task in ctx.pending_result_support_tasks if "execution" in task["result"]["action_facts"]
    ]
    assert [(r["source_id"], e["action_id"]) for r in results for e in r["events"] if e["type"] == "CAST"] == [
        ("1", "second_breath")
    ]
    counter = [r for r in results if r["action_facts"]["execution"]["origin"] == "counter"]
    assert len(counter) == 1
    assert (counter[0]["source_id"], counter[0]["target_id"]) == ("monster", "1")
    assert counter[0]["action_facts"]["execution"]["owner_id"] == "monster"
    # The existing resolver also marks the parried primary is_counter when it
    # triggers a reaction. AG-01 must preserve the explicit is_counter guard.
    assert results[0 if not swapped else 1]["is_counter"] is True
    assert player.meta.tokens.get("gift", 0) == 0
    assert_exchange_gift(results, *([] if forced else [monster]))
    if forced:
        assert monster.meta.tokens.get("gift", 0) == 0
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
    results = [
        task["result"] for task in ctx.pending_result_support_tasks if "execution" in task["result"]["action_facts"]
    ]
    assert [(r["source_id"], r["target_id"]) for r in results] == [
        ("1", "monster"),
        ("monster", "1"),
        ("1", "other"),
        ("monster", "ally"),
    ]
    assert sum(e["type"] == "CAST" for r in results for e in r["events"]) == 2
    assert_exchange_gift(results, player, monster)
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
    results = [
        task["result"] for task in ctx.pending_result_support_tasks if "execution" in task["result"]["action_facts"]
    ]
    assert len(results) == 1
    assert results[0]["feint_activation"]["state"] == "rejected"
    if block == "forbidden":
        assert results[0]["skip_reason"] is None
        assert results[0]["is_hit"]
        assert_exchange_gift(results, player)
    else:
        assert results[0]["skip_reason"] == "NO_RESOURCE"
        assert player.meta.tokens.get("gift", 0) == 0
        assert results[0]["tokens_awarded_attacker"].get("gift", 0) == 0
        assert not any(f["token"] == "gift" for f in results[0]["token_facts"])
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
async def test_controlled_primary_grants_no_exchange_gift(deterministic_resolver):
    player, monster = actor("1", "a"), actor("monster", "b")
    player.statuses.effects.append(
        ActiveEffectDTO(
            uid="controlled",
            effect_id="stun",
            source_id="monster",
            expire_at_exchange=99,
            control=CombatCatalogIntegrator.get_effect_catalog_entry("stun").technical.control_logic,
        )
    )
    ctx = battle(player, monster)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster"), is_forced=True)
    )
    results = [
        task["result"] for task in ctx.pending_result_support_tasks if "execution" in task["result"]["action_facts"]
    ]
    assert len(results) == 1
    assert results[0]["skip_reason"] == "CONTROLLED"
    assert player.meta.tokens.get("gift", 0) == 0
    assert results[0]["tokens_awarded_attacker"].get("gift", 0) == 0
    assert not any(f["token"] == "gift" for f in results[0]["token_facts"])


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


@pytest.mark.unit
@pytest.mark.parametrize(
    ("context_overrides", "result_overrides", "expected"),
    [
        ({}, {}, 1),
        ({}, {"hand": "off_hand"}, 0),
        ({}, {"hand": "main"}, 0),
        ({"source_type": "off_hand"}, {}, 0),
        ({}, {"action_facts": {"execution": {"origin": "offhand"}}}, 0),
        ({}, {"action_facts": {"execution": {"origin": "secondary"}}}, 0),
        ({}, {"action_facts": {"execution": {"origin": "counter"}}}, 0),
        ({}, {"is_counter": True}, 0),
        *[({}, {"skip_reason": reason}, 0) for reason in ("CONTROLLED", "NO_RESOURCE", "DEAD", "COOLDOWN", "")],
        ({}, {"action_facts": {}}, 0),
        *[({}, {"action_facts": {"execution": value}}, 0) for value in (None, "primary", [], {})],
        *[({}, {"action_facts": {"execution": {"origin": value}}}, 0) for value in (None, "", "PRIMARY", 1)],
        ({}, {"is_miss": True}, 1),
        ({}, {"is_blocked": True}, 1),
        ({}, {"is_parried": True}, 1),
        ({"grant_exchange_gift": False}, {}, 0),
        ({"action_mode": "unidirectional"}, {}, 0),
    ],
)
def test_exchange_gift_requires_completed_primary_main_hand(context_overrides, result_overrides, expected):
    source, target = actor("1", "a"), actor("monster", "b")
    source.meta.tokens["gift"] = 4
    ctx = PipelineContextDTO()
    ctx.flags.meta.grant_exchange_gift = True
    ctx.flags.meta.action_mode = "exchange"
    ctx.flags.meta.source_type = "main_hand"
    for key, value in context_overrides.items():
        setattr(ctx.flags.meta, key, value)
    values = {
        "source_id": source.char_id,
        "target_id": target.char_id,
        "hand": "main_hand",
        "action_facts": {"execution": {"origin": "primary"}},
    }
    values.update(result_overrides)
    result = InteractionResultDTO(**values)

    MechanicsService().apply_interaction_result(ctx, source, target, result)

    assert source.meta.tokens["gift"] == 4 + expected
    assert result.tokens_awarded_attacker.get("gift", 0) == expected
    facts = [fact for fact in result.token_facts if fact.token == "gift"]
    assert len(facts) == expected
    if facts:
        assert (facts[0].before, facts[0].after, facts[0].amount) == (4, 5, 1)
        assert (facts[0].reason, facts[0].tags) == ("exchange", ["exchange"])


@pytest.mark.unit
@pytest.mark.parametrize("case", ["dispel", "refresh", "force_close", "duration"])
async def test_ag03_persistent_changes_survive_executor_copies(monkeypatch, deterministic_resolver, case):
    from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine
    from src.backend.features.game_catalog.combat.resources.common.modifier_applications import ModifierApplicationDTO

    get_entry = CombatCatalogIntegrator.get_feint_catalog_entry
    entry = get_entry("second_breath").model_copy(deep=True)
    entry.technical.preparation_effects = []
    entry.technical.effects = []
    player, enemy = actor("1", "a"), actor("monster", "b")
    if case in {"dispel", "refresh"}:
        enemy.statuses.effects.append(
            ActiveEffectDTO(
                uid="old-prep",
                effect_id="prep_second_breath",
                source_id="monster",
                expire_at_exchange=2,
                modified_sources={"parry": ["old-source"]},
            )
        )
        enemy.raw.modifiers["parry"] = {"base": 0, "source": {}, "temp": {"old-source": "+0.2"}}
        entry.technical.preparation_effects = [
            {"id": "dispel_preparations" if case == "dispel" else "prep_second_breath", "target_actor": "target"}
        ]
    elif case == "force_close":
        enemy.loadout.layout["tactical_style"] = "skill_ranged_combat"
        entry.technical.preparation_effects = [{"id": "force_ranged_close", "target_actor": "target"}]
    else:
        entry.technical.modifier_applications = [
            ModifierApplicationDTO(
                modifier_id="physical_damage_bonus_add",
                target_actor="self",
                scope="duration",
                duration_exchanges=3,
                value_override=17,
            )
        ]
    monkeypatch.setattr(
        CombatCatalogIntegrator,
        "get_feint_catalog_entry",
        staticmethod(lambda key: entry if key == "second_breath" else get_entry(key)),
    )
    ctx = battle(player, enemy)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster", "second_breath"), is_forced=True)
    )
    if case == "dispel":
        assert not enemy.statuses.effects
        assert enemy.raw.modifiers["parry"]["temp"] == {}
    elif case == "refresh":
        assert enemy.statuses.effects[0].uid == "old-prep"
        assert enemy.statuses.effects[0].expire_at_exchange > 2
        assert enemy.raw.modifiers["parry"]["temp"] == {"old-source": "+0.2"}
    elif case == "force_close":
        assert enemy.statuses.effects[0].params["position"] == "close"
    else:
        StatsEngine.ensure_stats(player)
        assert player.stats.mods.physical_damage_bonus == 17
        assert player.statuses.effects[0].modified_sources


@pytest.mark.unit
@pytest.mark.parametrize("same_result_dispel", [False, True])
async def test_ag03_loop_counter_preparation_reaches_next_executor_wave(monkeypatch, same_result_dispel):
    player, enemy = actor("1", "a"), actor("monster", "b")
    enemy.statuses.effects.append(
        ActiveEffectDTO(
            uid="loop-parry", effect_id="prep_dual_blade_loop_parry", source_id="monster", expire_at_exchange=99
        )
    )
    if same_result_dispel:
        get_entry = CombatCatalogIntegrator.get_feint_catalog_entry
        entry = get_entry("second_breath").model_copy(deep=True)
        entry.technical.preparation_effects = [{"id": "dispel_preparations", "target_actor": "target"}]
        monkeypatch.setattr(
            CombatCatalogIntegrator,
            "get_feint_catalog_entry",
            staticmethod(lambda key: entry if key == "second_breath" else get_entry(key)),
        )
    resolve = CombatResolver.resolve_exchange
    seen = []

    def forced_parry(source, target, ctx):
        ctx.flags.force.hit = True
        ctx.stages.check_evasion = False
        ctx.stages.check_block = False
        ctx.stages.check_crit = False
        if ctx.result.action_facts["execution"]["origin"] == "counter":
            seen.extend(effect.effect_id for effect in enemy.statuses.effects)
            ctx.stages.check_parry = False
        else:
            ctx.flags.force.parry = True
        return resolve(source, target, ctx)

    monkeypatch.setattr(CombatResolver, "resolve_exchange", staticmethod(forced_parry))
    ctx = battle(player, enemy)
    await CombatExecutor()._handle_exchange(
        ctx,
        CombatActionDTO(
            action_type="exchange",
            move=move("1", "monster", "second_breath" if same_result_dispel else None),
            is_forced=True,
        ),
    )
    assert "prep_dual_blade_loop_counter" in seen
    assert "prep_dual_blade_loop_parry" not in seen
    assert any(e.effect_id == "debuff_2h_damage_halved" for e in player.statuses.effects)


@pytest.mark.unit
@pytest.mark.parametrize("reverse", [False, True])
def test_ag03_wave_removals_then_applications_and_conflicts_are_order_independent(reverse):
    from src.backend.features.combat.dto import CombatStatusApplicationDTO, CombatStatusRemovalDTO

    player, enemy = actor("1", "a"), actor("monster", "b")
    player.statuses.effects.append(
        ActiveEffectDTO(
            uid="old",
            effect_id="prep_second_breath",
            source_id="1",
            expire_at_exchange=5,
            modified_sources={"parry": ["old"]},
        )
    )
    player.raw.modifiers["parry"] = {"base": 0, "source": {}, "temp": {"old": "+0.2"}}

    def application(uid, owner, effect):
        return CombatStatusApplicationDTO(
            actor_id="1",
            source_id=owner,
            effect_id=effect,
            active_effect=ActiveEffectDTO(
                uid=uid, effect_id=effect, source_id=owner, expire_at_exchange=8, resolved_temp_commands=[]
            ).model_dump(mode="json"),
        )

    own = InteractionResultDTO(
        source_id="1",
        target_id="monster",
        action_facts={"execution": {"origin": "primary", "strike_id": "own"}},
        status_applications=[application("own", "1", "prep_second_breath")],
    )
    foreign = InteractionResultDTO(
        source_id="monster",
        target_id="1",
        action_facts={"execution": {"origin": "primary", "strike_id": "foreign"}},
        status_applications=[application("foreign", "monster", "prep_perfect_riposte")],
        status_removals=[CombatStatusRemovalDTO(actor_id="1", effect_uid="old")],
    )
    pairs = [(player, enemy, own), (enemy, player, foreign)]
    MechanicsService().apply_exchange_results(PipelineContextDTO(), list(reversed(pairs)) if reverse else pairs)
    assert [(e.uid, e.effect_id) for e in player.statuses.effects] == [("own", "prep_second_breath")]
    assert player.raw.modifiers["parry"]["temp"] == {}


@pytest.mark.unit
@pytest.mark.parametrize("reverse", [False, True])
def test_ag03_resolved_dynamic_commands_survive_roundtrip_replace_and_commit_order(reverse):
    from src.backend.features.combat.dto import CombatStatusApplicationDTO, CombatStatusRemovalDTO
    from src.backend.features.combat.runtime.engine.modifier_application_service import ModifierApplicationService
    from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine
    from src.backend.features.game_catalog.combat.resources.common.modifier_applications import ModifierApplicationDTO

    player, enemy = actor("1", "a"), actor("monster", "b")
    player.raw.modifiers["armor"] = {"base": 10, "source": {}, "temp": {"old": "+20"}}
    player.statuses.effects.append(
        ActiveEffectDTO(
            uid="old", effect_id="old-armor", source_id="1", expire_at_exchange=5, modified_sources={"armor": ["old"]}
        )
    )
    StatsEngine.ensure_stats(player)
    copy = player.model_copy(deep=True)
    applied = ModifierApplicationService.apply(
        applications=[
            ModifierApplicationDTO(
                modifier_id="physical_damage_bonus_add",
                source_modifier_id="armor",
                value_mode="source_modifier_multiplier",
                value_multiplier=2,
            )
        ],
        owner="effect",
        owner_uid="frozen",
        owner_id="frozen-buff",
        source=copy,
        target=copy,
    )
    effect = ActiveEffectDTO(
        uid="frozen",
        effect_id="frozen-buff",
        source_id="1",
        expire_at_exchange=5,
        modified_sources=applied.modified_sources,
        resolved_temp_commands=ModifierApplicationService.capture_commands([copy], applied.modified_sources),
    )
    effect = ActiveEffectDTO.model_validate_json(effect.model_dump_json())
    buff = InteractionResultDTO(
        source_id="1",
        target_id="monster",
        status_applications=[
            CombatStatusApplicationDTO(
                actor_id="1",
                source_id="1",
                effect_id=effect.effect_id,
                active_effect=effect.model_dump(mode="json"),
                mode="replace",
            )
        ],
    )
    dispel = InteractionResultDTO(
        source_id="monster", target_id="1", status_removals=[CombatStatusRemovalDTO(actor_id="1", effect_uid="old")]
    )
    pairs = [(player, enemy, buff), (enemy, player, dispel)]
    MechanicsService().apply_exchange_results(PipelineContextDTO(), list(reversed(pairs)) if reverse else pairs)
    StatsEngine.ensure_stats(player)
    assert player.stats.mods.physical_damage_bonus == 60
    assert player.stats.mods.armor == 10
    # Replacing with the same resolved command does not duplicate its strength.
    MechanicsService().apply_exchange_results(PipelineContextDTO(), [(player, enemy, buff)])
    StatsEngine.ensure_stats(player)
    assert player.stats.mods.physical_damage_bonus == 60


@pytest.mark.unit
@pytest.mark.parametrize("reverse", [False, True])
def test_ag03_replace_priority_and_local_consumption(reverse):
    from src.backend.features.combat.dto import CombatStatusApplicationDTO, CombatStatusRemovalDTO

    player, enemy = actor("1", "a"), actor("monster", "b")

    def result(origin, uid, value):
        effect = ActiveEffectDTO(
            uid=uid,
            effect_id="test-buff",
            source_id="1",
            expire_at_exchange=5,
            modified_sources={"strength": [uid]},
            resolved_temp_commands=[
                {
                    "actor_id": "1",
                    "layer": "attributes",
                    "stat_key": "strength",
                    "source_id": uid,
                    "command": f"+{value}",
                    "base": 0,
                }
            ],
        )
        return InteractionResultDTO(
            source_id="1",
            target_id="monster",
            action_facts={"execution": {"origin": origin}},
            status_applications=[
                CombatStatusApplicationDTO(
                    actor_id="1",
                    source_id="1",
                    effect_id="test-buff",
                    active_effect=effect.model_dump(mode="json"),
                    mode="replace",
                )
            ],
        )

    primary, offhand = result("primary", "primary-buff", 7), result("offhand", "offhand-buff", 30)
    consumed = result("primary", "consumed", 99)
    consumed.status_applications[0].effect_id = "consumed-prep"
    consumed.status_applications[0].active_effect["effect_id"] = "consumed-prep"
    consumed.status_removals.append(CombatStatusRemovalDTO(actor_id="1", effect_uid="consumed"))
    pairs = [(player, enemy, primary), (player, enemy, offhand), (player, enemy, consumed)]
    MechanicsService().apply_exchange_results(PipelineContextDTO(), list(reversed(pairs)) if reverse else pairs)
    assert [(e.uid, e.effect_id) for e in player.statuses.effects] == [("primary-buff", "test-buff")]
    assert player.raw.attributes["strength"]["temp"] == {"primary-buff": "+7"}


@pytest.mark.unit
@pytest.mark.parametrize("reverse", [False, True])
def test_ag03_refresh_cannot_resurrect_dispelled_snapshot_uid(reverse):
    from src.backend.features.combat.dto import CombatStatusApplicationDTO, CombatStatusRemovalDTO

    player, enemy = actor("1", "a"), actor("monster", "b")
    effect = ActiveEffectDTO(uid="old", effect_id="prep_second_breath", source_id="1", expire_at_exchange=5)
    player.statuses.effects.append(effect)
    refresh = InteractionResultDTO(
        source_id="1",
        target_id="monster",
        status_applications=[
            CombatStatusApplicationDTO(
                actor_id="1",
                source_id="1",
                effect_id=effect.effect_id,
                active_effect=effect.model_copy(update={"expire_at_exchange": 20}).model_dump(mode="json"),
            )
        ],
    )
    dispel = InteractionResultDTO(
        source_id="monster", target_id="1", status_removals=[CombatStatusRemovalDTO(actor_id="1", effect_uid="old")]
    )
    pairs = [(player, enemy, refresh), (enemy, player, dispel)]
    MechanicsService().apply_exchange_results(PipelineContextDTO(), list(reversed(pairs)) if reverse else pairs)
    assert not player.statuses.effects
