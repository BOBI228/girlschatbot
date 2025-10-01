from __future__ import annotations

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    TELEGRAM_BOT_TOKEN: str
    OPENAI_API_KEY: str

    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_MODERATION_MODEL: str = "omni-moderation-latest"


settings = Settings()  # type: ignore[arg-type]


class AppInfo(BaseModel):
    name: str = "CompanionBot"
    version: str = "0.1.0"
    description: str = (
        "A supportive, friendly Telegram AI companion with light, tasteful flirting."
    )
