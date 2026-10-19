from dataclasses import FrozenInstanceError, replace

import pytest
from pydantic import ValidationError

from src.backend.features.monsters.catalog.authoring import define_base_clan
from src.backend.features.monsters.catalog.families.prepared_wolves import PREPARED_WOLVES_FAMILY
from src.backend.features.monsters.catalog.families.wolf_catalog.family import WOLF_FAMILY
from src.backend.features.monsters.catalog.nested_contracts import BaseStatsDTO, resolve_family
from src.backend.features.monsters.catalog.prepared import WOLVES
from src.backend.features.monsters.catalog.presentation import MEMBER_PRESENTATION
from src.backend.features.monsters.catalog.validation import validate_catalog


def test_resolved_wolves_preserve_every_existing_field():
    old_family, old_clan, old_members = define_base_clan(
        PREPARED_WOLVES_FAMILY,
        family_name="Волки",
        clan_id="wolf_pack.base",
        clan_name="Базовая волчья стая",
        normal_spawn=True,
        presentation=MEMBER_PRESENTATION["wolf_pack"],
        assembly_costs={member.variant_id: member.assembly_cost for member in WOLVES[2]},
    )
    family, clan, members = WOLVES
    assert family.id == old_family.id
    assert family.mechanics == old_family.mechanics
    assert clan.member_ids == old_clan.member_ids
    assert clan.tags == old_clan.tags
    assert len(members) == 11
    for actual, previous in zip(members, old_members, strict=True):
        assert actual.base_stats == previous.base_stats
        from tests.backend.features.monsters.catalog.alpha_expectations import approved_mechanics

        expected = approved_mechanics("wolf_pack", actual.variant_id, {
            "fixed_loadout": dict(previous.fixed_loadout), "skills": list(previous.skills), "min_tier": 0,
        })
        assert dict(actual.fixed_loadout) == expected["fixed_loadout"]
        assert list(actual.skills) == expected["skills"]
        assert actual.image == previous.image
        assert previous.min_tier == 0  # Historical snapshot remains frozen.
        assert (actual.min_tier, actual.max_tier) == (1, previous.max_tier)
        assert actual.base_id == actual.variant_id


def test_new_clan_variant_reuses_stats_with_independent_skills_abilities_and_art():
    base_clan = WOLF_FAMILY.clans[0]
    ordinary = base_clan.members[0]
    alternate = replace(
        ordinary, id="ice_cub", name="Test ice cub", skills=(), ability_ids=("test_frost_bite",), image=None
    )
    alternate_clan = replace(base_clan, id="wolf_pack.test", tags=("test_ice",), members=(alternate,))
    family, clans, members = resolve_family(replace(WOLF_FAMILY, clans=(base_clan, alternate_clan)))
    assert family.clan_ids == ("wolf_pack.base", "wolf_pack.test")
    assert clans[1].member_ids == ("wolf_pack.test.ice_cub",)
    assert members[-1].base_stats == members[0].base_stats
    assert members[-1].fixed_loadout == members[0].fixed_loadout
    assert members[-1].base_id == members[0].base_id
    assert members[-1].skills == ()
    assert members[-1].ability_ids == ("test_frost_bite",)
    assert members[-1].image == WOLF_FAMILY.bases[0].default_image
    assert "test_ice" in members[-1].tags
    validate_catalog((family,), clans, members)


def test_definitions_and_nested_stats_are_immutable():
    with pytest.raises(FrozenInstanceError):
        WOLF_FAMILY.bases[0].spawn_weight = 10
    with pytest.raises(ValidationError):
        WOLF_FAMILY.bases[0].stats.strength = 10
    with pytest.raises(FrozenInstanceError):
        WOLF_FAMILY.traits.resource_version = 9
    with pytest.raises(ValidationError):
        WOLF_FAMILY.traits.loot_profile.materials = ()


def test_unknown_and_duplicate_references_fail_before_loading():
    clan = WOLF_FAMILY.clans[0]
    bad = replace(clan.members[0], base_id="missing")
    with pytest.raises(ValueError, match="Unknown member basis"):
        replace(WOLF_FAMILY, clans=(replace(clan, members=(bad,)),))
    with pytest.raises(ValueError, match="Duplicate member basis"):
        replace(WOLF_FAMILY, bases=(*WOLF_FAMILY.bases, WOLF_FAMILY.bases[0]))
    with pytest.raises(ValueError, match="Duplicate clan member"):
        replace(clan, members=(clan.members[0], clan.members[0]))
    with pytest.raises(ValueError, match="Duplicate clan"):
        replace(WOLF_FAMILY, clans=(clan, clan))


def test_stats_are_strictly_typed_and_validated():
    stats = WOLF_FAMILY.bases[0].stats.model_dump()
    with pytest.raises(ValidationError):
        BaseStatsDTO(**{**stats, "strength": -1})
    with pytest.raises(ValidationError):
        BaseStatsDTO(**{**stats, "strength": "15"})
    with pytest.raises(ValueError, match="Spawn weight"):
        replace(WOLF_FAMILY.bases[0], spawn_weight=0)


def test_active_wolf_catalog_does_not_load_historical_resources():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-c", "import sys; from src.backend.features.monsters.catalog.registry import get_catalog; assert len(get_catalog().clans['wolf_pack.base'].member_ids) == 11; assert 'src.backend.features.monsters.catalog.families.wolves' not in sys.modules; assert 'src.backend.features.monsters.catalog.families.prepared_wolves' not in sys.modules"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
