"""CI and runtime builds must consume the same locked dependency sources."""

import re
import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILES = sorted(p for p in (ROOT / "deploy").glob("*/Dockerfile") if "uv export" in p.read_text())


@pytest.mark.parametrize("path", DOCKERFILES, ids=lambda p: p.parent.name)
def test_runtime_export_honors_sources_and_checks_lock(path):
    text = path.read_text()
    command = next(line.removeprefix("RUN ") for line in text.splitlines() if line.startswith("RUN uv export "))
    args = shlex.split(command)
    assert "--locked" in args
    assert not {"--no-sources", "--frozen", "--no-hashes"}.intersection(args)
    assert "--no-emit-project" in args
    install = next(line.strip() for line in text.splitlines() if "/venv/bin/pip install" in line)
    assert "--require-hashes" in shlex.split(install)
    assert "-r requirements.txt" in install


def test_ci_and_docker_use_the_same_explicit_uv_version():
    assert {p.parent.name for p in DOCKERFILES} == {"backend", "chat", "frontend", "studio", "tg_bot", "worker"}
    docker_versions = {re.search(r"pip install --no-cache-dir uv==([\d.]+)", p.read_text())[1] for p in DOCKERFILES}
    assert len(docker_versions) == 1
    count = 0
    for name in ("ci.yml", "build-images.yml"):
        workflow = yaml.safe_load((ROOT / ".github/workflows" / name).read_text())
        for job in workflow["jobs"].values():
            for step in job.get("steps", []):
                if step.get("uses", "").startswith("astral-sh/setup-uv@"):
                    count += 1
                    assert step.get("with", {}).get("version") in docker_versions
                if "uv sync " in step.get("run", ""):
                    args = shlex.split(step["run"])
                    assert "--locked" in args
                    assert not {"--no-sources", "--frozen"}.intersection(args)
    assert count == 4
