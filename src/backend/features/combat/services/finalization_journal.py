from __future__ import annotations

import copy
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.backend.core.database import get_session_context
from src.backend.infrastructure.combat.models import CombatFinalization
from src.backend.infrastructure.combat.repositories import CombatFinalizationRepository


class CombatFinalizationJournal:
    """Durable work journal in the existing finalization metadata row.

    Each checkpoint holds a PostgreSQL row lock through its side effect. An
    uncertain external result is replayed using the owner's idempotency key.
    Frozen core facts have no TTL; large exchange traces stay in Redis/Mongo.
    """

    async def load(self, combat_id: str) -> dict[str, Any] | None:
        async with get_session_context() as session:
            row = await CombatFinalizationRepository(session).get_by_combat_id(combat_id)
            if row is None:
                return None
            work = (row.metadata_ or {}).get("finalization_work")
            if not work:
                if row.status == "finalized":
                    # Pre-journal results have no safe reward replay contract.
                    return {"combat_id": combat_id, "legacy_finalized": True}
                raise RuntimeError("Combat finalization has no recoverable frozen facts")
            return copy.deepcopy(work["payload"])

    async def freeze(self, payload: dict[str, Any]) -> dict[str, Any]:
        core = copy.deepcopy(payload)
        core["analytics"] = {}
        values = CombatFinalizationRepository._model_values(core, mongo_status="pending")
        values["status"] = "pending"
        async with get_session_context() as session:
            await session.execute(
                insert(CombatFinalization)
                .values(
                    combat_id=str(core["combat_id"]),
                    metadata_={"finalization_work": {"payload": core, "completed": []}},
                    **values,
                )
                .on_conflict_do_nothing(index_elements=[CombatFinalization.combat_id])
            )
            row = await CombatFinalizationRepository(session).get_by_combat_id(str(core["combat_id"]))
            work = (row.metadata_ or {}).get("finalization_work") if row else None
            if not work:
                raise RuntimeError("Existing combat result has no resumable finalization journal")
            return copy.deepcopy(work["payload"])

    async def run_step(self, combat_id: str, step: str, action: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        async with get_session_context() as session:
            result = await session.execute(
                select(CombatFinalization).where(CombatFinalization.combat_id == combat_id).with_for_update()
            )
            row = result.scalar_one()
            metadata = copy.deepcopy(row.metadata_ or {})
            work = metadata["finalization_work"]
            if step in work["completed"]:
                return
            await action(copy.deepcopy(work["payload"]))
            work["completed"].append(step)
            if step == "complete":
                row.status = "finalized"
            row.metadata_ = metadata

    async def block_retired(self, combat_id: str) -> None:
        async with get_session_context() as session:
            result = await session.execute(
                select(CombatFinalization).where(CombatFinalization.combat_id == combat_id).with_for_update()
            )
            row = result.scalar_one()
            row.status = "blocked_retired"
            row.metadata_ = {**(row.metadata_ or {}), "blocked_reason": "legacy_rift_retired"}

    async def pending(self, *, limit: int = 100, after_combat_id: str = "") -> list[dict[str, Any]]:
        async with get_session_context() as session:
            result = await session.execute(
                select(CombatFinalization)
                .where(
                    CombatFinalization.status == "pending",
                    CombatFinalization.combat_id > after_combat_id,
                    CombatFinalization.metadata_.has_key("finalization_work"),  # noqa: W601
                )
                .order_by(CombatFinalization.combat_id)
                .limit(limit)
            )
            return [
                {"session_id": row.combat_id, "winner": row.winner_team}
                for row in result.scalars()
                if (row.metadata_ or {}).get("finalization_work")
            ]

    async def pending_archives(self, *, limit: int = 100, after_combat_id: str = "") -> list[str]:
        async with get_session_context() as session:
            result = await session.execute(
                select(CombatFinalization.combat_id)
                .where(
                    CombatFinalization.status == "finalized",
                    CombatFinalization.mongo_status == "pending",
                    CombatFinalization.metadata_.has_key("finalization_work"),  # noqa: W601
                    CombatFinalization.combat_id > after_combat_id,
                )
                .order_by(CombatFinalization.combat_id)
                .limit(limit)
            )
            return list(result.scalars())
