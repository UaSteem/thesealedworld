"""Old storage adapters cannot accidentally revive the archived node runtime."""

import importlib

import pytest

from src.backend.features.rift.retirement import LegacyRiftRetiredError


@pytest.mark.parametrize(
    ("module", "name", "operation"),
    [
        ("managers.instance", "RiftInstanceStore", "get_instance"),
        ("managers.session", "RiftRunSessionStore", "get_session"),
        ("managers.portal", "RiftPortalStore", "get_portal"),
        ("managers.presence", "RiftPresenceStore", "get_node_occupants"),
        ("managers.restore", "RiftRestoreLock", "run_once"),
        ("repositories.state", "RiftMembershipRepository", "get_active_for_participant"),
        ("repositories.snapshots", "RiftRuntimeSnapshotRepository", "get_snapshot"),
        ("repositories.catalog_documents", "RiftCatalogDocumentRepository", "ensure_indexes"),
    ],
)
def test_retired_storage_rejects_before_access(module, name, operation):
    class ForbiddenStorage:
        def __getattr__(self, key):
            raise AssertionError(f"Retired adapter accessed storage: {key}")

    adapter_type = getattr(importlib.import_module(f"src.backend.infrastructure.rift.{module}"), name)
    adapter = adapter_type(ForbiddenStorage())
    with pytest.raises(LegacyRiftRetiredError):
        getattr(adapter, operation)("old-id").send(None)
