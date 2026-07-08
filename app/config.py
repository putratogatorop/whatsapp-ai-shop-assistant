from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    # WhatsApp Cloud API (Meta for Developers)
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = "change-me"
    whatsapp_app_secret: str = ""
    whatsapp_api_version: str = "v21.0"

    # LLM provider selection: groq | openai | anthropic | gemini
    llm_provider: str = "groq"
    llm_model: str = ""  # optional override, otherwise a sane per-provider default is used
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # Database
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/whatsapp_agent"

    # Redis (Celery broker/backend + session cache)
    redis_url: str = "redis://localhost:6379/0"

    # Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "shop_knowledge_base"

    # Optional integrations
    n8n_webhook_url: str = ""

    store_name: str = "Toko Maju Jaya"


@lru_cache
def get_settings() -> Settings:
    return Settings()
