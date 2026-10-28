"""Reject direct attempts to run the retired Rift persistence job."""

from typing import Any

from src.backend.features.rift.retirement import LegacyRiftRetiredError


async def flush_rift_run_task(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    raise LegacyRiftRetiredError("Legacy Rift persistence is retired")
