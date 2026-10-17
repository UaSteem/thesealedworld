from dataclasses import replace

import pytest

from src.backend.features.monsters.catalog.contracts import thaw_catalog_value
from src.backend.features.monsters.catalog.prepared_equipment import get_prepared_equipment, list_prepared_equipment
from src.backend.features.monsters.catalog.registry import get_catalog


def inputs():
    catalog = get_catalog()
    member = catalog.members["goblin_tribe.base.goblin_spearman"]
    family = catalog.families[member.family_id]
    prepared = get_prepared_equipment(family_id=family.id, variant_id=member.variant_id, tier=3)
    return member, family, prepared


def check(member=None, family=None, prepared=None, tier=3):
    from src.backend.features.monsters.instances.services.build_readiness import MonsterBuildReadinessService

    m, f, p = inputs()
    return MonsterBuildReadinessService().check(
        member=member or m,
        family=family or f,
        tier=tier,
        prepared=prepared or p,
    )


@pytest.mark.parametrize("family_id", ("goblin_tribe", "wolf_pack", "rat_swarm", "bandit_gang"))
def test_all_existing_prepared_members_are_ready(family_id):
    from src.backend.features.monsters.instances.services.build_readiness import MonsterBuildReadinessService

    catalog = get_catalog()
    for variant, tier in list_prepared_equipment(family_id=family_id):
        member = catalog.members[f"{family_id}.base.{variant}"]
        report = MonsterBuildReadinessService().check(member=member, family=catalog.families[family_id], tier=tier)
        assert report.ready, (member.id, tier, report.issues)


@pytest.mark.parametrize("tier", (True, -1, 8, 1.5, "3"))
def test_unsupported_tier_has_explicit_reason(tier):
    report = check(tier=tier)
    assert not report.ready
    assert "unsupported_tier" in {i.code for i in report.issues}


def test_member_tier_window_is_enforced():
    member, _, _ = inputs()
    report = check(member=replace(member, min_tier=4))
    assert "tier_unavailable" in {i.code for i in report.issues}


@pytest.mark.parametrize(
    "field,value",
    (
        ("clan_id", "goblin_tribe.other"),
        ("variant_id", "other"),
        ("family_id", "bandit_gang"),
        ("role", "boss"),
        ("equipment_set_id", "wrong"),
        ("tier", 2),
    ),
)
def test_foreign_or_wrong_equipment_is_rejected(field, value):
    _, _, prepared = inputs()
    report = check(prepared=prepared.model_copy(update={field: value}))
    assert "equipment_identity_mismatch" in {i.code for i in report.issues}


def test_missing_equipment_slot_is_rejected():
    _, _, prepared = inputs()
    report = check(prepared=prepared.model_copy(update={"items": prepared.items[:-1]}))
    assert "equipment_slots_mismatch" in {i.code for i in report.issues}


def test_unknown_skill_and_ability_are_reported_together():
    member, _, _ = inputs()
    mechanics = thaw_catalog_value(member.mechanics)
    mechanics["skills"] = ["skill_missing"]
    report = check(member=replace(member, mechanics=mechanics, ability_ids=("missing_ability",)))
    assert {"unknown_skill", "unknown_ability"} <= {i.code for i in report.issues}


def test_builder_rejects_unready_content_before_math(monkeypatch):
    from src.backend.features.monsters.instances.services.build_readiness import MonsterBuildNotReadyError
    from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder

    member, family, prepared = inputs()

    def forbidden(*args, **kwargs):
        raise AssertionError("Unready content must fail before calculations")

    monkeypatch.setattr(MonsterInstanceBuilder, "_calculate", forbidden)
    with pytest.raises(MonsterBuildNotReadyError) as error:
        MonsterInstanceBuilder().build(member=replace(member, min_tier=4), family=family, prepared=prepared)
    assert error.value.report.member_id == member.id
    assert not error.value.report.ready


def test_known_declared_ability_reaches_both_projections():
    from src.backend.features.game_catalog.combat.resources.abilities import get_all_ability_catalog_entries
    from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder

    member, family, prepared = inputs()
    ability_id = get_all_ability_catalog_entries()[0].technical.ability_id
    member = replace(member, ability_ids=(ability_id,))
    assert check(member=member).ready
    built = MonsterInstanceBuilder().build(member=member, family=family, prepared=prepared)
    assert ability_id in built.equipped.loadout["known_abilities"]
    assert ability_id in built.baseline.loadout["known_abilities"]


def test_missing_clan_equipment_is_a_report_not_a_fallback(monkeypatch):
    from src.backend.features.monsters.instances.services import build_readiness

    member, family, _ = inputs()

    def unavailable(**kwargs):
        raise LookupError("No set for the requested clan")

    monkeypatch.setattr(build_readiness, "get_member_prepared_equipment", unavailable)
    report = build_readiness.MonsterBuildReadinessService().check(member=member, family=family, tier=3)
    assert not report.ready
    assert [i.code for i in report.issues] == ["equipment_unavailable"]
    assert "requested clan" in report.issues[0].message


@pytest.mark.parametrize(
    "damage,code",
    (
        ("base", "unknown_item_base"),
        ("material", "unknown_material"),
        ("natural", "unknown_natural_equipment"),
        ("skill", "unknown_skill"),
    ),
)
def test_broken_item_catalog_references_are_reported(damage, code):
    _, _, prepared = inputs()
    item = prepared.items[0].model_copy(deep=True)
    if damage == "base":
        item.base_id = "missing_base"
    elif damage == "material":
        item.generation.material_id = "missing_material"
    elif damage == "natural":
        item.generation.natural_key = "missing_natural_key"
    else:
        item.combat.related_skill = "skill_missing"
    report = check(prepared=prepared.model_copy(update={"items": (item, *prepared.items[1:])}))
    assert code in {i.code for i in report.issues}


def test_noncombat_skill_is_not_silently_discarded():
    member, _, _ = inputs()
    mechanics = thaw_catalog_value(member.mechanics)
    mechanics["skills"] = ["skill_scouting"]
    report = check(member=replace(member, mechanics=mechanics))
    assert "unsupported_skill" in {i.code for i in report.issues}


def test_check_is_independent_of_combat_calculations(monkeypatch):
    from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder

    def forbidden(*args, **kwargs):
        raise AssertionError("Readiness must not calculate an actor")

    monkeypatch.setattr(MonsterInstanceBuilder, "_calculate", forbidden)
    assert check().ready
