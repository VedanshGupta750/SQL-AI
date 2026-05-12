import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENAI_API_KEYS: list[str] = [k for k in [
        os.getenv("OPENAI_API_KEY"),
        os.getenv("OPENAI_API_KEY_1"),
        os.getenv("OPENAI_API_KEY_2"),
        os.getenv("OPENAI_API_KEY_3"),
        os.getenv("OPENAI_API_KEY_4"),
        os.getenv("OPENAI_API_KEY_5"),
    ] if k]
    CACHE_DB_URL: str = os.getenv(
        "CACHE_DB_URL",
        "postgresql://neondb_owner:npg_UCdk9eMi2vGn@ep-mute-firefly-amtmu27v-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
    )
    MODELS: list[str] = [
        m.strip() for m in os.getenv("OPENAI_MODELS", "gpt-4o-mini,gpt-4o").split(",") if m.strip()
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
