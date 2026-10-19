import pytest

from src.backend.features.monsters.catalog.registry import get_family_config, get_starter_family_ids
from src.backend.features.monsters.catalog.resources.stat_ladders import (
    ATTRIBUTE_LADDER,
    ORGANIZATION_ATTRIBUTE_OFFSETS,
    ROLE_ATTRIBUTE_BASE,
    role_attribute_base,
)

CALIBRATED_GOBLIN_MINIONS = {
    "goblin_scavenger": (9, 11, 9, 8, 6, 6, 10, 5, 6),
    "goblin_sparkpick": (10, 12, 10, 8, 6, 7, 9, 6, 6),
    "goblin_sneak": (9, 14, 9, 8, 6, 7, 12, 5, 7),
    "goblin_cutter": (11, 13, 11, 8, 6, 8, 11, 5, 7),
}
CALIBRATED_RAT_ATTRIBUTES = {'sewer_rat': (7, 10, 7, 3, 4, 6, 8, 3, 5), 'scavenger_rat': (9, 10, 8, 4, 4, 6, 8, 3, 5), 'swarm_rat': (8, 12, 8, 4, 6, 5, 9, 3, 7), 'tunnel_rat': (13, 15, 14, 9, 8, 11, 12, 7, 10), 'pack_rat': (14, 13, 15, 10, 8, 11, 12, 7, 9), 'screecher': (12, 15, 13, 10, 8, 11, 14, 7, 9), 'burrow_guard': (15, 14, 17, 11, 10, 13, 12, 9, 8), 'ironfang': (17, 15, 14, 11, 10, 12, 13, 8, 9), 'heavy_rat': (15, 13, 17, 11, 10, 14, 12, 9, 8), 'rat_brute': (23, 21, 24, 16, 15, 22, 20, 19, 18), 'brood_alpha': (22, 24, 23, 19, 16, 20, 21, 18, 15), 'rat_king': (23, 16, 24, 19, 18, 22, 21, 20, 15)}


@pytest.mark.unit
def test_starter_monster_stats_use_role_ladder_contract() -> None:
    expected_ladder = sorted(ATTRIBUTE_LADDER)

    for family_id in get_starter_family_ids():
        family = get_family_config(family_id)
        assert family is not None

        for variant in family.variants.values():
            role_base = role_attribute_base(variant.role, family.organization_type)
            values = variant.base_stats.model_dump(mode="json").values()
            if family_id == "golem_foundry":
                from tests.backend.features.monsters.catalog.alpha_expectations import GOLEM_STATS

                assert tuple(variant.base_stats.model_dump(mode="json").values()) == GOLEM_STATS[variant.id]
                continue
            if family_id == "rat_swarm" and variant.id in CALIBRATED_RAT_ATTRIBUTES:
                assert tuple(values) == CALIBRATED_RAT_ATTRIBUTES[variant.id]
                continue
            if family_id == "goblin_tribe" and variant.id in CALIBRATED_GOBLIN_MINIONS:
                assert tuple(values) == CALIBRATED_GOBLIN_MINIONS[variant.id]
                continue
            assert sorted(value - role_base for value in values) == expected_ladder


@pytest.mark.unit
def test_starter_monster_role_stat_totals_include_organization_mass_offset() -> None:
    expected_neutral_totals = {
        "minion": 99,
        "veteran": 108,
        "elite": 117,
        "boss": 162,
    }

    for family_id in get_starter_family_ids():
        family = get_family_config(family_id)
        assert family is not None

        for variant in family.variants.values():
            if family_id == "golem_foundry":
                from tests.backend.features.monsters.catalog.alpha_expectations import GOLEM_STATS

                assert tuple(variant.base_stats.model_dump(mode="json").values()) == GOLEM_STATS[variant.id]
                continue
            if family_id == "rat_swarm" and variant.id in CALIBRATED_RAT_ATTRIBUTES:
                assert sum(variant.base_stats.model_dump(mode="json").values()) == sum(
                    CALIBRATED_RAT_ATTRIBUTES[variant.id]
                )
                continue
            if family_id == "goblin_tribe" and variant.id in CALIBRATED_GOBLIN_MINIONS:
                assert sum(variant.base_stats.model_dump(mode="json").values()) == sum(
                    CALIBRATED_GOBLIN_MINIONS[variant.id]
                )
                continue
            organization_offset = 0 if variant.role == "boss" else ORGANIZATION_ATTRIBUTE_OFFSETS[family.organization_type]
            assert (
                sum(variant.base_stats.model_dump(mode="json").values())
                == expected_neutral_totals[variant.role] + organization_offset * len(ATTRIBUTE_LADDER)
            )


@pytest.mark.unit
def test_monster_role_bases_are_player_baseline_offsets() -> None:
    assert ROLE_ATTRIBUTE_BASE == {
        "minion": 6,
        "veteran": 7,
        "elite": 8,
        "boss": 13,
    }
    assert ORGANIZATION_ATTRIBUTE_OFFSETS == {
        "swarm": -2,
        "horde": -1,
        "pack": 0,
        "gang": 1,
        "solitary": 2,
    }
    assert role_attribute_base("minion", "swarm") == 4
    assert role_attribute_base("minion", "gang") == 7
    assert role_attribute_base("elite", "horde") == 7
    assert role_attribute_base("boss", "swarm") == 13
