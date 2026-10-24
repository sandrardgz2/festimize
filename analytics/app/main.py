"""
Festimize analytics service — FastAPI entrypoint.

This service is the batch/analytics side of Festimize: it reads and writes
the star-schema tables in db/schema.sql (dim_artist, artist_tag,
artist_score, artist_momentum, fact_performance) to compute taste-match
scores and the rising-artist "momentum" measure. It does not serve the web
app's day-to-day CRUD (that's app_user, plan, plan_item, etc.) — it just
writes the cached numbers the web app reads.

Targets Python 3.9 syntax.
"""
import contextlib
import logging

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import schema_check
from app.db import SessionLocal, get_db
from app.routes import planning, scoring, tagging, trajectory

log = logging.getLogger("uvicorn.error")

@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Say at once if this is the wrong database.

    analytics/.env points at a hosted database last migrated in early
    October. Started without overriding DATABASE_URL, the service connects
    to it happily and the first sign of trouble is a schedule behaving
    oddly, with nothing naming the cause. Reachable is not the same as
    right, so the difference is reported here rather than discovered later.

    It warns rather than refuses: a database that is merely behind is still
    worth serving /health from, and that is the page somebody checks when
    they are trying to work out what is wrong.
    """
    db = SessionLocal()
    try:
        state, detail = schema_check.describe(db)
    except Exception as exc:                       # pragma: no cover
        state, detail = 'unreachable', str(exc).splitlines()[0][:200]
    finally:
        db.close()
    if state == 'ok':
        log.info('database schema is up to date')
    else:
        log.error('DATABASE IS NOT USABLE BY THIS SERVICE (%s) — %s', state, detail)
        log.error('check DATABASE_URL: it is probably pointing somewhere stale')
    yield


app = FastAPI(title="Festimize Analytics Service", lifespan=lifespan)
app.include_router(scoring.router)
app.include_router(planning.router)
app.include_router(tagging.router)
app.include_router(trajectory.router)


class HealthResponse(BaseModel):
    status: str
    database: str
    schema_state: str = "ok"
    detail: str = ""


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    """
    Reports liveness, reachability, and whether the schema is the one this
    service needs. "SELECT 1" alone passes against any Postgres at all,
    which is how a database ten migrations behind went unnoticed.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return HealthResponse(status="degraded", database="unreachable",
                              schema_state="unknown")
    state, detail = schema_check.describe(db)
    return HealthResponse(status="ok" if state == "ok" else "degraded",
                          database="connected", schema_state=state,
                          detail=detail or "")
