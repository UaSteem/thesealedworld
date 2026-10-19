import hashlib
import json

import pytest

from src.backend.features.monsters.catalog.contracts import thaw_catalog_value
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.policies.composition import MonsterCompositionPolicyResolver
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


def test_golem_price_ladder_preserves_nonstat_mechanics_skills_abilities_art_and_equipment():
    members = [m for m in get_catalog().members.values() if m.family_id == "golem_foundry"]
    assert len(members) == 12
    proof = {}
    for m in members:
        assert m.assembly_cost == {"stone_thrower": 13, "stone_worker": 14, "stone_sentry": 15, "stone_ram": 16}.get(
            m.variant_id, {"veteran": 23, "elite": 30, "boss": 45}.get(m.role)
        )
        proof[m.id] = {
            "role": m.role,
            "mechanics": {k: v for k, v in thaw_catalog_value(m.mechanics).items() if k != "base_stats"},
            "skills": list(m.skills),
            "min_tier": m.min_tier,
            "max_tier": m.max_tier,
            "equipment_set_id": m.equipment_set_id,
            "ability_ids": list(m.ability_ids),
            "image": m.image.model_dump(mode="json") if m.image else None,
        }
    assert (
        hashlib.sha256(json.dumps(proof, sort_keys=True).encode()).hexdigest()
        == "8020b645796b8d7d9bf2142108feea22fd68dd4ebc0fa7e0ff94e5ade7fb3ab9"
    )


@pytest.mark.parametrize("kind", ("ordinary", "patrol", "guard", "leader"))
@pytest.mark.parametrize("difficulty", ("easy", "normal", "hard"))
def test_golem_builtin_total_limit_and_affordable_first_tier(kind, difficulty):
    from src.backend.features.monsters.encounters.profiles.registry import MINION_REFERENCE_GS

    order = MonsterEncounterOrderDTO(
        encounter_type=kind,
        difficulty=difficulty,
        location_tier=2,
        family_ids=("golem_foundry",),
        seed=13,
        player_gear_score=MINION_REFERENCE_GS[2],
    )
    resolver = MonsterCompositionPolicyResolver()
    profile = resolver.profile(order)
    expected = (2, 3) if kind == "ordinary" else (1, 2)
    assert (profile.min_members, profile.max_members) == expected
    result = MonsterEncounterSelectionService().select(order)
    assert result.status == "selected"
    assert expected[0] <= len(result.selection.members) <= expected[1]
    roles = [member.role for member in result.selection.members]
    for rule in profile.roles:
        assert roles.count(rule.role) >= rule.min_count
    external = profile.model_copy(update={"min_members": 1, "max_members": 8})
    assert resolver.profile(order.model_copy(update={"profile_override": external})) == external


def test_golem_senior_singleton_is_selectable_when_minions_are_unaffordable():
    from src.backend.features.monsters.encounters.profiles.registry import MINION_REFERENCE_GS

    order = MonsterEncounterOrderDTO(
        encounter_type="patrol",
        difficulty="easy",
        location_tier=2,
        family_ids=("golem_foundry",),
        seed=13,
        player_gear_score=MINION_REFERENCE_GS[2] * 0.01,
    )
    result = MonsterEncounterSelectionService().select(order)
    assert result.status == "selected"
    assert len(result.selection.members) == 1
    assert result.selection.members[0].role == "veteran"


@pytest.mark.parametrize("tier", (0, 1))
def test_golems_reject_below_first_family_tier(tier):
    order = MonsterEncounterOrderDTO(
        encounter_type="ordinary",
        difficulty="easy",
        location_tier=tier,
        family_ids=("golem_foundry",),
        seed=13,
        player_gear_score=100,
    )
    assert MonsterEncounterSelectionService().select(order).status == "rejected"


EXPECTED_GOLEM_ATTRIBUTES = {
    "stone_worker": {
        "strength": 22,
        "agility": 8,
        "endurance": 24,
        "intellect": 7,
        "memory": 8,
        "mental": 12,
        "perception": 9,
        "projection": 6,
        "prediction": 8,
    },
    "stone_sentry": {
        "strength": 20,
        "agility": 10,
        "endurance": 23,
        "intellect": 9,
        "memory": 10,
        "mental": 13,
        "perception": 15,
        "projection": 7,
        "prediction": 12,
    },
    "stone_thrower": {
        "strength": 19,
        "agility": 12,
        "endurance": 20,
        "intellect": 8,
        "memory": 9,
        "mental": 12,
        "perception": 18,
        "projection": 9,
        "prediction": 14,
    },
    "stone_ram": {
        "strength": 25,
        "agility": 7,
        "endurance": 25,
        "intellect": 6,
        "memory": 7,
        "mental": 13,
        "perception": 10,
        "projection": 6,
        "prediction": 9,
    },
    "stone_crusher": {
        "strength": 32,
        "agility": 10,
        "endurance": 31,
        "intellect": 9,
        "memory": 10,
        "mental": 17,
        "perception": 13,
        "projection": 9,
        "prediction": 13,
    },
    "stone_bulwark": {
        "strength": 28,
        "agility": 10,
        "endurance": 35,
        "intellect": 11,
        "memory": 13,
        "mental": 20,
        "perception": 15,
        "projection": 9,
        "prediction": 15,
    },
    "stone_catcher": {
        "strength": 29,
        "agility": 15,
        "endurance": 30,
        "intellect": 11,
        "memory": 12,
        "mental": 18,
        "perception": 19,
        "projection": 10,
        "prediction": 17,
    },
    "rune_guardian": {
        "strength": 32,
        "agility": 12,
        "endurance": 40,
        "intellect": 16,
        "memory": 18,
        "mental": 25,
        "perception": 18,
        "projection": 17,
        "prediction": 20,
    },
    "rune_punisher": {
        "strength": 38,
        "agility": 16,
        "endurance": 34,
        "intellect": 14,
        "memory": 15,
        "mental": 23,
        "perception": 22,
        "projection": 15,
        "prediction": 22,
    },
    "rune_resonator": {
        "strength": 29,
        "agility": 13,
        "endurance": 35,
        "intellect": 23,
        "memory": 22,
        "mental": 26,
        "perception": 20,
        "projection": 24,
        "prediction": 21,
    },
    "quarry_overseer": {
        "strength": 39,
        "agility": 17,
        "endurance": 42,
        "intellect": 24,
        "memory": 25,
        "mental": 31,
        "perception": 26,
        "projection": 23,
        "prediction": 26,
    },
    "stone_colossus": {
        "strength": 46,
        "agility": 11,
        "endurance": 48,
        "intellect": 14,
        "memory": 17,
        "mental": 30,
        "perception": 20,
        "projection": 16,
        "prediction": 19,
    },
}


def test_golem_senior_ten_percent_attributes_and_unchanged_minions():
    members = [m for m in get_catalog().members.values() if m.family_id == "golem_foundry"]
    for member in members:
        assert thaw_catalog_value(member.mechanics)["base_stats"] == EXPECTED_GOLEM_ATTRIBUTES[member.variant_id]


def test_golem_limits_follow_allowed_ranks_instead_of_encounter_label(monkeypatch):
    from src.backend.features.monsters.encounters.policies import composition
    from src.backend.features.monsters.encounters.profiles.registry import get_profile

    ordinary = get_profile("solo", "ordinary", "easy", 2)
    patrol = get_profile("solo", "patrol", "easy", 2)
    resolver = MonsterCompositionPolicyResolver()
    for kind, authored, expected in (("ordinary", patrol, (1, 2)), ("patrol", ordinary, (2, 3))):
        monkeypatch.setattr(composition, "get_profile", lambda *args, authored=authored: authored)
        order = MonsterEncounterOrderDTO(
            encounter_type=kind,
            difficulty="easy",
            location_tier=2,
            family_ids=("golem_foundry",),
            seed=1,
            player_gear_score=100,
        )
        profile = resolver.profile(order)
        assert (profile.min_members, profile.max_members) == expected
