from __future__ import annotations

import asyncio
import os
import subprocess
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from arq.connections import ArqRedis
from arq.jobs import Job
from redis.exceptions import ConnectionError as RedisConnectionError
from tests.backend.features.generation_ai import test_input_durability as input_contract
from tests.backend.features.generation_ai.test_input_durability import spec, store

from src.backend.features.generation_ai.identity import build_generation_task_identity_key
from src.backend.features.generation_ai.repositories import AIGenerationTaskRepository

input_databases = input_contract.input_databases
stores = input_contract.stores


@pytest.fixture(scope="module")
def recovery_redis_port():
    if os.environ.get("RUN_GENERATION_INPUT_STORE_TESTS") != "1":
        pytest.skip("Opt-in disposable SQL/Mongo/Redis recovery tests")
    name = f"generation-recovery-{uuid4().hex}"
    try:
        subprocess.check_output(
            ["docker", "run", "-d", "--rm", "--name", name, "-p", "127.0.0.1::6379", "redis:7-alpine"], timeout=60
        )
        port = (
            subprocess.check_output(["docker", "port", name, "6379/tcp"], text=True, timeout=15)
            .strip()
            .rsplit(":", 1)[1]
        )
        yield int(port)
    finally:
        subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=30)


@pytest.fixture
async def recovery_queue(recovery_redis_port):
    client = ArqRedis(host="127.0.0.1", port=recovery_redis_port, default_queue_name=f"recovery:{uuid4().hex}")
    try:
        for _ in range(50):
            try:
                await client.ping()
                break
            except RedisConnectionError:
                await asyncio.sleep(0.1)
        yield client
    finally:
        await client.aclose()


async def create_task(sessions, database, **updates):
    request = spec()
    async with sessions.begin() as session:
        task = await AIGenerationTaskRepository(session, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        for key, value in updates.items():
            setattr(task, key, value)
        task_id = task.id
    return task_id


@pytest.mark.external
@pytest.mark.integration
async def test_committed_task_is_discoverable_after_original_process_is_gone(stores):
    sessions, database, _ = stores
    task_id = await create_task(sessions, database)
    async with sessions() as fresh_session:
        ids = await AIGenerationTaskRepository(fresh_session).list_schedulable_ids(limit=100)
    assert task_id in ids


@pytest.mark.external
@pytest.mark.integration
async def test_recovery_replays_after_queue_loss_and_deduplicates_concurrent_scans(stores, recovery_queue):
    from src.backend.features.generation_ai.scheduling import replay_scheduling_page

    sessions, database, _ = stores
    task_id = await create_task(sessions, database)
    # Original process died after commit: no in-memory scheduling list remains.
    async with sessions() as session:
        ids = await AIGenerationTaskRepository(session).list_schedulable_ids()
    assert task_id in ids
    counts = await asyncio.gather(
        replay_scheduling_page([task_id], recovery_queue), replay_scheduling_page([task_id], recovery_queue)
    )
    assert sum(counts) == 1
    job_id = f"generation-ai-recovery:{task_id}"
    info = await Job(job_id, recovery_queue).info()
    assert info.function == "generation_ai_process_task"
    assert info.args == (task_id,)
    assert await recovery_queue.zcard(recovery_queue.default_queue_name) == 1
    # Redis queue and job bookkeeping loss; durable SQL intent is unchanged.
    await recovery_queue.delete(recovery_queue.default_queue_name, f"arq:job:{job_id}")
    assert await replay_scheduling_page([task_id], recovery_queue) == 1
    async with sessions.begin() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        assert await repository.claim_by_id(task_id) is not None
    async with sessions.begin() as session:
        repository = AIGenerationTaskRepository(session, payload_store=store(database))
        assert await repository.claim_by_id(task_id) is None
        assert task_id not in await repository.list_schedulable_ids()


@pytest.mark.external
@pytest.mark.integration
async def test_due_filter_and_rollback_visibility(stores):
    sessions, database, _ = stores
    now = datetime.now(UTC)
    expected = []
    excluded = []
    for updates in ({}, {"status": "cooldown", "not_before": now - timedelta(seconds=1)}):
        expected.append(await create_task(sessions, database, **updates))
    for updates in (
        {"not_before": now + timedelta(hours=1)},
        {"status": "running"},
        {"status": "done"},
        {"status": "failed"},
        {"status": "cancelled"},
        {"attempts": 3, "max_attempts": 3},
        {"task_type": "news.cover_image"},
        {"output_kind": "image"},
    ):
        excluded.append(await create_task(sessions, database, **updates))
    request = spec()
    async with sessions() as uncommitted:
        task = await AIGenerationTaskRepository(uncommitted, payload_store=store(database)).create(
            request, batch_id=str(uuid4()), identity_key=build_generation_task_identity_key(request)
        )
        excluded.append(task.id)
        async with sessions() as reader:
            assert task.id not in await AIGenerationTaskRepository(reader).list_schedulable_ids(now=now)
        await uncommitted.rollback()
    async with sessions() as session:
        ids = await AIGenerationTaskRepository(session).list_schedulable_ids(now=now)
    assert set(expected) <= set(ids)
    assert not set(excluded) & set(ids)


@pytest.mark.external
@pytest.mark.integration
async def test_enqueue_exception_or_none_keeps_sql_replayable(stores, recovery_queue):
    from src.backend.features.generation_ai.scheduling import replay_scheduling_page

    sessions, database, _ = stores
    task_id = await create_task(sessions, database)

    class Denied:
        async def enqueue_job(self, *args, **kwargs):
            raise ConnectionError("injected queue denial")

    class SilentDenied:
        async def enqueue_job(self, *args, **kwargs):
            return None

    assert await replay_scheduling_page([task_id], Denied()) == 0
    assert await replay_scheduling_page([task_id], SilentDenied()) == 0
    async with sessions() as session:
        assert task_id in await AIGenerationTaskRepository(session).list_schedulable_ids()
    assert await replay_scheduling_page([task_id], recovery_queue) == 1


@pytest.mark.external
@pytest.mark.integration
async def test_bounded_keyset_scan_reaches_backlog_and_worker_is_wired(stores, recovery_queue, monkeypatch):
    from src.backend.features.generation_ai.workers import tasks
    from src.backend.features.generation_ai.workers.arq import GenerationAIArqSettings

    sessions, database, _ = stores
    ids = {await create_task(sessions, database) for _ in range(5)}
    monkeypatch.setattr(tasks, "get_manual_session_context", sessions)
    monkeypatch.setattr(tasks, "RECOVERY_PAGE_SIZE", 2)
    ctx = {"generation_ai_arq": recovery_queue}
    for _ in range(100):
        result = await tasks.generation_ai_recover_scheduling(ctx)
        assert result["scanned"] <= 2
        if ctx["generation_ai_recovery_cursor"] is None:
            break
    else:
        pytest.fail("Recovery failed to finish a bounded backlog traversal")
    for task_id in ids:
        assert await Job(f"generation-ai-recovery:{task_id}", recovery_queue).info() is not None
    # Cursor loss/restart only replays stable IDs; no queue multiplication.
    count = await recovery_queue.zcard(recovery_queue.default_queue_name)
    await tasks.generation_ai_recover_scheduling({"generation_ai_arq": recovery_queue})
    assert await recovery_queue.zcard(recovery_queue.default_queue_name) == count
    cron_job = next(
        job for job in GenerationAIArqSettings.cron_jobs if job.coroutine is tasks.generation_ai_recover_scheduling
    )
    assert cron_job.run_at_startup
    assert cron_job.second == {0, 30}


@pytest.mark.parametrize("limit", [0, 1001])
async def test_invalid_recovery_bound_is_rejected(limit):
    with pytest.raises(ValueError):
        await AIGenerationTaskRepository(None).list_schedulable_ids(limit=limit)
