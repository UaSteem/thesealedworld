"""Fail closed before production access, with main-ancestor rollback support."""

import copy
import json
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest
import yaml
from tools.deploy import verified_images as gate

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40


class Policy:
    def __init__(self):
        self.comparison = {"status": "ahead", "merge_base_commit": {"sha": SHA}}
        self.environment = {
            "name": "production",
            "protection_rules": [
                {
                    "type": "required_reviewers",
                    "prevent_self_review": False,
                    "reviewers": [{"type": "User", "reviewer": {"id": 1}}],
                }
            ],
        }
        self.calls = []

    def json(self, path):
        self.calls.append(path)
        if path == f"/compare/{SHA}...main":
            return copy.deepcopy(self.comparison)
        assert path == "/environments/production"
        return copy.deepcopy(self.environment)


@pytest.mark.parametrize("status", ["ahead", "identical"])
@pytest.mark.parametrize("self_review", [False, True])
def test_main_ancestor_or_current_main_with_configured_approval(status, self_review):
    policy = Policy()
    policy.comparison["status"] = status
    policy.environment["protection_rules"][0]["prevent_self_review"] = self_review
    assert gate.production_policy(policy, "workflow_dispatch", "refs/heads/main", SHA) is self_review
    assert policy.calls == [f"/compare/{SHA}...main", "/environments/production"]


def test_team_reviewer_is_supported_without_requiring_another_person():
    policy = Policy()
    policy.environment["protection_rules"][0]["reviewers"] = [{"type": "Team", "reviewer": {"id": 7}}]
    assert gate.production_policy(policy, "workflow_dispatch", "refs/heads/main", SHA) is False


@pytest.mark.parametrize("change", ["environment", "main"])
def test_rechecking_after_approval_detects_policy_changes(change):
    policy = Policy()
    gate.production_policy(policy, "workflow_dispatch", "refs/heads/main", SHA)
    if change == "environment":
        policy.environment["protection_rules"] = []
    else:
        policy.comparison["status"] = "diverged"
    with pytest.raises(gate.VerificationError):
        gate.production_policy(policy, "workflow_dispatch", "refs/heads/main", SHA)


@pytest.mark.parametrize("sha", [None, "main", "a" * 12, "a" * 40 + "...foreign"])
def test_invalid_source_cannot_change_comparison_endpoint(sha):
    policy = Policy()
    with pytest.raises(gate.VerificationError):
        gate.production_policy(policy, "workflow_dispatch", "refs/heads/main", sha)
    assert policy.calls == []


@pytest.mark.parametrize(
    ("event", "ref"),
    [
        ("push", "refs/heads/main"),
        ("pull_request", "refs/heads/main"),
        ("workflow_dispatch", "refs/heads/develop"),
        ("workflow_dispatch", "refs/tags/v1.0.0"),
        ("workflow_dispatch", "refs/heads/foreign"),
    ],
)
def test_untrusted_dispatch_fails_before_api_calls(event, ref):
    policy = Policy()
    with pytest.raises(gate.VerificationError):
        gate.production_policy(policy, event, ref, SHA)
    assert policy.calls == []


@pytest.mark.parametrize(
    "comparison",
    [
        None,
        {},
        {"status": "behind", "merge_base_commit": {"sha": SHA}},
        {"status": "diverged", "merge_base_commit": {"sha": SHA}},
        {"status": "ahead", "merge_base_commit": {"sha": "b" * 40}},
        {"status": "identical", "merge_base_commit": None},
    ],
)
def test_unrelated_or_future_build_source_blocks_production(comparison):
    policy = Policy()
    policy.comparison = comparison
    with pytest.raises(gate.VerificationError):
        gate.production_policy(policy, "workflow_dispatch", "refs/heads/main", SHA)
    assert "/environments/production" not in policy.calls


@pytest.mark.parametrize(
    "environment",
    [
        None,
        {},
        {"name": "production", "protection_rules": []},
        {"name": "production", "protection_rules": [{"type": "wait_timer"}]},
        {"name": "production", "protection_rules": [{"type": "required_reviewers", "reviewers": []}]},
        {"name": "production", "protection_rules": [None]},
    ],
)
def test_missing_or_unprotected_environment_blocks_production(environment):
    policy = Policy()
    policy.environment = environment
    with pytest.raises(gate.VerificationError):
        gate.production_policy(policy, "workflow_dispatch", "refs/heads/main", SHA)


@pytest.mark.parametrize("reviewers", [None, [], [{}], [{"type": "User", "reviewer": {"id": True}}]])
def test_malformed_reviewers_block_production(reviewers):
    policy = Policy()
    policy.environment["protection_rules"][0]["reviewers"] = reviewers
    with pytest.raises(gate.VerificationError):
        gate.production_policy(policy, "workflow_dispatch", "refs/heads/main", SHA)


@pytest.mark.parametrize("endpoint", ["compare", "environments"])
@pytest.mark.parametrize("code", [403, 404, 500])
def test_api_denial_or_missing_environment_cannot_authorize(endpoint, code):
    policy = Policy()
    original = policy.json

    def request(path):
        if endpoint in path:
            raise urllib.error.HTTPError("https://api.github.com", code, "denied", {}, None)
        return original(path)

    policy.json = request
    with pytest.raises(OSError):
        gate.production_policy(policy, "workflow_dispatch", "refs/heads/main", SHA)


def test_policy_cli_network_failure_is_sanitized(monkeypatch, capsys):
    for name, value in {
        "GITHUB_REPOSITORY": "example/project",
        "GH_TOKEN": "synthetic",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/main",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        sys, "argv", ["verified_images.py", "production-policy", "--source-sha", SHA, "--layer", "site"]
    )

    def fail(*_):
        raise OSError("canary-secret")

    monkeypatch.setattr(gate.GitHub, "json", fail)
    assert gate.main() == 1
    assert "canary-secret" not in capsys.readouterr().err


@pytest.mark.parametrize("layer", ["", "invalid", "site;echo injected"])
def test_invalid_layer_is_rejected_before_api(monkeypatch, layer):
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/project")
    monkeypatch.setattr(sys, "argv", ["verified_images.py", "production-policy", "--source-sha", SHA, "--layer", layer])
    assert gate.main() == 1


@pytest.mark.parametrize("approved", [True, False])
def test_isolated_cli_runs_policy_without_project_imports(tmp_path, approved):
    # Fixture the external API at its adapter; execute the real CLI under -I.
    helper = ROOT / "tools/deploy/verified_images.py"
    policy = Policy()
    if not approved:
        policy.environment["protection_rules"] = []
    fixture = tmp_path / "policy.json"
    fixture.write_text(json.dumps([policy.comparison, policy.environment]))
    code = """
import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location('verified', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
responses = iter(json.load(open(sys.argv[2])))
module.GitHub.json = lambda self, path: next(responses)
os.environ.update(GITHUB_REPOSITORY='example/project', GH_TOKEN='synthetic',
                  GITHUB_EVENT_NAME='workflow_dispatch', GITHUB_REF='refs/heads/main')
sys.argv = ['verified_images.py', 'production-policy', '--source-sha', 'a'*40, '--layer', 'site']
raise SystemExit(module.main())
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(helper), str(fixture)], capture_output=True, text=True
    )
    assert result.returncode == (0 if approved else 1), result.stderr
    if approved:
        assert "prevent_self_review=false" in result.stdout


def test_workflow_approval_and_policy_dominate_every_server_step():
    workflow = yaml.safe_load((ROOT / ".github/workflows/deploy-production.yml").read_text())
    assert workflow["concurrency"] == {"group": "production", "cancel-in-progress": False}
    jobs = workflow["jobs"]
    assert set(jobs) == {"verify-images", "deploy"}
    assert jobs["verify-images"]["if"] == "github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'"
    assert "environment" not in jobs["verify-images"]
    assert jobs["deploy"]["environment"] == "production"
    assert jobs["deploy"]["needs"] == "verify-images"
    for name, job in jobs.items():
        policy_index = next(i for i, s in enumerate(job["steps"]) if "production-policy" in s.get("run", ""))
        for index, step in enumerate(job["steps"]):
            assert not step.get("continue-on-error")
            if step.get("uses", "").startswith(("appleboy/ssh-action@", "appleboy/scp-action@")):
                assert name == "deploy" and index > policy_index
                assert not step.get("if")
        policy_step = job["steps"][policy_index]
        assert policy_step["env"]["GH_TOKEN"] == "${{ github.token }}"
        assert policy_step["env"]["SOURCE_SHA"].endswith("outputs.head_sha }}")
    deploy_steps = jobs["deploy"]["steps"]
    assert "with" not in deploy_steps[0]  # Policy comes from dispatch main, not old rollback source.
    assert deploy_steps[2]["with"]["ref"] == "${{ needs.verify-images.outputs.head_sha }}"
