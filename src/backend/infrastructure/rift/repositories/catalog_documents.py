"""Retired node Rift storage boundary; original implementation is archived."""

from typing import Any

from src.backend.features.rift.retirement import LegacyRiftRetiredError


class RiftCatalogDocumentRepository:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def ensure_indexes(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def upsert_setting_document(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def upsert_node_document(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()
