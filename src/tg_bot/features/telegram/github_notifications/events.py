"""Pure GitHub event filtering and bounded Telegram HTML rendering."""

import re
from dataclasses import dataclass
from datetime import datetime
from html import escape
from typing import Any


@dataclass(frozen=True)
class Notification:
    topic: str
    text: str
    entity: str = ""
    version: int = 0
    merged: bool = False


def _text(value: Any, limit: int = 400) -> str:
    # Bound escaped output, without cutting an HTML entity or an open tag.
    result = ""
    for character in str(value or "")[:limit]:
        escaped = escape(character)
        if len(result) + len(escaped) > limit:
            break
        result += escaped
    return result


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object")
    return value


def notification_for(
    event: str, payload: dict[str, Any], repositories: set[str], branches: set[str]
) -> Notification | None:
    repository = _object(payload.get("repository", {}))
    repo = str(repository.get("full_name", ""))
    if repo.casefold() not in repositories or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}", repo):
        return None
    repo_url = f"https://github.com/{repo}"
    heading = f"<b>{_text(repo, 200)}</b>"
    if event == "push":
        ref = str(payload.get("ref", ""))
        if (
            not ref.startswith("refs/heads/")
            or ref.removeprefix("refs/heads/") not in branches
            or payload.get("deleted")
        ):
            return None
        branch = ref.removeprefix("refs/heads/")
        commits = payload.get("commits", [])
        if not isinstance(commits, list):
            raise ValueError("Expected commits list")
        lines = []
        for raw_commit in commits[:3]:
            commit = _object(raw_commit)
            lines.append(
                f"• {_text(str(commit.get('id', ''))[:7], 10)} {_text(str(commit.get('message', '')).splitlines()[0] if commit.get('message') else '', 500)}"
            )
        text = f"{heading}\nPush → <code>{_text(branch, 200)}</code>\n" + "\n".join(lines)
        return Notification("github", f'{text}\n<a href="{escape(repo_url)}">Репозиторий</a>')
    if event == "pull_request":
        if payload.get("action") not in {
            "opened",
            "reopened",
            "synchronize",
            "closed",
            "edited",
            "ready_for_review",
            "converted_to_draft",
        }:
            return None
        pr = _object(payload.get("pull_request", {}))
        base = _object(pr.get("base", {}))
        if base.get("ref") not in branches:
            return None
        base_repo = _object(base.get("repo", {})).get("full_name", repo)
        if str(base_repo).casefold() != repo.casefold():
            return None
        number = int(pr.get("number", payload.get("number", 0)))
        if number <= 0:
            raise ValueError("Invalid PR number")
        updated_at = datetime.fromisoformat(str(pr.get("updated_at", "")).replace("Z", "+00:00"))
        if updated_at.tzinfo is None:
            raise ValueError("PR updated_at requires a timezone")
        version = int(updated_at.timestamp() * 1000)
        merged = bool(pr.get("merged"))
        status = "merged" if merged else str(pr.get("state", "open"))
        text = f'{heading}\nPR #{number}: <b>{_text(status, 50)}</b> → <code>{_text(base["ref"], 200)}</code>\n{_text(pr.get("title"), 1200)}\n<a href="{escape(repo_url)}/pull/{number}">Открыть PR</a>'
        return Notification("github", text, f"pr:{repo.casefold()}:{number}", version, merged)
    if event in {"check_run", "workflow_run"}:
        if payload.get("action") != "completed":
            return None
        run = _object(payload.get(event, {}))
        run_branch = run.get("head_branch")
        if event == "check_run":
            run_branch = _object(run.get("check_suite", {})).get("head_branch")
        if run_branch not in branches or run.get("conclusion") not in {
            "success",
            "failure",
            "timed_out",
            "action_required",
            "cancelled",
            "startup_failure",
        }:
            return None
        text = f'{heading}\n{_text(event)}: <b>{_text(run.get("conclusion"), 100)}</b>\n{_text(run.get("name"), 1000)}\nВетка: <code>{_text(run_branch, 200)}</code>\n<a href="{escape(repo_url)}/actions">GitHub Actions</a>'
        return Notification("deploy", text)
    if event == "deployment_status":
        deployment = _object(payload.get("deployment", {}))
        deployment_status = _object(payload.get("deployment_status", {}))
        branch = str(deployment.get("ref", "")).removeprefix("refs/heads/")
        if branch not in branches or deployment_status.get("state") not in {"success", "failure", "error"}:
            return None
        text = f'{heading}\nDeployment: <b>{_text(deployment_status.get("state"), 100)}</b>\n{_text(deployment.get("environment"), 400)} → <code>{_text(branch, 200)}</code>\n{_text(deployment_status.get("description"), 1000)}\n<a href="{escape(repo_url)}/deployments">Деплои</a>'
        return Notification("deploy", text)
    return None
