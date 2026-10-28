import hashlib
import json

import pytest

from src.backend.features.monsters.catalog.contracts import thaw_catalog_value
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.policies.composition import MonsterCompositionPolicyResolver
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService
from tests.backend.features.monsters.catalog.equipment_slot_expectations import before_equipment_slots


def test_wolf_prices_and_single_attack_keep_other_authored_mechanics():
    members = [m for m in get_catalog().members.values() if m.family_id == "wolf_pack"]
    assert len(members) == 11
    proof = {}
    for member in members:
        expected = {"cub": 10, "runner": 12, "mangy_biter": 14}.get(
            member.variant_id, {"veteran": 23, "elite": 30, "boss": 45}.get(member.role)
        )
        assert member.assembly_cost == expected
        proof[member.id] = {
            "role": member.role,
            "mechanics": thaw_catalog_value(member.mechanics),
            "skills": list(member.skills),
            "min_tier": member.min_tier,
            "max_tier": member.max_tier,
            "equipment_set_id": member.equipment_set_id,
        }
    assert (
        hashlib.sha256(json.dumps(before_equipment_slots(proof), sort_keys=True).encode()).hexdigest()
        == "3942633649e21c5a993f564610b1f27dd05b7f08c16ba709dcebe1b8eecf18a6"
    )


@pytest.mark.parametrize("kind", ("ordinary", "patrol", "guard", "leader"))
@pytest.mark.parametrize("difficulty", ("easy", "normal", "hard"))
def test_builtin_wolf_total_limits_affordable_at_first_tier(kind, difficulty):
    from src.backend.features.monsters.encounters.profiles.registry import MINION_REFERENCE_GS

    order = MonsterEncounterOrderDTO(
        encounter_type=kind,
        difficulty=difficulty,
        location_tier=1,
        family_ids=("wolf_pack",),
        seed=13,
        player_gear_score=MINION_REFERENCE_GS[1],
    )
    resolver = MonsterCompositionPolicyResolver()
    profile = resolver.profile(order)
    assert (profile.min_members, profile.max_members) == (2, 5)
    result = MonsterEncounterSelectionService().select(order)
    assert result.status == "selected"
    assert 2 <= len(result.selection.members) <= 5
    override = profile.model_copy(update={"min_members": 1, "max_members": 8})
    assert resolver.profile(order.model_copy(update={"profile_override": override})) == override


def test_wolves_reject_below_minimum_family_tier():
    order = MonsterEncounterOrderDTO(
        encounter_type="ordinary",
        difficulty="easy",
        location_tier=0,
        family_ids=("wolf_pack",),
        seed=13,
        player_gear_score=40,
    )
    assert MonsterEncounterSelectionService().select(order).status == "rejected"


@pytest.mark.parametrize("tier", range(1, 6))
def test_wolf_natural_hide_has_no_damage_reflection(tier):
    from src.backend.features.monsters.catalog.prepared_equipment import get_prepared_equipment

    for member in get_catalog().members.values():
        if member.family_id != "wolf_pack":
            continue
        prepared = get_prepared_equipment(family_id=member.family_id, variant_id=member.variant_id, tier=tier)
        hide = next(item for item in prepared.items if item.slot == "chest_armor")
        data = hide.model_dump(mode="json")
        assert "thorns_damage_flat" not in data["combat"]["bonuses"]
        assert "thorns_damage_bonus" not in data["combat"]["bonuses"]
        assert not any(affix["affix_id"] == "thorns_damage_bonus" for affix in data["generation"]["affixes"])


def test_retained_wolf_prepared_fields_are_unchanged_after_thorns_and_offhand_removal():
    from copy import deepcopy
    from pathlib import Path

    from tools.monsters.prepare_wolf_equipment import read_data

    root = Path("src/backend/features/monsters/catalog/families/wolf_catalog/equipment/prepared")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf8"))
    data = {key: deepcopy(read_data(root / key)) for key in manifest["files"]}
    assert len(data) == 66
    for payload in data.values():
        for item in payload["items"]:
            if item["slot"] != "chest_armor":
                continue
            assert not any(a["affix_id"] == "thorns_damage_bonus" for a in item["generation"]["affixes"])
            assert "thorns_damage_flat" not in item["combat"]["bonuses"]
    assert (
        hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        == "06aab6483e608b9b9b06faa5262f62e2a997906c20f8cdf419458f73f2c59ceb"
    )


@pytest.mark.parametrize("variant", ("cub", "runner", "mangy_biter"))
def test_wolf_minions_have_one_natural_attack_and_no_dual_style(variant):
    from tools.monsters.balance_probe.runner import _monster_payload

    catalog = get_catalog()
    member = catalog.members[f"wolf_pack.base.{variant}"]
    assert member.fixed_loadout["off_hand"] is None
    assert member.skills == ("skill_fencing", "skill_light_armor")
    for tier in range(1, 6):
        payload = _monster_payload(member, tier, catalog)
        assert "off_hand" not in payload["loadout"]["layout"]
        assert payload["loadout"]["layout"].get("tactical_style") != "skill_dual_wield"
        assert payload["preview_values"]["off_hand_weapon_power"] == 0
        assert all(item["slot"] != "off_hand" for item in payload["equipment"]["items"])
        assert not any(key.startswith("dual_") for key in payload["loadout"]["known_feints"])


@pytest.mark.parametrize(
    "variant,armor",
    (("stalker", "skill_light_armor"), ("flanker", "skill_medium_armor"), ("snapper", "skill_light_armor")),
)
def test_wolf_veterans_have_one_natural_attack_and_keep_native_armor(variant, armor):
    from tools.monsters.balance_probe.runner import _monster_payload

    catalog = get_catalog()
    member = catalog.members[f"wolf_pack.base.{variant}"]
    assert member.assembly_cost == 23
    assert member.fixed_loadout["off_hand"] is None
    assert member.skills == ("skill_fencing", armor)
    for tier in range(1, 6):
        payload = _monster_payload(member, tier, catalog)
        assert "off_hand" not in payload["loadout"]["layout"]
        assert payload["loadout"]["layout"].get("tactical_style") != "skill_dual_wield"
        assert payload["preview_values"]["off_hand_weapon_power"] == 0
        assert all(item["slot"] != "off_hand" for item in payload["equipment"]["items"])
