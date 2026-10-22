from typing import Any

from codex_ai.providers.gemini import GeminiProvider
from loguru import logger as log

from src.backend.config.runtime import runtime_settings as settings


class AIService:
    """JSON provider facade for item names and descriptions."""

    def __init__(self) -> None:
        self.provider: GeminiProvider | None = None

        if settings.gemini_api_key:
            log.info("AiServiceInitializing")
            self.provider = GeminiProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
            )
        else:
            log.warning("AiServiceGeminiApiKeyMissing")

    async def generate_json(self, prompt: Any, *, schema: type[Any], **kwargs: Any) -> Any | None:
        if self.provider is None:
            log.debug("AiJsonGenerationSkipped")
            return None
        prompt_text, prompt_kwargs = _normalize_prompt(prompt)
        return await self.provider.generate_json(
            prompt_text, schema=schema, **_merge_prompt_kwargs(prompt_kwargs, kwargs)
        )


def _normalize_prompt(prompt: Any) -> tuple[str, dict[str, Any]]:
    messages = getattr(prompt, "messages", None)
    if not isinstance(messages, list):
        return str(prompt), {}

    parts: list[str] = []
    prompt_system = getattr(prompt, "system", "")
    if prompt_system:
        parts.append(f"System:\n{prompt_system}")

    for message in messages:
        role = _message_value(message, "role") or "user"
        content = _message_value(message, "content")
        if not content:
            continue
        parts.append(f"{str(role).title()}:\n{content}")

    prompt_kwargs: dict[str, Any] = {}
    for key in ("model", "temperature", "max_tokens"):
        value = getattr(prompt, key, None)
        if value is not None:
            prompt_kwargs[key] = value

    return "\n\n".join(parts), prompt_kwargs


def _message_value(message: Any, key: str) -> Any:
    if isinstance(message, dict):
        return message.get(key)
    return getattr(message, key, None)


def _merge_prompt_kwargs(prompt_kwargs: dict[str, Any], call_kwargs: dict[str, Any]) -> dict[str, Any]:
    merged = dict(prompt_kwargs)
    merged.update(call_kwargs)
    return merged
