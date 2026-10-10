"""
Rules a finished schedule has to obey.

These are not unit tests of the algorithm; they are the promises the product
makes to the person using it, checked against every demonstration festival in
the database. Each one exists because it was broken at some point:

  * a day lost a set so the scheduler could insert a break
  * breaks stacked up into two hours of standing around
  * the discovery quota traded away an artist the user had chosen

Needs DATABASE_URL (analytics/.env). Skipped when no database is reachable.
"""
import os
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, text

from app.scheduler import Candidate, build_day

LONGEST_ACCEPTABLE_BREAK = 60      # minutes: an hour off your feet is fine, more is not
MOST_LONG_BREAKS_PER_DAY = 1


def _url():
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    env = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env):
        for line in open(env):
            if line.startswith("DATABASE_URL="):
                return line.strip().split("=", 1)[1]
    return None


@pytest.fixture(scope="module")
def days():
    url = _url()
    if not url:
        pytest.skip("no DATABASE_URL")
    try:
        engine = create_engine(url)
        rows = engine.connect().execute(text("""
            select e.edition_id, f.name, p.performance_id, a.artist_id, a.name,
                   coalesce(s.name,'TBA'), p.starts_at, p.ends_at,
                   coalesce(sc.match_score,0), (ua.artist_id is not null)
            from fact_performance p
            join dim_artist a using(artist_id)
            join dim_festival_edition e on e.edition_id = p.edition_id
            join dim_festival f on f.festival_id = e.festival_id
            left join dim_stage s on s.stage_id = p.stage_id
            left join artist_score sc on sc.artist_id = a.artist_id and sc.user_id = 1
            left join user_artist ua on ua.artist_id = a.artist_id and ua.user_id = 1
            where p.starts_at is not null
            order by p.starts_at""")).fetchall()
    except Exception as exc:                      # pragma: no cover
        pytest.skip("database unreachable: %s" % exc)

    grouped = {}
    for r in rows:
        key = (r[1], r[6].date())
        grouped.setdefault(key, []).append(
            Candidate(r[2], r[3], r[4], r[5], r[6], r[7], float(r[8]), bool(r[9])))
    if not grouped:
        pytest.skip("no seeded festivals")
    return {k: build_day(v) for k, v in grouped.items()}


def test_no_break_runs_longer_than_an_hour(days):
    for (festival, date), slots in days.items():
        slots = sorted(slots, key=lambda s: s.starts_at)
        run = 0
        for slot in slots:
            minutes = int((slot.ends_at - slot.starts_at).total_seconds() // 60)
            run = run + minutes if slot.kind == "REST" else 0
            assert run <= LONGEST_ACCEPTABLE_BREAK, (
                "%s %s: %d minutes of rest in a row" % (festival, date, run))


def test_the_scheduler_adds_at_most_one_long_break(days):
    """
    Gaps the lineup leaves are not the scheduler's fault — on a two-stage
    festival there are stretches with nothing worth walking to. What the
    scheduler chooses to add is its responsibility, and that is one break.
    """
    for (festival, date), slots in days.items():
        chosen_breaks = [s for s in slots
                         if s.kind == "REST" and not s.reason.startswith("gap")
                         and (s.ends_at - s.starts_at) >= timedelta(minutes=45)]
        assert len(chosen_breaks) <= MOST_LONG_BREAKS_PER_DAY, (
            "%s %s: scheduler added %d long breaks" % (festival, date, len(chosen_breaks)))


def test_only_the_meal_break_may_cost_a_set(days):
    for (festival, date), slots in days.items():
        for slot in slots:
            if "skipped" in slot.reason:
                assert slot.reason.startswith("meal"), (
                    "%s %s: a %s gave up a set" % (festival, date, slot.reason.split(" —")[0]))


def test_every_day_has_music_and_a_break(days):
    for (festival, date), slots in days.items():
        sets = [s for s in slots if s.kind == "SET"]
        assert sets, "%s %s: no sets at all" % (festival, date)
        music = sum((s.ends_at - s.starts_at).total_seconds() / 3600 for s in sets)
        assert music >= 4, "%s %s: only %.1f hours of music" % (festival, date, music)
        assert any(s.kind == "REST" for s in slots), "%s %s: no break" % (festival, date)


def test_the_timeline_has_no_holes_or_overlaps(days):
    for (festival, date), slots in days.items():
        slots = sorted(slots, key=lambda s: s.starts_at)
        for earlier, later in zip(slots, slots[1:]):
            assert earlier.ends_at <= later.starts_at, (
                "%s %s: %s overlaps the next slot" % (festival, date, earlier.artist or earlier.reason))
            gap = int((later.starts_at - earlier.ends_at).total_seconds() // 60)
            assert gap < 15, (
                "%s %s: %d unexplained minutes after %s" % (
                    festival, date, gap, earlier.artist or earlier.reason))
