from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from pydantic import ValidationError

from src.backend.infrastructure.generation_ai import (
    AI_GENERATION_TASK_DOCUMENT_SCHEMA_VERSION,
    AIGenerationTaskDocumentRepository,
)
from src.backend.infrastructure.generation_ai.task_documents import AI_GENERATION_TASK_DOCUMENT_KIND

if TYPE_CHECKING:
    from src.backend.features.generation_ai.dto import AIGenerationTaskResultDTO, AIGenerationTaskSpecDTO
    from src.backend.features.generation_ai.models import AIGenerationTask


class AIGenerationTaskPayloadStore:
    """Feature-facing boundary for heavy AI generation task payload documents."""

    def __init__(self, repository: AIGenerationTaskDocumentRepository | None = None) -> None:
        self.repository = repository or AIGenerationTaskDocumentRepository()

    async def create_task_document(
        self,
        *,
        task: AIGenerationTask,
        spec: AIGenerationTaskSpecDTO,
        identity_key: str,
    ) -> str:
        return await self.repository.write_initial(task=task, spec=spec, identity_key=identity_key)

    async def fetch_task_document(self, task_id: str) -> dict[str, Any] | None:
        return await self.repository.fetch_by_task_id(task_id)

    async def reconciliation_page(self, **kwargs: Any) -> list[dict[str, Any]]:
        return await self.repository.reconciliation_page(**kwargs)

    async def mark_reconciliation(self, document: dict[str, Any], state: str) -> bool:
        return await self.repository.mark_reconciliation(document, state)

    @staticmethod
    def validate_input_document(task: AIGenerationTask, document: dict[str, Any] | None) -> None:
        """Validate durable input before accepting or consuming a live item job."""
        from src.backend.features.generation_ai.dto import AIGenerationTaskSpecDTO
        from src.backend.features.generation_ai.identity import build_generation_task_identity_key
        from src.backend.features.items.dto.instance import ItemGenerationRequestDTO

        if not isinstance(document, dict):
            raise ValueError(f"Missing AI generation input document for task_id={task.id}")
        expected = {
            "document_kind": AI_GENERATION_TASK_DOCUMENT_KIND,
            "schema_version": AI_GENERATION_TASK_DOCUMENT_SCHEMA_VERSION,
            "task_id": task.id,
            "identity_key": task.identity_key,
            "task_type": task.task_type,
            "entity_type": task.entity_type,
            "entity_id": task.entity_id,
            "output_kind": task.output_kind,
        }
        if not document.get("_id") or any(document.get(key) != value for key, value in expected.items()):
            raise ValueError(f"Invalid AI generation input document identity/schema for task_id={task.id}")
        if task.mongo_document_id is not None and str(document["_id"]) != task.mongo_document_id:
            raise ValueError(f"Invalid AI generation input document pointer for task_id={task.id}")
        payload = document.get("input_payload")
        if not isinstance(payload, dict) or not isinstance(payload.get("request"), dict):
            raise ValueError(f"Invalid AI generation input payload for task_id={task.id}")
        try:
            ItemGenerationRequestDTO.model_validate(payload["request"])
        except ValidationError:
            raise ValueError(f"Invalid AI generation item request for task_id={task.id}") from None
        prompt = document.get("prompt_payload")
        if not isinstance(prompt, dict):
            raise ValueError(f"Invalid AI generation prompt payload for task_id={task.id}")
        persisted_spec = AIGenerationTaskSpecDTO(
            task_type=task.task_type,
            entity_type=task.entity_type,
            entity_id=task.entity_id,
            season_id=task.season_id,
            asset_hash=task.asset_hash,
            output_kind="json",
            input_payload=payload,
            prompt_payload=prompt,
        )
        if build_generation_task_identity_key(persisted_spec) != task.identity_key:
            raise ValueError(f"AI generation input no longer matches task identity for task_id={task.id}")

    async def record_result(
        self,
        *,
        task: AIGenerationTask,
        result: AIGenerationTaskResultDTO,
        metadata: dict[str, Any],
    ) -> str:
        document = await self.fetch_task_document(task.id)
        self.validate_input_document(task, document)
        return await self.repository.record_result(task=task, result=result, metadata=metadata)

    async def record_error(self, *, task: AIGenerationTask, error: dict[str, Any]) -> str:
        return await self.repository.record_error(task=task, error=error)

    @staticmethod
    def apply_document(task: AIGenerationTask, document: dict[str, Any]) -> AIGenerationTask:
        schema_version = int(document.get("schema_version") or 0)
        if schema_version != AI_GENERATION_TASK_DOCUMENT_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported AI generation task document schema_version={schema_version} for task_id={task.id}"
            )
        hydrated_task = cast("Any", task)
        hydrated_task.prompt_payload = _payload_dict(document.get("prompt_payload"))
        hydrated_task.input_payload = _payload_dict(document.get("input_payload"))
        hydrated_task.output_payload = _payload_dict(document.get("output_payload"))
        hydrated_task.metadata_ = _payload_dict(document.get("metadata"))
        hydrated_task.error = _payload_dict(document.get("error"))
        return task


def _payload_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
