import pytest
from pydantic import ValidationError

from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO


def test_order_keeps_composition_inside_monsters():
    order = MonsterEncounterOrderDTO(encounter_type="ordinary", location_tier=1, seed=7, family_ids=("goblin_tribe",))
    assert order.location_tier == 1
    assert set(order.model_dump()) == {
        "encounter_type",
        "location_tier",
        "family_ids",
        "seed",
        "difficulty",
        "party_mode",
        "player_gear_score",
        "profile_override",
    }
    for key, value in [
        ("tier", 1),
        ("roles", []),
        ("count", {}),
        ("gs", 200),
        ("clan_ids", []),
        ("required_tags", []),
        ("excluded_tags", []),
    ]:
        with pytest.raises(ValidationError):
            MonsterEncounterOrderDTO(**order.model_dump(), **{key: value})


@pytest.mark.parametrize("value", [True, "1", -1, 8])
def test_tier_is_strict_and_supported(value):
    with pytest.raises(ValidationError):
        MonsterEncounterOrderDTO(encounter_type="ordinary", location_tier=value, seed=7)


def test_order_seed_required():
    with pytest.raises(ValidationError):
        MonsterEncounterOrderDTO(encounter_type="ordinary", location_tier=1)
