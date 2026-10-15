from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.backend.features.generation_ai.bootstrap import build_generation_ai_registry
from src.backend.features.generation_ai.services import GenerationAIService


@pytest.mark.parametrize("task_type", ["monster.clan_flavor", "monster.clan_image", "monster.member_image"])
async def test_old_monster_task_fails_terminally_without_provider(task_type):
    task = SimpleNamespace(id="legacy-monster-task", task_type=task_type)
    repository = SimpleNamespace(claim_by_id=AsyncMock(return_value=task), mark_failed=AsyncMock())
    executor = SimpleNamespace(generate=AsyncMock())
    service = GenerationAIService(repository=repository, registry=build_generation_ai_registry(), executor=executor)

    assert await service.process_task(task.id) is None
    executor.generate.assert_not_awaited()
    repository.mark_failed.assert_awaited_once()
    assert repository.mark_failed.await_args.args[1]["type"] == "RetiredTaskType"


def test_registry_preserves_other_generations_and_excludes_monsters():
    registry = build_generation_ai_registry()
    for task_type in ("monster.clan_flavor", "monster.clan_image", "monster.member_image"):
        assert not registry.has(task_type)
    for task_type in ("news.cover_image", "items.text", "world.zone_lore", "world.location_batch"):
        assert registry.has(task_type)
