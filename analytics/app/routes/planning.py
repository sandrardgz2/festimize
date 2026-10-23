"""
Schedule building.

POST /plan/{user_id}?edition_id=N builds a day-by-day schedule for one festival
edition and saves it to plan and plan_item, replacing any previous plan for that
user and edition.

The choosing is in app/scheduler.py; this module is the database half: load the
candidates, call the scheduler once per festival day, write the result back.

Targets Python 3.9 syntax.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.scheduler import Candidate, build_day

# Hours between the last set of one day and the first of the next. Nine is a
# night in a tent rather than a night in a bed: enough to be upright, not
# enough to be rested, which is what a festival actually offers.
SLEEP_FLOOR_HOURS = 9

router = APIRouter(tags=["planning"])


class PlanSlot(BaseModel):
    kind: str
    starts_at: datetime
    ends_at: datetime
    artist: Optional[str] = None
    stage: Optional[str] = None
    reason: str = ""


class PlanResponse(BaseModel):
    user_id: int
    edition_id: int
    days: int
    sets: int
    rests: int
    discoveries: int
    slots: List[PlanSlot]


@router.post("/plan/{user_id}", response_model=PlanResponse)
def build_plan(
    user_id: int,
    edition_id: int = Query(..., description="Which festival edition to plan"),
    discovery_quota: float = Query(1 / 3, ge=0.0, le=1.0),
    # Keep in step with the scheduler default; overriding it here silently
    # changed pacing behaviour and cost a set.
    max_run_minutes: int = Query(180, ge=60, le=600),
    db: Session = Depends(get_db),
) -> PlanResponse:
    rows = db.execute(
        text(
            """
            select p.performance_id, a.artist_id, a.name,
                   coalesce(s.name, 'TBA') as stage,
                   p.starts_at, p.ends_at,
                   coalesce(sc.match_score, 0) as score,
                   (ua.artist_id is not null) as is_pick
            from fact_performance p
            join dim_artist a on a.artist_id = p.artist_id
            left join dim_stage s on s.stage_id = p.stage_id
            left join artist_score sc on sc.artist_id = p.artist_id and sc.user_id = :uid
            left join user_artist ua on ua.artist_id = p.artist_id and ua.user_id = :uid
            where p.edition_id = :eid and p.starts_at is not null
            order by p.starts_at
            """
        ),
        {"uid": user_id, "eid": edition_id},
    ).fetchall()

    # Sets this person has already turned down on this plan. Filtered out
    # before the scheduler sees them, so the solver optimises the day that is
    # actually on offer rather than choosing a set and having it removed
    # afterwards — which would leave the hole it was filling.
    declined = {r.performance_id for r in db.execute(
        text("""select d.performance_id from plan_declined d
                   join plan pl on pl.plan_id = d.plan_id
                  where pl.user_id = :uid and pl.edition_id = :eid"""),
        {"uid": user_id, "eid": edition_id}).fetchall()}
    if declined:
        rows = [r for r in rows if r.performance_id not in declined]

    # The person's own pacing, set on the profile page. These were constants
    # in the scheduler until that page existed; the caller may still override
    # max_run_minutes, which is what the existing query parameter does.
    pace = db.execute(
        text("""select stamina, max_run_minutes, meal_by, earliest_start, latest_end
                   from app_user where user_id = :uid"""),
        {"uid": user_id},
    ).first()
    cap = {"light": 300, "hard": 600}.get(pace.stamina if pace else "", 450)
    if pace and pace.max_run_minutes and max_run_minutes == 180:
        max_run_minutes = int(pace.max_run_minutes)

    if not rows:
        raise HTTPException(status_code=404, detail="No performances with set times for that edition.")

    by_day = {}
    for r in rows:
        by_day.setdefault(r.starts_at.date(), []).append(
            Candidate(r.performance_id, r.artist_id, r.name, r.stage,
                      r.starts_at, r.ends_at, float(r.score), bool(r.is_pick))
        )

    # Days are solved in order rather than independently, because one of the
    # pacing rules spans them: how late you were out last night decides how
    # early you can be out this morning. Each day is told the earliest it may
    # begin, which the previous day's finish and the sleep floor determine.
    # Sets outside the hours this person will attend are not offered at all,
    # rather than offered and then dropped: the schedule should not argue with
    # someone about when their day starts.
    if pace and (pace.earliest_start or pace.latest_end):
        for day, found in list(by_day.items()):
            kept = [c for c in found
                    if (not pace.earliest_start or c.starts_at.time() >= pace.earliest_start)
                    and (not pace.latest_end or c.ends_at.time() <= pace.latest_end)]
            by_day[day] = kept or found        # never leave a day with nothing

    slots = []
    not_before = None
    for day in sorted(by_day):
        built = build_day(by_day[day],
                          discovery_quota=discovery_quota,
                          max_run_minutes=max_run_minutes,
                          not_before=not_before,
                          music_cap_minutes=cap,
                          meal_by=pace.meal_by if pace else None)
        slots.extend(built)
        finished = max((s.ends_at for s in built if s.kind == 'SET'), default=None)
        not_before = finished + timedelta(hours=SLEEP_FLOOR_HOURS) if finished else None

    # One plan per user per edition; rewrite it wholesale rather than diffing.
    plan_id = db.execute(
        text(
            """
            insert into plan (user_id, edition_id) values (:uid, :eid)
            on conflict (user_id, edition_id) do update set updated_at = now()
            returning plan_id
            """
        ),
        {"uid": user_id, "eid": edition_id},
    ).scalar_one()
    db.execute(text("delete from plan_item where plan_id = :p"), {"p": plan_id})

    for s in slots:
        db.execute(
            text(
                """
                insert into plan_item (plan_id, item_type, performance_id, starts_at, ends_at, reason)
                values (:p, :kind, :perf, :start, :end, :reason)
                """
            ),
            {"p": plan_id, "kind": s.kind, "perf": s.performance_id,
             "start": s.starts_at, "end": s.ends_at, "reason": s.reason},
        )
    db.commit()

    picks = sum(1 for s in slots if s.kind == "SET" and s.reason == "your pick")
    sets = sum(1 for s in slots if s.kind == "SET")
    return PlanResponse(
        user_id=user_id, edition_id=edition_id, days=len(by_day),
        sets=sets, rests=sum(1 for s in slots if s.kind == "REST"),
        discoveries=sets - picks,
        slots=[PlanSlot(kind=s.kind, starts_at=s.starts_at, ends_at=s.ends_at,
                        artist=s.artist, stage=s.stage, reason=s.reason) for s in slots],
    )
