import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEYS: list[str] = [k for k in [
        os.getenv("GEMINI_API_KEY_1"),
        os.getenv("GEMINI_API_KEY_2"),
        os.getenv("GEMINI_API_KEY_3"),
        os.getenv("GEMINI_API_KEY_4"),
        os.getenv("GEMINI_API_KEY_5")
    ] if k]
    CACHE_DB_URL: str = os.getenv("CACHE_DB_URL", "postgresql://neondb_owner:npg_UCdk9eMi2vGn@ep-mute-firefly-amtmu27v-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
    MODELS: list[str] = ["gemini-3.1-flash-lite-preview", "gemini-2.5-flash", "gemini-3.1-flash-lite-preview"]

    class Config:
        env_file = ".env"

settings = Settings()
