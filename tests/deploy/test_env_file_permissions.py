"""Run the workflow's env-writing block in an offline disposable Linux container."""

import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(os.getenv("RUN_ENV_FILE_CONTAINER_TEST") != "1", reason="Opt-in isolated Docker check")
@pytest.mark.parametrize("existing", ["missing", "regular", "symlink", "failed_update"])
def test_workflow_env_is_private_from_first_write_and_replaced_safely(existing):
    workflow = yaml.safe_load((ROOT / ".github/workflows/deploy-production.yml").read_text())
    step = next(step for step in workflow["jobs"]["deploy"]["steps"] if step.get("name") == "SSH Deploy")
    script, boundary, _ = step["with"]["script"].partition('echo "$GITHUB_TOKEN"')
    assert boundary, "Stop before registry login and deployment commands"
    setup = """
set -eu
umask 000
mkdir -p /opt/turnbasedmmorpg/deploy
chmod 755 /opt /opt/turnbasedmmorpg /opt/turnbasedmmorpg/deploy
cd /opt/turnbasedmmorpg/deploy
export ENV_FILE_CONTENT='TEST_VALUE=canary-env-content
DOCKER_IMAGE_SITE=old-image'
export REPO_LOWER=example/project IMAGE_REF=synthetic-sha
"""
    if existing != "missing":
        setup += "echo old-content > /tmp/original-env\nchmod 666 /tmp/original-env\n"
        setup += "ln -s /tmp/original-env .env\n" if existing == "symlink" else "cp /tmp/original-env .env\n"
    # Check the output descriptor at the first credential write, before chmod
    # could hide a permissive creation mode. Contents are never printed.
    instrumentation = """
printf() {
    mode=$(stat -L -c '%a' /proc/$$/fd/1)
    [ "$mode" = 600 ] || return 91
    command printf "$@"
}
"""
    if existing == "failed_update":
        checks = """
[ "$result" = 73 ]
[ "$(cat .env)" = old-content ]
[ -z "$(find . -name '.env.tmp.*' -print)" ]
"""
    else:
        checks = """
[ "$result" = 0 ]
[ ! -L .env ]
[ "$(stat -c '%a' .env)" = 600 ]
[ "$(stat -c '%u' .env)" = "$(id -u)" ]
grep -Fxq 'TEST_VALUE=canary-env-content' .env
grep -Fxq 'DOCKER_IMAGE_SITE=ghcr.io/example/project-site:synthetic-sha' .env
[ "$(grep -c '^DOCKER_IMAGE_' .env)" = 6 ]
su -s /bin/sh nobody -c '[ "$(id -u)" != 0 ]'
! su -s /bin/sh nobody -c 'cat /opt/turnbasedmmorpg/deploy/.env >/dev/null 2>&1'
[ -z "$(find . -name '.env.tmp.*' -print)" ]
"""
        if existing == "symlink":
            checks += '[ "$(cat /tmp/original-env)" = old-content ]\n'
    # A separate shell keeps the workflow's set -e semantics for failure cleanup.
    if existing == "failed_update":
        instrumentation = "sed() { return 73; }\n" + instrumentation
    command = (
        setup
        + "\nset +e\nsh <<'WORKFLOW_SCRIPT'\n"
        + instrumentation
        + script
        + "\nWORKFLOW_SCRIPT\nresult=$?\nset -e\n"
        + checks
    )
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--pull",
            "never",
            "--network",
            "none",
            "--entrypoint",
            "sh",
            os.getenv("ENV_TEST_IMAGE", "deploy-nginx:latest"),
            "-c",
            command,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"Isolated env permission check failed: {existing} (exit {result.returncode})"
    assert "canary-env-content" not in result.stdout + result.stderr
