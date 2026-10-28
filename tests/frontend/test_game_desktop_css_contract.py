"""Guard the desktop-only game CSS import graph while mobile is archived."""

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "src/frontend/static/css"
IMPORT = re.compile(r'@import\s+url\([\"\']([^\"\']+)[\"\']\)\s*;')
MAX_WIDTH = re.compile(r"@media\s*([^{}]+)\{", re.I)


def game_sources():
    pending = [CSS / "game_bundle.css"]
    visited = set()
    while pending:
        path = pending.pop().resolve()
        if path in visited:
            continue
        visited.add(path)
        source = path.read_text(encoding="utf-8")
        yield path, source
        pending.extend(path.parent / name for name in IMPORT.findall(source))


def test_active_game_css_has_no_deferred_mobile_width_branches():
    deferred = []
    for path, source in game_sources():
        # Comments and CSS string content are not executable media conditions.
        syntax = re.sub(r'/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "", source, flags=re.S)
        for condition in MAX_WIDTH.findall(syntax):
            alternatives = re.split(r",|\bor\b", condition, flags=re.I)
            bounds = [re.findall(r"max-width\s*:\s*(\d+(?:\.\d+)?)px", part) for part in alternatives]
            if all(widths and min(map(float, widths)) < 1366 for widths in bounds):
                deferred.append(f"{path.relative_to(ROOT)}: {condition.strip()}")
    assert not deferred, "Mobile/tablet branches remain active:\n" + "\n".join(deferred)


def test_desktop_laptop_tier_remains_in_active_import_graph():
    source = "\n".join(source for _, source in game_sources())
    assert "@media (max-width: 1439px)" in source
    assert "--side-panel-width: 320px" in source
    assert "@media (min-width: 1440px)" in source
    assert "@media (min-width: 1600px)" in source


def test_mobile_archive_preserves_exact_source_and_extracted_ranges():
    manifest_path = ROOT / "archive/game_mobile_legacy/2026-10-24/manifest.json"
    if not manifest_path.exists():
        pytest.skip("Local mobile archive is intentionally not versioned; its manifest is absent")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["desktop_minimum_width_css_px"] == 1366
    assert manifest["entries"]
    for entry in manifest["entries"]:
        original = (ROOT / entry["original_archive_path"]).read_bytes()
        assert hashlib.sha256(original).hexdigest() == entry["original_sha256"]
        for chunk in entry["extracted"]:
            extracted = (ROOT / chunk["archive_path"]).read_bytes()
            assert extracted == original[chunk["source_start_byte"]:chunk["source_end_byte_exclusive"]]
            assert hashlib.sha256(extracted).hexdigest() == chunk["sha256"]
        if entry["action"] == "removed-mobile-only-file":
            assert not (ROOT / entry["original_path"]).exists()
    for entry in manifest["related_shared_sources"]:
        original = (ROOT / entry["archive_path"]).read_bytes()
        assert hashlib.sha256(original).hexdigest() == entry["sha256"]


def test_required_legacy_css_fixtures_match_manifest():
    fixture_root = ROOT / "tests/fixtures/legacy_css"
    manifest = json.loads((fixture_root / "manifest.json").read_text(encoding="utf-8"))
    records = manifest["files"]
    assert {record["path"] for record in records} == {
        "chat/input.css",
        "responsive/mobile_drawers.css",
        "responsive/mobile_header.css",
        "responsive/narrow_phone.css",
    }
    assert len(records) == 4
    for record in records:
        fixture = fixture_root / record["path"]
        assert hashlib.sha256(fixture.read_bytes()).hexdigest() == record["sha256"]
