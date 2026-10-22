from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.backend.core.ai import AIService
from src.backend.features.generation_ai.bootstrap import build_generation_ai_registry
from src.backend.features.generation_ai.dto import AIGenerationTaskSpecDTO
from src.backend.features.generation_ai.services import GenerationAIService


def test_real_registry_only_contains_item_text():
    assert build_generation_ai_registry().task_types == ("items.text",)


def test_core_ai_has_only_json_generation():
    assert not hasattr(AIService, "generate_text")
    assert not hasattr(AIService, "generate_image_bytes")
    assert not hasattr(AIService, "validate_generated_image_no_text")


@pytest.mark.parametrize(
    "task_type", ["news.cover_image", "world.zone_lore", "world.location_batch", "items.image", "unknown.future"]
)
async def test_retired_jobs_are_terminal_without_handler_or_provider(task_type):
    task = SimpleNamespace(id="old", task_type=task_type, output_kind="json")
    repository = SimpleNamespace(
        retire_unsupported_by_id=AsyncMock(return_value=False),
        claim_by_id=AsyncMock(return_value=task),
        mark_failed=AsyncMock(),
    )
    executor = SimpleNamespace(generate=AsyncMock())
    registry = SimpleNamespace(resolve=lambda _: pytest.fail("Retired task resolved a handler"))
    service = GenerationAIService(repository=repository, registry=registry, executor=executor)
    assert await service.process_task(task.id) is None
    repository.mark_failed.assert_awaited_once()
    assert repository.mark_failed.await_args.args[1]["type"] == "RetiredTaskType"
    executor.generate.assert_not_awaited()


@pytest.mark.parametrize(
    "task_type,kind",
    [("news.cover_image", "image"), ("unknown.future", "json"), ("items.text", "text"), ("items.text", "image")],
)
async def test_enqueue_rejects_non_item_json_even_if_custom_registry_accepts_it(task_type, kind):
    repository = SimpleNamespace(find_by_identity_key=AsyncMock())
    service = GenerationAIService(repository=repository, registry=SimpleNamespace(has=lambda _: True))
    spec = AIGenerationTaskSpecDTO(task_type=task_type, entity_type="item", entity_id="1", output_kind=kind)
    with pytest.raises(ValueError, match="Only items.text JSON"):
        await service.enqueue_many([spec])
    repository.find_by_identity_key.assert_not_awaited()


async def test_worker_retires_unsupported_job_before_normal_claim():
    repository = SimpleNamespace(retire_unsupported_by_id=AsyncMock(return_value=True), claim_by_id=AsyncMock())
    executor = SimpleNamespace(generate=AsyncMock())
    service = GenerationAIService(repository=repository, registry=build_generation_ai_registry(), executor=executor)
    assert await service.process_task("future-or-exhausted") is None
    repository.retire_unsupported_by_id.assert_awaited_once_with("future-or-exhausted")
    repository.claim_by_id.assert_not_awaited()
    executor.generate.assert_not_awaited()
