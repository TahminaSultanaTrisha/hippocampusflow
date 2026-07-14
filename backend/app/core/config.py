"""Central configuration. All tunables live here, loaded from env/.env."""
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "HippocampusFlow API"
    database_url: str = "sqlite:///./dev.db"
    jwt_secret: str = "dev-only-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30

    upload_dir: str = "./uploads"
    max_upload_bytes: int = 10 * 1024 * 1024

    # Phase 2: the AI pipeline.
    anthropic_api_key: str = ""          # set in .env -- never in code
    classifier_model: str = "claude-haiku-4-5"   # fast + cheap: category detection
    free_scan_limit: int = 10                    # scans per calendar month on the free tier
    agent_model: str = "claude-sonnet-4-6"       # stronger: full analysis + chat


    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        # Cloud hosts (Railway, Heroku) provide postgres:// URLs;
        # SQLAlchemy needs the explicit driver scheme.
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
