from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from loguru import logger

from src.backend.features.generation_ai.dto import (
    AIGenerationEnqueueResultDTO,
    AIGenerationTaskResultDTO,
    AIGenerationTaskSpecDTO,
)
from src.backend.features.generation_ai.identity import build_generation_task_identity_key

if TYPE_CHECKING:
    from src.backend.features.generation_ai.handlers import AIGenerationExecutor
    from src.backend.features.generation_ai.registry import AIGenerationTaskRegistry
    from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository

GENERATION_AI_ARQ_TASK = "generation_ai_process_task"
ALLOWED_TASK_TYPES = frozenset({"items.text"})


class GenerationAIService:
    def __init__(
        self,
        *,
        repository: AIGenerationTaskRepository,
        registry: AIGenerationTaskRegistry,
        executor: AIGenerationExecutor | None = None,
        arq: Any | None = None,
        auto_schedule: bool = True,
    ) -> None:
        self.repository = repository
        self.registry = registry
        self.executor = executor
        self.arq = arq
        self.auto_schedule = auto_schedule
        self._pending_schedule_tasks: list[tuple[str, datetime | None]] = []

    async def enqueue_many(
        self,
        specs: list[AIGenerationTaskSpecDTO] | tuple[AIGenerationTaskSpecDTO, ...],
    ) -> AIGenerationEnqueueResultDTO:
        batch_id = str(uuid4())
        task_ids: list[str] = []
        schedulable_task_ids: list[str] = []
        created = 0
        reused = 0

        for spec in specs:
            self._validate_spec(spec)
            identity_key = build_generation_task_identity_key(spec)
            task = await self.repository.find_by_identity_key(identity_key)
            if task is None:
                task = await self.repository.create(spec, batch_id=batch_id, identity_key=identity_key)
                created += 1
            else:
                task = await self.repository.prepare_existing_for_enqueue(task, max_attempts=spec.max_attempts)
                reused += 1
            task_ids.append(task.id)
            if task.status in {"pending", "cooldown"}:
                schedulable_task_ids.append(task.id)

        if self.auto_schedule:
            scheduled = await self._schedule_tasks(schedulable_task_ids)
        else:
            self._pending_schedule_tasks.extend((task_id, None) for task_id in schedulable_task_ids)
            scheduled = 0
        logger.bind(batch_id=batch_id, created_count=created, reused_count=reused, scheduled_count=scheduled).info(
            "GenerationAiBatchEnqueued"
        )
        return AIGenerationEnqueueResultDTO(
            batch_id=batch_id,
            task_ids=task_ids,
            created=created,
            reused=reused,
            scheduled=scheduled,
        )

    async def process_task(self, task_id: str) -> AIGenerationTaskResultDTO | None:
        """Process on a dedicated manual-commit session.

        Commits the prepared claim internally before AI. The caller commits final
        application/retry and dispatches followups afterwards; do not wrap this
        operation in session.begin() or share its session with unrelated writes.
        """
        if await self.repository.retire_unsupported_by_id(task_id):
            logger.bind(task_id=task_id).info("GenerationAiRetiredTaskSkipped")
            return None
        task = await self.repository.claim_by_id(task_id)
        if task is None:
            existing = await self.repository.get(task_id)
            if existing is None:
                logger.bind(task_id=task_id).warning("GenerationAiTaskMissing")
            else:
                logger.bind(task_id=task_id, status=existing.status).info("GenerationAiTaskSkipped")
            return None
        return await self._execute_claimed_task(task)

    async def _execute_claimed_task(self, task: Any) -> AIGenerationTaskResultDTO | None:
        if task.task_type not in ALLOWED_TASK_TYPES or getattr(task, "output_kind", None) != "json":
            await self.repository.mark_failed(
                task.id,
                {
                    "type": "RetiredTaskType",
                    "message": "Only items.text JSON generation remains available.",
                },
            )
            logger.bind(task_id=task.id, task_type=task.task_type).info("GenerationAiRetiredTaskSkipped")
            return None
        try:
            handler = self.registry.resolve(task.task_type)
            if self.executor is None:
                raise RuntimeError("AI generation executor is not configured")
            request = await handler.build_request(task)
            self._validate_request(task, request)
        except Exception as exc:
            await self._mark_retry_or_failed(task.id, exc)
            return None

        # This is a processing-owned boundary, not an enqueue caller's unit of
        # work. Commit failures propagate; a provider must never run on an
        # uncommitted claim. No SQL transaction/connection exists during generate.
        token = await self.repository.commit_claim_for_provider(task)
        try:
            result = await self.executor.generate(task, request)
            if not isinstance(result, AIGenerationTaskResultDTO):
                result = AIGenerationTaskResultDTO.model_validate(result)
        except Exception as exc:
            owned = await self.repository.reacquire_claim(token)
            if owned is not None:
                await self._mark_retry_or_failed(owned.id, exc)
            else:
                logger.bind(task_id=token.task_id).warning("GenerationAiStaleProviderFailureSkipped")
            return None

        owned = await self.repository.reacquire_claim(token)
        if owned is None:
            logger.bind(task_id=token.task_id).warning("GenerationAiStaleProviderResultSkipped")
            return None
        # Roll back all handler SQL writes and completion before recording retry.
        # Keep identifiers outside the savepoint: rollback expires mapped state.
        owned_id = owned.id
        task_type = owned.task_type
        pending_schedule_count = len(self._pending_schedule_tasks)
        try:
            async with self.repository.application_transaction():
                followup_specs = await handler.apply_result(owned, result)
                await self.repository.mark_done(owned_id, result)
                await self._enqueue_followups(followup_specs)
        except Exception as exc:
            del self._pending_schedule_tasks[pending_schedule_count:]
            await self._mark_retry_or_failed(owned_id, exc)
            return None
        logger.bind(task_id=owned_id, task_type=task_type).info("GenerationAiTaskDone")
        return result

    async def claim_and_process_next(self) -> str | None:
        task = await self.repository.claim_next()
        if task is None:
            return None
        await self._execute_claimed_task(task)
        return task.id

    def _validate_spec(self, spec: AIGenerationTaskSpecDTO) -> None:
        if spec.task_type not in ALLOWED_TASK_TYPES or spec.output_kind != "json":
            raise ValueError("Only items.text JSON generation remains available")
        if not self.registry.has(spec.task_type):
            raise ValueError(f"AI generation task type is not registered: {spec.task_type}")

    def _validate_request(self, task: Any, request: dict[str, Any]) -> None:
        if not isinstance(request, dict):
            raise ValueError(f"AI generation handler returned invalid request for task_type={task.task_type}")

        kind = request.get("kind")
        if kind != task.output_kind:
            raise ValueError(
                f"AI generation request kind mismatch for task_type={task.task_type}: "
                f"request={kind!r} task_output_kind={task.output_kind!r}"
            )

        if kind == "json" and request.get("schema") is None:
            raise ValueError(f"AI JSON generation requires schema for task_type={task.task_type}")

    async def _schedule_tasks(self, task_ids: list[str]) -> int:
        scheduled = 0
        for task_id in task_ids:
            if await self._schedule_task(task_id):
                scheduled += 1
        return scheduled

    async def schedule_task_ids(self, task_ids: list[str] | tuple[str, ...]) -> int:
        return await self._schedule_tasks(list(task_ids))

    async def schedule_pending_task_ids(self) -> int:
        pending = list(dict.fromkeys(self._pending_schedule_tasks))
        self._pending_schedule_tasks.clear()
        scheduled = 0
        for task_id, not_before in pending:
            if await self._schedule_task(task_id, not_before=not_before):
                scheduled += 1
        return scheduled

    async def _enqueue_followups(
        self,
        specs: list[AIGenerationTaskSpecDTO] | tuple[AIGenerationTaskSpecDTO, ...] | None,
    ) -> AIGenerationEnqueueResultDTO | None:
        if not specs:
            return None
        return await self.enqueue_many(specs)

    async def _mark_retry_or_failed(self, task_id: str, exc: Exception) -> None:
        task = await self.repository.get(task_id)
        if task is None:
            return
        error = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        retry_limit = self._retry_limit(task, exc)
        if int(task.attempts or 0) >= retry_limit:
            await self.repository.mark_failed(task.id, error)
            logger.bind(task_id=task.id, attempt_count=task.attempts, retry_limit=retry_limit, error=error).warning(
                "GenerationAiTaskFailed"
            )
            return

        # Claim predicates use the persisted budget; save the effective limit in
        # the same transaction as cooldown so the next attempt remains reachable.
        task.max_attempts = retry_limit
        not_before = datetime.now(UTC) + timedelta(seconds=30)
        await self.repository.mark_cooldown(
            task.id,
            not_before=not_before,
            error=error,
        )
        if self.auto_schedule:
            await self._schedule_task(task.id, not_before=not_before)
        else:
            self._pending_schedule_tasks.append((task.id, not_before))
        logger.bind(task_id=task.id, attempt_count=task.attempts, retry_limit=retry_limit, error=error).warning(
            "GenerationAiTaskCooldown"
        )

    @staticmethod
    def _retry_limit(task: Any, exc: Exception) -> int:
        base_limit = max(1, int(task.max_attempts or 1))
        if GenerationAIService._is_retryable_json_schema_error(task, exc):
            return max(base_limit, 8)
        return base_limit

    @staticmethod
    def _is_retryable_json_schema_error(task: Any, exc: Exception) -> bool:
        if getattr(task, "output_kind", None) != "json":
            return False
        error_type = type(exc).__name__
        message = str(exc).lower()
        if error_type == "LLMProviderError" and "schema validation" in message:
            return True
        return "json generation failed schema validation" in message or "validation error for" in message

    async def _schedule_task(self, task_id: str, *, not_before: datetime | None = None) -> bool:
        if self.arq is None:
            return False
        kwargs: dict[str, Any] = {}
        if not_before is not None:
            kwargs["_defer_until"] = not_before
        await self.arq.enqueue_job(GENERATION_AI_ARQ_TASK, task_id, **kwargs)
        return True
