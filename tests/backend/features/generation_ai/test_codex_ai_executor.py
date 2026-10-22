from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from src.backend.features.generation_ai.integrations.codex_ai_executor import CodexAIExecutor


class ItemText(BaseModel):
    name: str
    description: str


async def test_item_json_provider_result_is_preserved():
    ai = SimpleNamespace(generate_json=AsyncMock(return_value=ItemText(name="Sword", description="Old iron")))
    task = SimpleNamespace(task_type="items.text", output_kind="json")
    result = await CodexAIExecutor(ai).generate(task, {"kind": "json", "prompt": "item", "schema": ItemText})
    assert result.output_payload == {"name": "Sword", "description": "Old iron"}
    ai.generate_json.assert_awaited_once_with("item", schema=ItemText)


@pytest.mark.parametrize("kind", ["image", "text", "audio", "video"])
async def test_executor_has_no_non_json_provider_path(kind):
    ai = SimpleNamespace(generate_json=AsyncMock())
    with pytest.raises(RuntimeError, match="Unsupported"):
        await CodexAIExecutor(ai).generate(SimpleNamespace(task_type="items.text", output_kind=kind), {"kind": kind})
    ai.generate_json.assert_not_awaited()


async def test_executor_requires_schema():
    with pytest.raises(RuntimeError, match="requires schema"):
        await CodexAIExecutor(SimpleNamespace()).generate(
            SimpleNamespace(task_type="items.text", output_kind="json"), {"kind": "json"}
        )


async def test_executor_rejects_empty_provider_response():
    ai = SimpleNamespace(generate_json=AsyncMock(return_value=None))
    with pytest.raises(RuntimeError, match="no response"):
        await CodexAIExecutor(ai).generate(
            SimpleNamespace(task_type="items.text", output_kind="json"),
            {"kind": "json", "prompt": "item", "schema": ItemText},
        )


async def test_executor_rejects_output_kind_mismatch():
    with pytest.raises(RuntimeError, match="kind mismatch"):
        await CodexAIExecutor(SimpleNamespace()).generate(
            SimpleNamespace(task_type="items.text", output_kind="json"), {"kind": "image"}
        )
