from copy import deepcopy

import pytest

from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.inspection.services.catalog_view_service import CatalogMonsterViewService


def test_spearman_preview_includes_actual_equipment_and_keeps_catalog_immutable():
    member = get_catalog().members["goblin_tribe.base.goblin_spearman"]
    before = dict(member.base_stats)
    preview = CatalogMonsterViewService().equipment(member_id=member.id, tier=4).stats_preview
    assert preview is not None
    naked, equipped = preview.technical["base"], preview.technical["equipped"]
    assert naked["strength"] == round(before["strength"] * 2.7) == 35
    assert preview.tier_multiplier == 2.7
    assert equipped["armor"] > naked["armor"]
    assert equipped["shield_guard_power"] > 0
    assert equipped["main_hand_damage_base"] > equipped["main_hand_weapon_power"] > 0
    assert preview.technical["skills"]["skill_polearms"] == round(4 / 7, 4)
    assert dict(member.base_stats) == before
    rows = {row.key: row for group in preview.groups for row in group.rows}
    assert rows["armor"].delta_value.startswith("+")
    assert rows["strength"].catalog_value == "13"
    assert rows["strength"].base_value == "35"
    assert rows["physical_resistance"].equipped_value.endswith("%")
    assert "off_hand_damage_spread" not in rows


@pytest.mark.parametrize("tier", range(6))
def test_all_goblins_have_deterministic_inspection_math_without_item_generation(monkeypatch, tier):
    from src.backend.features.items.services.generation_service import ItemGenerationService

    def forbidden(*args, **kwargs):
        raise AssertionError("Inspection cannot generate new items")

    monkeypatch.setattr(ItemGenerationService, "generate_runtime_projections", forbidden)
    service = CatalogMonsterViewService()
    for member in get_catalog().members.values():
        if member.family_id != "goblin_tribe":
            continue
        first = service.equipment(member_id=member.id, tier=tier).stats_preview
        second = service.equipment(member_id=member.id, tier=tier).stats_preview
        assert first == second
        assert first.technical["tier"] == tier
        assert first.technical["base"]["hp"] > 0
        assert all(group.rows for group in first.groups)
        snapshot = deepcopy(second)
        first.technical["equipped"]["hp"] = -1
        assert service.equipment(member_id=member.id, tier=tier).stats_preview == snapshot


@pytest.mark.parametrize("tier,multiplier", enumerate([1, 1.2, 1.7, 2.2, 2.7, 3.2, 3.7, 4.2]))
def test_existing_tier_growth_scales_attributes_only(tier, multiplier):
    from src.backend.features.monsters.encounters.resources.spawn_config import TIER_SCALING_CONFIG
    from src.backend.features.monsters.instances.runtime.tier_scaling import scale_monster_attributes

    original = {"strength": 13, "agility": 14}
    assert TIER_SCALING_CONFIG[tier]["stat_mult"] == multiplier
    assert scale_monster_attributes(original, tier) == {
        key: int(round(value * multiplier)) for key, value in original.items()
    }
    assert original == {"strength": 13, "agility": 14}


def test_item_catalog_metadata_reaches_existing_armor_and_item_sync_rules():
    result = CatalogMonsterViewService().equipment(member_id="goblin_tribe.base.goblin_spearman", tier=4)
    trace = result.stats_preview.technical["equipped_trace"]
    cap_sources = trace["raw"]["modifiers"]["dodge_cap"]["source"]
    assert any("medium_cap_penalty" in key for key in cap_sources)
    assert "skill:skill_medium_armor" in cap_sources
    assert (
        trace["raw"]["modifiers"]["dodge_cap"]
        != result.stats_preview.technical["base_trace"]["raw"]["modifiers"]["dodge_cap"]
    )
