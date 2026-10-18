"""Equipment-only comparison must not accidentally change native build strength."""

import pytest
from tools.monsters.prepare_full_t0_comparison import prepare_pairs


@pytest.fixture(scope="module")
def prepared():
    return prepare_pairs()


def test_exact_current_fourteen_pairs(prepared):
    inputs, preparation = prepared
    assert preparation["pair_count"] == 14
    assert len(inputs["resolved_players"]) == 28


def test_full_t0_preserves_build_and_weapon_identity(prepared):
    inputs, preparation = prepared
    for pair in preparation["pairs"]:
        starter = inputs["resolved_players"][pair["starter_key"]]
        full = inputs["resolved_players"][pair["full_key"]]
        assert starter["skills"] == full["skills"]
        for field in ("attributes", "symbiote"):
            assert starter["input_context"][field] == full["input_context"][field]
        assert set(starter["loadout"]["known_feints"]) == set(full["loadout"]["known_feints"])
        assert len(full["loadout"]["known_feints"]) > 0
        native_slots = starter["equipment"]["layout"]["equipment"]
        full_slots = full["equipment"]["layout"]["equipment"]
        assert {
            "head_armor",
            "chest_armor",
            "arms_armor",
            "legs_armor",
            "belt_accessory",
            "ring_1",
            "ring_2",
            "amulet",
            "earring",
        } <= full_slots.keys()
        for slot in ("main_hand", "off_hand", "two_hand", "quiver"):
            assert (slot in native_slots) == (slot in full_slots)
            if slot in native_slots:
                assert (
                    starter["equipment"]["by_id"][native_slots[slot]]["base_id"]
                    == full["equipment"]["by_id"][full_slots[slot]]["base_id"]
                )
        assert all(item["material_tier"] == 0 and item["affixes"] == [] for item in full["equipment_review"])
        assert full["gear_score"] > 0
        assert full["regen"]["combat"]["en"] > 0
