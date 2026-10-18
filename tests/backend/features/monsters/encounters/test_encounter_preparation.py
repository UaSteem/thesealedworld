import pytest
from pydantic import ValidationError

from src.backend.features.monsters.encounters.dto.selection import (
    MonsterEncounterOrderDTO,
    MonsterSquadAssemblyInputDTO,
    MonsterSquadSelectionDTO,
)
from src.backend.features.monsters.encounters.services.encounter_preparation_service import (
    MonsterEncounterPreparationService,
)


def order(**kwargs):
    return MonsterEncounterOrderDTO(
        encounter_type="ordinary",
        difficulty="easy",
        location_tier=0,
        seed=12,
        **({"family_ids": ("goblin_tribe",), "player_gear_score": 36.326} | kwargs),
    )


def test_unknown_type_explicit_rejection_before_search():
    class Forbidden:
        def search(self, **kwargs):
            raise AssertionError("search must not run")

    result = MonsterEncounterPreparationService(candidate_search=Forbidden()).prepare(
        MonsterEncounterOrderDTO(encounter_type="unknown", location_tier=1, seed=1, family_ids=("goblin_tribe",))
    )
    assert result.status == "rejected"
    assert result.reasons[0].code == "unknown_encounter_type"


def test_empty_and_unready_distinguished():
    service = MonsterEncounterPreparationService()
    assert service.prepare(order(family_ids=("absent",))).reasons[0].code == "no_candidates"
    result = service.prepare(
        MonsterEncounterOrderDTO(encounter_type="ordinary", location_tier=7, family_ids=("goblin_tribe",), seed=1, player_gear_score=814.358)
    )
    assert result.reasons[0].code == "no_ready_candidates"
    assert result.excluded


def test_system_content_excluded():
    result = MonsterEncounterPreparationService().prepare(order())
    assert all("anchor" not in member.family_id for member in result.candidates)


def test_exception_not_disguised_as_rejection():
    class Broken:
        def search(self, **kwargs):
            raise RuntimeError("unexpected failure")

    with pytest.raises(RuntimeError, match="unexpected failure"):
        MonsterEncounterPreparationService(candidate_search=Broken()).prepare(order())


def test_internal_selection_checks_ready_pool_and_composition():
    result = MonsterEncounterPreparationService().prepare(order(family_ids=("goblin_tribe",)))
    config = result.configurations[0]
    context = MonsterSquadAssemblyInputDTO(
        order=result.order, admission=result.admission, configuration=config, candidates=result.candidates
    )
    minions = tuple(m for m in result.candidates if m.role == "minion")[: config.count.min_count]
    selected = MonsterSquadSelectionDTO(assembly_input=context, members=minions)
    assert selected.status == "selected"
    with pytest.raises(ValidationError, match="outside ready candidate pool"):
        MonsterSquadSelectionDTO(
            assembly_input=context, members=(minions[0].model_copy(update={"tier": 1}), *minions[1:])
        )
    with pytest.raises(ValidationError, match="outside configuration"):
        MonsterSquadSelectionDTO(assembly_input=context, members=())


def test_rolewise_admission_range_filters_ready_and_excluded_entries():
    from src.backend.features.monsters.encounters.dto.selection import MonsterAdmissionPolicyDTO, MonsterTierRuleDTO

    class RoleRanges:
        def resolve(self, tier):
            return MonsterAdmissionPolicyDTO(
                location_tier=tier,
                roles=(
                    MonsterTierRuleDTO(role="minion", min_tier=0, max_tier=0),
                    MonsterTierRuleDTO(role="boss", min_tier=7, max_tier=7),
                ),
            )

    result = MonsterEncounterPreparationService(admission=RoleRanges()).prepare(order(family_ids=("goblin_tribe",)))
    assert result.status == "prepared"
    assert len(result.candidates) == 4
    assert all(m.role == "minion" and m.tier == 0 for m in result.candidates)
    assert len(result.excluded) == 2
    assert all(report.tier == 7 for report in result.excluded)


def test_missing_configuration_is_explicit():
    class NoConfiguration:
        def supports(self, encounter_type):
            return True

        def profile(self, order):
            return None

        def resolve(self, **kwargs):
            return ()

    result = MonsterEncounterPreparationService(composition=NoConfiguration()).prepare(
        order(family_ids=("goblin_tribe",))
    )
    assert result.status == "rejected"
    assert result.reasons[0].code == "configuration_unavailable"
    assert result.candidates


def test_internal_duplicate_clan_and_role_constraints():
    from src.backend.features.monsters.encounters.dto.selection import MonsterSquadConfigurationDTO

    result = MonsterEncounterPreparationService().prepare(order(family_ids=("goblin_tribe",)))
    config = MonsterSquadConfigurationDTO.model_validate(
        {**result.configurations[0].model_dump(), "allow_repeated_members": False}
    )
    context = MonsterSquadAssemblyInputDTO(
        order=result.order, admission=result.admission, configuration=config, candidates=result.candidates
    )
    minions = tuple(m for m in result.candidates if m.role == "minion")[: config.count.min_count]
    with pytest.raises(ValidationError, match="repeated members"):
        MonsterSquadSelectionDTO(assembly_input=context, members=(minions[0],) * config.count.min_count)
    boss = next(m for m in result.candidates if m.role == "boss")
    with pytest.raises(ValidationError, match="violates configuration"):
        MonsterSquadSelectionDTO(assembly_input=context, members=(boss, *minions[1:]))
    other = minions[0].model_copy(update={"clan_id": "goblin_tribe.other"})
    context = context.model_copy(
        update={"candidates": (other, *(m for m in context.candidates if m.member_id != other.member_id))}
    )
    with pytest.raises(ValidationError, match="same clan"):
        MonsterSquadSelectionDTO(assembly_input=context, members=(other, *minions[1:]))
