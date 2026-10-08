"""
SQLAlchemy engine and session helpers.

One engine per process, one session per request. Routes should depend on
`get_db` rather than importing `SessionLocal` directly, so tests can override
the dependency with a fake/in-memory session (see tests/test_health.py).

Targets Python 3.9 syntax.
"""
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings

settings = get_settings()

# pool_pre_ping guards against stale connections to a remote (Neon) database
# that may close idle connections between requests.
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yields a session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
