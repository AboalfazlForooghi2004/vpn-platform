from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://vpn:vpn-dev-only@127.0.0.1:5432/vpn"
    telegram_bot_token: SecretStr | None = None
    admin_telegram_ids: str = ""
    admin_api_token: SecretStr | None = None
    awg_agent_socket: Path = Path("/run/vpn-platform/awg-agent.sock")
    config_encryption_key: SecretStr | None = None
    receipt_storage_path: Path = Path("./runtime/receipts")
    job_poll_seconds: float = 1.0

    @property
    def admin_ids(self) -> frozenset[int]:
        return frozenset(
            int(value.strip()) for value in self.admin_telegram_ids.split(",") if value.strip()
        )

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
