"""Build catalog monsters with prepared equipment, without persistence or inspection."""

from copy import deepcopy
from typing import Any

from src.backend.core.calculators.stats_waterfall_calculator import COMBAT_MATH_VERSION, StatsWaterfallCalculator
from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder
from src.backend.features.character.runtime.rules.base_power_assembler import BasePowerAssembler
from src.backend.features.items.services.catalog_service import ItemCatalogService
from src.backend.features.monsters.catalog.contracts import FamilyDefinition, MemberDefinition
from src.backend.features.monsters.catalog.materialization.generation_fields import _skill_value_for_tier
from src.backend.features.monsters.catalog.prepared_equipment import PreparedEquipmentSetDTO
from src.backend.features.monsters.catalog.resources.equipment_mapping import get_natural_equipment_mapping
from src.backend.features.monsters.instances.dto.instance_build import (
    MonsterCombatProjectionDTO,
    MonsterInstanceBuildDTO,
)
from src.backend.features.monsters.instances.runtime.combat_math_model import MonsterCombatMathModelBuilder
from src.backend.features.monsters.instances.runtime.feint_loadout import build_monster_feint_loadout
from src.backend.features.monsters.instances.runtime.tier_scaling import TIER_SCALING_CONFIG, scale_monster_attributes
from src.backend.features.monsters.instances.services.build_readiness import MonsterBuildReadinessService


def _mapped_items(prepared: PreparedEquipmentSetDTO) -> dict[str, Any]:
    # Runtime item projections keep combat fields nested. Actor mappers consume
    # the same flattened mechanics shape used by the monster snapshot adapter.
    items = prepared.to_items_projection().model_dump(mode="json")
    catalog = ItemCatalogService.load_default()
    for item in items["by_id"].values():
        combat = item["combat"]
        item.update(combat)
        item["mechanics"] = dict(combat)
        natural_key = item["generation"].get("natural_key")
        natural = get_natural_equipment_mapping(natural_key) if natural_key else None
        if natural is not None:
            item["base_id"] = natural.base_id
        base = catalog.get_base_item(item["base_id"])
        material_id = item["generation"].get("material_id")
        material = catalog.get_material(material_id) if material_id else None
        # These are item catalog metadata, absent from the compact runtime DTO.
        # Combat power and rolled bonuses remain exactly as prepared on disk.
        if base is not None:
            item["armor_class"] = base.armor_class
            item["mechanics"]["armor_class"] = base.armor_class
            item["mechanics"]["implicit_bonuses_base"] = dict(base.implicit_bonuses)
            for key in ("ammo_charge_base", "ammo_charge_skill_bonus", "ammo_effect_payload"):
                value = getattr(base, key, None)
                if value is not None:
                    item["mechanics"][key] = deepcopy(value)
        if material is not None:
            item["tier_mult"] = material.tier_mult
            item["mechanics"]["tier_mult"] = material.tier_mult
            item["material"] = {"tier": material.tier, "tier_mult": material.tier_mult}
        item["type"] = item["item_type"]
        item["rarity_tier"] = item["generation"].get("rarity_tier", 0)
        item["affixes"] = item["generation"].get("affixes", [])
    return items


class MonsterInstanceBuilder:
    """Assemble detached pre-combat projections using the existing monster rules."""

    def build(
        self, *, member: MemberDefinition, family: FamilyDefinition, prepared: PreparedEquipmentSetDTO
    ) -> MonsterInstanceBuildDTO:
        MonsterBuildReadinessService().require_ready(
            member=member, family=family, tier=prepared.tier, prepared=prepared
        )
        skills = {key: _skill_value_for_tier(prepared.tier) for key in member.skills}
        meta = {
            "family_id": family.id,
            "archetype": family.mechanics.get("archetype", "humanoid"),
            "organization_type": family.mechanics.get("organization_type", "solitary"),
            "role": member.role,
            "tags": sorted(member.tags),
        }
        tier_attributes = scale_monster_attributes(member.base_stats, prepared.tier)
        baseline = self._calculate(tier_attributes, {}, skills, meta)
        equipped = self._calculate(tier_attributes, _mapped_items(prepared), skills, meta)
        for projection in (baseline, equipped):
            if member.ability_ids:
                projection.loadout["known_abilities"] = list(
                    dict.fromkeys([*projection.loadout.get("known_abilities", []), *member.ability_ids])
                )
        return MonsterInstanceBuildDTO(
            family_id=family.id,
            member_id=member.id,
            clan_id=member.clan_id,
            variant_id=member.variant_id,
            role=member.role,
            tier=prepared.tier,
            tier_multiplier=TIER_SCALING_CONFIG[prepared.tier]["stat_mult"],
            combat_math_version=COMBAT_MATH_VERSION,
            catalog_attributes=dict(member.base_stats),
            tier_attributes=tier_attributes,
            skills=skills,
            baseline=baseline,
            equipped=equipped,
        )

    @staticmethod
    def _calculate(
        attributes: dict[str, int], items: dict[str, Any], skills: dict[str, float], meta: dict[str, Any]
    ) -> MonsterCombatProjectionDTO:
        loadout = CharacterCombatActorInputBuilder._loadout(items, skills, include_basic_gift_abilities=False)
        loadout = build_monster_feint_loadout(loadout, role=meta.get("role"))
        raw = MonsterCombatMathModelBuilder().build_raw(
            attributes=attributes, items=items, skills=skills, monster_meta=meta
        )
        values, formulas = StatsWaterfallCalculator.calculate_waterfall(raw)
        BasePowerAssembler.apply_to_values(values, loadout_layout=loadout["layout"], skills=skills)
        return MonsterCombatProjectionDTO(values=values, raw=raw, formulas=formulas, loadout=loadout)
