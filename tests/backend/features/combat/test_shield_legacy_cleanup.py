"""The retired item bash must not coexist with the working shield style."""

from pathlib import Path

from src.backend.features.combat.dto.pipeline import ChainTriggersDTO, PipelineContextDTO
from src.backend.features.combat.dto.trigger_rules import BlockTriggersDTO
from src.backend.features.combat.runtime.engine.trigger_activation import activate_trigger
from src.backend.features.game_catalog.combat.resources.common.pipeline_mutations import (
    get_pipeline_mutation_contract,
)
from src.backend.features.game_catalog.combat.resources.triggers import (
    get_trigger_catalog_entry_by_key,
    get_trigger_technical,
)
from src.backend.features.items.resources.base_item.weapons.offhand import OFFHAND_DB


def test_shields_do_not_assign_retired_item_bash():
    retired = {"weapon_shield_bash_on_block", "block.weapon_shield_bash_on_block"}
    assert all(retired.isdisjoint(item.triggers) for item in OFFHAND_DB.values())


def test_retired_item_bash_is_not_registered_or_exposed_as_flag():
    assert get_trigger_technical("weapon_shield_bash_on_block") is None
    assert get_trigger_catalog_entry_by_key("combat.trigger.weapon.shield_bash_on_block") is None
    assert "weapon_shield_bash_on_block" not in BlockTriggersDTO.model_fields


def test_unexecuted_extra_strike_chain_is_not_an_available_command():
    assert get_pipeline_mutation_contract("chain.trigger_extra_strike") is None
    assert "trigger_extra_strike" not in ChainTriggersDTO.model_fields


def test_persisted_retired_trigger_is_ignored_without_enabling_any_response():
    ctx = PipelineContextDTO.model_validate({"triggers": {"block": {"weapon_shield_bash_on_block": True}}})
    assert activate_trigger(ctx, "block.weapon_shield_bash_on_block", source="weapon") is False
    assert activate_trigger(ctx, "weapon_shield_bash_on_block", source="weapon") is False
    assert ctx.trigger_activations == {}
    assert ctx.triggers.block.style_shield_reflect is False
    assert not any(ctx.result.chain_events.model_dump().values())


def test_prepared_equipment_does_not_reintroduce_retired_item_bash():
    root = Path(__file__).resolve().parents[4] / "src/backend/features/monsters/catalog"
    offenders = [
        str(path.relative_to(root))
        for path in root.rglob("tier_*.py")
        if "shield_bash_on_block" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
