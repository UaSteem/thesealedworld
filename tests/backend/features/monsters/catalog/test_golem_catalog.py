"""Authored stone golem invariants independent of persistence and combat execution."""

from collections import Counter

from src.backend.features.game_catalog.combat.resources.abilities import get_ability_catalog_entry
from src.backend.features.monsters.catalog.families.golem_catalog.family import GOLEM_FAMILY
from src.backend.features.monsters.catalog.nested_contracts import resolve_family
from src.backend.features.monsters.catalog.skill_contract import MONSTER_COMBAT_SKILL_KEYS


def test_stone_golem_roster_is_complete_and_separates_basis_from_clan():
    family, clans, members = resolve_family(GOLEM_FAMILY)
    assert family.id == "golem_foundry"
    assert family.mechanics["organization_type"] == "solitary"
    assert len(clans) == 1
    assert clans[0].normal_spawn
    assert clans[0].id == "golem_foundry.base"
    assert len(members) == 12
    assert Counter(member.role for member in members) == {"minion": 4, "veteran": 3, "elite": 3, "boss": 2}
    assert len({member.variant_id for member in members}) == 12
    assert all(member.base_id == member.variant_id for member in members)
    assert all(member.image is None for member in members)


def test_stone_golems_use_positive_draft_costs_current_stats_and_existing_skills():
    _, _, members = resolve_family(GOLEM_FAMILY)
    expected_costs = {"veteran": 23, "elite": 30, "boss": 45}
    expected_stats = {
        "strength",
        "agility",
        "endurance",
        "intellect",
        "memory",
        "mental",
        "perception",
        "projection",
        "prediction",
    }
    for member in members:
        price = (
            {"stone_thrower": 13, "stone_worker": 14, "stone_sentry": 15, "stone_ram": 16}[member.variant_id]
            if member.role == "minion"
            else expected_costs[member.role]
        )
        assert member.assembly_cost == price
        assert set(member.base_stats) == expected_stats
        assert all(type(value) is int and value > 0 for value in member.base_stats.values())
        assert member.min_tier == 2 and member.max_tier == 5
        assert member.skills and set(member.skills) <= MONSTER_COMBAT_SKILL_KEYS
        assert all(get_ability_catalog_entry(key) is not None for key in member.ability_ids)
        assert "heal" not in member.ability_ids
        assert "basic_blood_hunger" not in member.ability_ids


def test_stone_golem_localized_names_and_natural_loadouts_are_authored():
    family, clans, members = resolve_family(GOLEM_FAMILY)
    assert family.name == "Големы"
    assert clans[0].name == "Каменные големы"
    assert {member.name for member in members} >= {"Каменный работник", "Рунный резонатор", "Каменный колосс"}
    for member in members:
        assert member.description
        assert member.fixed_loadout["chest_armor"] == "golem_shell"
        assert member.fixed_loadout["amulet"] == "golem_core"
        assert all(key.startswith("golem_") for key in member.fixed_loadout.values() if key)
