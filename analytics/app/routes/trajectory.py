"""
One artist's share of the circuit, year by year.

The artist page draws this as the bars under "on the way up". It lives here
rather than in the web app because it is the series the rising measure is
computed from, and computing it twice in two languages is how the chart and
the badge come to disagree — which they did: a first version counted
festivals played per year, in Java, and drew falling bars under a caption
that said "a growing share".

Two things make the difference, and both are in app/momentum.py already:
the denominator is every booking that year rather than every festival, and
a year the artist did not play is a zero in the series rather than a gap.
The climb that earns the badge is usually the climb out of those zeros.

Targets Python 3.9 syntax.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.momentum import shares, usable_years

router = APIRouter(tags=["momentum"])

# The same rows score_momentum.py measures: finished festivals only, and
# historical rows only — the demonstration lineups carry set times and would
# put 2027 into a chart about what has already happened.
HISTORY = text("""
    SELECT e.year, f.name AS festival, a.name AS artist
      FROM fact_performance p
      JOIN dim_festival_edition e USING (edition_id)
      JOIN dim_festival f USING (festival_id)
      JOIN dim_artist a USING (artist_id)
     WHERE e.happened
       AND p.starts_at IS NULL
""")


class Point(BaseModel):
    year: int
    # Share of that year's bookings, as a percentage, to one decimal. Small
    # numbers: a well-booked artist holds a fraction of one per cent of a
    # circuit this size, so the bars are scaled by the caller.
    share: float
    # Festivals they played that year, for the tooltip. Zero is a real
    # answer, not a missing one.
    festivals: int


class Trajectory(BaseModel):
    artist_id: int
    years: List[Point]


@router.get("/artists/{artist_id}/trajectory", response_model=Trajectory)
def trajectory(artist_id: int, db: Session = Depends(get_db)) -> Trajectory:
    name = db.execute(text("select name from dim_artist where artist_id = :a"),
                      {"a": artist_id}).scalar()
    if name is None:
        raise HTTPException(status_code=404, detail="No such artist")

    rows = [(r.year, r.festival, r.artist) for r in db.execute(HISTORY).fetchall()]
    years = usable_years(rows)
    held = shares(rows, years)

    played = {}
    for year, festival, artist in rows:
        if artist == name and year in years:
            played.setdefault(year, set()).add(festival)

    return Trajectory(artist_id=artist_id, years=[
        Point(year=year,
              share=round(100.0 * held.get(year, {}).get(name, 0.0), 3),
              festivals=len(played.get(year, ())))
        for year in years
    ])
