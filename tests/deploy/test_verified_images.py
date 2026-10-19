"""Release promotion rejects unverified builds before any server operation."""

import copy
import hashlib
import io
import json
import subprocess
import sys
import urllib.error
import zipfile
from pathlib import Path

import pytest
import yaml
from tools.deploy import verified_images as gate

ROOT = Path(__file__).resolve().parents[2]
REPO = "example/project"
SHA = "a" * 40


class Build:
    def __init__(self):
        self.manifest = {
            "schema": 1,
            "repository": REPO,
            "run_id": 123,
            "run_attempt": 2,
            "head_sha": SHA,
            "version": "v0.5.2",
            "images": {name: f"ghcr.io/{REPO}-{name}@sha256:{'b' * 64}" for name in gate.SERVICES},
        }
        self.run = {
            "id": 123,
            "workflow_id": 42,
            "path": gate.WORKFLOW,
            "event": "push",
            "repository": {"full_name": REPO, "id": 1},
            "head_repository": {"full_name": REPO, "id": 1},
            "head_sha": SHA,
            "run_attempt": 2,
            "status": "completed",
            "conclusion": "success",
        }
        self.jobs = {
            "total_count": 2,
            "jobs": [
                {"name": name, "run_id": 123, "head_sha": SHA, "status": "completed", "conclusion": "success"}
                for name in ("Quality Gate", "Build and Push Images")
            ],
        }
        self.artifact = {
            "id": 345,
            "name": "release-images-2",
            "expired": False,
            "workflow_run": {"id": 123, "head_sha": SHA, "repository_id": 1, "head_repository_id": 1},
        }
        self.archive_name = gate.MANIFEST_FILE
        self.calls = []

    def archive(self, artifact_id):
        assert artifact_id == 345
        target = io.BytesIO()
        with zipfile.ZipFile(target, "w") as archive:
            archive.writestr(zipfile.ZipInfo(self.archive_name), json.dumps(self.manifest))
        return target.getvalue()

    def json(self, path):
        self.calls.append(path)
        if path.endswith("build-images.yml"):
            return {"id": 42, "path": gate.WORKFLOW}
        if "/jobs?" in path:
            assert "/attempts/2/" in path
            return self.jobs
        if "/artifacts?" in path:
            artifact = copy.deepcopy(self.artifact)
            artifact.setdefault("digest", "sha256:" + hashlib.sha256(self.archive(345)).hexdigest())
            return {"total_count": 1, "artifacts": [artifact]}
        return self.run


@pytest.mark.parametrize("ref", [SHA, "v0.5.2"])
def test_verified_build_returns_only_immutable_images(ref):
    build = Build()
    result = gate.verify(build, REPO, 123, ref)
    assert result["head_sha"] == SHA
    assert result["image_tg_bot"] == build.manifest["images"]["tg-bot"]
    assert len(result) == 7


@pytest.mark.parametrize(
    "change",
    [
        lambda b: b.run.update(conclusion="failure"),
        lambda b: b.run.update(conclusion="cancelled"),
        lambda b: b.run.update(status="in_progress"),
        lambda b: b.run.update(workflow_id=43),
        lambda b: b.run.update(path=".github/workflows/foreign.yml"),
        lambda b: b.run["head_repository"].update(full_name="foreign/fork"),
        lambda b: b.run.update(event="pull_request"),
        lambda b: b.jobs["jobs"][0].update(conclusion="skipped"),
        lambda b: b.jobs["jobs"][1].update(conclusion="failure"),
        lambda b: b.jobs.update(total_count=101),
        lambda b: b.artifact.update(name="release-images-1"),
        lambda b: b.artifact.update(expired=True),
        lambda b: b.artifact["workflow_run"].update(id=999),
        lambda b: b.artifact.update(digest="sha256:" + "0" * 64),
        lambda b: b.manifest.update(repository="foreign/project"),
        lambda b: b.manifest.update(head_sha="c" * 40),
        lambda b: b.manifest.update(run_attempt=1),
        lambda b: b.manifest["images"].pop("worker"),
        lambda b: b.manifest["images"].update(site=f"ghcr.io/{REPO}-site:latest"),
        lambda b: b.manifest["images"].update(site="ghcr.io/foreign/project-site@sha256:" + "b" * 64),
        lambda b: b.manifest["images"].update(site=f"ghcr.io/{REPO}-site@sha256:invalid"),
        lambda b: setattr(b, "archive_name", "../release-images.json"),
    ],
)
def test_build_or_manifest_mismatch_blocks_promotion(change):
    build = Build()
    change(build)
    with pytest.raises(gate.VerificationError):
        gate.verify(build, REPO, 123, SHA)


@pytest.mark.parametrize("ref", ["latest", "v0.5.1", "a" * 12, "injected\nimage_site=evil"])
def test_unrelated_ref_blocks_promotion(ref):
    with pytest.raises(gate.VerificationError):
        gate.verify(Build(), REPO, 123, ref)


def test_rerun_during_verification_blocks_promotion():
    build = Build()
    original = build.json

    def changing_run(path):
        result = copy.deepcopy(original(path))
        if len(build.calls) > 4 and path == "/actions/runs/123":
            result["run_attempt"] = 3
        return result

    build.json = changing_run
    with pytest.raises(gate.VerificationError):
        gate.verify(build, REPO, 123, SHA)


def test_manifest_cli_uses_build_action_digests(tmp_path, monkeypatch):
    build = Build()
    for key, value in {
        "GITHUB_REPOSITORY": REPO,
        "GITHUB_SHA": SHA,
        "GITHUB_RUN_ATTEMPT": "2",
        "VERSION": "v0.5.2",
        **{f"DIGEST_{name.upper().replace('-', '_')}": "sha256:" + "b" * 64 for name in gate.SERVICES},
    }.items():
        monkeypatch.setenv(key, value)
    output = tmp_path / gate.MANIFEST_FILE
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ROOT / "tools/deploy/verified_images.py"),
            "manifest",
            "--run-id",
            "123",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text()) == build.manifest
    monkeypatch.setenv("DIGEST_SITE", "invalid")
    output.unlink()
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ROOT / "tools/deploy/verified_images.py"),
            "manifest",
            "--run-id",
            "123",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert not output.exists()


def test_api_failure_cli_writes_no_authorization(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GH_TOKEN", "synthetic-credential")
    monkeypatch.setattr(
        sys,
        "argv",
        ["verified_images.py", "verify", "--run-id", "123", "--image-ref", SHA, "--output", str(tmp_path / "outputs")],
    )

    def fail(*args):
        raise OSError("signed-url?token=canary-do-not-log")

    monkeypatch.setattr(gate.GitHub, "json", fail)
    assert gate.main() == 1
    assert not (tmp_path / "outputs").exists()
    assert "canary" not in capsys.readouterr().err


def test_successful_verify_cli_writes_complete_authorization(tmp_path, monkeypatch):
    output = tmp_path / "github-outputs"
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GH_TOKEN", "synthetic-credential")
    monkeypatch.setattr(
        sys, "argv", ["verified_images.py", "verify", "--run-id", "123", "--image-ref", SHA, "--output", str(output)]
    )
    monkeypatch.setattr(gate, "GitHub", lambda *_: Build())
    assert gate.main() == 0
    assert dict(line.split("=", 1) for line in output.read_text().splitlines()) == gate.verify(Build(), REPO, 123, SHA)


def test_signed_archive_download_does_not_forward_api_token():
    client = gate.GitHub(REPO, "synthetic-credential")
    requests = []

    class Transport:
        def open(self, request, timeout):
            requests.append(request)
            assert timeout == 30
            if len(requests) == 1:
                raise urllib.error.HTTPError(
                    request.full_url, 302, "Found", {"Location": "https://storage.example/signed?token=download"}, None
                )
            return io.BytesIO(b"archive")

    client.opener = Transport()
    assert client.archive(345) == b"archive"
    assert requests[0].get_header("Authorization") == "Bearer synthetic-credential"
    assert requests[1].get_header("Authorization") is None


@pytest.mark.parametrize("metadata", [None, [], {"jobs": None}])
def test_malformed_api_metadata_blocks_promotion(metadata):
    build = Build()
    build.json = lambda _: metadata
    with pytest.raises(gate.VerificationError):
        gate.verify(build, REPO, 123, SHA)


def test_workflow_gate_dominates_all_ssh_and_uses_verified_source():
    deploy = yaml.safe_load((ROOT / ".github/workflows/deploy-production.yml").read_text())["jobs"]
    assert deploy["deploy"]["needs"] == "verify-images"
    assert "if" not in deploy["deploy"]
    selected_checkout = [step for step in deploy["deploy"]["steps"] if step.get("with", {}).get("ref")]
    assert selected_checkout[0]["with"]["ref"] == "${{ needs.verify-images.outputs.head_sha }}"
    for job in deploy.values():
        assert not job.get("continue-on-error")
        for step in job["steps"]:
            assert not step.get("continue-on-error")
    ssh = next(step for step in deploy["deploy"]["steps"] if step.get("name") == "SSH Deploy")
    assert "IMAGE_REF" not in ssh["with"]["script"]
    for name in gate.SERVICES:
        suffix = name.upper().replace("-", "_")
        assert f'update_var "DOCKER_IMAGE_{suffix}" "${{IMAGE_{suffix}}}"' in ssh["with"]["script"]
    build = yaml.safe_load((ROOT / ".github/workflows/build-images.yml").read_text())["jobs"]
    assert build["build-images"]["needs"] == "quality"
    steps = build["build-images"]["steps"]
    upload = steps[-1]
    action_repo, action_commit = upload["uses"].split("@")
    assert action_repo == "actions/upload-artifact"
    assert len(action_commit) == 40 and all(char in "0123456789abcdef" for char in action_commit)
    assert upload["with"]["name"] == "release-images-${{ github.run_attempt }}"
    assert not upload.get("if") and not upload.get("continue-on-error")
    assert len([step for step in steps[:-2] if step.get("id", "").startswith("image_")]) == 6
