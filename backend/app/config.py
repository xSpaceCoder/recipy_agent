from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    google_ai_api_key: str = ""

    class Config:
        env_file = "../.env"
        extra = "ignore"


@lru_cache
def get_settings():
    return Settings()
