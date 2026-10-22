"""Exercise the installed runner and pytest selection, without application fixtures."""

import subprocess
import sys
from pathlib import Path

import pytest
from codex_core.dev.check_runner import BaseCheckRunner

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[3]


def selector(command):
    return command[len(command) - command[::-1].index("-m")]


def test_unit_stage_is_filtered_and_full_coverage_gate_is_preserved():
    runner = BaseCheckRunner(ROOT)
    assert runner.config.test_stages == ["unit", "integration", "regression", "suite"]
    for stage in ("unit", "integration", "regression"):
        assert "--no-cov" in runner._test_command(stage)
    assert selector(runner._test_command("unit")) == "unit and not integration and not external"
    assert selector(runner._test_command("suite")) == "not external"
    assert "--no-cov" not in runner._test_command("suite")
    assert "external" not in runner.config.test_stages


def test_real_pytest_partitions_keep_unmarked_and_external_tests_distinct(tmp_path):
    sample = tmp_path / "test_levels.py"
    sample.write_text("""import pytest
@pytest.mark.unit
def test_unit(): pass
@pytest.mark.integration
def test_http(): pass
@pytest.mark.unit
@pytest.mark.integration
def test_overlap(): pass
def test_unmarked(): pass
@pytest.mark.external
@pytest.mark.integration
def test_external(): pass
@pytest.mark.external
@pytest.mark.unit
def test_external_unit(): pass
""")
    runner = BaseCheckRunner(ROOT)
    selections = {}
    for stage in runner.config.test_stages:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(sample),
                "-c",
                str(ROOT / "pyproject.toml"),
                "--collect-only",
                "-q",
                "--no-cov",
                "-o",
                "addopts=",
                "-m",
                selector(runner._test_command(stage)),
            ],
            cwd=tmp_path,
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        selections[stage] = {line.rsplit("::", 1)[1] for line in result.stdout.splitlines() if "::test_" in line}
    assert selections["unit"] == {"test_unit"}
    assert selections["integration"] == {"test_http", "test_overlap"}
    assert selections["regression"] == {"test_unmarked"}
    assert selections["suite"] == set.union(*(selections[s] for s in ("unit", "integration", "regression")))
