"""Recovery monitor rejects stale, corrupt or unrelated backup attestations."""

import copy
import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from tools.ops.recovery_check import REQUIRED_STORES, check_evidence, main

NOW = datetime(2026, 10, 22, tzinfo=UTC)


@pytest.fixture
def evidence(tmp_path):
    payload = b"synthetic backup bytes"
    digest = hashlib.sha256(payload).hexdigest()
    (tmp_path / "backup.bin").write_bytes(payload)
    entry = {
        "file": "backup.bin",
        "sha256": digest,
        "completed_at": (NOW - timedelta(hours=1)).isoformat(),
        "restore": {"backup_sha256": digest, "completed_at": NOW.isoformat(), "duration_seconds": 2},
    }
    return {
        "version": 1,
        "policy": {
            "max_backup_age_seconds": 7200,
            "max_restore_age_seconds": 86400,
            "max_restore_duration_seconds": 30,
        },
        "stores": {name: copy.deepcopy(entry) for name in REQUIRED_STORES},
    }


def test_complete_evidence_is_read_only(tmp_path, evidence):
    before = (tmp_path / "backup.bin").read_bytes()
    assert check_evidence(evidence, tmp_path, now=NOW) == []
    assert (tmp_path / "backup.bin").read_bytes() == before


@pytest.mark.parametrize("field", ["max_backup_age_seconds", "max_restore_age_seconds", "max_restore_duration_seconds"])
@pytest.mark.parametrize("value", [0, -1, True, "3600", float("nan"), float("inf")])
def test_policy_must_be_explicit_and_finite(tmp_path, evidence, field, value):
    evidence["policy"][field] = value
    with pytest.raises(ValueError):
        check_evidence(evidence, tmp_path, now=NOW)


@pytest.mark.parametrize("kind", ["corrupt", "different_restore", "escape", "future", "naive", "missing"])
def test_invalid_artifact_or_attestation_fails(tmp_path, evidence, kind):
    entry = evidence["stores"]["mongo"]
    if kind == "corrupt":
        (tmp_path / "backup.bin").write_bytes(b"corrupted")
    elif kind == "different_restore":
        entry["restore"]["backup_sha256"] = "0" * 64
    elif kind == "escape":
        entry["file"] = "../outside.bin"
    elif kind == "future":
        entry["restore"]["completed_at"] = (NOW + timedelta(seconds=1)).isoformat()
    elif kind == "naive":
        entry["completed_at"] = "2026-10-21T00:00:00"
    else:
        entry["file"] = "missing.bin"
    assert "mongo:invalid_evidence" in check_evidence(evidence, tmp_path, now=NOW)


def test_stale_and_slow_have_actionable_codes(tmp_path, evidence):
    evidence["policy"].update(max_backup_age_seconds=1, max_restore_duration_seconds=1)
    result = check_evidence(evidence, tmp_path, now=NOW + timedelta(days=2))
    assert "redis:backup_stale" in result
    assert "redis:restore_stale" in result
    assert "redis:restore_slow" in result


def test_missing_store_cannot_report_success(tmp_path, evidence):
    del evidence["stores"]["redis"]
    with pytest.raises(ValueError):
        check_evidence(evidence, tmp_path, now=NOW)


def test_cli_does_not_echo_sensitive_invalid_input(tmp_path, capsys):
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"private": "synthetic private credential"}')
    assert main([str(manifest), "--artifact-root", str(tmp_path)]) == 2
    assert capsys.readouterr().err == "recovery_evidence:invalid_manifest\n"


@pytest.mark.parametrize("document", [[], None, "invalid", {"version": True}])
def test_malformed_root_is_rejected(tmp_path, document):
    with pytest.raises(ValueError):
        check_evidence(document, tmp_path, now=NOW)
