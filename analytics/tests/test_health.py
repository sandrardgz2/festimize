"""
Tests the /health endpoint with the real database dependency overridden,
so this passes with no database configured or reachable.

Targets Python 3.9 syntax.
"""
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app


class _FakeSession:
    """Stands in for a SQLAlchemy Session: any query "succeeds"."""

    def execute(self, *args, **kwargs):
        return None


def _get_fake_db():
    yield _FakeSession()


app.dependency_overrides[get_db] = _get_fake_db
client = TestClient(app)


def test_health_reports_connected_database():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
