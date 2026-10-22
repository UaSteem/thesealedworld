from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from loguru import logger
from sqlalchemy import and_, func, or_, select

from src.backend.features.generation_ai.dto import AIGenerationClaimToken
from src.backend.features.generation_ai.identity import build_generation_task_identity_key
from src.backend.features.generation_ai.integrations import AIGenerationTaskPayloadStore
from src.backend.features.generation_ai.leases import RUNNING_LEASE
from src.backend.features.generation_ai.models import AIGenerationTask
from src.backend.infrastructure.generation_ai import AI_GENERATION_TASK_DOCUMENT_SCHEMA_VERSION

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

    from src.backend.features.generation_ai.dto import AIGenerationTaskResultDTO, AIGenerationTaskSpecDTO


class AIGenerationTaskRepository:
    def __init__(
        self,
        session: AsyncSession,
        *,
        payload_store: AIGenerationTaskPayloadStore | None = None,
    ) -> None:
        self.session = session
        self.payload_store = payload_store or AIGenerationTaskPayloadStore()

    async def create(
        self,
        spec: AIGenerationTaskSpecDTO,
        *,
        batch_id: str,
        identity_key: str,
        status: str = "pending",
    ) -> AIGenerationTask:
        task = AIGenerationTask(
            id=str(uuid4()),
            batch_id=batch_id,
            identity_key=identity_key,
            task_type=spec.task_type,
            entity_type=spec.entity_type,
            entity_id=spec.entity_id,
            season_id=spec.season_id,
            output_kind=spec.output_kind,
            status=status,
            priority=spec.priority,
            attempts=0,
            max_attempts=spec.max_attempts,
            model=spec.model,
            asset_hash=spec.asset_hash,
            storage_prefix=spec.storage_prefix,
            mongo_status="legacy",
        )
        await self._store_initial_payload(task, spec=spec, identity_key=identity_key)
        await self._require_live_input(task)
        self.session.add(task)
        await self.session.flush()
        return task

    async def find_by_identity_key(self, identity_key: str) -> AIGenerationTask | None:
        stmt = select(AIGenerationTask).where(AIGenerationTask.identity_key == identity_key)
        task = await self.session.scalar(stmt)
        return await self._hydrate_task(task)

    async def get(self, task_id: str) -> AIGenerationTask | None:
        task = await self.session.scalar(select(AIGenerationTask).where(AIGenerationTask.id == task_id))
        return await self._hydrate_task(task)

    async def find_existing(self, spec: AIGenerationTaskSpecDTO) -> AIGenerationTask | None:
        return await self.find_by_identity_key(build_generation_task_identity_key(spec))

    async def prepare_existing_for_enqueue(
        self,
        task: AIGenerationTask,
        *,
        max_attempts: int,
    ) -> AIGenerationTask:
        await self._require_live_input(task)
        if task.status in {"failed", "cancelled"}:
            task.status = "pending"
            task.attempts = 0
            task.max_attempts = max(int(task.max_attempts or 1), int(max_attempts))
            task.storage_key = None
            task.generated_url = None
            task.not_before = None
            task.claimed_at = None
            task.completed_at = None
            task.last_error_type = None
            task.last_error_message = None
            cast("Any", task).error = {}
            await self._record_error_payload(task, {})
            task.bump_revision()
            await self.session.flush()
            return task

        if task.status in {"pending", "cooldown"} and int(task.max_attempts or 1) < int(max_attempts):
            task.max_attempts = int(max_attempts)
            task.bump_revision()
            await self.session.flush()
        return task

    async def lock_for_reconciliation(self, task_id: str) -> AIGenerationTask | None:
        return await self.session.scalar(
            select(AIGenerationTask).where(AIGenerationTask.id == task_id).with_for_update(skip_locked=True)
        )

    async def exists_for_reconciliation(self, task_id: str) -> bool:
        return await self.session.scalar(select(AIGenerationTask.id).where(AIGenerationTask.id == task_id)) is not None

    async def list_schedulable_ids(
        self, *, after_id: str | None = None, limit: int = 100, now: datetime | None = None
    ) -> list[str]:
        """Read a bounded page of committed work; SQL status is the delivery intent.

        A separate recovery session must be used, never an enqueue caller's
        uncommitted transaction. No claim, payload hydration or attempt is made.
        """
        if not 1 <= limit <= 1000:
            raise ValueError("Recovery page limit must be between 1 and 1000")
        stmt = select(AIGenerationTask.id).where(
            AIGenerationTask.task_type == "items.text",
            AIGenerationTask.output_kind == "json",
            AIGenerationTask.status.in_(("pending", "cooldown")),
            AIGenerationTask.attempts < AIGenerationTask.max_attempts,
            or_(AIGenerationTask.not_before.is_(None), AIGenerationTask.not_before <= (now or datetime.now(UTC))),
        )
        if after_id is not None:
            stmt = stmt.where(AIGenerationTask.id > after_id)
        return list(await self.session.scalars(stmt.order_by(AIGenerationTask.id).limit(limit)))

    async def claim_next(self, *, now: datetime | None = None) -> AIGenerationTask | None:
        moment = now or await self._database_now()
        stmt = (
            select(AIGenerationTask)
            .where(
                AIGenerationTask.status.in_(("pending", "cooldown")),
                AIGenerationTask.attempts < AIGenerationTask.max_attempts,
                or_(AIGenerationTask.not_before.is_(None), AIGenerationTask.not_before <= moment),
            )
            .order_by(AIGenerationTask.priority.asc(), AIGenerationTask.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        task = await self.session.scalar(stmt)
        if task is None:
            return None
        if not await self._prepare_queued_claim(task, moment=moment):
            return None
        task.status = "running"
        task.attempts = int(task.attempts or 0) + 1
        task.claimed_at = moment
        task.not_before = None
        cast("Any", task).error = {}
        task.bump_revision()
        await self.session.flush()
        return task

    async def retire_unsupported_by_id(self, task_id: str) -> bool:
        """Terminally retire a queued unsupported job, irrespective of retry/time gates.

        Lock the selected row in this transaction; skip active competing workers and
        preserve historic terminal/running jobs. This never scans or repairs a queue.
        """
        task = await self.session.scalar(
            select(AIGenerationTask)
            .where(
                AIGenerationTask.id == task_id,
                AIGenerationTask.status.in_(("pending", "cooldown")),
                or_(AIGenerationTask.task_type != "items.text", AIGenerationTask.output_kind != "json"),
            )
            .with_for_update(skip_locked=True)
        )
        if task is None:
            return False
        await self.mark_failed(
            task.id,
            {
                "type": "RetiredTaskType",
                "message": "Only items.text JSON generation remains available.",
            },
        )
        return True

    async def claim_by_id(self, task_id: str, *, now: datetime | None = None) -> AIGenerationTask | None:
        moment = now or await self._database_now()
        stmt = (
            select(AIGenerationTask)
            .where(
                AIGenerationTask.id == task_id,
                AIGenerationTask.status.in_(("pending", "cooldown")),
                AIGenerationTask.attempts < AIGenerationTask.max_attempts,
                or_(AIGenerationTask.not_before.is_(None), AIGenerationTask.not_before <= moment),
            )
            .with_for_update(skip_locked=True)
        )
        task = await self.session.scalar(stmt)
        if task is None:
            return None
        if not await self._prepare_queued_claim(task, moment=moment):
            return None
        task.status = "running"
        task.attempts = int(task.attempts or 0) + 1
        task.claimed_at = moment
        task.not_before = None
        cast("Any", task).error = {}
        task.bump_revision()
        await self.session.flush()
        return task

    async def commit_claim_for_provider(self, task: AIGenerationTask) -> AIGenerationClaimToken:
        """Commit the prepared claim and release its connection before external AI.

        Processing owns this session's transaction boundary. Detach the provider
        snapshot before commit (including expire_on_commit=True sessions), and
        expire other loaded ORM state so apply reads fresh domain data afterwards.
        """
        await self.session.flush()
        token = AIGenerationClaimToken(task.id, task.revision, task.attempts, task.claimed_at, task.identity_key)
        self.session.expunge(task)
        await self.session.commit()
        self.session.expire_all()
        return token

    async def reacquire_claim(
        self, token: AIGenerationClaimToken, *, now: datetime | None = None
    ) -> AIGenerationTask | None:
        moment = now or await self._database_now()
        task = await self.session.scalar(
            select(AIGenerationTask)
            .where(
                AIGenerationTask.id == token.task_id,
                AIGenerationTask.status == "running",
                AIGenerationTask.revision == token.revision,
                AIGenerationTask.attempts == token.attempts,
                AIGenerationTask.claimed_at == token.claimed_at,
                AIGenerationTask.claimed_at > moment - RUNNING_LEASE,
                AIGenerationTask.identity_key == token.identity_key,
            )
            .with_for_update()
        )

        # A row lock may have waited across the deadline; check DB time again
        # after acquiring it, not only at statement construction.
        if (
            task is not None
            and now is None
            and (task.claimed_at is None or task.claimed_at <= await self._database_now() - RUNNING_LEASE)
        ):
            return None
        return task

    async def _database_now(self) -> datetime:
        moment = await self.session.scalar(select(func.clock_timestamp()))
        if not isinstance(moment, datetime):
            raise RuntimeError("GenerationAI requires a database clock")
        return moment

    async def recover_expired_running(self, *, limit: int = 100, now: datetime | None = None) -> dict[str, int]:
        """Recover abandoned execution intent without replaying stored results.

        A caller commits this bounded SKIP LOCKED batch before any ARQ delivery.
        Storage outages propagate; they must roll back, not terminalize, the batch.
        """
        if not 1 <= limit <= 1000:
            raise ValueError("Running recovery page limit must be between 1 and 1000")
        moment = now or await self._database_now()
        cutoff = moment - RUNNING_LEASE
        tasks = list(
            await self.session.scalars(
                select(AIGenerationTask)
                .where(
                    AIGenerationTask.task_type == "items.text",
                    AIGenerationTask.output_kind == "json",
                    AIGenerationTask.status == "running",
                    or_(
                        AIGenerationTask.claimed_at <= cutoff,
                        and_(AIGenerationTask.claimed_at.is_(None), AIGenerationTask.created_at <= cutoff),
                    ),
                )
                .order_by(AIGenerationTask.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
        )
        counts = {"scanned": len(tasks), "requeued": 0, "failed": 0}
        for task in tasks:
            reason = "LeaseExpired"
            message = "GenerationAI execution lease expired; retry delivery restored."
            failed = False
            if task.claimed_at is None:
                reason, message, failed = (
                    "MissingClaimTimestamp",
                    "Running task has no execution timestamp; review required.",
                    True,
                )
            else:
                try:
                    document = await self.payload_store.fetch_task_document(task.id)
                    AIGenerationTaskPayloadStore.validate_input_document(task, document)
                except ValueError:
                    reason, message, failed = (
                        "InvalidDurableInput",
                        "Durable generation input is missing or invalid; review required.",
                        True,
                    )
                else:
                    # Inspect raw durable output, not tolerant history hydration
                    # which intentionally coerces malformed payloads to {}.
                    output = (document or {}).get("output_payload")
                    if not isinstance(output, dict) or output:
                        reason, message, failed = (
                            "StoredResultNeedsReview",
                            "Stored result retained; automatic provider replay refused.",
                            True,
                        )
                    elif task.attempts >= task.max_attempts:
                        reason, message, failed = (
                            "LeaseAttemptsExhausted",
                            "Execution lease expired with no attempts remaining.",
                            True,
                        )
            task.status = "failed" if failed else "pending"
            task.claimed_at = None
            task.not_before = None
            task.completed_at = moment if failed else None
            error = {"type": reason, "message": message}
            cast("Any", task).error = error
            self._set_short_error(task, error)
            task.bump_revision()
            counts["failed" if failed else "requeued"] += 1
        await self.session.flush()
        return counts

    def application_transaction(self) -> AsyncSessionTransaction:
        """Rollback SQL application/completion together, retaining the outer claim lock.

        Mongo cannot join this savepoint: confirmed or ambiguous output remains
        durable evidence even when SQL application rolls back before retry.
        """
        return self.session.begin_nested()

    async def mark_done(self, task_id: str, result: AIGenerationTaskResultDTO) -> AIGenerationTask | None:
        task = await self.get(task_id)
        if task is None:
            return None
        await self._require_live_input(task)
        asset_metadata = {
            key: value
            for key, value in {
                "storage_backend": result.storage_backend,
                "content_type": result.content_type,
                "size_bytes": result.size_bytes,
            }.items()
            if value is not None
        }
        metadata = {**dict(getattr(task, "metadata_", {}) or {}), **asset_metadata, **result.metadata}
        # Do not mutate mapped completion fields until Mongo confirms the result.
        # A caller may catch the storage error and still commit this SQL session.
        await self._record_result_payload(task, result, metadata=metadata)
        task.status = "done"
        task.storage_key = result.storage_key
        task.generated_url = result.generated_url
        task.asset_hash = result.asset_hash or task.asset_hash
        cast("Any", task).metadata_ = metadata
        task.completed_at = datetime.now(UTC)
        cast("Any", task).error = {}
        task.last_error_type = None
        task.last_error_message = None
        task.bump_revision()
        await self.session.flush()
        return task

    async def mark_cooldown(
        self,
        task_id: str,
        *,
        not_before: datetime,
        error: dict[str, Any] | None = None,
    ) -> AIGenerationTask | None:
        task = await self.get(task_id)
        if task is None:
            return None
        task.status = "cooldown"
        task.not_before = not_before
        task_error = dict(error or {})
        cast("Any", task).error = task_error
        self._set_short_error(task, task_error)
        await self._record_error_payload(task, task_error)
        task.bump_revision()
        await self.session.flush()
        return task

    async def mark_failed(self, task_id: str, error: dict[str, Any]) -> AIGenerationTask | None:
        task = await self.get(task_id)
        if task is None:
            return None
        task.status = "failed"
        task_error = dict(error)
        cast("Any", task).error = task_error
        task.completed_at = datetime.now(UTC)
        self._set_short_error(task, task_error)
        await self._record_error_payload(task, task_error)
        task.bump_revision()
        await self.session.flush()
        return task

    async def _store_initial_payload(
        self,
        task: AIGenerationTask,
        *,
        spec: AIGenerationTaskSpecDTO,
        identity_key: str,
    ) -> None:
        document_id = await self.payload_store.create_task_document(
            task=task,
            spec=spec,
            identity_key=identity_key,
        )
        task.mongo_document_id = document_id
        task.mongo_status = "stored"
        task.mongo_schema_version = AI_GENERATION_TASK_DOCUMENT_SCHEMA_VERSION

    async def _prepare_queued_claim(self, task: AIGenerationTask, *, moment: datetime) -> bool:
        document = await self._require_live_input(task)
        if document is None:
            return True
        # Raw Mongo output is evidence, even when tolerant history hydration
        # would coerce it to {}. Never pay for/overwrite an ambiguous result.
        output = document.get("output_payload")
        if isinstance(output, dict) and not output:
            return True
        error = {
            "type": "StoredResultNeedsReview",
            "message": "Stored output exists or is malformed; review required before retry.",
        }
        task.status = "failed"
        task.claimed_at = None
        task.not_before = None
        task.completed_at = moment
        cast("Any", task).error = error
        self._set_short_error(task, error)
        task.bump_revision()
        # Preserve the complete Mongo document, including original result/error.
        # This matches lease recovery's manual-review policy without replaying it.
        await self.session.flush()
        return False

    async def _require_live_input(self, task: AIGenerationTask) -> dict[str, Any] | None:
        if task.task_type != "items.text" or task.output_kind != "json":
            return None
        # Always read anew. A transient ORM payload from GET or an earlier attempt
        # cannot prove that the durable document is currently readable and valid.
        document = await self.payload_store.fetch_task_document(task.id)
        AIGenerationTaskPayloadStore.validate_input_document(task, document)
        self.payload_store.apply_document(task, cast("dict[str, Any]", document))
        return cast("dict[str, Any]", document)

    async def _hydrate_task(self, task: AIGenerationTask | None) -> AIGenerationTask | None:
        if task is None:
            return None
        try:
            document = await self.payload_store.fetch_task_document(task.id)
        except Exception as exc:  # pragma: no cover - integration failure is environment-specific
            logger.bind(task_id=task.id, error=str(exc)).warning("GenerationAiPayloadHydrateFailed")
            return task
        if document is None:
            return task
        try:
            return self.payload_store.apply_document(task, document)
        except (ValueError, TypeError):
            logger.bind(task_id=task.id).warning("GenerationAiPayloadHydrateInvalid")
            return task

    async def _record_result_payload(
        self,
        task: AIGenerationTask,
        result: AIGenerationTaskResultDTO,
        *,
        metadata: dict[str, Any],
    ) -> None:
        document_id = await self.payload_store.record_result(task=task, result=result, metadata=metadata)
        task.mongo_document_id = document_id
        task.mongo_status = "stored"
        task.mongo_schema_version = AI_GENERATION_TASK_DOCUMENT_SCHEMA_VERSION

    async def _record_error_payload(self, task: AIGenerationTask, error: dict[str, Any]) -> None:
        try:
            document_id = await self.payload_store.record_error(task=task, error=error)
        except Exception as exc:  # pragma: no cover - integration failure is environment-specific
            task.mongo_status = "write_failed"
            logger.bind(task_id=task.id, task_type=task.task_type, error=str(exc)).warning(
                "GenerationAiPayloadErrorWriteFailed"
            )
            return
        task.mongo_document_id = document_id
        task.mongo_status = "stored"
        task.mongo_schema_version = AI_GENERATION_TASK_DOCUMENT_SCHEMA_VERSION

    @staticmethod
    def _set_short_error(task: AIGenerationTask, error: dict[str, Any]) -> None:
        task.last_error_type = str(error.get("type") or "")[:120] or None
        task.last_error_message = str(error.get("message") or "")[:1000] or None
