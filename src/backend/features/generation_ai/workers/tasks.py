from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from loguru import logger

from src.backend.core.ai import AIService
from src.backend.core.database import get_manual_session_context
from src.backend.features.generation_ai.bootstrap import build_generation_ai_registry
from src.backend.features.generation_ai.integrations import AIGenerationTaskPayloadStore, CodexAIExecutor
from src.backend.features.generation_ai.leases import RUNNING_RECOVERY_PAGE_SIZE
from src.backend.features.generation_ai.reconciliation import (
    RECONCILIATION_GRACE,
    RECONCILIATION_PAGE_SIZE,
    reconcile_document,
)
from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository
from src.backend.features.generation_ai.scheduling import RECOVERY_PAGE_SIZE, replay_scheduling_page
from src.backend.features.generation_ai.services import GenerationAIService
from src.shared.infrastructure.log_task_wrapper import logged_task


@logged_task
async def generation_ai_process_task(ctx: dict[str, Any], task_id: str) -> dict[str, Any]:
    async with get_manual_session_context() as session:
        ai = ctx.get("ai")
        if ai is None:
            ai = AIService()
            ctx["ai"] = ai
        arq = ctx.get("generation_ai_arq")
        service = GenerationAIService(
            repository=AIGenerationTaskRepository(session),
            registry=build_generation_ai_registry(session=session),
            executor=CodexAIExecutor(ai),
            arq=arq,
            auto_schedule=False,
        )
        await service.process_task(task_id)
        await session.commit()
        await service.schedule_pending_task_ids()

    logger.bind(task_id=task_id).info("GenerationAiWorkerTaskProcessed")
    return {"status": "ok", "task_id": task_id}


async def generation_ai_recover_scheduling(ctx: dict[str, Any]) -> dict[str, int]:
    # Own short read-only session: only committed rows are visible, no provider
    # or Mongo access and no SQL transaction held during Redis operations.
    async with get_manual_session_context() as session:
        task_ids = await AIGenerationTaskRepository(session).list_schedulable_ids(
            after_id=ctx.get("generation_ai_recovery_cursor"), limit=RECOVERY_PAGE_SIZE
        )
    scheduled = await replay_scheduling_page(task_ids, ctx["generation_ai_arq"])
    # Keyset pagination avoids starvation by a full first page of already queued
    # jobs. Cursor loss is safe: restart at the beginning, SQL remains authority.
    ctx["generation_ai_recovery_cursor"] = task_ids[-1] if len(task_ids) == RECOVERY_PAGE_SIZE else None
    logger.bind(scanned_count=len(task_ids), scheduled_count=scheduled).info("GenerationAiSchedulingRecovered")
    return {"scanned": len(task_ids), "scheduled": scheduled}


async def generation_ai_reconcile_documents(ctx: dict[str, Any]) -> dict[str, int]:
    payload_store = AIGenerationTaskPayloadStore()
    documents = await payload_store.reconciliation_page(
        before=datetime.now(UTC) - RECONCILIATION_GRACE,
        after_id=ctx.get("generation_ai_reconciliation_cursor"),
        limit=RECONCILIATION_PAGE_SIZE,
    )
    counts: dict[str, int] = {}
    for document in documents:
        # A failed SQL/Mongo operation aborts the pass before cursor advancement.
        # One transaction per document bounds locks and allows partial progress.
        async with get_manual_session_context() as session:
            state = await reconcile_document(AIGenerationTaskRepository(session, payload_store=payload_store), document)
            await session.commit()
        counts[state] = counts.get(state, 0) + 1
    ctx["generation_ai_reconciliation_cursor"] = (
        str(documents[-1]["_id"]) if len(documents) == RECONCILIATION_PAGE_SIZE else None
    )
    logger.bind(outcomes=counts, scanned_count=len(documents)).info("GenerationAiDocumentsReconciled")
    return counts


async def generation_ai_recover_running(ctx: dict[str, Any]) -> dict[str, int]:
    async with get_manual_session_context() as session:
        counts = await AIGenerationTaskRepository(session).recover_expired_running(limit=RUNNING_RECOVERY_PAGE_SIZE)
        await session.commit()
    # A05-08 SQL scheduling recovery delivers pending rows after this commit;
    # no Redis success or in-memory state is needed to retain recovered intent.
    logger.bind(**counts).info("GenerationAiExpiredRunningRecovered")
    return counts


GENERATION_AI_TASKS = (generation_ai_process_task,)
