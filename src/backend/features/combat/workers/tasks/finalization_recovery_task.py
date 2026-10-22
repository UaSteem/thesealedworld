from __future__ import annotations

from src.backend.features.combat.services.finalization_journal import CombatFinalizationJournal
from src.shared.infrastructure.log_task_wrapper import logged_task


@logged_task
async def combat_finalization_recovery_task(ctx: dict) -> None:
    """Redis jobs are delivery hints; PostgreSQL pending work survives restarts."""
    journal = ctx.get("combat_finalization_journal") or CombatFinalizationJournal()
    queue = ctx["redis"]
    cursor = ""
    while True:
        pending = await journal.pending(after_combat_id=cursor)
        for payload in pending:
            await queue.enqueue_job("victory_finalizer_task", payload)
        if len(pending) < 100:
            break
        cursor = pending[-1]["session_id"]
    cursor = ""
    while True:
        archives = await journal.pending_archives(after_combat_id=cursor)
        for combat_id in archives:
            await queue.enqueue_job("combat_finalization_persist_task", {"combat_id": combat_id})
        if len(archives) < 100:
            break
        cursor = archives[-1]
