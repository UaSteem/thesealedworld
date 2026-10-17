from copy import deepcopy
from types import SimpleNamespace

import pytest

from src.backend.features.game_catalog.combat.resources.feints import get_all_feint_catalog_entries
from src.backend.features.monsters.instances.runtime.combat_actor_input import MonsterCombatActorInputBuilder
from src.backend.features.monsters.instances.runtime.feint_loadout import build_monster_feint_loadout

HEALING = {"second_breath", "shield_blood_mend", "2h_perfect_riposte"}


@pytest.mark.parametrize("role", ["minion", "veteran"])
def test_ordinary_monster_arsenal_excludes_hp_heals_without_mutating_catalog_or_input(role):
    entries = get_all_feint_catalog_entries()
    before_catalog = [entry.model_dump() for entry in entries]
    loadout = {"known_feints": [entry.technical.feint_id for entry in entries], "layout": {"main_hand": "skill_swords"}}
    original = deepcopy(loadout)
    result = build_monster_feint_loadout(loadout, role=role)
    assert set(loadout["known_feints"]) - set(result["known_feints"]) == HEALING
    assert result["known_feints"] == [key for key in loadout["known_feints"] if key not in HEALING]
    assert result["layout"] == loadout["layout"]
    assert loadout == original
    assert [entry.model_dump() for entry in entries] == before_catalog


@pytest.mark.parametrize("role", ["elite", "boss", None])
def test_other_monster_ranks_keep_all_feints(role):
    known = ["second_breath", "shield_blood_mend", "2h_perfect_riposte", "foresight_parry"]
    assert build_monster_feint_loadout({"known_feints": known}, role=role)["known_feints"] == known


def test_existing_snapshot_input_is_filtered_without_modifying_saved_snapshot():
    saved = {"meta": {"role": "veteran"}, "loadout": {"known_feints": ["second_breath", "foresight_parry"]}}
    original = deepcopy(saved)
    monster = SimpleNamespace(active_snapshot={"combat_snapshot_input": saved})
    result = MonsterCombatActorInputBuilder().build_input(monster)
    assert result["loadout"]["known_feints"] == ["foresight_parry"]
    assert saved == original


def test_existing_snapshot_can_read_explicit_monster_role_when_input_meta_lacks_it():
    monster = SimpleNamespace(
        role="minion", active_snapshot={"combat_snapshot_input": {"loadout": {"known_feints": ["second_breath"]}}}
    )
    assert MonsterCombatActorInputBuilder().build_input(monster)["loadout"]["known_feints"] == []
