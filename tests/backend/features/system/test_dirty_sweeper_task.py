from __future__ import annotations

from unittest.mock import AsyncMock

from src.backend.features.system.workers.tasks.dirty_sweeper import system_dirty_sweeper_task
from src.backend.infrastructure.exploration.managers import ExplorationKnowledgeRuntimeManager
from src.backend.infrastructure.inventory.managers import InventorySessionManager
from src.shared.schemas.inventory import InventoryRuntimeSessionDTO


async def _sweep_case(fake_redis_service):
    inventory = InventorySessionManager(fake_redis_service)
    await inventory.set(InventoryRuntimeSessionDTO(char_id=1, is_dirty=True, dirty={"dirty": True}))

    knowledge = ExplorationKnowledgeRuntimeManager(fake_redis_service)
    await knowledge.set(
        2,
        "52_48",
        {
            "movement_xp_spent": 1.0,
            "scouting_xp_spent": 0.0,
            "hunting_xp_spent": 0.0,
            "movement_xp_cap": 1.0,
            "scouting_xp_cap": 1.0,
            "hunting_xp_cap": 1.0,
        },
    )
    # Existing legacy keys must remain untouched, even if a Redis scan finds them.
    legacy_session_key = "game:rift:session:rift:run:dirty"
    legacy_portal_key = "game:rift:portal:portal-1"
    legacy_session = {"rift_session_id": "rift:run:dirty", "rift_instance_id": "rift-1", "is_dirty": True}
    legacy_portal = {"portal_id": "portal-1", "status": "completed"}
    await fake_redis_service.json_module.set(legacy_session_key, "$", legacy_session)
    await fake_redis_service.json_module.set(legacy_portal_key, "$", legacy_portal)
    arq = AsyncMock()

    result = await system_dirty_sweeper_task(
        {"redis_managers": type("Managers", (), {"redis": fake_redis_service})(), "system_arq": arq},
        {"limit": 10},
    )

    assert result["inventory_char_ids"] == [1]
    assert result["exploration_knowledge_char_ids"] == [2]
    assert not any("rift" in key for key in result)
    arq.enqueue_job.assert_any_await(
        "flush_inventory_session_task",
        {"char_id": 1, "source": "system_dirty_sweeper"},
    )
    arq.enqueue_job.assert_any_await(
        "flush_exploration_knowledge_task",
        {"char_id": 2, "source": "system_dirty_sweeper"},
    )
    assert arq.enqueue_job.await_count == 2
    assert await fake_redis_service.json_module.get(legacy_session_key, "$") == [legacy_session]
    assert await fake_redis_service.json_module.get(legacy_portal_key, "$") == [legacy_portal]


def test_system_dirty_sweeper_enqueues_domain_flush_jobs(fake_redis_service):
    # Fake Redis and AsyncMock complete without external I/O or an event loop.
    coroutine = _sweep_case(fake_redis_service)
    try:
        coroutine.send(None)
    except StopIteration:
        return
    raise AssertionError("Unexpected external suspension in isolated dirty sweeper test")
