import hashlib
import json
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from src.backend.features.monsters.catalog import registry
from src.backend.features.monsters.catalog.contracts import thaw_catalog_value
from src.backend.features.monsters.catalog.indexes import MonsterCatalog
from src.backend.features.monsters.catalog.registry import (
    get_all_family_configs,
    get_catalog,
)
from src.backend.features.monsters.catalog.validation import CatalogValidationError, validate_catalog

MECHANICS_DIGESTS = {
    "rat_swarm": "8410910f6fcaac75373139a7496b78e8cb2991fd01c2672a14f01f5f363c2833",
    "wolf_pack": "032312f9fc55b6c4ff06bef07eaba2a8708df0dfbc6535e657cd59a2ed5aadf7",
    "bandit_gang": "26381b9dc37411ce36b2fdfc4e723da728987e87ddb9e8e5aea86de1fc6d3956",
    "goblin_tribe": "0207992c941183e6d817c67a58b7ecb5aa69ab48508cc48e84c16f5f09152ad5",
    "anchor_sovereigns": "a30d56119b767070be294a4b71871b0debccd8058a8a92f1b3483240534d5cd3",
}


def test_original_resources_and_retained_stats_are_preserved():
    from src.backend.features.monsters.catalog.contracts import MonsterFamilyDTO
    from src.backend.features.monsters.catalog.families.bandits import BANDITS_FAMILY
    from src.backend.features.monsters.catalog.families.goblins import GOBLINS_FAMILY
    from src.backend.features.monsters.catalog.families.rats import RATS_FAMILY
    from src.backend.features.monsters.catalog.families.system.anchor_sovereigns import ANCHOR_SOVEREIGNS_FAMILY
    from src.backend.features.monsters.catalog.families.wolves import WOLVES_FAMILY

    sources = [RATS_FAMILY, WOLVES_FAMILY, GOBLINS_FAMILY, BANDITS_FAMILY, ANCHOR_SOVEREIGNS_FAMILY]
    assert {
        source["id"]: hashlib.sha256(json.dumps(MonsterFamilyDTO.model_validate(source).model_dump(), sort_keys=True).encode()).hexdigest()
        for source in sources
    } == MECHANICS_DIGESTS
    aliases = {"pack_huntmaster": "winter_maw", "burrow_guard": "plague_rat", "ironfang": "rotfang", "heavy_rat": "blight_carrier"}
    for source in sources:
        old = MonsterFamilyDTO.model_validate(source)
        for variant_id, member in get_all_family_configs()[source["id"]].variants.items():
            original = old.variants[aliases.get(variant_id, variant_id)]
            expected_stats = dict(original.base_stats)
            # Approved goblin minion balance; historical resources remain frozen.
            if source["id"] == "goblin_tribe" and variant_id in {
                "goblin_scavenger", "goblin_sparkpick", "goblin_sneak", "goblin_cutter"
            }:
                values = {
                    "goblin_scavenger": (9, 11, 9, 8, 6, 6, 10, 5, 6),
                    "goblin_sparkpick": (10, 12, 10, 8, 6, 7, 9, 6, 6),
                    "goblin_sneak": (9, 14, 9, 8, 6, 7, 12, 5, 7),
                    "goblin_cutter": (11, 13, 11, 8, 6, 8, 11, 5, 7),
                }[variant_id]
                expected_stats = dict(zip((
                    "strength", "agility", "endurance", "intellect", "memory", "mental",
                    "perception", "projection", "prediction",
                ), values, strict=True))
            assert member.base_stats.model_dump() == expected_stats
            assert member.fixed_loadout == original.fixed_loadout
            assert member.skills == original.skills
            assert (member.min_tier, member.max_tier, member.spawn_weight) == (original.min_tier, original.max_tier, original.spawn_weight)


def test_complete_clan_membership_and_system_spawning():
    catalog = get_catalog()
    assert len(catalog.families) == len(catalog.clans) == 6
    for family in catalog.families.values():
        clan = catalog.clans[family.clan_ids[0]]
        assert clan.family_id == family.id
        for member_id in clan.member_ids:
            member = catalog.members[member_id]
            assert member.family_id == family.id
            assert member.clan_id == clan.id
            assert member.id != member.variant_id
    assert not catalog.clans["anchor_sovereigns.base"].normal_spawn
    assert "anchor_sovereigns.base" not in {c.id for c in catalog.find_clans()}
    assert {c.family_id for c in catalog.find_clans(tags={"wolf"})} == {"wolf_pack"}


def test_catalog_and_nested_mechanics_are_immutable():
    catalog = get_catalog()
    member = catalog.members["wolf_pack.base.cub"]
    with pytest.raises(FrozenInstanceError):
        member.name = "Changed"
    with pytest.raises(TypeError):
        member.mechanics["base_stats"]["strength"] = 999
    with pytest.raises(TypeError):
        catalog.members[member.id] = member
    legacy = get_all_family_configs()
    legacy["wolf_pack"].variants["cub"].base_stats.strength = 999
    assert get_all_family_configs()["wolf_pack"].variants["cub"].base_stats.strength != 999


def test_validation_rejects_duplicates_and_broken_membership():
    catalog = get_catalog()
    families = tuple(catalog.families.values())
    clans = tuple(catalog.clans.values())
    members = tuple(catalog.members.values())
    with pytest.raises(CatalogValidationError, match="duplicate family"):
        validate_catalog((*families, families[0]), clans, members)
    with pytest.raises(CatalogValidationError, match="missing member"):
        validate_catalog(families, (replace(clans[0], member_ids=("missing",)), *clans[1:]), members)
    with pytest.raises(CatalogValidationError, match="clan membership"):
        validate_catalog(families, clans, (replace(members[0], clan_id=clans[1].id), *members[1:]))


def test_authored_assets_are_local_references_not_s3_or_database_ids():
    catalog = get_catalog()
    for member in catalog.members.values():
        if member.image is not None:
            assert member.image.source_path.startswith("assets/monster_defaults/")
            assert member.image.asset_id
            assert not member.image.source_path.startswith("http")
            assert Path(member.image.source_path).is_file()
    assert catalog.members["wolf_pack.base.alpha_prime"].name == "Фенрир"
    assert "wolf_pack.base.winter_maw" not in catalog.members
    assert "wolf_pack.base.blood_howl" not in catalog.members
    hunter = catalog.members["wolf_pack.base.pack_huntmaster"]
    assert hunter.name == "Вожак-загонщик"
    assert hunter.image.source_path.endswith("pack_huntmaster-v1.png")
    assert not {"ice", "blood", "elemental", "vampiric"} & hunter.tags
    assert len(catalog.clans["wolf_pack.base"].member_ids) == 11
    assert catalog.members["goblin_tribe.base.goblin_sneak"].image.source_path.endswith("-face-v1.png")


def test_additional_clan_does_not_change_legacy_base_lookup(monkeypatch):
    catalog = get_catalog()
    family = catalog.families["wolf_pack"]
    base = catalog.clans["wolf_pack.base"]
    other_id = "wolf_pack.test"
    # A subtype need not repeat the entire family hierarchy or roster.
    cub = catalog.members[base.member_ids[0]]
    roster = (replace(cub, id=f"{other_id}.{cub.variant_id}", clan_id=other_id),)
    other = replace(base, id=other_id, member_ids=tuple(m.id for m in roster))
    extended = MonsterCatalog(
        {**catalog.families, family.id: replace(family, clan_ids=(*family.clan_ids, other_id))},
        {**catalog.clans, other.id: other},
        {**catalog.members, **{m.id: m for m in roster}},
    )
    monkeypatch.setattr(registry, "_CATALOG", extended)
    assert registry.get_family_config("wolf_pack").variants.keys() == {
        catalog.members[mid].variant_id for mid in base.member_ids
    }
    assert registry.get_monster_template("cub").id == "cub"
    assert registry.get_catalog_member("wolf_pack.test.cub") is roster[0]
    assert registry.get_catalog_member("missing") is None
    assert extended.find_clans(tags={"wolf", "missing"}) == ()


@pytest.mark.parametrize("damage", ["stats", "tier", "role"])
def test_direct_definitions_cannot_bypass_mechanics_validation(damage):
    catalog = get_catalog()
    members = tuple(catalog.members.values())
    member = members[0]
    mechanics = thaw_catalog_value(member.mechanics)
    changes = {}
    if damage == "stats":
        mechanics["base_stats"]["strength"] = -1
    elif damage == "tier":
        mechanics["max_tier"] = 99
        changes["max_tier"] = 99
    else:
        mechanics["role"] = "invalid"
        changes["role"] = "invalid"
    invalid = replace(member, mechanics=mechanics, **changes)
    with pytest.raises(CatalogValidationError, match="invalid member mechanics"):
        validate_catalog(tuple(catalog.families.values()), tuple(catalog.clans.values()), (invalid, *members[1:]))


def test_duplicate_variant_ids_in_clan_are_rejected():
    catalog = get_catalog()
    families = tuple(catalog.families.values())
    clans = tuple(catalog.clans.values())
    members = tuple(catalog.members.values())
    duplicate = replace(members[0], id=members[0].id + ".duplicate")
    clan = replace(clans[0], member_ids=(*clans[0].member_ids, duplicate.id))
    with pytest.raises(CatalogValidationError, match="duplicate clan variant"):
        validate_catalog(families, (clan, *clans[1:]), (*members, duplicate))


def test_catalog_loads_without_database_clients_network_or_json_files():
    script = """
import builtins
import socket
from pathlib import Path
original_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name.split(".")[0] in {"sqlalchemy", "pymongo", "motor", "redis"}:
        raise AssertionError("Persistence client imported: " + name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
original_open = builtins.open
def guarded_open(file, *args, **kwargs):
    if str(file).lower().endswith(".json"):
        raise AssertionError("JSON file read: " + str(file))
    return original_open(file, *args, **kwargs)
builtins.open = guarded_open
original_path_open = Path.open
def guarded_path_open(path, *args, **kwargs):
    if path.suffix.lower() == ".json":
        raise AssertionError("JSON file read: " + str(path))
    return original_path_open(path, *args, **kwargs)
Path.open = guarded_path_open
def forbidden_connection(*args, **kwargs):
    raise AssertionError("Network connection attempted")
socket.create_connection = forbidden_connection
socket.socket.connect = forbidden_connection
from src.backend.features.monsters.catalog.registry import get_catalog
assert len(get_catalog().families) == 6
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
