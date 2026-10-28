"""Retired node Rift storage boundary; original implementation is archived."""

from typing import Any

from src.backend.features.rift.retirement import LegacyRiftRetiredError


class RiftSettingRepository:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def get(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def upsert(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()


class RiftNodePoolRepository:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def get(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def list_by_setting(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def upsert(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()


class RiftMembershipRepository:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def get(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def get_by_session(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def get_active_for_participant(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def list_by_instance(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def upsert(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def upsert_from_session_payload(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def update_snapshot_refs(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()

    async def mark_status(self, *args: Any, **kwargs: Any) -> Any:
        raise LegacyRiftRetiredError()
