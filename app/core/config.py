from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr
from typing import Optional

class Settings(BaseSettings):
    app_env: str = "production"
    api_prefix: str = "/api"
    secret_key: str
    access_token_expire_minutes: int = 60

    database_url: str

    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    openai_api_key: Optional[str] = None

    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: Optional[str] = None

    serpapi_api_key: Optional[str] = None
    youtube_api_key: Optional[str] = None

    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[EmailStr] = None

    sentry_dsn: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

settings = Settings()

