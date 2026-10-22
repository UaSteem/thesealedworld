"""Full quality workflows must declare their complete synthetic settings contract."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ["ci.yml", "build-images.yml"]
SERVICE_KEYS = {"FRONTEND_INTERNAL_SERVICE_KEY", "SITE_TO_GAME_SERVICE_KEY", "BACKEND_INTERNAL_SERVICE_KEY"}
PRELUDE = """
import pydantic_settings
original = pydantic_settings.SettingsConfigDict
def without_dotenv(*args, **kwargs):
    kwargs['env_file'] = None
    return original(*args, **kwargs)
pydantic_settings.SettingsConfigDict = without_dotenv
"""


def quality_environment(workflow):
    definition = yaml.safe_load((ROOT / ".github/workflows" / workflow).read_text())
    job = definition["jobs"]["quality"]
    steps = [step for step in job["steps"] if "tools/dev/check.py" in step.get("run", "")]
    assert len(steps) == 1
    return {**definition.get("env", {}), **job.get("env", {}), **steps[0]["env"]}, steps[0]["env"]


def isolated_python(environment, script, cwd):
    # Retain only process bootstrap/OS variables, never ambient application config.
    inherited = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "COMSPEC", "PATHEXT"}
    }
    return subprocess.run(
        [sys.executable, "-c", PRELUDE + script],
        env={**inherited, **{key: str(value) for key, value in environment.items()}, "PYTHONPATH": str(ROOT)},
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_declared_quality_env_imports_strict_settings_and_collects(workflow, tmp_path):
    environment, _ = quality_environment(workflow)
    script = """
import os
assert os.environ['DEBUG'] == 'False'
from src.backend.config.settings import settings as backend
from src.frontend.config.settings import settings as frontend
assert backend.debug is False and frontend.debug is False
assert backend.frontend_internal_service_key == frontend.backend_internal_service_key
assert backend.site_to_game_service_key == frontend.backend_internal_service_key
import pytest
raise SystemExit(pytest.main(['--collect-only', '-q', '--no-cov', '-o', 'addopts=',
    {backend_test!r}, {frontend_test!r}]))
""".format(
        backend_test=str(ROOT / "tests/backend/core/test_production_settings.py"),
        frontend_test=str(ROOT / "tests/frontend/integrations/backend_api/test_game_config.py"),
    )
    result = isolated_python(environment, script, tmp_path)
    assert result.returncode == 0, result.stderr + result.stdout
    assert "collected" in result.stdout


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_quality_service_keys_are_explicit_matching_synthetic_literals(workflow):
    environment, step = quality_environment(workflow)
    assert step.keys() >= SERVICE_KEYS
    values = {step[key] for key in SERVICE_KEYS}
    assert len(values) == 1
    value = values.pop()
    assert "synthetic" in value and "${{" not in value
    assert not value.startswith(("dev-", "change-me-"))
    assert environment["DEBUG"] == "False"


@pytest.mark.parametrize("workflow", WORKFLOWS)
@pytest.mark.parametrize("module", ["src.backend.config.settings", "src.frontend.config.settings"])
def test_production_missing_service_keys_remains_rejected(workflow, module, tmp_path):
    environment, _ = quality_environment(workflow)
    environment = {key: value for key, value in environment.items() if key not in SERVICE_KEYS}
    result = isolated_python(environment, f"import importlib; importlib.import_module({module!r})", tmp_path)
    assert result.returncode != 0
    assert "Production settings cannot use default or development secret keys" in result.stderr
