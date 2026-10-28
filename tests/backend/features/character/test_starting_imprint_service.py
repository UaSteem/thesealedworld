import pytest

from src.backend.features.character.resources.starting_imprints import (
    ATTRIBUTE_KEYS,
    STARTING_IMPRINTS,
    _attribute_values,
)
from src.backend.features.character.services import StartingImprintService

# Reviewed reference vectors, in ATTRIBUTE_KEYS order. Tests do not load var/ artifacts.
EXPECTED_ATTRIBUTES = {
    "starter_guard_01": (17, 14, 20, 12, 16, 13, 16, 13, 14),
    "starter_heavy_sword_guard_01": (17, 14, 20, 12, 16, 13, 16, 13, 14),
    "starter_mace_guard_01": (19, 13, 20, 12, 15, 14, 16, 12, 14),
    "starter_heavy_guard_01": (19, 13, 20, 12, 15, 14, 16, 12, 14),
    "starter_tactician_01": (18, 16, 19, 12, 15, 13, 16, 12, 14),
    "starter_heavy_tactician_01": (18, 16, 19, 12, 15, 13, 16, 12, 14),
    "starter_medium_breaker_01": (20, 13, 19, 12, 14, 13, 18, 12, 14),
    "starter_breaker_01": (20, 13, 19, 12, 14, 13, 18, 12, 14),
    "starter_rift_survivor_01": (19, 15, 18, 12, 14, 13, 17, 12, 15),
    "starter_heavy_rift_survivor_01": (19, 15, 18, 12, 14, 13, 17, 12, 15),
    "starter_dual_blades_01": (12, 20, 15, 15, 16, 13, 17, 13, 14),
    "starter_medium_dual_blades_01": (12, 20, 15, 15, 16, 13, 17, 13, 14),
    "starter_hunter_01": (12, 19, 16, 12, 16, 13, 18, 15, 14),
    "starter_archer_01": (13, 18, 16, 12, 15, 14, 18, 15, 14),
}


@pytest.mark.unit
@pytest.mark.parametrize("key,vector", EXPECTED_ATTRIBUTES.items())
def test_reviewed_starting_profile_is_materialized_exactly(key, vector):
    build = StartingImprintService().build(key)
    assert build.attributes == dict(zip(ATTRIBUTE_KEYS, vector, strict=True))
    assert sum(vector) == 135
    assert max(vector) - min(vector) <= 8
    assert all(len(set(vector[i : i + 3])) == 3 for i in (0, 3, 6))
    assert len(build.skill_xp) == 3
    assert tuple(build.skill_xp.values()) == (0.10, 0.075, 0.05)
    assert build.item_base_ids[-4:] == ("shirt", "pants", "boots", "belt")
    assert "amulet" not in build.item_base_ids
    assert set(build.primary_stats).issubset(ATTRIBUTE_KEYS)
    assert "endurance" in build.primary_stats


@pytest.mark.unit
def test_catalog_replaces_ten_with_fourteen_complete_styles():
    assert set(STARTING_IMPRINTS) == set(EXPECTED_ATTRIBUTES)
    service = StartingImprintService()
    compositions = []
    for key in EXPECTED_ATTRIBUTES:
        build = service.build(key)
        compositions.append((build.combat_style, build.armor_pack))
    assert len(set(compositions)) == 14
    for old_key in ("starter_dual_sword_01", "starter_dual_mace_01"):
        with pytest.raises(ValueError, match="Unknown starting imprint"):
            service.build(old_key)


@pytest.mark.unit
@pytest.mark.parametrize("key", ["starter_mace_guard_01", "starter_heavy_guard_01"])
def test_mace_shield_uses_reviewed_plain_shield(key):
    assert StartingImprintService().build(key).item_base_ids[:2] == ("mace", "shield")


@pytest.mark.unit
def test_random_start_selection_covers_all_styles_and_is_reproducible():
    service = StartingImprintService()
    observed = {service.build_random(seed=str(seed)).imprint_key for seed in range(250)}
    assert observed == set(EXPECTED_ATTRIBUTES)
    assert service.build_random(seed="new-body") == service.build_random(seed="new-body")


@pytest.mark.unit
def test_weight_selection_still_uses_authored_style_priorities():
    service = StartingImprintService()
    assert service.build_for_weights(None).imprint_key == "starter_guard_01"
    assert service.build_for_weights({"w_endurance": 10}).imprint_key == "starter_guard_01"
    assert service.build_for_weights({"w_agility": 10, "w_perception": 8}).imprint_key == "starter_dual_blades_01"


@pytest.mark.unit
@pytest.mark.parametrize(
    "vector,message",
    [
        ((17, 14, 19, 12, 16, 13, 16, 13, 14), "total 135"),
        ((18, 14, 20, 11, 16, 13, 16, 13, 14), "spread"),
        ((17, 17, 17, 12, 16, 13, 16, 13, 14), "distinct"),
        ((17.0, 14, 20, 12, 16, 13, 16, 13, 14), "positive integers"),
    ],
)
def test_attribute_contract_rejects_invalid_manual_profiles(vector, message):
    with pytest.raises(ValueError, match=message):
        _attribute_values(**dict(zip(ATTRIBUTE_KEYS, vector, strict=True)))
