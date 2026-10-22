from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.backend.features.generation_ai.dto import AIGenerationTaskResultDTO

if TYPE_CHECKING:
    from src.backend.core.ai import AIService
    from src.backend.features.generation_ai.models import AIGenerationTask


class CodexAIExecutor:
    def __init__(self, ai: AIService) -> None:
        self.ai = ai

    async def generate(self, task: AIGenerationTask, request: dict[str, Any]) -> AIGenerationTaskResultDTO:
        task_output_kind = getattr(task, "output_kind", None)
        if task_output_kind is not None and request.get("kind") != task_output_kind:
            raise RuntimeError(
                f"AI generation request kind mismatch for task_type={task.task_type}: "
                f"request={request.get('kind')!r} task_output_kind={task_output_kind!r}"
            )
        if request.get("kind") == "json":
            return await self._generate_json(task, request)

        raise RuntimeError(
            f"Unsupported AI generation request kind for task_type={task.task_type}: {request.get('kind')!r}"
        )

    async def _generate_json(self, task: AIGenerationTask, request: dict[str, Any]) -> AIGenerationTaskResultDTO:
        schema = request.get("schema")
        if schema is None:
            raise RuntimeError(f"AI JSON generation requires schema for task_type={task.task_type}")

        kwargs = dict(request.get("kwargs") or {})
        generated = await self.ai.generate_json(request["prompt"], schema=schema, **kwargs)
        if generated is None:
            raise RuntimeError(f"AI JSON provider returned no response for task_type={task.task_type}")
        if hasattr(generated, "model_dump"):
            payload = generated.model_dump(mode="json")
        elif isinstance(generated, dict):
            payload = generated
        else:
            payload = schema.model_validate(generated).model_dump(mode="json")
        return AIGenerationTaskResultDTO(output_payload=payload)
