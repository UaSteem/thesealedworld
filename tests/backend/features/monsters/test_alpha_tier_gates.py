"""Authored alpha availability gates preserve historical saved equipment."""

from importlib import import_module

import pytest

from src.backend.features.monsters.catalog.prepared_equipment import (
    get_member_prepared_equipment,
    get_prepared_equipment,
    list_prepared_equipment,
)
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.instances.services.build_readiness import MonsterBuildReadinessService


@pytest.mark.parametrize(
    "family,minimum,count",
    [
        ("wolf_pack", 1, 11),
        ("bandit_gang", 1, 12),
        ("golem_foundry", 2, 12),
    ],
)
def test_alpha_gate_controls_public_equipment_and_readiness(family, minimum, count):
    catalog = get_catalog()
    members = [m for m in catalog.members.values() if m.family_id == family]
    assert len(members) == count
    assert {(m.min_tier, m.max_tier) for m in members} == {(minimum, 5)}
    assert set(list_prepared_equipment(family_id=family)) == {
        (m.variant_id, t) for m in members for t in range(minimum, 6)
    }
    readiness = MonsterBuildReadinessService()
    for member in members:
        for tier in (minimum, 5):
            kit = get_member_prepared_equipment(member=member, tier=tier)
            assert readiness.check(member=member, family=catalog.families[family], tier=tier, prepared=kit).ready
        for tier in range(minimum):
            with pytest.raises(LookupError):
                get_prepared_equipment(family_id=family, variant_id=member.variant_id, tier=tier)
            with pytest.raises(LookupError):
                get_member_prepared_equipment(member=member, tier=tier)
            report = readiness.check(member=member, family=catalog.families[family], tier=tier)
            assert not report.ready
            assert "tier_unavailable" in {issue.code for issue in report.issues}


@pytest.mark.parametrize(
    "package,family,count",
    [
        ("wolf_catalog", "wolf_pack", 66),
        ("bandit_catalog", "bandit_gang", 72),
    ],
)
def test_historical_saved_sets_remain_readable_only_through_raw_loader(package, family, count):
    loader = import_module(f"src.backend.features.monsters.catalog.families.{package}.equipment.prepared_loader")
    refs = loader.list_prepared_equipment()
    assert len(refs) == count
    historical = [(variant, tier) for variant, tier in refs if tier == 0]
    assert len(historical) == count // 6
    for variant, tier in historical:
        assert loader.get_prepared_equipment(variant, tier).tier == 0
        with pytest.raises(LookupError):
            get_prepared_equipment(family_id=family, variant_id=variant, tier=tier)


def test_t0_starter_members_remain_available():
    catalog = get_catalog()
    assert {m.family_id for m in catalog.members.values() if m.min_tier <= 0 <= m.max_tier} == {
        "goblin_tribe",
        "rat_swarm",
    }


@pytest.mark.parametrize(
    "damage", ["missing_active", "unknown_member", "unexpected_tier", "duplicate_input", "historical_payload"]
)
def test_historical_bandit_manifest_rejects_corruption(tmp_path, damage):
    import json
    from shutil import copytree

    from tools.monsters.prepare_family_equipment import default_output, validate

    output = tmp_path / "prepared"
    copytree(default_output("bandit_gang"), output)
    path = output / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if damage == "missing_active":
        relative = "bandit_thug/tier_1.py"
        del manifest["files"][relative]
        manifest["inputs"] = [x for x in manifest["inputs"] if x["path"] != relative]
    elif damage in {"unknown_member", "unexpected_tier"}:
        relative = "unknown/tier_0.py" if damage == "unknown_member" else "bandit_thug/tier_6.py"
        manifest["files"][relative] = "invalid"
    elif damage == "duplicate_input":
        manifest["inputs"].append(manifest["inputs"][0])
    else:
        payload = output / "bandit_thug/tier_0.py"
        payload.write_bytes(payload.read_bytes() + b"\n# tampered historical payload\n")
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError):
        validate(output, "bandit_gang")


def test_historical_bandit_manifest_validates_all_saved_sets():
    from tools.monsters.prepare_family_equipment import default_output, validate

    assert validate(default_output("bandit_gang"), "bandit_gang")["sets"] == 72
