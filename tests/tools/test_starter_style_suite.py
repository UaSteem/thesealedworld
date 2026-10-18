"""Validate offline proposals and preserved combat input, without battles."""

import random

import pytest
from tools.monsters.build_starter_style_suite import build_suite, definitions, validate_attributes, write_report


@pytest.fixture(scope="module")
def suite():
    return build_suite()


def test_matrix_respects_catalog(suite):
    assert len(definitions()) == 18
    assert len(suite["resolved_players"]) == 14
    assert len(suite["excluded"]) == 4
    assert {(r["weapon"], r["armor"]) for r in suite["excluded"]} == {
        ("swords", "light"),
        ("swords", "medium"),
        ("macing", "light"),
        ("macing", "medium"),
    }
    assert suite["battles"] == 0


def test_attributes_and_equal_skill_budget(suite):
    for row in suite["rows"]:
        validate_attributes(row["attributes"])
        assert sorted(row["skills"].values()) == [0.05, 0.075, 0.1]


def test_arsenal_survives_as_actual_actor_input(suite):
    for player in suite["resolved_players"].values():
        assert player["known_feints"]
        assert player["known_feints"] == player["loadout"]["known_feints"]
        assert player["known_feints"] == player["meta"]["feints"]["arsenal"]
        assert player["gear_score"] > 0
        assert set(player["input_context"]) == {"attributes", "items", "symbiote"}


def test_items_legal_and_no_affixes(suite):
    from src.backend.features.items.runtime.item_factory import ItemFactory

    factory = ItemFactory()
    utility = None
    for player in suite["resolved_players"].values():
        items = player["equipment"]
        current = {}
        for slot, iid in items["layout"]["equipment"].items():
            item = items["by_id"][iid]
            base = factory.catalog.get_base_item(item["base_id"])
            assert slot in {base.slot, *base.extra_slots}
            assert not item["mechanics"]["affixes"]
            if slot in {"chest_garment", "legs_garment", "feetwear", "belt_accessory"}:
                current[slot] = item["base_id"]
        if utility is None:
            utility = current
        assert utility == current


def test_deterministic_and_does_not_consume_global_random(suite):
    state = random.getstate()
    again = build_suite()
    assert random.getstate() == state
    assert again == suite


def test_report_contains_all_proposals_and_exclusion_reasons(suite, tmp_path):
    write_report(suite, tmp_path)
    assert all((tmp_path / name).exists() for name in ("players.json", "report.json", "report.html"))
    page = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert all(row["id"] in page for row in suite["rows"])
    assert "Catalog does not permit slots" in page
