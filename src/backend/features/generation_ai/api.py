from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, cast

from fastapi import APIRouter, Depends

from src.backend.core.database import get_db
from src.backend.core.operator_auth import require_operator_read
from src.backend.features.generation_ai.dto import (
    AIGenerationOutputKind,
    AIGenerationTaskStatus,
    AIGenerationTaskViewDTO,
)
from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository

if TYPE_CHECKING:
    from src.backend.features.generation_ai.models import AIGenerationTask

router = APIRouter(
    prefix="/api/admin/generation-ai", tags=["generation-ai-admin"], dependencies=[Depends(require_operator_read)]
)


def get_generation_task_repository(db_session=Depends(get_db)) -> AIGenerationTaskRepository:
    return AIGenerationTaskRepository(db_session)


@router.get("/tasks/{task_id}", response_model=AIGenerationTaskViewDTO)
async def get_generation_task(
    task_id: str,
    repository: Annotated[AIGenerationTaskRepository, Depends(get_generation_task_repository)],
) -> AIGenerationTaskViewDTO:
    task = await repository.get(task_id)
    if task is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="AI generation task not found")
    return _task_view(task)


def _task_view(task: AIGenerationTask) -> AIGenerationTaskViewDTO:
    error = dict(getattr(task, "error", {}) or {})
    if getattr(task, "last_error_type", None) and error.get("type") != task.last_error_type:
        error = {"type": task.last_error_type, "message": task.last_error_message or ""}
    return AIGenerationTaskViewDTO(
        task_id=task.id,
        task_type=task.task_type,
        entity_type=task.entity_type,
        entity_id=task.entity_id,
        output_kind=cast("AIGenerationOutputKind", task.output_kind),
        status=cast("AIGenerationTaskStatus", task.status),
        storage_key=task.storage_key,
        generated_url=task.generated_url,
        asset_hash=task.asset_hash,
        metadata=dict(getattr(task, "metadata_", {}) or {}),
        error=error,
    )
