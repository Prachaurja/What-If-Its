"""All configuration comes from environment variables (or a .env file in dev).
Nothing secret is ever hard-coded. See .env.example for the full list.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres in prod; SQLite fallback keeps tests and first-run dead simple.
    database_url: str = "postgresql+psycopg://swipe:swipe@localhost:5432/swipe"
    redis_url: str = "redis://localhost:6379/0"

    # object storage (MinIO in dev, any S3 in prod) — unused until Phase 2
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "swipe"
    s3_secret_key: str = "swipe-secret"

    # similarity engine knobs
    shingle_k: int = 5
    winnow_w: int = 8
    min_shared: int = 3

    # auth
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30

    environment: str = "dev"

settings = Settings()
