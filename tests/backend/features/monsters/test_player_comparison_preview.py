import pytest

from src.backend.features.character.resources.starting_imprints import STARTING_IMPRINTS
from src.backend.features.monsters.inspection.services.catalog_view_service import CatalogMonsterViewService
from src.backend.features.monsters.inspection.services.player_comparison_service import validate_player_attributes

MEMBER = "goblin_tribe.base.goblin_spearman"


def test_dual_blades_jewelry_is_selected_for_build_with_normal_player_rolls():
    player = CatalogMonsterViewService().equipment(member_id=MEMBER, tier=5).player_comparison
    jewelry = [
        item for item in player.technical["equipment"] if item["slot"] in {"ring_1", "ring_2", "amulet", "earring"}
    ]
    assert len(jewelry) == 4
    expected = {
        "ring_1": "attribute_agility",
        "ring_2": "attribute_perception",
        "amulet": "attribute_endurance",
        "earring": "attribute_strength",
    }
    for item in jewelry:
        affixes = item["mechanics"]["affixes"]
        assert len(affixes) == 4
        assert {affix["affix_id"] for affix in affixes if affix["affix_id"].startswith("attribute_")} == {
            expected[item["slot"]]
        }
        assert all(affix["roll"]["step_count"] == 5 for affix in affixes)
    assert player.technical["equipped"]["endurance"] > player.input_attributes["endurance"]


def test_reference_player_uses_real_player_rolls_and_complete_legal_equipment():
    service = CatalogMonsterViewService()
    payload = service.equipment(member_id=MEMBER, tier=5)
    player = payload.player_comparison
    assert player.input_attributes == dict(STARTING_IMPRINTS["starter_dual_blades_01"].attribute_values)
    gear = player.technical["equipment"]
    assert len(gear) == 14
    slots = {item["slot"] for item in gear}
    assert len(slots) == 14
    assert {"main_hand", "off_hand", "ring_1", "ring_2"} <= slots
    assert not {"two_hand", "quiver"} & slots
    assert all(affix["roll"]["step_count"] == 5 for item in gear for affix in item["mechanics"]["affixes"])
    assert player.technical["equipped"]["armor"] > 0
    assert player.technical["equipped"]["off_hand_damage_base"] > 0
    assert player.technical["equipped"]["hp"] > 100
    assert any(row.key == "off_hand_damage_base" for group in player.groups for row in group.rows)
    assert service.equipment(member_id=MEMBER, tier=5).player_comparison == player


def test_custom_attributes_change_only_reference_player():
    service = CatalogMonsterViewService()
    before = service.equipment(member_id=MEMBER, tier=5)
    custom = dict(before.player_comparison.input_attributes, strength=60, endurance=60)
    after = service.equipment(member_id=MEMBER, tier=5, player_attributes=custom)
    assert after.stats_preview == before.stats_preview
    assert after.items == before.items
    assert after.player_comparison.technical["equipment"] == before.player_comparison.technical["equipment"]
    assert after.player_comparison.technical["equipped"]["hp"] > before.player_comparison.technical["equipped"]["hp"]
    assert after.player_comparison.input_attributes == custom


def test_comparison_exposes_raw_avoidance_critical_accuracy_and_caps():
    payload = CatalogMonsterViewService().equipment(member_id=MEMBER, tier=5)
    player = payload.player_comparison
    rows = {row.key: row for group in player.groups for row in group.rows}
    for key in (
        "evasion",
        "parry",
        "crit_chance",
        "main_hand_crit_chance",
        "off_hand_crit_chance",
        "main_hand_accuracy",
        "off_hand_accuracy",
        "armor_penetration_pct",
        "dodge_cap",
        "resistance_cap",
    ):
        assert key in rows
        assert rows[key].player_value.endswith("%")
        assert rows[key].monster_value.endswith("%")
    assert rows["resistance_cap"].monster_value == "85%"
    assert player.technical["equipped"]["evasion"] > 0
    assert any("не итоговые шансы" in note for note in player.notes)


@pytest.mark.parametrize("bad", [{}, [], {"strength": 60}])
def test_input_requires_all_nine_attributes(bad):
    with pytest.raises(ValueError):
        validate_player_attributes(bad)


@pytest.mark.parametrize("bad", [True, 0, -1, 501, 5.5, "50"])
def test_input_requires_bounded_strict_integers(bad):
    inputs = dict(STARTING_IMPRINTS["starter_dual_blades_01"].attribute_values)
    inputs["strength"] = bad
    with pytest.raises(ValueError):
        validate_player_attributes(inputs)
