"""Real SQL/Mongo result application rollback contracts using disposable stores."""

from uuid import uuid4

import pytest
from sqlalchemy import select
from tests.backend.features.generation_ai import test_input_durability as input_contract
from tests.backend.features.generation_ai.test_input_durability import spec, store

from src.backend.features.generation_ai.dto import AIGenerationTaskResultDTO
from src.backend.features.generation_ai.identity import build_generation_task_identity_key
from src.backend.features.generation_ai.models import AIGenerationTask
from src.backend.features.generation_ai.registry import AIGenerationTaskRegistry
from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository
from src.backend.features.generation_ai.services import GenerationAIService
from src.backend.features.items.models.instance import ItemGeneratedTemplate, ItemInstance
from src.backend.features.items.tasks_ai import ItemTextTaskHandler

input_databases = input_contract.input_databases
stores = input_contract.stores

pytestmark = [pytest.mark.external, pytest.mark.integration]


@pytest.mark.parametrize(
    "fault",
    ["result_write", "partial_apply", "partial_sql", "sql_completion", "sql_flush", "mongo_ack", "followup", "success"],
)
async def test_result_application_is_atomic_before_retry_commit(stores, fault):
    sessions, database, _ = stores
    engine = sessions.kw["bind"]
    async with engine.begin() as connection:
        await connection.run_sync(ItemGeneratedTemplate.__table__.create, checkfirst=True)
        await connection.run_sync(ItemInstance.__table__.create, checkfirst=True)
    request = spec()
    template_id, peer_id = str(uuid4()), str(uuid4())
    async with sessions.begin() as session:
        session.add(
            ItemGeneratedTemplate(
                id=template_id,
                text_visual_hash=str(uuid4()),
                prompt_version="test",
                base_id="sword",
                item_type="weapon",
                rarity="common",
                rarity_tier=0,
                name="original",
                description="original text",
            )
        )
        await session.flush()
        for item_id in [request.entity_id, peer_id]:
            session.add(
                ItemInstance(
                    id=item_id,
                    generated_template_id=template_id,
                    base_id="sword",
                    item_type="weapon",
                    rarity="common",
                    rarity_tier=0,
                    name="original",
                    description="original text",
                )
            )
        task = await AIGenerationTaskRepository(session, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id

    class Handler(ItemTextTaskHandler):
        async def build_request(self, task):
            return {"kind": "json", "schema": dict}

        async def apply_result(self, task, result):
            if fault in {"partial_apply", "partial_sql"}:
                item = await self.session.get(ItemInstance, request.entity_id)
                item.name = None if fault == "partial_sql" else "partial text"
                await self.session.flush()
                raise RuntimeError("synthetic partial handler failure")
            return await super().apply_result(task, result)

    class Provider:
        async def generate(self, task, request):
            assert not repository.session.in_transaction()
            return AIGenerationTaskResultDTO(
                output_payload={"name": "generated text", "description": "generated description"}
            )

    payload_store = store(database)
    real_record = payload_store.record_result

    async def record_result(**kwargs):
        if fault == "result_write":
            raise ConnectionError("synthetic result persistence failure")
        result = await real_record(**kwargs)
        if fault == "mongo_ack":
            raise ConnectionError("synthetic lost Mongo acknowledgement")
        return result

    payload_store.record_result = record_result
    async with sessions() as session:
        repository = AIGenerationTaskRepository(session, payload_store=payload_store)
        real_done = repository.mark_done

        async def mark_done(task_id, result):
            done = await real_done(task_id, result)
            if fault == "sql_flush":
                done.priority = None
                await session.flush()
            if fault == "sql_completion":
                raise RuntimeError("synthetic SQL completion failure after Mongo result")
            return done

        repository.mark_done = mark_done
        registry = AIGenerationTaskRegistry()
        registry.register(Handler(session=session))
        service = GenerationAIService(
            repository=repository, registry=registry, executor=Provider(), auto_schedule=False
        )
        followup = spec()
        if fault == "followup":

            async def fail_followup(specs):
                await service.enqueue_many([followup])
                raise RuntimeError("synthetic failure after followup SQL creation")

            service._enqueue_followups = fail_followup
        result = await service.process_task(task_id)
        assert (result is not None) is (fault == "success")
        if fault == "followup":
            assert [task_id for task_id, _ in service._pending_schedule_tasks] == [task_id]
        await session.commit()  # the worker's actual outer retry/application boundary
    async with sessions() as observer:
        items = list(
            await observer.scalars(select(ItemInstance).where(ItemInstance.id.in_([request.entity_id, peer_id])))
        )
        template = await observer.get(ItemGeneratedTemplate, template_id)
        task = await observer.get(AIGenerationTask, task_id)
        document = await database.ai_generation_task_documents.find_one({"task_id": task_id})
        assert task.attempts == 1  # committed claim survives rollback
        if fault == "followup":
            assert (
                await observer.scalar(select(AIGenerationTask).where(AIGenerationTask.entity_id == followup.entity_id))
                is None
            )
        if fault == "success":
            assert task.status == "done"
            assert all((i.name, i.text_status) == ("generated text", "generated") for i in items)
            assert {i.id: i.lifecycle_status for i in items} == {
                request.entity_id: "ready",
                peer_id: "mechanical_ready",
            }
            assert template.name == "generated text" and template.text_status == "generated"
            assert document["output_payload"]["name"] == "generated text"
        else:
            assert task.status == "cooldown" and task.not_before is not None
            assert all(
                (i.name, i.description, i.text_status, i.lifecycle_status)
                == ("original", "original text", "not_requested", "mechanical_ready")
                for i in items
            )
            assert (template.name, template.description, template.text_status) == (
                "original",
                "original text",
                "not_requested",
            )
            assert template.metadata_ == {} and template.text_payload == {}
            assert document["error"]
            if fault in {"sql_completion", "sql_flush", "mongo_ack", "followup"}:
                assert document["output_payload"]["name"] == "generated text"  # retained evidence, not SQL completion
            else:
                assert document["output_payload"] == {}


@pytest.mark.parametrize("claim", ["id", "next"])
@pytest.mark.parametrize("raw", ["stored", "malformed"])
async def test_ambiguous_output_is_preserved_before_second_provider_attempt(stores, claim, raw):
    sessions, database, _ = stores
    request = spec()
    engine = sessions.kw["bind"]
    async with engine.begin() as connection:
        await connection.run_sync(ItemGeneratedTemplate.__table__.create, checkfirst=True)
        await connection.run_sync(ItemInstance.__table__.create, checkfirst=True)
    async with sessions.begin() as session:
        session.add(
            ItemInstance(
                id=request.entity_id,
                base_id="sword",
                item_type="weapon",
                rarity="common",
                rarity_tier=0,
                name="original",
                description="original text",
            )
        )
        task = await AIGenerationTaskRepository(session, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        task_id = task.id

    class Handler(ItemTextTaskHandler):
        async def build_request(self, task):
            return {"kind": "json", "schema": dict}

    calls = []

    class Provider:
        async def generate(self, task, request):
            calls.append(task.id)
            return AIGenerationTaskResultDTO(output_payload={"name": "first result", "description": "saved output"})

    payload_store = store(database)
    real_record = payload_store.record_result

    async def lost_ack(**kwargs):
        await real_record(**kwargs)
        raise ConnectionError("synthetic lost result acknowledgement")

    payload_store.record_result = lost_ack
    async with sessions() as session:
        registry = AIGenerationTaskRegistry()
        registry.register(Handler(session=session))
        service = GenerationAIService(
            repository=AIGenerationTaskRepository(session, payload_store=payload_store),
            registry=registry,
            executor=Provider(),
            auto_schedule=False,
        )
        assert await service.process_task(task_id) is None
        await session.commit()
    async with sessions.begin() as session:
        task = await session.get(AIGenerationTask, task_id)
        assert task.status == "cooldown" and task.attempts == 1
        task.not_before = None
    collection = database.ai_generation_task_documents
    if raw == "malformed":
        await collection.update_one({"task_id": task_id}, {"$set": {"output_payload": ["retained ambiguous bytes"]}})
    before = await collection.find_one({"task_id": task_id})
    async with sessions() as session:
        registry = AIGenerationTaskRegistry()
        registry.register(Handler(session=session))
        service = GenerationAIService(
            repository=AIGenerationTaskRepository(session, payload_store=store(database)),
            registry=registry,
            executor=Provider(),
            auto_schedule=False,
        )
        if claim == "id":
            assert await service.process_task(task_id) is None
        else:
            assert await service.claim_and_process_next() is None
        await session.commit()
    assert calls == [task_id]
    async with sessions() as observer:
        task = await observer.get(AIGenerationTask, task_id)
        item = await observer.get(ItemInstance, request.entity_id)
        assert task.status == "failed" and task.last_error_type == "StoredResultNeedsReview"
        assert task.attempts == 1 and task.completed_at is not None
        assert (item.name, item.text_status, item.lifecycle_status) == ("original", "not_requested", "mechanical_ready")
    assert await collection.find_one({"task_id": task_id}) == before
