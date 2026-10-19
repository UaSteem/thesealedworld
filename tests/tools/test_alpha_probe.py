"""Portable alpha inputs, matrix boundaries and CLI preparation without simulations."""

import json
from hashlib import sha256

import pytest
from tools.monsters.balance_probe.alpha import DATA, FAMILIES, main, scenario_configs


def test_matrix_includes_every_accepted_family_tier_and_three_difficulties(tmp_path):
    configs = list(scenario_configs(families=FAMILIES, tiers=range(6), battles=25, workers=2, seed=7, output=tmp_path))
    assert len(configs) == 26
    assert sum(len(c.encounters) * len(c.difficulties) for c in configs) == 312
    assert all(c.tier >= FAMILIES[c.family] for c in configs)
    assert all(c.feints == "both" and c.seed == 7 and c.battles == 25 for c in configs)
    assert all(c.player_input.is_relative_to(DATA) for c in configs)


def test_preserved_inputs_have_exact_provenance_and_skill_assumptions():
    provenance = json.loads((DATA / "provenance.json").read_text(encoding="utf8"))
    assert sha256((DATA / "heavy_guard_players.json").read_bytes()).hexdigest() == provenance["fixture_sha256"]
    players = json.loads((DATA / "heavy_guard_players.json").read_text(encoding="utf8"))["resolved_players"]
    assert len(players) == 6
    for tier in range(6):
        player = players[f"starter_heavy_guard_01.t{tier}"]
        assert player["source"]["tier"] == tier
        assert player["skills"].get("skill_anatomy", 0) <= 0.5
        assert player["loadout"]["known_feints"]
        assert player["raw"] and player["loadout"] and player["input_context"]["items"]
    assert sorted(players["starter_heavy_guard_01.t0"]["skills"].values()) == [0.05, 0.075, 0.1]


def test_accepted_evidence_retains_samples_and_fingerprints_not_equipment():
    evidence = json.loads((DATA / "accepted_evidence.json").read_text(encoding="utf8"))
    assert {r["family"] for r in evidence["runs"]} == set(FAMILIES)
    assert sum(len(r["cases"]) for r in evidence["runs"]) == 312
    for run in evidence["runs"]:
        assert run["requested"] == run["completed"] and run["rejected"] == 0
        for case in run["cases"]:
            assert len(case["source_fingerprint"]) == 64
            assert len(case["seeds"]) == case["summary"]["requested"]
            assert len(case["seeds"]) == len(set(case["seeds"]))
            assert "monster_metrics" not in case


def test_dry_run_prepares_from_tracked_fixture_without_calling_simulator(tmp_path, monkeypatch):
    from tools.monsters.balance_probe import runner

    def forbidden(*args, **kwargs):
        raise AssertionError("dry-run must not run battles")

    monkeypatch.setattr(runner, "run_probe", forbidden)
    out = tmp_path / "portable"
    assert main(["--families", "golem_foundry", "--tiers", "0", "2", "--dry-run", "--output", str(out)]) == 0
    plan = json.loads((out / "plan.json").read_text(encoding="utf8"))
    assert len(plan["scenarios"]) == 1
    assert plan["scenarios"][0]["tier"] == 2
    assert plan["scenarios"][0]["gear_score"] > 0
    with pytest.raises(SystemExit):
        main(["--dry-run", "--output", str(out)])
