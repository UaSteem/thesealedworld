"""Balance-chain mechanics, progression decisions and safe resume contracts."""

import asyncio
import json
import multiprocessing
from argparse import Namespace
from concurrent.futures import ProcessPoolExecutor

import pytest
from tools.monsters import simulate_balance_chain as chain
from tools.monsters.simulate_catalog_duel import build_actor, build_reference_inputs


def settings(tmp_path):
    return Namespace(
        member_id="goblin_tribe.base.goblin_sneak",
        min_player_tier=0,
        max_player_tier=1,
        max_monster_tier=2,
        mastery_start=0.2,
        mastery_step=0.1,
        max_count=2,
        battles=2,
        max_rounds=2,
        workers=1,
        seed=100,
        output=tmp_path / "chain",
    )


def test_chain_rebuilds_player_with_three_confirmed_skills_and_independent_tiers():
    inputs = chain.build_chain_inputs("goblin_tribe.base.goblin_sneak", 1, 3, 0.3)
    original_player = build_reference_inputs("goblin_tribe.base.goblin_sneak", 1)["player"]
    original_monster = build_reference_inputs("goblin_tribe.base.goblin_sneak", 3)["monster"]
    assert inputs["player"]["equipment"] == original_player["equipment"]
    assert inputs["player"]["input_attributes"] == original_player["input_attributes"]
    assert inputs["player"]["skills"] == {"skill_fencing": 0.3, "skill_dual_wield": 0.3, "skill_light_armor": 0.3}
    assert inputs["monster"] == original_monster
    assert inputs["player"]["raw"] != original_player["raw"]
    actor = build_actor(inputs["player"], actor_id="player", team="player", kind="player")
    assert actor.stats.mods.main_hand_damage_base == inputs["player"]["preview_values"]["main_hand_damage_base"]
    assert len(inputs["player"]["equipment"]) == 16


def test_chain_frontier_uses_all_counts_and_resumes_without_replaying(tmp_path, monkeypatch):
    args = settings(tmp_path)
    calls = []
    monkeypatch.setattr(chain, "source_fingerprint", lambda: "fixed-test-source")
    monkeypatch.setattr(chain, "build_chain_inputs", lambda member, p, m, mastery: {"p": p, "m": m, "mastery": mastery})

    async def simulate(inputs, *, monsters, battles, seed, max_rounds):
        calls.append((inputs["p"], inputs["m"], monsters))
        player_wins = 1 if (inputs["p"], inputs["m"], monsters) == (1, 1, 2) else 0
        return {
            "monster_count": monsters,
            "battles": battles,
            "wins": {"player": player_wins, "monster": battles - player_wins, "draw": 0},
            "median_rounds": 1,
            "fights": [],
        }, {}

    monkeypatch.setattr(chain, "run_pressure_batch", simulate)
    report = asyncio.run(chain.run_chain(args))
    assert len(calls) == len(report["cases"]) == 6
    assert (0, 1, 1) not in calls
    assert (1, 2, 1) in calls  # Solo all-loss alone must NOT stop the chain.
    middle = next(row for row in report["transitions"] if (row["player_tier"], row["monster_tier"]) == (1, 1))
    assert middle["solo_all_losses"]
    assert not middle["all_counts_all_losses"]
    assert middle["action"] == "advance_monster"
    assert report["config"]["player_mastery_by_tier"] == [0.2, 0.3]
    assert report["status"] == "complete"
    again = asyncio.run(chain.run_chain(args))
    assert chain.digest(again) == chain.digest(report)
    assert len(calls) == 6
    saved = args.output / "p0-m0-n1/inputs.json"
    saved.write_text(json.dumps({"tampered": True}), encoding="utf-8")
    with pytest.raises(ValueError, match="mismatch"):
        asyncio.run(chain.run_chain(args))


def test_chain_rejects_nonempty_unrelated_output_and_changed_configuration(tmp_path, monkeypatch):
    args = settings(tmp_path)
    monkeypatch.setattr(chain, "source_fingerprint", lambda: "fixed-test-source")
    args.output.mkdir()
    (args.output / "unrelated.txt").write_text("preserve", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        asyncio.run(chain.run_chain(args))
    assert (args.output / "unrelated.txt").read_text() == "preserve"
    (args.output / "summary.json").write_text(json.dumps({"config_hash": "different"}), encoding="utf-8")
    with pytest.raises(ValueError, match="another configuration"):
        asyncio.run(chain.run_chain(args))


def test_process_worker_executes_real_bounded_case_with_pickled_inputs():
    inputs = chain.build_chain_inputs("goblin_tribe.base.goblin_sneak", 0, 0, 0.2)
    with ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context("spawn")) as pool:
        report, sample = pool.submit(chain.worker_case, inputs, monsters=1, battles=1, seed=7, max_rounds=1).result(
            timeout=60
        )
    assert report["battles"] == 1
    assert report["fights"][0]["rounds"] <= 1
    assert sample["resolver_results"]
