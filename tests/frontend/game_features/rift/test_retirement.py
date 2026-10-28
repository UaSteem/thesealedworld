"""Retirement prevents legacy calls while preserving the independent Hex harness."""

import hashlib
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import HTTPException

from src.frontend.game_features.rift.routes.pages import router
from src.frontend.game_features.rift.routes.test_hex_pages import router as hex_router
from src.frontend.integrations.backend_api.rift import BackendRiftApi
from src.frontend.integrations.backend_api.rift_dev import BackendRiftDevApi


@pytest.mark.parametrize("adapter,method", [
    (BackendRiftApi, "view"),
    (BackendRiftApi, "travel_start"),
    (BackendRiftApi, "travel_tick"),
    (BackendRiftApi, "action"),
    (BackendRiftApi, "complete"),
    (BackendRiftApi, "leave"),
    (BackendRiftDevApi, "start_starter_rift"),
    (BackendRiftDevApi, "screen"),
    (BackendRiftDevApi, "move"),
    (BackendRiftDevApi, "travel_start"),
    (BackendRiftDevApi, "travel_tick"),
    (BackendRiftDevApi, "action"),
    (BackendRiftDevApi, "rebuild"),
])
def test_legacy_adapter_refuses_without_network(adapter, method):
    client = Mock(spec=httpx.AsyncClient)
    api = adapter(client=client, base_url="http://backend.invalid")
    api._request = AsyncMock(side_effect=AssertionError("network must not run"))
    with pytest.raises(HTTPException) as error:
        getattr(api, method)().send(None)
    assert error.value.status_code == 410
    api._request.assert_not_awaited()


def test_node_routes_removed_hex_routes_preserved():
    assert not router.routes
    paths = {route.path for route in hex_router.routes}
    assert paths == {
        "/rifttest",
        "/game/rift/hex-test/move",
        "/game/rift/hex-test/resolve-combat",
        "/game/rift/hex-test/next-floor",
    }


def test_frontend_retirement_archive_hashes():
    root = Path(__file__).resolve().parents[4]
    manifest = root / "archive/rift_legacy_retirement/2026-10-22/frontend-manifest.json"
    if not manifest.exists():
        pytest.skip("Local retirement archive is intentionally not versioned; its manifest is absent")
    for entry in json.loads(manifest.read_text(encoding="utf-8"))["files"]:
        saved = root / entry["archive"]
        assert hashlib.sha256(saved.read_bytes()).hexdigest() == entry["sha256"]
        if entry["action"] == "removed":
            assert not (root / entry["source"]).exists()
