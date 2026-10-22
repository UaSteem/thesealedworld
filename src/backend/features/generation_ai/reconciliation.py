from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from src.backend.features.generation_ai.integrations.task_payload_store import AIGenerationTaskPayloadStore
from src.backend.features.items.dto.ai import GeneratedItemTextDTO
from src.backend.infrastructure.generation_ai import AI_GENERATION_TASK_DOCUMENT_SCHEMA_VERSION

if TYPE_CHECKING:
    from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository

RECONCILIATION_GRACE = timedelta(hours=1)
RECONCILIATION_PAGE_SIZE = 100


async def reconcile_document(repository: AIGenerationTaskRepository, document: dict[str, Any]) -> str:
    """Repair only a provable missing pointer; retain all ambiguous payloads.

    Never create SQL work from Mongo, change task execution state or apply output.
    The caller owns the SQL transaction. Mongo classifications are observations,
    not authoritative state; the next pass corrects them after a late commit.
    """
    updated = document.get("updated_at")
    if not isinstance(updated, datetime):
        return "deferred"
    updated = updated.replace(tzinfo=UTC) if updated.tzinfo is None else updated.astimezone(UTC)
    if updated > datetime.now(UTC) - RECONCILIATION_GRACE:
        return "deferred"
    task_id = document.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        state = "invalid"
        task = None
    else:
        task = await repository.lock_for_reconciliation(task_id)
        if task is None:
            if await repository.exists_for_reconciliation(task_id):
                return "busy"
            state = "orphan"
        else:
            try:
                if task.task_type != "items.text" or task.output_kind != "json":
                    raise ValueError("Unsupported reconciliation task")
                AIGenerationTaskPayloadStore.validate_input_document(task, document)
                output = document.get("output_payload")
                if not isinstance(output, dict) or not isinstance(document.get("metadata"), dict):
                    raise ValueError("Invalid result document shape")
                if task.status == "done" or output:
                    GeneratedItemTextDTO.model_validate(output)
                state = "result_pending_review" if output and task.status != "done" else "linked"
            except (ValueError, TypeError, ValidationError):
                state = "conflict"
    if not await repository.payload_store.mark_reconciliation(document, state):
        return "stale"
    if task is not None and state in {"linked", "result_pending_review"} and task.mongo_document_id is None:
        task.mongo_document_id = str(document["_id"])
        task.mongo_schema_version = AI_GENERATION_TASK_DOCUMENT_SCHEMA_VERSION
        task.mongo_status = "stored"
        await repository.session.flush()
        return "repaired" if state == "linked" else "repaired_result_pending_review"
    return state
