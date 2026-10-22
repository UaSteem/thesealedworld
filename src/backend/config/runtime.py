"""Shared runtime configuration for persistence, queues and item-text generation.

API authentication belongs to BackendSettings, not to these infrastructure consumers.
"""

import os
from pathlib import Path

from codex_core.settings import BaseCommonSettings
from pydantic_settings import SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]
_BUNDLED_TRAINED_COMBAT_AI_POLICY = (
    Path(__file__).resolve().parents[1] / "features/combat/runtime/ai/policies/trained_g500_seed0.json"
)


class RuntimeSettings(BaseCommonSettings):
    """Settings needed by shared infrastructure, with no API credentials."""

    debug: bool = True
    log_level_console: str = "DEBUG"
    log_level_file: str = "DEBUG"
    log_rotation: str = "10 MB"
    log_dir: str = "logs"
    game_database_url: str = (
        "postgresql+asyncpg://tbmmorpg:tbmmorpg_dev@127.0.0.1:5432/tbmmorpg_game"  # pragma: allowlist secret
    )
    database_url: str = game_database_url
    database_echo: bool = False
    mongo_url: str = "mongodb://127.0.0.1:27017"
    mongo_database: str = "tbmmorpg_analytics"
    mongo_server_selection_timeout_ms: int = 5_000
    default_symbiote_name: str = "SYSTEM"
    game_refresh_token_expire_minutes: int = 12 * 60
    game_stream_name: str = "game_events"
    game_stream_maxlen: int = 10_000
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    combat_ai_policy_path: str | None = None

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def effective_redis_url(self) -> str:
        return os.getenv("REDIS_URL") or self.redis_url


runtime_settings = RuntimeSettings()


def apply_runtime_environment_overrides() -> None:
    """Export the existing local-policy selection without changing its precedence."""
    policy_path = runtime_settings.combat_ai_policy_path
    if not policy_path and _BUNDLED_TRAINED_COMBAT_AI_POLICY.exists():
        policy_path = str(_BUNDLED_TRAINED_COMBAT_AI_POLICY)
    if policy_path:
        os.environ.setdefault("COMBAT_AI_POLICY_PATH", policy_path)
