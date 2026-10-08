"""
Runtime configuration for the analytics service.

Values come from environment variables (or a local .env file, if one is
present). Nothing here should be hard-coded per-environment; that is the
whole point of pulling it out of the app.

Targets Python 3.9 syntax.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Same Postgres (Neon) database as the web app, per db/schema.sql:
    # this service reads and writes dim_artist, artist_tag, artist_score,
    # and artist_momentum alongside the fact_* tables it needs for scoring.
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/festimize"

    # Surfaced on /health and useful in logs; not load-bearing yet.
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    """Cached so we parse the environment once per process."""
    return Settings()
