"""
Does this database have the schema the service needs?

The health endpoint used to answer "SELECT 1", which any reachable Postgres
passes — including one several migrations behind. That is not a theoretical
worry: analytics/.env points at a hosted database that was last migrated in
early October, so starting the service without overriding DATABASE_URL
connects it to something that looks fine, answers queries, and is missing
most of the tables the planner writes to.

The failure that produces is the worst kind. The service starts, the web app
calls it, and the first thing anybody sees is a schedule behaving oddly —
not an error naming the cause. So the cause is named here instead, once, at
startup and on /health.

Only what this service actually reads or writes is listed. A column the web
app owns and the planner never touches is not this module's business.

Targets Python 3.9 syntax.
"""
from typing import List, Optional, Tuple

from sqlalchemy import text

# (table, column) — column None means the table itself is enough.
REQUIRED = [
    ('dim_artist', None),
    ('fact_performance', None),
    ('artist_score', None),
    ('plan', 'fit_inside_limit'),      # 007
    ('plan_item', None),
    ('plan_declined', None),           # 003
    ('plan_pinned', 'from_at'),        # 004, 005
    ('plan_meal', None),               # 006
    ('plan_day', None),                # 009
    ('plan_omitted', None),            # 010
    ('user_artist', 'must_see'),       # 008
    ('app_user', 'stamina'),           # 002
    ('app_user', 'earliest_start'),    # 002
]


def missing(db) -> List[str]:
    """What this service needs and the connected database does not have."""
    tables = {r[0] for r in db.execute(text(
        "select table_name from information_schema.tables "
        "where table_schema = 'public'")).fetchall()}
    columns = {(r[0], r[1]) for r in db.execute(text(
        "select table_name, column_name from information_schema.columns "
        "where table_schema = 'public'")).fetchall()}
    gaps = []
    for table, column in REQUIRED:
        if table not in tables:
            gaps.append(table)
        elif column is not None and (table, column) not in columns:
            gaps.append('%s.%s' % (table, column))
    return gaps


def describe(db) -> Tuple[str, Optional[str]]:
    """('ok', None), or ('behind', what is missing) — never raises."""
    try:
        gaps = missing(db)
    except Exception as exc:                       # pragma: no cover
        return 'unreachable', str(exc).splitlines()[0][:200]
    if gaps:
        return 'behind', 'missing: ' + ', '.join(gaps)
    return 'ok', None
