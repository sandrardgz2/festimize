# Festimize analytics service

This service owns the batch/analytics side of Festimize: computing taste-match
scores (`artist_score`) and the rising-artist momentum measure
(`artist_momentum`) against the star schema in `db/schema.sql`
(`dim_artist`, `artist_tag`, `fact_performance`, ...). It does **not** own the
web app's day-to-day CRUD (`app_user`, `plan`, `plan_item`, auth, etc.) —
those belong to the main app, not here.

Scaffolded against Python 3.9 syntax (the system interpreter here is 3.9.6),
avoiding anything newer than 3.10; a newer interpreter works fine too if the
developer prefers one.

## Setup

```bash
cd analytics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configure

Set `DATABASE_URL` (a `.env` file in this directory works too, see
`app/config.py`):

```bash
export DATABASE_URL="postgresql+psycopg://user:password@host:5432/festimize"
```

## Run

```bash
uvicorn app.main:app --reload
```

Then check `GET http://127.0.0.1:8000/health`.

## Test

```bash
pytest
```

## What belongs here / what doesn't

This service is FastAPI plumbing, database access, and the eventual
recommender + momentum jobs; it is deliberately **not** where scoring or
momentum logic lives yet — `app/routes/scoring.py` is a placeholder (HTTP 501)
until the developer's own data-science work replaces it.
