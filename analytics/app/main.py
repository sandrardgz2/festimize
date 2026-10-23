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
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.routes import planning, scoring, tagging, trajectory

app = FastAPI(title="Festimize Analytics Service")
app.include_router(scoring.router)
app.include_router(planning.router)
app.include_router(tagging.router)
app.include_router(trajectory.router)


class HealthResponse(BaseModel):
    status: str
    database: str


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    """Reports service liveness and whether the database is reachable."""
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(status="ok", database="connected")
    except Exception:
        return HealthResponse(status="degraded", database="unreachable")
