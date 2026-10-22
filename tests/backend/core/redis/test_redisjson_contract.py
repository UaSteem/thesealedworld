"""Disposable RedisJSON contracts; opt in with RUN_REDISJSON_CONTRACT_TESTS=1."""

import asyncio
import os
import subprocess
import time
from uuid import uuid4

import pytest
import redis as sync_redis
from codex_platform.redis_service import RedisService
from redis.asyncio import Redis

from src.backend.infrastructure.actor_commitments import ActorCommitmentManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.external,
    pytest.mark.skipif(
        os.environ.get("RUN_REDISJSON_CONTRACT_TESTS") != "1",
        reason="Set RUN_REDISJSON_CONTRACT_TESTS=1 for disposable Docker Redis Stack",
    ),
]


@pytest.fixture(scope="module")
def redisjson_url():
    name = f"tbmmorpg-redisjson-contract-{uuid4().hex}"
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "--detach",
                "--name",
                name,
                "--publish",
                "127.0.0.1::6379",
                "--env",
                "REDIS_ARGS=--save '' --appendonly no",
                "redis/redis-stack-server:7.2.0-v14",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        endpoint = subprocess.run(
            ["docker", "port", name, "6379/tcp"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
        url = f"redis://{endpoint}/0"
        with sync_redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1) as probe:
            for attempt in range(50):
                try:
                    probe.ping()
                    break
                except sync_redis.ConnectionError:
                    if attempt == 49:
                        raise
                    time.sleep(0.1)
            # Require RedisJSON itself, not just a server accepting PING.
            assert probe.execute_command("COMMAND", "INFO", "JSON.GET")
        yield url
    finally:
        subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=20, check=False)


@pytest.fixture
async def adapter(redisjson_url):
    async with Redis.from_url(redisjson_url, decode_responses=True) as client:
        yield ActorCommitmentManager(RedisService(client)), client


async def test_json_wire_roundtrip_sections_and_missing_batch_entry(adapter):
    manager, client = adapter
    actor_id, missing = uuid4().hex, uuid4().hex
    payload = {"meta": {"label": "Тест ☃", "flags": [True, None]}, "source": {"id": 7}}
    assert await manager.save_snapshot(actor_id, payload, ttl=30) == actor_id
    expected = {
        "schema_version": 1,
        "actor_id": actor_id,
        **payload,
        "runtime": None,
        "combat": None,
        "inventory": None,
        "status": None,
    }
    assert await manager.get_snapshot(actor_id) == expected
    assert await client.json().get(manager.build_key(actor_id), "$") == [expected]
    assert await manager.get_snapshots_batch([actor_id, missing]) == {actor_id: expected, missing: None}
    assert await manager.get_sections_batch([actor_id, missing], "meta") == {
        actor_id: payload["meta"],
        missing: None,
    }


async def test_snapshot_expires_on_server_and_can_be_recreated(adapter):
    manager, client = adapter
    actor_id = uuid4().hex
    await manager.save_snapshot(actor_id, {"source": {"revision": 1}}, ttl=1)
    assert 0 < await client.pttl(manager.build_key(actor_id)) <= 1000
    deadline = asyncio.get_running_loop().time() + 4
    while await client.exists(manager.build_key(actor_id)):
        assert asyncio.get_running_loop().time() < deadline, "Redis did not expire snapshot"
        await asyncio.sleep(0.05)
    assert await manager.get_snapshot(actor_id) is None
    await manager.save_snapshot(actor_id, {"source": {"revision": 2}}, ttl=30)
    assert await manager.get_source(actor_id) == {"revision": 2}


async def test_pipeline_wrongtype_does_not_report_failed_document_as_saved(adapter):
    manager, client = adapter
    first, broken, last = (uuid4().hex for _ in range(3))
    # Redis generates a real command error in the middle of a non-atomic pipeline.
    await client.set(manager.build_key(broken), "not-a-json-document")
    saved = await manager.save_snapshots(
        {actor_id: {"source": {"id": actor_id}} for actor_id in [first, broken, last]},
        ttl=30,
    )
    assert saved == {first: first, last: last}
    assert await client.get(manager.build_key(broken)) == "not-a-json-document"
    documents = await manager.get_snapshots_batch([first, broken, last])
    assert documents[broken] is None
    for actor_id in [first, last]:
        assert documents[actor_id]["source"] == {"id": actor_id}
        assert 0 < await client.ttl(manager.build_key(actor_id)) <= 30
    sections = await manager.get_sections_batch([first, broken, last], "source")
    assert sections == {first: {"id": first}, broken: None, last: {"id": last}}
