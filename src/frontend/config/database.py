"""Database and logging configuration shared by site migrations and HTTP runtime."""

from pathlib import Path

from codex_core.settings import BaseCommonSettings
from pydantic_settings import SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent.parent


class DatabaseSettings(BaseCommonSettings):
    """No API, session signing, email or asset credentials are needed for migrations."""

    # Logging
    debug: bool = True
    log_level_console: str = "DEBUG"
    log_level_file: str = "INFO"
    log_rotation: str = "10 MB"
    log_dir: str = "logs"

    site_database_url: str = (
        "postgresql+asyncpg://tbmmorpg:tbmmorpg_dev@127.0.0.1:5432/tbmmorpg_site"  # pragma: allowlist secret
    )
    database_url: str = site_database_url
    database_echo: bool = False
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")


database_settings = DatabaseSettings()
