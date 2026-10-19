"""Bind manual deployment to a successful release build and immutable images."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

SERVICES = ("site", "game", "chat", "worker", "tg-bot", "nginx")
WORKFLOW = ".github/workflows/build-images.yml"
MANIFEST_FILE = "release-images.json"
MAX_ARCHIVE = 2 * 1024 * 1024
MAX_JSON = 64 * 1024


class VerificationError(ValueError):
    """The selected build cannot authorize deployment."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def positive_id(value: Any) -> int:
    require(type(value) is int and value > 0, "Invalid build identity")
    return value


def mapping(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "Invalid structured build metadata")
    return value


def validate_manifest(data: Any, repository: str, run_id: int, attempt: int, sha: str) -> dict[str, str]:
    require(isinstance(data, dict), "Invalid image manifest")
    require(type(data.get("schema")) is int and data["schema"] == 1, "Unsupported image manifest schema")
    require(data.get("repository") == repository, "Foreign image manifest")
    require(positive_id(data.get("run_id")) == run_id, "Image manifest run mismatch")
    require(positive_id(data.get("run_attempt")) == attempt, "Image manifest attempt mismatch")
    require(re.fullmatch(r"[0-9a-f]{40}", sha) is not None, "Invalid source SHA")
    require(data.get("head_sha") == sha, "Image manifest source mismatch")
    version = data.get("version")
    require(
        isinstance(version, str) and re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", version) is not None,
        "Invalid image version",
    )
    require(version != "latest", "Mutable latest alias is not a deployment target")
    images = data.get("images")
    require(isinstance(images, dict) and set(images) == set(SERVICES), "Incomplete image manifest")
    prefix = f"ghcr.io/{repository.lower()}-"
    for service, image in images.items():
        require(
            isinstance(image, str)
            and re.fullmatch(re.escape(f"{prefix}{service}@sha256:") + r"[0-9a-f]{64}", image) is not None,
            "Invalid immutable image reference",
        )
    return images


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


class GitHub:
    """Authenticated API requests; signed archive download never receives the token."""

    def __init__(self, repository: str, token: str) -> None:
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is not None, "Invalid repository")
        require(bool(token), "GitHub token is required")
        self.base = f"https://api.github.com/repos/{repository}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.opener = urllib.request.build_opener(NoRedirect())

    def json(self, path: str) -> Any:
        request = urllib.request.Request(self.base + path, headers=self.headers)
        with self.opener.open(request, timeout=30) as response:
            raw = response.read(MAX_ARCHIVE + 1)
        require(len(raw) <= MAX_ARCHIVE, "GitHub API response too large")
        return json.loads(raw)

    def archive(self, artifact_id: int) -> bytes:
        request = urllib.request.Request(self.base + f"/actions/artifacts/{artifact_id}/zip", headers=self.headers)
        try:
            self.opener.open(request, timeout=30).close()
        except urllib.error.HTTPError as error:
            require(error.code == 302, "Artifact download was not authorized")
            location = error.headers.get("Location", "")
        else:
            raise VerificationError("Expected signed artifact download")
        parsed = urllib.parse.urlsplit(location)
        require(
            parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password,
            "Invalid artifact download location",
        )
        # No Authorization header, including on subsequent redirects.
        with self.opener.open(urllib.request.Request(location), timeout=30) as response:
            raw = response.read(MAX_ARCHIVE + 1)
        require(len(raw) <= MAX_ARCHIVE, "Artifact archive too large")
        return raw


def verify(client: Any, repository: str, run_id: int, image_ref: str) -> dict[str, str]:
    positive_id(run_id)
    workflow = mapping(client.json("/actions/workflows/build-images.yml"))
    run = mapping(client.json(f"/actions/runs/{run_id}"))
    require(
        run.get("id") == run_id and run.get("workflow_id") == positive_id(workflow.get("id")), "Wrong build workflow"
    )
    require(workflow.get("path") == WORKFLOW and run.get("path") == WORKFLOW, "Wrong build workflow path")
    require(
        mapping(run.get("repository")).get("full_name") == repository
        and mapping(run.get("head_repository")).get("full_name") == repository,
        "Foreign build repository",
    )
    require(run.get("event") in {"push", "workflow_dispatch"}, "Unsupported build event")
    require(run.get("status") == "completed" and run.get("conclusion") == "success", "Build has not succeeded")
    attempt = positive_id(run.get("run_attempt"))
    sha = run.get("head_sha")
    if not isinstance(sha, str):
        raise VerificationError("Invalid build SHA")
    require(re.fullmatch(r"[0-9a-f]{40}", sha) is not None, "Invalid build SHA")
    jobs = mapping(client.json(f"/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100"))
    require(isinstance(jobs.get("jobs"), list), "Invalid build job listing")
    require(
        type(jobs.get("total_count")) is int
        and jobs["total_count"] == len(jobs.get("jobs", []))
        and jobs["total_count"] <= 100,
        "Incomplete build job listing",
    )
    for name in ("Quality Gate", "Build and Push Images"):
        selected = [job for job in jobs["jobs"] if mapping(job).get("name") == name]
        require(
            len(selected) == 1
            and selected[0].get("conclusion") == "success"
            and selected[0].get("status") == "completed"
            and selected[0].get("run_id") == run_id
            and selected[0].get("head_sha") == sha,
            "Required build job has not succeeded",
        )
    artifacts = mapping(client.json(f"/actions/runs/{run_id}/artifacts?per_page=100"))
    require(isinstance(artifacts.get("artifacts"), list), "Invalid build artifact listing")
    require(
        type(artifacts.get("total_count")) is int
        and artifacts["total_count"] == len(artifacts.get("artifacts", []))
        and artifacts["total_count"] <= 100,
        "Incomplete build artifact listing",
    )
    matching = [item for item in artifacts["artifacts"] if mapping(item).get("name") == f"release-images-{attempt}"]
    require(len(matching) == 1 and matching[0].get("expired") is False, "Build image manifest missing or expired")
    artifact = matching[0]
    origin = mapping(artifact.get("workflow_run"))
    require(
        origin.get("id") == run_id
        and origin.get("head_sha") == sha
        and origin.get("repository_id") == positive_id(run["repository"].get("id"))
        and origin.get("head_repository_id") == positive_id(run["head_repository"].get("id")),
        "Foreign build artifact",
    )
    raw = client.archive(positive_id(artifact.get("id")))
    require(artifact.get("digest") == "sha256:" + hashlib.sha256(raw).hexdigest(), "Artifact digest mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(archive.namelist() == [MANIFEST_FILE], "Unexpected image manifest archive contents")
        require(archive.getinfo(MANIFEST_FILE).file_size <= MAX_JSON, "Image manifest too large")
        data = json.loads(archive.read(MANIFEST_FILE))
    images = validate_manifest(data, repository, run_id, attempt, sha)
    require(image_ref in {sha, data["version"]}, "Selected image_ref does not belong to this build")
    # Catch a rerun begun while verification was in progress, before authorization.
    final = mapping(client.json(f"/actions/runs/{run_id}"))
    require(
        final.get("run_attempt") == attempt
        and final.get("status") == "completed"
        and final.get("conclusion") == "success",
        "Build changed during verification",
    )
    return {"head_sha": sha, **{f"image_{service.replace('-', '_')}": images[service] for service in SERVICES}}


def production_policy(client: Any, event: str, ref: str, sha: str) -> bool:
    """Require trusted dispatch, a main ancestor and configured environment approval.

    GitHub enforces the actual approval before starting the environment job. This
    check rejects an accidentally auto-created, unprotected environment as well.
    Return the configured self-review policy without imposing a second operator.
    """
    require(event == "workflow_dispatch" and ref == "refs/heads/main", "Production dispatch must use main")
    require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha) is not None, "Invalid source SHA")
    comparison = mapping(client.json(f"/compare/{sha}...main"))
    require(
        comparison.get("status") in {"ahead", "identical"}
        and mapping(comparison.get("merge_base_commit")).get("sha") == sha,
        "Production source is not in main history",
    )
    environment = mapping(client.json("/environments/production"))
    require(environment.get("name") == "production", "Wrong production environment")
    rules = environment.get("protection_rules")
    if not isinstance(rules, list):
        raise VerificationError("Production approval configuration unavailable")
    approvals = [rule for rule in rules if mapping(rule).get("type") == "required_reviewers"]
    require(len(approvals) == 1, "Production requires reviewer approval")
    approval = approvals[0]
    reviewers = approval.get("reviewers")
    require(isinstance(reviewers, list) and bool(reviewers), "Production reviewers missing")
    for reviewer in reviewers:
        entry = mapping(reviewer)
        require(entry.get("type") in {"User", "Team"}, "Invalid production reviewer type")
        positive_id(mapping(entry.get("reviewer")).get("id"))
    prevent_self_review = approval.get("prevent_self_review")
    require(type(prevent_self_review) is bool, "Production self-review policy unavailable")
    return prevent_self_review


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("manifest", "verify", "production-policy"))
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--image-ref")
    parser.add_argument("--source-sha")
    parser.add_argument("--layer")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        repository = os.environ["GITHUB_REPOSITORY"]
        if args.mode == "production-policy":
            require(args.layer in {"infra", "site", "game", "tg-bot", "full"}, "Invalid production layer")
            prevent_self_review = production_policy(
                GitHub(repository, os.environ["GH_TOKEN"]),
                os.environ["GITHUB_EVENT_NAME"],
                os.environ["GITHUB_REF"],
                args.source_sha or "",
            )
            print(f"Production approval configured; prevent_self_review={str(prevent_self_review).lower()}")
            return 0
        positive_id(args.run_id)
        require(args.output is not None, "Output path is required")
        if args.mode == "manifest":
            sha = os.environ["GITHUB_SHA"]
            attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
            data = {
                "schema": 1,
                "repository": repository,
                "run_id": args.run_id,
                "run_attempt": attempt,
                "head_sha": sha,
                "version": os.environ["VERSION"],
                "images": {
                    service: f"ghcr.io/{repository.lower()}-{service}@{os.environ['DIGEST_' + service.upper().replace('-', '_')]}"
                    for service in SERVICES
                },
            }
            validate_manifest(data, repository, args.run_id, attempt, sha)
            args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        else:
            data = verify(GitHub(repository, os.environ["GH_TOKEN"]), repository, args.run_id, args.image_ref or "")
            args.output.write_text("".join(f"{key}={value}\n" for key, value in data.items()), encoding="utf-8")
    except (VerificationError, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile):
        # Never print API exceptions: signed URLs and credentials are not diagnostics.
        print("Release image verification failed; deployment is blocked.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
