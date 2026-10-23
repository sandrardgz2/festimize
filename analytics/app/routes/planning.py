"""
Schedule building.

POST /plan/{user_id}?edition_id=N builds a day-by-day schedule for one festival
edition and saves it to plan and plan_item, replacing any previous plan for that
user and edition.

GET /plan/{user_id}/cost?edition_id=N answers a different question about the
same machinery: for every set not currently in the schedule, what would adding
it cost? It is the "add" button's own counterfactual, run before the click.

The choosing is in app/scheduler.py; this module is the database half: load the
candidates, call the scheduler once per festival day, write the result back.

Targets Python 3.9 syntax.
"""
import dataclasses
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence

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


class AddCost(BaseModel):
    performance_id: int
    artist: str
    # Sets that are in the schedule now and would not be afterwards. Empty
    # means the addition is free: there is room for it.
    costs: List[str]
    # Of those, the ones that actually overlap the set being added. The rest
    # were dropped to stay inside the daily cap and may be playing hours
    # away, which reads as nonsense unless the page says so: adding Scowl at
    # 13:30 "cost" Code Orange at 16:30, because a 430-minute day plus 40
    # minutes exceeds a 450-minute limit and something had to go.
    clashes: List[str]
    # Sets that are not in the schedule now and would be afterwards, besides
    # the one being added. Moving one set can open a gap that fits another,
    # so an addition is not always a straight trade.
    gains: List[str]
    # False when the set falls outside the hours this person said they would
    # attend, in which case adding it would do nothing at all.
    available: bool
    # Minutes of music on the day this set falls on, after adding it. The
    # page needs this to say whether the addition puts the day past the
    # hours the person set, which is a different question from what it
    # displaces and the more important one.
    day_minutes_after: int = 0


class AddCostResponse(BaseModel):
    user_id: int
    edition_id: int
    costs: List[AddCost]


class _Bill:
    """One edition's candidates and one person's pacing, loaded once.

    The cost endpoint solves the same festival a few dozen times over. Loading
    the bill per solve made that a few dozen round trips for data that cannot
    have changed in between, so loading and solving are separated here.
    """

    def __init__(self, by_day, pinned, cap, meal_by, max_run_minutes, joined_late=None,
                 windows=None, meals=None, leaves_early=None, fit_inside=False):
        self.by_day = by_day
        self.pinned = pinned
        self.cap = cap
        self.meal_by = meal_by
        self.max_run_minutes = max_run_minutes
        # performance_id -> (minutes missed, the time it really started)
        self.joined_late = joined_late or {}
        # performance_ids pinned to only part of their set
        self.windows = windows or {}
        # date -> the moment this person wants their meal break to start
        self.meals = meals or {}
        # performance_id -> (minutes cut from the end, when it really finishes)
        self.leaves_early = leaves_early or {}
        # Should the limit cover the whole day, including what was asked for?
        self.fit_inside = fit_inside

    def offered(self) -> Dict[int, Candidate]:
        return {c.performance_id: c for day in self.by_day.values() for c in day}


def _load(db: Session, user_id: int, edition_id: int, max_run_minutes: int) -> _Bill:
    rows = db.execute(
        text(
            """
            select p.performance_id, a.artist_id, a.name,
                   coalesce(s.name, 'TBA') as stage,
                   p.starts_at, p.ends_at,
                   coalesce(sc.match_score, 0) as score,
                   (ua.artist_id is not null) as is_pick,
                   coalesce(ua.must_see, false) as must_see
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
    pin_rows = db.execute(
        text("""select p.performance_id, p.from_at, p.to_at from plan_pinned p
                   join plan pl on pl.plan_id = p.plan_id
                  where pl.user_id = :uid and pl.edition_id = :eid"""),
        {"uid": user_id, "eid": edition_id}).fetchall()
    pinned = [r.performance_id for r in pin_rows]
    # A pin may name only part of a set: the part that falls in a gap, when
    # the rest of it runs under something already in the day. Clamping the
    # candidate before the solver sees it means a set you are catching the
    # end of is simply a shorter set that starts when you arrive, so it fits
    # the gap and displaces nothing. The original start is kept so the page
    # can say you are joining late rather than pretending the band went on
    # when you did.
    windows = {r.performance_id: (r.from_at, r.to_at)
               for r in pin_rows if r.from_at is not None or r.to_at is not None}


    # Where this person said they want to eat, a day at a time.
    meals = {r.meal_on: r.starts_at for r in db.execute(
        text("""select m.meal_on, m.starts_at from plan_meal m
                   join plan pl on pl.plan_id = m.plan_id
                  where pl.user_id = :uid and pl.edition_id = :eid"""),
        {"uid": user_id, "eid": edition_id}).fetchall()}

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
    fit_inside = bool(db.execute(
        text("""select fit_inside_limit from plan
                 where user_id = :uid and edition_id = :eid"""),
        {"uid": user_id, "eid": edition_id}).scalar())

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
    joined_late = {}
    leaves_early = {}
    for r in rows:
        starts, ends = r.starts_at, r.ends_at
        window = windows.get(r.performance_id)
        if window:
            from_at, to_at = window
            starts = max(starts, from_at) if from_at else starts
            ends = min(ends, to_at) if to_at else ends
            if ends <= starts:                 # a window that leaves nothing
                starts, ends = r.starts_at, r.ends_at
            late = int((starts - r.starts_at).total_seconds() // 60)
            if late > 0:
                joined_late[r.performance_id] = (late, r.starts_at)
            early = int((r.ends_at - ends).total_seconds() // 60)
            if early > 0:
                leaves_early[r.performance_id] = (early, r.ends_at)
        by_day.setdefault(starts.date(), []).append(
            Candidate(r.performance_id, r.artist_id, r.name, r.stage,
                      starts, ends, float(r.score), bool(r.is_pick),
                      bool(r.must_see))
        )

    # Sets outside the hours this person will attend are not offered at all,
    # rather than offered and then dropped: the schedule should not argue with
    # someone about when their day starts.
    if pace and (pace.earliest_start or pace.latest_end):
        for day, found in list(by_day.items()):
            kept = [c for c in found
                    if (not pace.earliest_start or c.starts_at.time() >= pace.earliest_start)
                    and (not pace.latest_end or c.ends_at.time() <= pace.latest_end)]
            by_day[day] = kept or found        # never leave a day with nothing

    return _Bill(by_day, pinned, cap, meal_by=pace.meal_by if pace else None,
                 max_run_minutes=max_run_minutes, joined_late=joined_late,
                 windows=windows, meals=meals, leaves_early=leaves_early,
                 fit_inside=fit_inside)


def _solve(bill: _Bill, discovery_quota: float, also_pin: Sequence[int] = ()) -> list:
    """Solve the whole edition. also_pin forces extra sets into the schedule.

    Days are solved in order rather than independently, because one of the
    pacing rules spans them: how late you were out last night decides how
    early you can be out this morning. Each day is told the earliest it may
    begin, which the previous day's finish and the sleep floor determine —
    which is also why a counterfactual has to re-solve the whole edition and
    not just the day the added set falls on.
    """
    pinned = list(bill.pinned) + list(also_pin)
    slots = []
    not_before = None
    for day in sorted(bill.by_day):
        # Fresh copies every solve. build_day rewrites starts_at on a set
        # joined late, in place, so handing it the same objects twice has the
        # second solve planning a day that drifts later than the real one —
        # harmless when a plan was built once, wrong as soon as the cost
        # endpoint solves the same festival twenty times over.
        fresh = [dataclasses.replace(c) for c in bill.by_day[day]]
        built = build_day(fresh,
                          discovery_quota=discovery_quota,
                          max_run_minutes=bill.max_run_minutes,
                          not_before=not_before,
                          music_cap_minutes=bill.cap,
                          meal_by=bill.meal_by,
                          pinned=pinned,
                          tight=list(bill.joined_late) + list(bill.windows),
                          meal_at=bill.meals.get(day),
                          fit_inside=bill.fit_inside)
        slots.extend(built)
        finished = max((s.ends_at for s in built if s.kind == 'SET'), default=None)
        not_before = finished + timedelta(hours=SLEEP_FLOOR_HOURS) if finished else None
    return slots


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
    bill = _load(db, user_id, edition_id, max_run_minutes)
    slots = _solve(bill, discovery_quota)

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
        reason = s.reason
        # Say that this is part of a set rather than all of it. The solver was
        # handed a clamped candidate and has no idea the band went on earlier,
        # so the page would otherwise show a 40-minute set that is really the
        # back half of a 60-minute one.
        late = bill.joined_late.get(s.performance_id) if s.kind == "SET" else None
        if late:
            missed, really_started = late
            reason += " · you join %d min in; they start at %s" % (
                missed, really_started.strftime("%H:%M"))
        # And say when you are leaving before the end, which a clamped window
        # can also mean: the set the solver was given finishes when you do.
        early = bill.leaves_early.get(s.performance_id) if s.kind == "SET" else None
        if early:
            left, really_ends = early
            reason += " · you leave %d min early; they play until %s" % (
                left, really_ends.strftime("%H:%M"))
        db.execute(
            text(
                """
                insert into plan_item (plan_id, item_type, performance_id, starts_at, ends_at, reason, alternative_id)
                values (:p, :kind, :perf, :start, :end, :reason, :alt)
                """
            ),
            {"p": plan_id, "kind": s.kind, "perf": s.performance_id,
             "start": s.starts_at, "end": s.ends_at, "reason": reason,
             "alt": s.alternative_id},
        )
    db.commit()

    picks = sum(1 for s in slots if s.kind == "SET" and s.reason == "your pick")
    sets = sum(1 for s in slots if s.kind == "SET")
    return PlanResponse(
        user_id=user_id, edition_id=edition_id, days=len(bill.by_day),
        sets=sets, rests=sum(1 for s in slots if s.kind == "REST"),
        discoveries=sets - picks,
        slots=[PlanSlot(kind=s.kind, starts_at=s.starts_at, ends_at=s.ends_at,
                        artist=s.artist, stage=s.stage, reason=s.reason) for s in slots],
    )


@router.get("/plan/{user_id}/cost", response_model=AddCostResponse)
def add_cost(
    user_id: int,
    edition_id: int = Query(..., description="Which festival edition"),
    discovery_quota: float = Query(1 / 3, ge=0.0, le=1.0),
    max_run_minutes: int = Query(180, ge=60, le=600),
    db: Session = Depends(get_db),
) -> AddCostResponse:
    """What each absent set would cost, if it were added.

    This is not an estimate. Adding a set pins it and re-solves, so the answer
    is got by pinning it and re-solving: the same code path the button runs,
    and therefore the same schedule, as long as nothing else changes in
    between. Nothing is written.
    """
    bill = _load(db, user_id, edition_id, max_run_minutes)
    offered = bill.offered()

    base = {s.performance_id for s in _solve(bill, discovery_quota) if s.kind == "SET"}

    # Every set on the bill that is not already in the schedule, including the
    # ones the person's hours have filtered out — the lineup page offers those
    # too, and "adding" one silently does nothing, which is worth saying.
    absent = db.execute(
        text(
            """
            select p.performance_id, a.name
              from fact_performance p
              join dim_artist a on a.artist_id = p.artist_id
             where p.edition_id = :eid and p.starts_at is not null
             order by p.starts_at
            """
        ),
        {"eid": edition_id},
    ).fetchall()

    out = []
    for r in absent:
        if r.performance_id in base:
            continue
        if r.performance_id not in offered:
            out.append(AddCost(performance_id=r.performance_id, artist=r.name,
                               costs=[], clashes=[], gains=[], available=False))
            continue
        solved = _solve(bill, discovery_quota, also_pin=[r.performance_id])
        after = {s.performance_id for s in solved if s.kind == "SET"}
        adding = offered[r.performance_id]
        lost_ids = [p for p in base - after if p in offered]
        lost = [offered[p].artist for p in lost_ids]
        clashes = [offered[p].artist for p in lost_ids
                   if offered[p].starts_at < adding.ends_at
                   and adding.starts_at < offered[p].ends_at]
        gained = [offered[p].artist for p in after - base
                  if p != r.performance_id and p in offered]
        on_the_day = offered[r.performance_id].starts_at.date()
        minutes = sum((s.ends_at - s.starts_at).total_seconds() / 60
                      for s in solved
                      if s.kind == "SET" and s.starts_at.date() == on_the_day)
        out.append(AddCost(performance_id=r.performance_id, artist=r.name,
                           costs=sorted(lost), clashes=sorted(clashes),
                           gains=sorted(gained), available=True,
                           day_minutes_after=int(round(minutes))))

    return AddCostResponse(user_id=user_id, edition_id=edition_id, costs=out)
