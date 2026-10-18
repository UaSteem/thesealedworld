"""Concrete point-budget selection over real authored candidates."""

import pytest
from pydantic import ValidationError

from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


def order(**changes):
    return MonsterEncounterOrderDTO.model_validate(
        dict(
            encounter_type="ordinary",
            location_tier=0,
            family_ids=["goblin_tribe"],
            seed=13,
            difficulty="easy",
            player_gear_score=36.326,
        )
        | changes
    )


def override(points=80, core=None):
    return dict(
        id="test",
        minions=dict(base_points=points, gs_bonus_max=10, gs_threshold=35, gs_step_size=5, gs_points_per_step=3),
        seniors=dict(base_points=points if core else 0),
        roles=[dict(role="minion", min_count=2, max_count=8)]
        + [dict(role=role, min_count=count, max_count=count) for role, count in (core or {}).items()],
    )


@pytest.mark.parametrize("family", ["goblin_tribe", "rat_swarm", "wolf_pack", "bandit_gang"])
@pytest.mark.parametrize("kind", ["ordinary", "patrol", "guard", "leader"])
def test_real_family_selection_respects_budget_core_clan_and_tier(family, kind):
    from src.backend.features.monsters.encounters.profiles.registry import get_profile

    profile = get_profile("solo", kind, "easy").model_dump()
    # Reserve accompaniment without filling all eight slots before required seniors.
    profile["minions"].update(mode="fixed", reference_gs=None, base_points=100)
    profile["roles"][0]["max_count"] = 2
    profile["seniors"]["base_points"] = 240
    result = MonsterEncounterSelectionService().select(
        order(family_ids=[family], encounter_type=kind, profile_override=profile)
    )
    assert result.status == "selected"
    members = result.selection.members
    config = result.selection.assembly_input.configuration
    assert len({m.clan_id for m in members}) == 1
    assert all(m.tier == 0 and m.family_id == family for m in members)
    assert 2 <= len(members) <= 8
    assert result.budget_spent == sum(m.assembly_cost for m in members) <= result.budget_effective
    assert result.budget_remaining == result.budget_effective - result.budget_spent
    for role in ("veteran", "elite", "boss"):
        rule = next((r for r in config.roles if r.role == role), None)
        assert sum(m.role == role for m in members) >= (rule.min_count if rule else 0)


def test_seed_is_reproducible_and_does_not_use_combat_math(monkeypatch):
    from src.backend.features.character.runtime.gear_score import CharacterGearScoreCalculator

    monkeypatch.setattr(
        CharacterGearScoreCalculator,
        "calculate_from_calculated",
        lambda *a: pytest.fail("monster GS must not be evaluated"),
    )
    service = MonsterEncounterSelectionService()
    assert service.select(order(player_gear_score=500)) == service.select(order(player_gear_score=500))


def test_override_replaces_builtin_and_exact_core():
    result = MonsterEncounterSelectionService().select(order(profile_override=override(100, {"veteran": 2})))
    assert result.status == "selected"
    assert result.profile_source == "external" and result.profile_id == "test" and result.variant_id == "ranks"
    assert sum(m.role == "veteran" for m in result.selection.members) == 2
    assert all(m.role in ("veteran", "minion") for m in result.selection.members)


def test_unaffordable_core_rejects_without_budget_increase():
    result = MonsterEncounterSelectionService().select(order(profile_override=override(1, {"elite": 1})))
    assert result.status == "rejected"
    assert any(r.code == "budget_insufficient" for a in result.attempts for r in a.reasons)


def test_group_rejects_even_with_external_profile():
    result = MonsterEncounterSelectionService().select(order(party_mode="group", profile_override=override()))
    assert result.reasons[0].code == "group_profile_unavailable"


@pytest.mark.parametrize("families", [[], ["goblin_tribe", "rat_swarm"]])
def test_exactly_one_family(families):
    with pytest.raises(ValidationError):
        order(family_ids=families)


def test_external_profile_bypasses_builtin_type_lookup():
    result = MonsterEncounterSelectionService().select(
        order(encounter_type="custom_event", profile_override=override())
    )
    assert result.status == "selected" and result.profile_source == "external"


def test_budget_rejection_reports_missing_core_instead_of_silent_substitution():
    from types import SimpleNamespace

    from src.backend.features.monsters.catalog.registry import get_catalog
    from src.backend.features.monsters.encounters.services.encounter_preparation_service import (
        MonsterEncounterPreparationService,
    )

    catalog = get_catalog()

    class MinionsOnly:
        def search(self, tier, filters):
            return SimpleNamespace(
                candidates=tuple(
                    m for m in catalog.members.values() if m.family_id == "goblin_tribe" and m.role == "minion"
                ),
                excluded=(),
            )

    service = MonsterEncounterSelectionService(
        preparation=MonsterEncounterPreparationService(candidate_search=MinionsOnly())
    )
    result = service.select(order(profile_override=override(100, {"elite": 1})))
    assert result.status == "rejected"
    assert result.attempts[0].reasons[0].code == "core_unavailable"


@pytest.mark.parametrize(
    "field,value", [("budget_spent", 0), ("budget_remaining", 999), ("profile_id", "wrong"), ("variant_id", "wrong")]
)
def test_result_rejects_inconsistent_budget_diagnostics(field, value):
    from src.backend.features.monsters.encounters.dto.result import MonsterEncounterSelectionDTO

    result = MonsterEncounterSelectionService().select(order())
    with pytest.raises(ValidationError):
        MonsterEncounterSelectionDTO.model_validate(result.model_dump() | {field: value})


def test_distinct_identity_states_keep_feasible_alternative_tiers():
    from src.backend.features.monsters.encounters.services.variant_pool import canonical_variants

    result = MonsterEncounterSelectionService().select(order())
    original = result.selection.assembly_input.configuration
    config = original.model_copy(
        update={
            "allow_repeated_members": False,
            "count": original.count.model_copy(update={"min_count": 2}),
            "minions": original.minions.model_copy(
                update={"base_points": 35, "effective_points": 35, "remaining_points": 35}
            ),
            "budget_base": 35,
            "budget_bonus": 0,
            "budget_effective": 35,
        }
    )
    base = next(m for m in result.preparation.candidates if m.role == "minion")
    pool = (
        base.model_copy(update={"member_id": "a", "assembly_cost": 20}),
        base.model_copy(update={"member_id": "a", "assembly_cost": 15, "tier": 1}),
        base.model_copy(update={"member_id": "b", "assembly_cost": 20}),
    )
    rosters = canonical_variants(config, pool)
    assert rosters
    assert all(len({member_id for member_id, tier in roster}) == len(roster) for roster in rosters)
    lookup = {(member.member_id, member.tier): member for member in pool}
    assert any(sum(lookup[ref].assembly_cost for ref in roster) == 35 for roster in rosters)


def test_external_profile_can_forbid_repeated_members():
    profile = override(1000)
    profile["allow_repeated_members"] = False
    result = MonsterEncounterSelectionService().select(order(profile_override=profile))
    assert result.status == "selected"
    assert len({m.member_id for m in result.selection.members}) == len(result.selection.members)
    assert len(result.selection.members) in (3, 4)
    profile["min_members"] = 5
    result = MonsterEncounterSelectionService().select(order(profile_override=profile))
    assert result.status == "rejected"
    assert any(r.code == "insufficient_distinct_members" for a in result.attempts for r in a.reasons)
