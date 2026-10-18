"""Contract checks for endurance variants, without running battles."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from tools.monsters.probe_endurance_variants import TRANSFERS, lowered_player, saved_rosters


@pytest.fixture(scope="module")
def players():
    return json.loads(Path("var/starter-style-goblins-t0-ordinary-verified/players.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("key", TRANSFERS)
def test_only_three_attributes_points_move_and_combat_assets_preserved(players, key):
    original = deepcopy(players[key])
    new = lowered_player(original, key)
    old_attrs = original["input_context"]["attributes"]
    new_attrs = new["input_context"]["attributes"]
    assert {k: new_attrs[k] - old_attrs[k] for k in old_attrs if new_attrs[k] != old_attrs[k]} == {
        "endurance": -3,
        TRANSFERS[key]: 3,
    }
    assert new["skills"] == original["skills"]
    assert new["loadout"] == original["loadout"]
    assert new["equipment"] == original["equipment"]
    assert new["known_feints"] == original["known_feints"]
    assert new["meta"]["feints"]["arsenal"] == original["meta"]["feints"]["arsenal"]
    assert new["gear_score"] < original["gear_score"]
    assert new["preview_values"]["hp"] < original["preview_values"]["hp"]
    assert original == players[key]


def test_saved_rosters_preserve_order_tiers_and_are_independent():
    fights = [
        {
            "seed": i,
            "status": "completed",
            "members": [{"member_id": "second", "tier": 0}, {"member_id": "first", "tier": 1}],
            "pools": {},
        }
        for i in range(50)
    ]
    rosters = saved_rosters(fights)
    assert rosters[3]["members"] == fights[3]["members"]
    rosters[3]["members"].reverse()
    assert fights[3]["members"][0]["member_id"] == "second"
    with pytest.raises(ValueError, match="Duplicate"):
        saved_rosters([fights[0]] * 50)
    with pytest.raises(ValueError, match="50 completed"):
        saved_rosters(fights[:-1])
