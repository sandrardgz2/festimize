"""
Tests the /health endpoint with the real database dependency overridden,
so this passes with no database configured or reachable.

The endpoint answers two different questions and they are not the same one:
whether a database is reachable, and whether it is the database this service
needs. "SELECT 1" passes against any Postgres in the world, which is how a
connection to one ten migrations behind went unnoticed — it reported
"connected" and then behaved strangely.

Targets Python 3.9 syntax.
"""
from fastapi.testclient import TestClient

from app import schema_check
from app.db import get_db
from app.main import app


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeSession:
    """
    Stands in for a Session, answering the two catalogue queries the schema
    check makes. `holding` is what this pretend database contains.
    """

    def __init__(self, holding):
        self.holding = holding

    def execute(self, statement, *args, **kwargs):
        sql = str(statement)
        if 'information_schema.tables' in sql:
            return _Result([(t,) for t, _ in self.holding])
        if 'information_schema.columns' in sql:
            return _Result([(t, c) for t, c in self.holding if c])
        return None

    def close(self):
        pass


def _serving(holding):
    def _get():
        yield _FakeSession(holding)
    return _get


EVERYTHING = [(t, c) for t, c in schema_check.REQUIRED]
client = TestClient(app)


def test_health_reports_a_database_with_the_schema_it_needs():
    app.dependency_overrides[get_db] = _serving(EVERYTHING)
    try:
        body = client.get("/health").json()
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["schema_state"] == "ok"


def test_health_is_degraded_against_a_database_that_is_behind():
    """
    The case this exists for. Reachable, answering queries, and missing the
    tables the planner writes to — which is what analytics/.env points at.
    """
    behind = [(t, c) for t, c in EVERYTHING if t not in ('plan_omitted', 'plan_day')]
    app.dependency_overrides[get_db] = _serving(behind)
    try:
        body = client.get("/health").json()
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert body["status"] == "degraded"
    assert body["database"] == "connected", 'it is reachable; that was never the question'
    assert body["schema_state"] == "behind"
    assert "plan_omitted" in body["detail"] and "plan_day" in body["detail"]
