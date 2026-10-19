"""Authored encounter prices are independent of combat math and equipment."""

from dataclasses import replace

import pytest

from src.backend.features.monsters.catalog.bootstrap import MonsterCatalogBootstrapService
from src.backend.features.monsters.catalog.families.goblin_catalog.family import GOBLIN_FAMILY
from src.backend.features.monsters.catalog.indexes import MonsterCatalog
from src.backend.features.monsters.catalog.nested_contracts import resolve_family
from src.backend.features.monsters.catalog.registry import get_catalog


@pytest.mark.parametrize(
    "family_id,prices",
    (
        ("rat_swarm", (11, 23, 30, 45)),
        ("goblin_tribe", (15, 23, 30, 45)),
        ("wolf_pack", (18, 23, 30, 45)),
        ("bandit_gang", (23, 23, 30, 45)),
        ("anchor_sovereigns", (40, 60, 80, 120)),
        ("golem_foundry", (40, 23, 30, 45)),
    ),
)
def test_all_authored_members_have_explicit_prices(family_id, prices):
    expected = dict(zip(("minion", "veteran", "elite", "boss"), prices, strict=True))
    members = [member for member in get_catalog().members.values() if member.family_id == family_id]
    assert members
    for member in members:
        minion_prices = {"goblin_scavenger": 7, "goblin_sparkpick": 8, "goblin_sneak": 9, "goblin_cutter": 10}
        price = (
            minion_prices[member.variant_id]
            if family_id == "goblin_tribe" and member.role == "minion"
            else expected[member.role]
        )
        if family_id == "rat_swarm" and member.role == "minion":
            price = {"sewer_rat": 5, "scavenger_rat": 6, "swarm_rat": 7}[member.variant_id]
        if family_id == "wolf_pack" and member.role == "minion":
            price = {"cub": 10, "runner": 12, "mangy_biter": 14}[member.variant_id]
        if family_id == "bandit_gang" and member.role == "minion":
            price = {"bandit_thug": 13, "bandit_lookout": 14, "bandit_poacher": 15, "bandit_knife_rat": 16}[
                member.variant_id
            ]
        if family_id == "golem_foundry" and member.role == "minion":
            price = {"stone_thrower": 13, "stone_worker": 14, "stone_sentry": 15, "stone_ram": 16}[member.variant_id]
        assert member.assembly_cost == price
        assert "assembly_cost" not in member.mechanics


@pytest.mark.parametrize("invalid", (0, -1, True, 1.5, "15", None))
def test_read_member_and_authored_basis_require_positive_strict_integer(invalid):
    member = next(member for member in get_catalog().members.values() if member.family_id == "goblin_tribe")
    with pytest.raises(ValueError, match="Assembly cost"):
        replace(member, assembly_cost=invalid)
    with pytest.raises(ValueError, match="Assembly cost"):
        replace(GOBLIN_FAMILY.bases[0], assembly_cost=invalid)


@pytest.mark.parametrize("invalid", (0, -1, True, 1.5, "15"))
def test_clan_price_override_requires_positive_strict_integer(invalid):
    with pytest.raises(ValueError, match="Assembly cost"):
        replace(GOBLIN_FAMILY.clans[0].members[0], assembly_cost=invalid)


def test_clan_member_can_override_price_without_changing_combat_data():
    clan = GOBLIN_FAMILY.clans[0]
    variant = replace(clan.members[0], assembly_cost=19)
    updated = replace(clan, members=(variant, *clan.members[1:]))
    _, _, before = resolve_family(GOBLIN_FAMILY)
    _, _, after = resolve_family(replace(GOBLIN_FAMILY, clans=(updated,)))
    assert before[0].assembly_cost == 9
    assert after[0].assembly_cost == 19
    assert before[0].mechanics == after[0].mechanics
    assert before[0].image == after[0].image
    assert before[1:] == after[1:]


def test_price_changes_member_cache_hash_without_changing_family_or_clan_hash():
    catalog = get_catalog()
    member = next(iter(catalog.members.values()))
    changed = MonsterCatalog(
        catalog.families,
        catalog.clans,
        {**catalog.members, member.id: replace(member, assembly_cost=member.assembly_cost + 1)},
    )
    before = MonsterCatalogBootstrapService(catalog).build()
    after = MonsterCatalogBootstrapService(changed).build()
    assert before.members[member.id].assembly_cost == member.assembly_cost
    assert after.members[member.id].assembly_cost == member.assembly_cost + 1
    assert before.version != after.version
    assert before.manifest.sections["members"] != after.manifest.sections["members"]
    for section in ("families", "clans"):
        assert before.manifest.sections[section] == after.manifest.sections[section]
