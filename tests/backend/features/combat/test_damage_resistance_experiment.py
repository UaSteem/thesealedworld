"""Temporary resistance experiment: modifiers remain, damage bypasses the layer."""

import pytest

from src.backend.features.combat.dto.actor import ActorStats
from src.backend.features.combat.dto.pipeline import InteractionResultDTO, PipelineContextDTO
from src.backend.features.combat.runtime.engine.math_core import MathCore
from src.backend.features.combat.runtime.engine.resolver.steps.damage import damage_step
from src.shared.schemas.modifier_dto import CombatModifiersDTO, CombatSkillsDTO


def actor(**mods: float) -> ActorStats:
    return ActorStats(mods=CombatModifiersDTO(**mods), skills=CombatSkillsDTO(skill_heavy_armor=1.0))


@pytest.mark.unit
@pytest.mark.parametrize("resistance,suppression", [(0.0, 0.0), (0.8, 0.0), (0.8, 0.2)])
def test_physical_damage_bypasses_resistance_but_keeps_armor_and_trace(
    monkeypatch: pytest.MonkeyPatch, resistance: float, suppression: float
) -> None:
    monkeypatch.setattr(MathCore, "random_range", staticmethod(lambda low, high: low))
    monkeypatch.setattr(MathCore, "check_chance", staticmethod(lambda chance: False))
    result = InteractionResultDTO(source_id=1, target_id=2)
    damage = damage_step.run(
        actor(main_hand_damage_base=100.0, main_hand_damage_spread=0.0, physical_suppression=suppression),
        actor(physical_resistance=resistance, armor=40.0),
        PipelineContextDTO(),
        result,
    )
    assert result.damage_trace is not None
    trace = result.damage_trace.details
    assert trace["after_resist"] == pytest.approx(100.0)
    assert trace["resl"]["effective"] == 0.0
    assert trace["resl"]["raw"] == pytest.approx(resistance)
    assert trace["physical_suppression"] == pytest.approx(suppression)
    assert 0.0 < damage < 100.0
    assert damage == pytest.approx(trace["after_armor"])


@pytest.mark.unit
@pytest.mark.parametrize("element", ["fire", "water", "air", "earth", "light", "darkness", "arcane", "nature"])
@pytest.mark.parametrize("penetration", [0.0, 0.2])
def test_elemental_damage_bypasses_resistance_but_keeps_magic_armor(
    monkeypatch: pytest.MonkeyPatch, element: str, penetration: float
) -> None:
    monkeypatch.setattr(MathCore, "random_range", staticmethod(lambda low, high: low))
    ctx = PipelineContextDTO()
    ctx.flags.meta.source_type = "magic"
    ctx.flags.damage.physical = False
    setattr(ctx.flags.damage, element, True)
    result = InteractionResultDTO(source_id=1, target_id=2)
    damage = damage_step.run(
        actor(magical_damage=20.0, magical_damage_spread=0.0, magical_penetration=penetration),
        actor(**{f"{element}_resistance": 0.8, "magic_armor": 4.0}),
        ctx,
        result,
    )
    assert damage == pytest.approx(16.0)
    assert result.damage_trace is not None
    trace = result.damage_trace.details
    assert trace["parts"][element] == pytest.approx(20.0)
    assert trace["resl"]["effective"] == 0.0
    assert trace["after_magic_armor"] == pytest.approx(16.0)
