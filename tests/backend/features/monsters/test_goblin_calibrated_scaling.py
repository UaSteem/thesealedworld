import hashlib
import json

import pytest

from src.backend.features.monsters.catalog.contracts import thaw_catalog_value
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.inspection.services.catalog_view_service import CatalogMonsterViewService
from src.backend.features.monsters.instances.runtime.tier_scaling import scale_monster_attributes
from tests.backend.features.monsters.catalog.equipment_slot_expectations import before_equipment_slots

ATTRIBUTES = (
    "strength",
    "agility",
    "endurance",
    "intellect",
    "memory",
    "mental",
    "perception",
    "projection",
    "prediction",
)
MINIONS = {
    "goblin_scavenger": (7, 70, (9, 11, 9, 8, 6, 6, 10, 5, 6)),
    "goblin_sparkpick": (8, 74, (10, 12, 10, 8, 6, 7, 9, 6, 6)),
    "goblin_sneak": (9, 77, (9, 14, 9, 8, 6, 7, 12, 5, 7)),
    "goblin_cutter": (10, 80, (11, 13, 11, 8, 6, 8, 11, 5, 7)),
}


def test_goblin_senior_definitions_prices_and_equipment_remain_unchanged():
    seniors = {
        member.id: {
            "mechanics": thaw_catalog_value(member.mechanics),
            "skills": member.skills,
            "assembly_cost": member.assembly_cost,
            "equipment_set_id": member.equipment_set_id,
        }
        for member in get_catalog().members.values()
        if member.family_id == "goblin_tribe" and member.role != "minion"
    }
    assert len(seniors) == 8
    assert hashlib.sha256(json.dumps(before_equipment_slots(seniors), sort_keys=True).encode()).hexdigest() == (
        "43fd795b4936c2ce96df8e9eb9580dd9ae872f0c61e6d7a6833027b8f8be0e96"
    )


@pytest.mark.parametrize("variant", MINIONS)
def test_live_goblin_minions_use_calibrated_base_without_changing_prices(variant):
    cost, total, values = MINIONS[variant]
    member = get_catalog().members[f"goblin_tribe.base.{variant}"]
    assert dict(member.base_stats) == dict(zip(ATTRIBUTES, values, strict=True))
    assert sum(member.base_stats.values()) == total
    assert member.assembly_cost == cost


@pytest.mark.parametrize("tier,multiplier", enumerate((1, 1.2, 1.7, 2.2, 2.7, 3.2, 3.7, 4.2)))
def test_monster_attribute_curve_uses_temporary_half_point_steps(tier, multiplier):
    original = {"strength": 13, "endurance": 11}
    assert scale_monster_attributes(original, tier) == {
        key: round(value * multiplier) for key, value in original.items()
    }
    assert original == {"strength": 13, "endurance": 11}


def test_actual_t5_inspection_uses_calibrated_attributes_for_minion_and_veteran():
    service = CatalogMonsterViewService()
    for variant in ("goblin_scavenger", "goblin_spearman"):
        member = get_catalog().members[f"goblin_tribe.base.{variant}"]
        preview = service.equipment(member_id=member.id, tier=5).stats_preview
        assert preview.tier_multiplier == 3.2
        assert {key: preview.technical["base"][key] for key in ATTRIBUTES} == {
            key: round(value * 3.2) for key, value in member.base_stats.items()
        }
