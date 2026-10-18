"""Equipment suite uses real item constraints and preserves native builds."""

import json
from types import SimpleNamespace

import pytest
from tools.monsters.balance_probe.equipment import build_full_players
from tools.monsters.balance_probe.players import _live_player

from src.backend.features.combat.runtime.simulation.starting_imprint_actors import DEFAULT_STARTER_SIMULATION_IMPRINTS
from src.backend.features.items.resources.item_grade import AFFIX_CONTAINER_RULES, GRADE_BY_RARITY_TIER


@pytest.fixture(scope="module")
def suite():
    return build_full_players(DEFAULT_STARTER_SIMULATION_IMPRINTS, tuple(range(5)))


@pytest.mark.parametrize("identity", DEFAULT_STARTER_SIMULATION_IMPRINTS)
def test_progression_preserves_native_build_and_legal_combat_items(suite, identity):
    native = _live_player(identity, SimpleNamespace(mastery=None))
    previous = {}
    native_slots = native["equipment"]["layout"]["equipment"]
    for tier in range(5):
        payload = suite[f"{identity}.t{tier}"]
        assert payload["skills"] == native["skills"]
        for field in ("attributes", "symbiote"):
            assert payload["input_context"][field] == native["input_context"][field]
        slots = payload["equipment"]["layout"]["equipment"]
        assert "belt_accessory" in slots
        assert {"head_armor", "arms_armor", "legs_armor", "ring_1", "ring_2", "earring"} <= slots.keys()
        assert "outer_garment" not in slots
        for slot in ("main_hand", "off_hand", "two_hand", "quiver"):
            assert (slot in slots) == (slot in native_slots)
            if slot in slots:
                expected = native["equipment"]["by_id"][native_slots[slot]]["base_id"]
                assert payload["equipment"]["by_id"][slots[slot]]["base_id"] == expected
        for item in payload["equipment_review"]:
            assert item["material_tier"] == tier
            rules = AFFIX_CONTAINER_RULES[GRADE_BY_RARITY_TIER[item["rarity_tier"]]]
            assert rules["min"] <= len(item["affixes"]) <= rules["max"]
            current = {affix["affix_id"]: affix for affix in item["affixes"]}
            assert not current.keys() & {
                "physical_resistance_bonus",
                "control_resistance_bonus",
                "control_chance_bonus",
                "thorns_damage_bonus",
                "hp_regen_bonus",
            }
            assert previous.get(item["slot"], {}).keys() <= current.keys()
            assert sum(key.startswith("attribute_") for key in current) <= 1
            for key, affix in current.items():
                assert 0.3 <= affix["roll_quality"] <= 0.7
                assert affix["roll"]["step_count"] == 5
                if key in previous.get(item["slot"], {}):
                    old = previous[item["slot"]][key]
                    assert old["roll"] == affix["roll"]
                    assert old["value"] <= affix["value"]
            previous[item["slot"]] = current
        assert payload["regen"]["combat"]["en"] > 0
    assert suite[f"{identity}.t4"]["build_notes"]["affix_count_target"] == 4


def test_suite_is_serializable_and_deterministic(suite):
    identity = DEFAULT_STARTER_SIMULATION_IMPRINTS[0]
    second = build_full_players((identity,), (0, 4))
    assert second == {key: suite[key] for key in second}
    json.dumps(suite, allow_nan=False)
    assert any(len(item["affixes"]) == 4 for item in second[f"{identity}.t4"]["equipment_review"])


def test_t5_preserves_existing_progression_and_uses_legal_four_affix_ceiling(suite):
    from src.backend.features.items.runtime.item_factory import ItemFactory

    factory = ItemFactory()
    extended = build_full_players(DEFAULT_STARTER_SIMULATION_IMPRINTS, (0, 4, 5))
    for identity in DEFAULT_STARTER_SIMULATION_IMPRINTS:
        for tier in (0, 4):
            assert extended[f"{identity}.t{tier}"] == suite[f"{identity}.t{tier}"]
        payload = extended[f"{identity}.t5"]
        assert payload["skills"] == suite[f"{identity}.t4"]["skills"]
        for field in ("attributes", "symbiote"):
            assert payload["input_context"][field] == suite[f"{identity}.t4"]["input_context"][field]
        assert payload["build_notes"]["affix_count_target"] == 4
        assert (
            payload["equipment"]["layout"]["equipment"].keys()
            == suite[f"{identity}.t4"]["equipment"]["layout"]["equipment"].keys()
        )
        for item in payload["equipment_review"]:
            assert item["material_tier"] == 5
            assert item["rarity_tier"] <= 5
            rules = AFFIX_CONTAINER_RULES[GRADE_BY_RARITY_TIER[item["rarity_tier"]]]
            assert rules["min"] <= len(item["affixes"]) <= rules["max"] <= 4
            base = factory.catalog.get_base_item(item["base_id"])
            tags = factory._build_affix_tags(base)
            kind = factory._affix_item_type(factory._resolve_item_type(base), item["slot"], tags)
            legal = factory._pool_for_item(kind, item["slot"], tags, 5, set())
            assert all(affix["affix_id"] in legal for affix in item["affixes"])
            previous = next(
                entry for entry in suite[f"{identity}.t4"]["equipment_review"] if entry["slot"] == item["slot"]
            )
            assert [entry["affix_id"] for entry in item["affixes"]] == [
                entry["affix_id"] for entry in previous["affixes"]
            ]
            for before, after in zip(previous["affixes"], item["affixes"], strict=True):
                assert before["roll"] == after["roll"]
                assert 0.3 <= after["roll_quality"] <= 0.7
                assert before["value"] <= after["value"]
    assert build_full_players((DEFAULT_STARTER_SIMULATION_IMPRINTS[0],), (5,)) == {
        key: value for key, value in extended.items() if key == f"{DEFAULT_STARTER_SIMULATION_IMPRINTS[0]}.t5"
    }


@pytest.mark.parametrize("tiers", [(), (-1,), (6,), (True,)])
def test_suite_rejects_unsupported_tiers(tiers):
    with pytest.raises(ValueError, match="T0..T5"):
        build_full_players((DEFAULT_STARTER_SIMULATION_IMPRINTS[0],), tiers)
