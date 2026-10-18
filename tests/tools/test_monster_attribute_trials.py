from copy import deepcopy

import pytest
from tools.monsters.balance_probe.attribute_profiles import ALLOCATIONS
from tools.monsters.balance_probe.attribute_trials import build_variants, validate_allocation


def test_allocations_cover_all_starters_and_rebuild_only_attributes():
    from src.backend.features.combat.runtime.simulation.starting_imprint_actors import (
        DEFAULT_STARTER_SIMULATION_IMPRINTS,
    )

    assert set(ALLOCATIONS) == set(DEFAULT_STARTER_SIMULATION_IMPRINTS)
    original_plans = deepcopy(ALLOCATIONS)
    variants = build_variants(ALLOCATIONS)
    for identity, allocation in ALLOCATIONS.items():
        validate_allocation(allocation)
        old = variants[f"{identity}.original"]
        for suffix in ("uniform135", "tailored135"):
            new = variants[f"{identity}.{suffix}"]
            assert new["skills"] == old["skills"]
            assert new["equipment"] == old["equipment"]
            assert new["loadout"] == old["loadout"]
            assert new["input_context"]["symbiote"] == old["input_context"]["symbiote"]
            expected = dict.fromkeys(allocation, 15) if suffix == "uniform135" else allocation
            assert new["input_context"]["attributes"] == expected
            assert {key: value["base"] for key, value in new["raw"]["attributes"].items()} == expected
            assert new["preview_values"]["hp"] > 0
        assert old["input_context"]["attributes"] == allocation
    assert original_plans == ALLOCATIONS


@pytest.mark.parametrize(
    "change",
    [
        lambda a: a.update(strength=100),
        lambda a: a.pop("memory"),
        lambda a: a.update(strength=17.0),
        lambda a: a.update(mental=-1),
    ],
)
def test_invalid_attribute_budget_or_shape_is_rejected(change):
    allocation = deepcopy(next(iter(ALLOCATIONS.values())))
    change(allocation)
    with pytest.raises(ValueError):
        validate_allocation(allocation)
