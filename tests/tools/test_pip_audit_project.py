"""Project-environment audit hook contract; scanner fixtures never query advisory services."""

import json
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "tools/dev/pip_audit_project.py"
IGNORE_IDS = [
    "CVE-2026-3219",
    "CVE-2026-6357",
    "PYSEC-2026-196",
    "PYSEC-2025-183",
    "PYSEC-2026-89",
    "CVE-2026-34993",
    "CVE-2026-47265",
]


def hook_config():
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    return next((repo, hook) for repo in config["repos"] for hook in repo["hooks"] if hook["id"] == "pip-audit")


def test_audit_hook_targets_project_environment_and_never_treats_source_filenames_as_requirements():
    repo, hook = hook_config()
    assert repo["repo"] == "local"
    assert hook["language"] == "system"
    assert hook["entry"] == "python -I tools/dev/pip_audit_project.py"
    assert hook["pass_filenames"] is False and hook["always_run"] is True
    assert hook["args"][:3] == ["--local", "--timeout", "15"]
    assert [hook["args"][i + 1] for i, arg in enumerate(hook["args"]) if arg == "--ignore-vuln"] == IGNORE_IDS
    assert "additional_dependencies" not in hook


@pytest.fixture(scope="module")
def sandbox(tmp_path_factory):
    root = tmp_path_factory.mktemp("project-audit-hook")
    helper = root / "tools/dev/pip_audit_project.py"
    helper.parent.mkdir(parents=True)
    shutil.copyfile(HELPER, helper)
    venv.EnvBuilder(with_pip=False).create(root / ".venv")
    python = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    purelib = Path(
        subprocess.check_output(
            [str(python), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"], text=True
        ).strip()
    )
    dist = purelib / "scope_app-1.2.3.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text("Metadata-Version: 2.1\nName: scope-app\nVersion: 1.2.3\n")
    scanner = purelib / "pip_audit.py"
    scanner.write_text(
        "import importlib.metadata as metadata, json, sys\nfrom pathlib import Path\nprint(json.dumps({'version':metadata.version('scope-app'),'argv':sys.argv[1:],'prefix':sys.prefix}))\ncode=int(Path(__file__).with_suffix('.exit').read_text())\nprint('SyntheticAdvisory' if code==1 else 'SyntheticScannerResult')\nsys.exit(code)\n"
    )
    return root, helper, python, scanner


def invoke(helper, *args):
    return subprocess.run([sys.executable, "-I", str(helper), *args], capture_output=True, text=True)


@pytest.mark.parametrize("scanner_exit", [0, 1, 2])
def test_project_inventory_is_used_and_scanner_exit_is_not_hidden(sandbox, scanner_exit):
    root, helper, python, scanner = sandbox
    scanner.with_suffix(".exit").write_text(str(scanner_exit))
    result = invoke(helper, "--local", "--timeout", "15")
    assert result.returncode == scanner_exit
    report = json.loads(result.stdout.splitlines()[0])
    assert report["version"] == "1.2.3"
    assert Path(report["prefix"]) == root / ".venv"
    assert report["argv"] == ["--local", "--timeout", "15"]
    isolated = subprocess.run(
        [sys.executable, "-I", "-c", "import importlib.metadata as m; m.version('scope-app')"],
        capture_output=True,
        text=True,
    )
    assert isolated.returncode != 0  # the outer/hook environment does not contain the app package


def test_missing_project_environment_fails_closed(tmp_path):
    helper = tmp_path / "tools/dev/pip_audit_project.py"
    helper.parent.mkdir(parents=True)
    shutil.copyfile(HELPER, helper)
    result = invoke(helper, "--local")
    assert result.returncode != 0
    assert "project .venv" in result.stderr


def test_missing_scanner_fails_closed(sandbox):
    root, helper, python, scanner = sandbox
    content = scanner.read_text()
    scanner.unlink()
    try:
        result = invoke(helper, "--local")
        assert result.returncode != 0
        assert "pip_audit" in result.stderr
    finally:
        scanner.write_text(content)


@pytest.mark.parametrize("scanner_exit,hook_exit", [(0, 0), (1, 1)])
def test_real_precommit_cli_observes_project_inventory_and_advisory_failure(sandbox, scanner_exit, hook_exit):
    root, helper, python, scanner = sandbox
    scanner.with_suffix(".exit").write_text(str(scanner_exit))
    _, hook = hook_config()
    (root / ".pre-commit-config.yaml").write_text(yaml.safe_dump({"repos": [{"repo": "local", "hooks": [hook]}]}))
    (root / "arbitrary.py").write_text("# ordinary source, never a requirements input\n")
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(root), "add", ".pre-commit-config.yaml", "arbitrary.py"], check=True, capture_output=True
    )
    env = os.environ.copy()
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(
        [sys.executable, "-m", "pre_commit", "run", "pip-audit", "--files", "arbitrary.py", "--verbose"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == hook_exit, result.stdout + result.stderr
    assert '"version": "1.2.3"' in result.stdout
    report = next(json.loads(line) for line in result.stdout.splitlines() if line.startswith('{"version"'))
    assert "arbitrary.py" not in report["argv"]
    if scanner_exit:
        assert "SyntheticAdvisory" in result.stdout
