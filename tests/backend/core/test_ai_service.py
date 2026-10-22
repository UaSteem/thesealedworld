from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from codex_ai.core import PromptResult

from src.backend.core.ai import AIService


@pytest.mark.unit
async def test_ai_service_initializes_direct_gemini_provider(monkeypatch):
    monkeypatch.setattr("src.backend.core.ai.settings.gemini_api_key", "test-key")  # pragma: allowlist secret
    monkeypatch.setattr("src.backend.core.ai.settings.gemini_model", "gemini-2.5-flash")

    with (
        patch("src.backend.core.ai.GeminiProvider") as provider_cls,
    ):
        provider = MagicMock()
        provider_cls.return_value = provider

        service = AIService()

    provider_cls.assert_called_once_with(
        api_key="test-key",  # pragma: allowlist secret
        model="gemini-2.5-flash",
    )
    assert service.provider is provider


@pytest.mark.unit
async def test_ai_service_generate_json_delegates_to_provider(monkeypatch):
    class DTO:
        pass

    monkeypatch.setattr("src.backend.core.ai.settings.gemini_api_key", "test-key")  # pragma: allowlist secret
    with (
        patch("src.backend.core.ai.GeminiProvider") as provider_cls,
    ):
        provider = MagicMock()
        provider.generate_json = AsyncMock(return_value={"ok": True})
        provider_cls.return_value = provider
        service = AIService()

        result = await service.generate_json("prompt", schema=DTO)

    assert result == {"ok": True}
    provider.generate_json.assert_awaited_once_with("prompt", schema=DTO)


@pytest.mark.unit
async def test_ai_service_generate_json_flattens_prompt_result(monkeypatch):
    class DTO:
        pass

    monkeypatch.setattr("src.backend.core.ai.settings.gemini_api_key", "test-key")  # pragma: allowlist secret
    with (
        patch("src.backend.core.ai.GeminiProvider") as provider_cls,
    ):
        provider = MagicMock()
        provider.generate_json = AsyncMock(return_value={"ok": True})
        provider_cls.return_value = provider
        service = AIService()

        result = await service.generate_json(
            PromptResult(
                messages=[
                    {"role": "system", "content": "Return JSON only"},
                    {"role": "user", "content": '{"id": "x"}'},
                ],
                temperature=0.3,
            ),
            schema=DTO,
            temperature=0.1,
        )

    assert result == {"ok": True}
    provider.generate_json.assert_awaited_once_with(
        'System:\nReturn JSON only\n\nUser:\n{"id": "x"}',
        schema=DTO,
        temperature=0.1,
    )


@pytest.mark.unit
async def test_missing_provider_returns_none(monkeypatch):
    monkeypatch.setattr("src.backend.core.ai.settings.gemini_api_key", None)
    service = AIService()
    assert await service.generate_json("prompt", schema=dict) is None
