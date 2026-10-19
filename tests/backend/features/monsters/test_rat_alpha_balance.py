import pytest

from src.backend.features.monsters.catalog.prepared_equipment import get_member_prepared_equipment
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.policies.composition import MonsterCompositionPolicyResolver

EXPECTED = {
    "sewer_rat": (5, (7, 10, 7, 3, 4, 6, 8, 3, 5)),
    "scavenger_rat": (6, (9, 10, 8, 4, 4, 6, 8, 3, 5)),
    "swarm_rat": (7, (8, 12, 8, 4, 6, 5, 9, 3, 7)),
}
EXPECTED_HP = {
    "scavenger_rat/tier_0.py:amulet": 1,
    "scavenger_rat/tier_1.py:amulet": 2,
    "scavenger_rat/tier_1.py:chest_armor": 2,
    "scavenger_rat/tier_2.py:amulet": 4,
    "scavenger_rat/tier_2.py:chest_armor": 4,
    "scavenger_rat/tier_3.py:chest_armor": 8,
    "scavenger_rat/tier_4.py:amulet": 16,
    "scavenger_rat/tier_4.py:chest_armor": 14,
    "scavenger_rat/tier_5.py:amulet": 26,
    "scavenger_rat/tier_5.py:chest_armor": 26,
    "sewer_rat/tier_0.py:amulet": 1,
    "sewer_rat/tier_1.py:amulet": 2,
    "sewer_rat/tier_1.py:chest_armor": 2,
    "sewer_rat/tier_2.py:amulet": 4,
    "sewer_rat/tier_2.py:chest_armor": 4,
    "sewer_rat/tier_3.py:amulet": 9,
    "sewer_rat/tier_3.py:chest_armor": 7,
    "sewer_rat/tier_4.py:amulet": 15,
    "sewer_rat/tier_4.py:chest_armor": 14,
    "sewer_rat/tier_5.py:amulet": 26,
    "sewer_rat/tier_5.py:chest_armor": 25,
    "swarm_rat/tier_0.py:amulet": 1,
    "swarm_rat/tier_1.py:amulet": 2,
    "swarm_rat/tier_1.py:chest_armor": 2,
    "swarm_rat/tier_2.py:chest_armor": 4,
    "swarm_rat/tier_3.py:amulet": 8,
    "swarm_rat/tier_3.py:chest_armor": 7,
    "swarm_rat/tier_4.py:chest_armor": 15,
    "swarm_rat/tier_5.py:amulet": 29,
    "swarm_rat/tier_5.py:chest_armor": 25,
}


@pytest.mark.parametrize("variant", EXPECTED)
def test_rat_minions_have_provisional_swarm_cost_and_base(variant):
    member = get_catalog().members[f"rat_swarm.base.{variant}"]
    cost, values = EXPECTED[variant]
    assert member.assembly_cost == cost
    assert tuple(member.base_stats.values()) == values


@pytest.mark.parametrize("tier", range(6))
def test_prepared_rat_curation_uses_correct_hand_and_minion_hp(tier):
    members = [m for m in get_catalog().members.values() if m.family_id == "rat_swarm"]
    assert len(members) == 12
    for member in members:
        prepared = get_member_prepared_equipment(member=member, tier=tier)
        for item in prepared.items:
            data = item.model_dump(mode="json")
            bonuses = data["combat"]["bonuses"]
            affixes = data["generation"]["affixes"]
            if item.slot == "off_hand" and item.item_type == "weapon":
                assert "main_hand_accuracy" not in bonuses
            if member.role == "minion":
                assert "thorns_damage_flat" not in bonuses
                assert not any(a["affix_id"] == "thorns_damage_bonus" for a in affixes)
                if "hp" in bonuses:
                    expected = EXPECTED_HP[f"{member.variant_id}/tier_{tier}.py:{item.slot}"]
                    assert float(bonuses["hp"]) == expected
                    assert next(a["value"] for a in affixes if a["affix_id"] == "hp_bonus") == expected


@pytest.mark.parametrize("kind", ("ordinary", "patrol", "guard", "leader"))
@pytest.mark.parametrize("difficulty", ("easy", "normal", "hard"))
def test_builtin_rat_whole_squad_limits(kind, difficulty):
    order = MonsterEncounterOrderDTO(
        encounter_type=kind,
        difficulty=difficulty,
        location_tier=0,
        family_ids=("rat_swarm",),
        seed=1,
        player_gear_score=36.326,
    )
    profile = MonsterCompositionPolicyResolver().profile(order)
    assert (profile.min_members, profile.max_members) == (4, 8)
    external = profile.model_copy(update={"min_members": 2, "max_members": 6})
    assert (
        MonsterCompositionPolicyResolver().profile(order.model_copy(update={"profile_override": external})) == external
    )


def _unmodified_equipment_fingerprint(payloads):
    import hashlib
    import json
    from copy import deepcopy

    payloads = deepcopy(payloads)
    for data in payloads.values():
        if data["role"] == "minion":
            data["items"] = [item for item in data["items"] if item["slot"] != "off_hand"]
        for item in data["items"]:
            bonuses = item["combat"]["bonuses"]
            generation = item["generation"]
            if data["role"] == "minion":
                for key in ("hp", "thorns_damage_flat", "thorns_damage_bonus"):
                    bonuses.pop(key, None)
                generation["affixes"] = [
                    a for a in generation["affixes"] if a["affix_id"] not in ("hp_bonus", "thorns_damage_bonus")
                ]
                if generation["natural_key"] == "rat_light_hide":
                    generation["affix_bundle_ids"] = []
                    item["combat"]["tags"] = [
                        t for t in item["combat"]["tags"] if t not in {"spiked", "reflective", "punishing", "thorns"}
                    ]
            if item["slot"] == "off_hand" and item["item_type"] == "weapon":
                bonuses.pop("main_hand_accuracy", None)
                bonuses.pop("off_hand_accuracy", None)
                generation["affixes"] = [
                    a for a in generation["affixes"] if a["affix_id"] not in ("weapon_accuracy", "off_hand_accuracy")
                ]
    return hashlib.sha256(json.dumps(payloads, sort_keys=True).encode()).hexdigest()


def test_all_72_prepared_sets_preserve_identity_power_skills_and_other_bonuses():
    payloads = {}
    for member in get_catalog().members.values():
        if member.family_id != "rat_swarm":
            continue
        for tier in range(6):
            payloads[f"{member.variant_id}/tier_{tier}.py"] = get_member_prepared_equipment(
                member=member, tier=tier
            ).model_dump(mode="json")
    assert len(payloads) == 72
    assert (
        _unmodified_equipment_fingerprint(payloads)
        == "fed28fa609b8406776d8b980c3def96bd1d9e8a2fe7b80f6fe1dc6da65ddbeca"
    )


def test_prepared_manifest_retains_original_generation_provenance():
    import json
    from pathlib import Path

    path = Path("src/backend/features/monsters/catalog/families/rat_catalog/equipment/prepared/manifest.json")
    manifest = json.loads(path.read_text(encoding="utf8"))
    assert manifest["generation_sources_original"]
    assert manifest["reviewed_adjustments"]["id"] == "rat-alpha-minion-base-and-natural-gear-v1"
    assert len(manifest["inputs"]) == 72
    assert len(manifest["generation_inputs_original"]) == 72
    assert sum(len(x["requests"]) for x in manifest["generation_inputs_original"]) == 276
    assert sum(len(x["requests"]) for x in manifest["inputs"]) == 258
    assert manifest["generation_sources_original"] != manifest["sources"]


def test_rat_roles_native_skills_loadouts_and_senior_bases_are_preserved():
    import hashlib
    import json

    actual = {
        member.id: {
            "role": member.role,
            "skills": list(member.skills),
            "loadout": dict(member.fixed_loadout),
            "senior_attributes": dict(member.base_stats) if member.role != "minion" else None,
            "senior_cost": member.assembly_cost if member.role != "minion" else None,
        }
        for member in get_catalog().members.values()
        if member.family_id == "rat_swarm"
    }
    assert (
        hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest()
        == "cf5352ea9dda69b6b14a5c93e964f9bbffebd99ba4e1261741b6af5150eb27d2"
    )


@pytest.mark.parametrize("variant", EXPECTED)
def test_rat_minion_has_one_natural_attack_without_dual_style(variant):
    from tools.monsters.balance_probe.runner import _monster_payload

    catalog = get_catalog()
    member = catalog.members[f"rat_swarm.base.{variant}"]
    assert member.fixed_loadout["off_hand"] is None
    assert member.skills == ("skill_fencing", "skill_light_armor")
    for tier in range(6):
        payload = _monster_payload(member, tier, catalog)
        layout = payload["loadout"]["layout"]
        assert "off_hand" not in layout
        assert layout.get("tactical_style") != "skill_dual_wield"
        assert (
            "off_hand" not in payload["equipment"]["items"]
            if isinstance(payload["equipment"]["items"], dict)
            else all(item["slot"] != "off_hand" for item in payload["equipment"]["items"])
        )
        assert payload["preview_values"]["off_hand_weapon_power"] == 0
        assert not any(feint.startswith("dual_") for feint in payload["loadout"]["known_feints"])


@pytest.mark.parametrize("role,price", (("veteran", 23), ("elite", 30), ("boss", 45)))
def test_rat_senior_prices_match_profile_anchor_costs(role, price):
    members = [m for m in get_catalog().members.values() if m.family_id == "rat_swarm" and m.role == role]
    assert len(members) == 3
    assert all(m.assembly_cost == price for m in members)
