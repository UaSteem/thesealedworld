"""Diagnostic policy must not accidentally turn baseline battles into feint AI."""

from types import SimpleNamespace

import pytest
from loguru import logger
from tools.monsters.simulate_encounter_matrix import BasicAttackIntentProvider, build_player, summarize


@pytest.fixture(autouse=True)
def silence_diagnostic_logging():
    logger.remove()


def test_basic_attack_provider_only_emits_plain_exchanges(monkeypatch):
    provider = BasicAttackIntentProvider()
    targets = [SimpleNamespace(meta=SimpleNamespace(id="m_000")), SimpleNamespace(meta=SimpleNamespace(id="m_001"))]
    monkeypatch.setattr(provider, "_candidate_targets", lambda state, actor: targets)
    moves = provider.choose_moves(SimpleNamespace(round_index=3), SimpleNamespace(meta=SimpleNamespace(id="a_player")))
    assert len(moves) == 2
    assert [move.payload.target_id for move in moves] == ["m_000", "m_001"]
    assert all(move.strategy == "exchange" and move.payload.feint_id is None for move in moves)


def test_rejections_do_not_become_losses_and_draws_stay_draws():
    fights = [
        {"status": "rejected"},
        {
            "status": "completed",
            "winner": "draw",
            "rounds": 100,
            "player_hp_fraction": 0.5,
            "monster_count": 4,
            "roster_id": "a",
            "completion_reason": "max_rounds_reached",
        },
    ]
    row = summarize("ordinary", "easy", fights)
    assert row["requested"] == 2 and row["completed"] == 1 and row["rejected"] == 1
    assert row["draws"] == 1 and row["player_wins"] == row["monster_wins"] == 0
    assert row["mean_player_hp_percent"] == 50


def test_reference_player_is_full_dual_blades_with_starting_mastery():
    player = build_player(0)
    assert len(player["equipment"]) == 16
    assert set(player["skills"].values()) == {0.2}
    slots = {item["slot"] for item in player["equipment"]}
    assert {"main_hand", "off_hand", "ring_1", "ring_2", "amulet", "earring"} <= slots
