"""Observable contracts for the read-only, reproducible balance CLI."""

import pytest
from tools.monsters.balance_probe.config import parse_config


@pytest.mark.parametrize(
    "args",
    [
        ["--battles", "0"],
        ["--battles", "-1"],
        ["--tier", "8"],
        ["--tier", "-1"],
        ["--mastery", "1.01"],
        ["--mastery", "nan"],
        ["--mode", "fixed"],
        ["--member", "goblin_tribe.base.goblin_scavenger=2"],
        ["--mode", "fixed", "--member", "broken=2"],
        ["--mode", "fixed", "--member", "goblin_tribe.base.goblin_scavenger=0"],
        ["--replay", "manifest.json", "--tier", "0"],
    ],
)
def test_invalid_run_is_rejected_before_execution(args):
    with pytest.raises((SystemExit, ValueError)):
        parse_config(args)


def test_fixed_composition_and_seed_are_explicit():
    config = parse_config([
        "--mode", "fixed", "--player", "starter_dual_blades_01",
        "--member", "goblin_tribe.base.goblin_scavenger=2",
        "--member", "goblin_tribe.base.goblin_slinger=1",
        "--seed", "13", "--battles", "2", "--feints", "both",
    ])
    assert config.members == (
        ("goblin_tribe.base.goblin_scavenger", 2),
        ("goblin_tribe.base.goblin_slinger", 1),
    )
    assert config.seed == 13 and config.battles == 2
    assert config.mastery is None

@pytest.mark.parametrize("args", [
    ["--workers", "0"],
    ["--max-rounds", "0"],
    ["--player-key", "missing"],
    ["--mode", "fixed", "--member", "goblin_tribe.base.goblin_scavenger=9"],
    ["--mode", "fixed", "--member", "goblin_tribe.base.goblin_scavenger=1",
     "--member", "goblin_tribe.base.goblin_scavenger=1"],
])
def test_inconsistent_execution_options_fail(args):
    with pytest.raises((SystemExit, ValueError)):
        parse_config(args)


def test_default_output_is_unique_and_parsing_creates_no_directory():
    first = parse_config([])
    second = parse_config([])
    assert first.output != second.output
    assert not first.output.exists()
    assert not second.output.exists()


def test_live_starter_preserves_native_skills_unless_explicitly_overridden():
    from tools.monsters.balance_probe.players import resolve_players

    native = resolve_players(parse_config(["--player", "starter_dual_blades_01"]))
    boosted = resolve_players(parse_config(["--player", "starter_dual_blades_01", "--mastery", "0.2"]))
    player = native["starter_dual_blades_01"]
    assert player["skills"] == {
        "skill_fencing": 0.1,
        "skill_dual_wield": 0.075,
        "skill_light_armor": 0.05,
    }
    assert boosted["starter_dual_blades_01"]["skills"] == dict.fromkeys(player["skills"], 0.2)
    assert native["starter_dual_blades_01"]["skills"] == player["skills"]
    assert player["loadout"]["known_feints"]
    assert boosted["starter_dual_blades_01"]["loadout"]["known_feints"]


@pytest.mark.parametrize("location", ["root", "loadout", "meta"])
def test_saved_explicit_runtime_arsenal_survives_normalization(tmp_path, location):
    import json

    from tools.monsters.balance_probe.players import resolve_players

    payload = resolve_players(parse_config([]))["starter_dual_blades_01"]
    arsenal = payload.pop("known_feints")
    payload["loadout"].pop("known_feints")
    if location == "root":
        payload["known_feints"] = arsenal
    elif location == "loadout":
        payload["loadout"]["known_feints"] = arsenal
    else:
        payload["meta"] = {"feints": {"arsenal": arsenal}}
    path = tmp_path / "player.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    restored = resolve_players(parse_config(["--player-input", str(path)]))["player"]
    assert restored["loadout"]["known_feints"] == arsenal


def test_conflicting_explicit_arsenals_are_rejected():
    from tools.monsters.balance_probe.players import _validate_payload, resolve_players

    payload = resolve_players(parse_config([]))["starter_dual_blades_01"]
    payload["known_feints"] = []
    with pytest.raises(ValueError, match="conflicting explicit feint arsenals"):
        _validate_payload(payload, name="conflict")


def test_saved_style_suite_arsenal_reaches_runtime_hand():
    from pathlib import Path

    from tools.monsters.balance_probe.players import resolve_players
    from tools.monsters.balance_probe.runner import _actor

    from src.backend.features.combat.dto import FeintHandDTO

    path = Path("var/starter-style-suite-18/players.json")
    if not path.exists():
        pytest.skip("Local style-suite artifact is not available")
    players = resolve_players(parse_config([
        "--player-input", str(path), "--player-key", "test18.two_handed.halberd.medium",
    ]))
    payload = next(iter(players.values()))
    actor = _actor(payload, identity="player", kind="player")
    actor.meta.feints = FeintHandDTO(arsenal=payload["loadout"]["known_feints"], hand={})
    assert actor.meta.feints.arsenal
    assert set(actor.meta.feints.arsenal) == set(payload["known_feints"])

@pytest.fixture(scope="module")
def fixed_probe(tmp_path_factory):
    import json

    from tools.monsters.balance_probe.runner import run_probe

    folder = tmp_path_factory.mktemp("balance-probe")
    first_dir = folder / "first"
    first = run_probe(parse_config([
        "--mode", "fixed", "--member", "goblin_tribe.base.goblin_scavenger=2",
        "--battles", "2", "--seed", "13", "--feints", "both",
        "--output", str(first_dir),
    ]))
    replay_dir = folder / "replay"
    replay = run_probe(parse_config([
        "--replay", str(first_dir / "manifest.json"), "--output", str(replay_dir),
    ]))
    def fights(report, output):
        return json.loads((output / report["cases"][0]["files"]["fights"]).read_text(encoding="utf-8"))
    return first, replay, fights(first, first_dir), fights(replay, replay_dir), first_dir


def test_real_fixed_battles_preserve_exact_composition_and_replay(fixed_probe):
    from collections import Counter

    first, replay, fights, replayed, output = fixed_probe
    assert first["metadata"]["status"] == "completed"
    assert replay["metadata"]["status"] == "completed"
    assert fights == replayed
    assert [fight["seed"] for fight in fights] == [13, 14]
    for fight in fights:
        assert fight["status"] == "completed"
        assert fight["rounds"] > 0
        assert Counter(member["member_id"] for member in fight["members"]) == {
            "goblin_tribe.base.goblin_scavenger": 2,
        }
    assert first["cases"][0]["completed"] == 2
    assert first["cases"][0]["rejected"] == 0
    assert (output / "report.html").is_file()
    assert (output / "summary.csv").is_file()


def test_existing_report_is_never_overwritten(fixed_probe):
    from tools.monsters.balance_probe.runner import run_probe

    _, _, _, _, output = fixed_probe
    before = (output / "summary.json").read_bytes()
    with pytest.raises(ValueError, match="empty|overwrit"):
        run_probe(parse_config(["--battles", "1", "--output", str(output)]))
    assert (output / "summary.json").read_bytes() == before


def test_unaffordable_encounters_are_rejections_not_losses(tmp_path):
    from tools.monsters.balance_probe.runner import run_probe

    report = run_probe(parse_config([
        "--family", "golem_foundry", "--battles", "2", "--output", str(tmp_path / "rejected"),
    ]))
    case = report["cases"][0]
    assert case["requested"] == case["rejected"] == 2
    assert case["completed"] == 0
    assert case["player_wins"] == case["monster_wins"] == case["draws"] == 0
    assert case["survival_percent"] is None


def test_unknown_catalog_member_fails_without_creating_report(tmp_path):
    from tools.monsters.balance_probe.runner import run_probe

    output = tmp_path / "invalid"
    with pytest.raises(ValueError):
        run_probe(parse_config([
            "--mode", "fixed", "--member", "goblin_tribe.base.unknown=1", "--output", str(output),
        ]))
    assert not output.exists()


def test_saved_players_require_unambiguous_selection_and_preserve_skills(tmp_path):
    import json

    from tools.monsters.balance_probe.players import resolve_players

    live = resolve_players(parse_config([]))["starter_dual_blades_01"]
    saved = tmp_path / "players.json"
    saved.write_text(json.dumps({"one": live, "two": live}), encoding="utf-8")
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_players(parse_config(["--player-input", str(saved)]))
    selected = resolve_players(parse_config(["--player-input", str(saved), "--player-key", "two"]))
    assert list(selected) == ["two"]
    assert selected["two"]["skills"] == live["skills"]
    assert selected["two"]["raw"] == live["raw"]


def test_replay_refuses_source_drift_before_creating_output(fixed_probe, tmp_path):
    import json

    from tools.monsters.balance_probe.runner import run_probe

    *_, original = fixed_probe
    manifest = json.loads((original / "manifest.json").read_text(encoding="utf-8"))
    manifest["source_fingerprint"] = "different-source"
    path = tmp_path / "drift.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="source fingerprint differs"):
        run_probe(parse_config(["--replay", str(path), "--output", str(output)]))
    assert not output.exists()


def test_parallel_cases_match_serial_and_none_disables_feints(tmp_path):
    import json

    from tools.monsters.balance_probe.runner import run_probe

    common = [
        "--mode", "fixed", "--member", "goblin_tribe.base.goblin_scavenger=1",
        "--player", "starter_dual_blades_01", "starter_medium_dual_blades_01",
        "--battles", "1", "--max-rounds", "3", "--feints", "none", "--seed", "17",
    ]
    serial_dir, parallel_dir = tmp_path / "serial", tmp_path / "parallel"
    serial = run_probe(parse_config([*common, "--output", str(serial_dir)]))
    parallel = run_probe(parse_config([*common, "--workers", "2", "--output", str(parallel_dir)]))
    assert len(serial["cases"]) == len(parallel["cases"]) == 2
    for left, right in zip(serial["cases"], parallel["cases"], strict=True):
        a = json.loads((serial_dir / left["files"]["fights"]).read_text(encoding="utf-8"))
        b = json.loads((parallel_dir / right["files"]["fights"]).read_text(encoding="utf-8"))
        assert a == b
        assert left["feints_selected"] == right["feints_selected"] == 0
        assert all(sum(fight["feint_pick_count"].values()) == 0 for fight in a)
