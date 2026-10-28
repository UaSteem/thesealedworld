import pytest

from src.backend.features.character.runtime import CharacterCombatMathModelBuilder
from src.backend.features.combat.dto.actor import ActorStats
from src.backend.features.combat.dto.pipeline import PipelineContextDTO
from src.backend.features.combat.runtime.engine.math_core import MathCore
from src.backend.features.combat.runtime.engine.resolver.steps.crit import CritStep
from src.backend.features.combat.runtime.engine.resolver.support import trigger_activator
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine
from src.backend.features.items.dto.instance import ItemGenerationRequestDTO
from src.backend.features.items.runtime.item_factory import ItemFactory
from src.shared.schemas.modifier_dto import CombatModifiersDTO, CombatSkillsDTO


@pytest.mark.unit
@pytest.mark.parametrize("source,weapon_chance", [("main_hand", 0.05), ("off_hand", 0.08)])
@pytest.mark.parametrize("skill", [0.0, 0.5, 1.0])
def test_weapon_mastery_scales_only_active_hand_crit(source, weapon_chance, skill, monkeypatch):
    actor = ActorStats(
        mods=CombatModifiersDTO(main_hand_crit_chance=0.05, off_hand_crit_chance=0.08, crit_chance=0.20),
        skills=CombatSkillsDTO(skill_swords=skill),
    )
    ctx = PipelineContextDTO()
    ctx.flags.meta.source_type = source
    ctx.flags.meta.weapon_class = "swords"
    observed = []
    monkeypatch.setattr(MathCore, "roll_chance", lambda chance: (observed.append(chance) or 0.99, False))
    CritStep().run(actor, actor, ctx, ctx.result)
    assert observed == [pytest.approx(weapon_chance * (1 + skill) + 0.20)]
    assert ctx.result.is_crit is False


@pytest.mark.unit
@pytest.mark.parametrize("skill", [0.0, 0.5, 1.0])
def test_global_crit_bonus_without_weapon_base_is_independent_of_mastery(skill, monkeypatch):
    actor = ActorStats(mods=CombatModifiersDTO(crit_chance=0.20), skills=CombatSkillsDTO(skill_swords=skill))
    ctx = PipelineContextDTO()
    ctx.flags.meta.weapon_class = "swords"
    observed = []
    monkeypatch.setattr(MathCore, "roll_chance", lambda chance: (observed.append(chance) or 0.99, False))
    CritStep().run(actor, actor, ctx, ctx.result)
    assert observed == [pytest.approx(0.20)]


@pytest.mark.unit
@pytest.mark.parametrize("source,elemental,expected", [("magic", False, 0.12), ("item", False, 0.15), ("main_hand", True, 0.12)])
def test_nonweapon_crit_does_not_use_weapon_mastery(source, elemental, expected, monkeypatch):
    actor = ActorStats(
        mods=CombatModifiersDTO(magical_crit_chance=0.12, item_crit_chance=0.15, crit_chance=0.20),
        skills=CombatSkillsDTO(skill_swords=1),
    )
    ctx = PipelineContextDTO()
    ctx.flags.meta.source_type = source
    ctx.flags.meta.weapon_class = "swords"
    ctx.flags.damage.fire = elemental
    observed = []
    monkeypatch.setattr(MathCore, "roll_chance", lambda chance: (observed.append(chance) or 0.99, False))
    CritStep().run(actor, actor, ctx, ctx.result)
    assert observed == [pytest.approx(expected)]


@pytest.mark.unit
@pytest.mark.parametrize("passed,hook", [(True, "ON_CRIT"), (False, "ON_CRIT_FAIL")])
def test_crit_bonus_keeps_caps_and_trigger_hooks(passed, hook, monkeypatch):
    actor = ActorStats(
        mods=CombatModifiersDTO(main_hand_crit_chance=0.5, crit_chance=0.20, main_hand_crit_cap=0.6),
        skills=CombatSkillsDTO(skill_swords=1),
    )
    ctx = PipelineContextDTO()
    ctx.flags.meta.weapon_class = "swords"
    observed, hooks = [], []
    monkeypatch.setattr(MathCore, "roll_chance", lambda chance: (observed.append(chance) or 0.5, passed))
    monkeypatch.setattr(trigger_activator, "resolve_triggers", lambda ctx_, res_, key: hooks.append(key))
    CritStep().run(actor, actor, ctx, ctx.result)
    assert observed == [0.6]
    assert ctx.result.is_crit == passed
    assert hooks == [hook]


@pytest.mark.unit
def test_missing_weapon_class_keeps_additive_base_and_global_chance(monkeypatch):
    actor = ActorStats(
        mods=CombatModifiersDTO(main_hand_crit_chance=0.05, crit_chance=0.20),
        skills=CombatSkillsDTO(skill_swords=1),
    )
    ctx = PipelineContextDTO()
    observed = []
    monkeypatch.setattr(MathCore, "roll_chance", lambda chance: (observed.append(chance) or 0.99, False))
    CritStep().run(actor, actor, ctx, ctx.result)
    assert observed == [pytest.approx(0.25)]


@pytest.mark.unit
@pytest.mark.parametrize("category", ["cloths", "leathers"])
@pytest.mark.parametrize("skill", [0.0, 0.5, 1.0])
def test_generated_t7_gloves_keep_twenty_point_bonus_through_actor_stats_and_roll(category, skill, monkeypatch):
    factory = ItemFactory()
    material = factory.catalog.get_material_for_tier(category, 7)
    gloves = factory.generate(ItemGenerationRequestDTO(base_id="gloves", material_id=material.id, rarity_tier=0))
    equipped = gloves.model_dump(mode="json")
    equipped.update(item_id="gloves", item_type=gloves.item_type)
    raw = CharacterCombatMathModelBuilder().build_raw(
        attributes={}, skills={"skill_swords": skill}, items={
            "layout": {"equipment": {gloves.slot: "gloves", "main_hand": "weapon"}},
            "by_id": {
                "gloves": equipped,
                "weapon": {
                    "item_id": "weapon", "item_type": "weapon", "slot": "main_hand",
                    "mechanics": {"implicit_bonuses": {"physical_crit_chance": 0.05}},
                },
            },
        },
    )
    actor, _ = StatsEngine.build_stats(raw=raw, skills={"skill_swords": skill}, loadout={})
    assert actor.mods.crit_chance == pytest.approx(0.20)
    assert actor.mods.main_hand_crit_chance == pytest.approx(0.05)
    ctx = PipelineContextDTO()
    ctx.flags.meta.weapon_class = "swords"
    observed = []
    monkeypatch.setattr(MathCore, "roll_chance", lambda chance: (observed.append(chance) or 0.99, False))
    CritStep().run(actor, actor, ctx, ctx.result)
    assert observed == [pytest.approx(0.05 * (1 + skill) + 0.20)]


@pytest.mark.unit
@pytest.mark.parametrize("forced,forbidden,suppressed,expected_hook", [
    (True, False, False, "ON_CRIT"),
    (True, False, True, None),
    (False, True, False, "ON_CRIT_FAIL"),
])
def test_forced_and_forbidden_crit_bypass_roll_and_preserve_hooks(forced, forbidden, suppressed, expected_hook, monkeypatch):
    actor = ActorStats()
    ctx = PipelineContextDTO()
    ctx.flags.force.crit = forced
    ctx.flags.restriction.cannot_crit = forbidden
    ctx.flags.restriction.suppress_crit_triggers = suppressed
    hooks = []
    monkeypatch.setattr(MathCore, "roll_chance", lambda chance: pytest.fail("Forced/forbidden crit must not roll"))
    monkeypatch.setattr(trigger_activator, "resolve_triggers", lambda ctx_, res_, key: hooks.append(key))
    CritStep().run(actor, actor, ctx, ctx.result)
    assert ctx.result.is_crit == forced
    assert hooks == ([] if expected_hook is None else [expected_hook])
