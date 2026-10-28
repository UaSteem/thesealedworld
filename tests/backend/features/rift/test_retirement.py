"""Retirement rejects gameplay while preserving the gated Hex prototype."""

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from src.backend.features.rift.api.router import build_rift_router
from src.backend.features.rift.integrations.runtime import RiftRuntimeIntegration
from src.backend.features.rift.retirement import LegacyRiftRetiredError


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("path", ["/api/game/rift/7/view", "/api/game/rift/7/leave", "/api/dev/rift/start"])
def test_old_node_routes_fail_without_app_state(method, path):
    from fastapi import HTTPException
    from starlette.routing import Match

    router = build_rift_router(enable_dev_routes=True)
    scope = {"type": "http", "path": path, "method": method, "root_path": ""}
    route = next(route for route in router.routes if route.matches(scope)[0] == Match.FULL)
    assert route.dependant.dependencies == []
    with pytest.raises(HTTPException) as error:
        route.endpoint().send(None)
    assert error.value.status_code == 410
    assert "retired" in error.value.detail


def test_disabled_dev_routes_remain_unavailable():
    router = build_rift_router(enable_dev_routes=False)
    assert all(not route.path.startswith("/api/dev/rift") for route in router.routes)
    assert any(route.path == "/api/game/rift/{legacy_path:path}" for route in router.routes)


def test_enabled_hex_routes_precede_legacy_catchall():
    router = build_rift_router(enable_dev_routes=True)
    paths = [route.path for route in router.routes]
    assert paths.index("/api/dev/rift/hex-test/start") < paths.index("/api/dev/rift/{legacy_path:path}")


def test_all_facade_operations_reject_without_touching_injected_stores():
    class ForbiddenStore:
        def __getattr__(self, name):
            raise AssertionError("Storage touched: " + name)

    runtime = RiftRuntimeIntegration(instance_store=ForbiddenStore(), session_store=ForbiddenStore())
    methods = [
        method for name, method in inspect.getmembers(runtime, inspect.iscoroutinefunction) if not name.startswith("_")
    ]
    assert len(methods) == 45
    for method in methods:
        with pytest.raises(LegacyRiftRetiredError) as error:
            method().send(None)
        assert error.value.status_code == 410
        assert error.value.error_code == "legacy_rift_retired"


def test_archived_domain_versions_match_original_hashes():
    root = Path(__file__).resolve().parents[4]
    manifest = root / "archive/rift_legacy_retirement/2026-10-22/domain-manifest.json"
    if not manifest.exists():
        pytest.skip("Local retirement archive is intentionally not versioned; its manifest is absent")
    entries = json.loads(manifest.read_text())["files"]
    assert entries
    for entry in entries:
        assert hashlib.sha256((root / entry["snapshot"]).read_bytes()).hexdigest() == entry["sha256"]
