"""
The pacing rules that span a day and a weekend.

Neither of these fires on the demonstration festivals — they are programmed
sanely, finishing at 20:15 and starting again at 10:30 — so they are proved
here instead of in the app. That is the honest reason these tests exist: a
rule nobody can see in the demo still has to be shown to work.

Task 5.1. The exertion cap, the meal window and the breathers were built with
the scheduler in 3.5 and are covered by test_schedule_quality.py.
"""
from datetime import datetime, timedelta

from app.scheduler import Candidate, build_day

DAY = datetime(2027, 8, 13, 10, 0)


def band(name, start_hour, minutes=60, score=0.5, pick=False, day=DAY):
    start = day.replace(hour=0, minute=0) + timedelta(hours=start_hour)
    return Candidate(performance_id=abs(hash((name, start_hour))) % 100000,
                     artist_id=abs(hash(name)) % 100000, artist=name,
                     stage='Main Stage', starts_at=start,
                     ends_at=start + timedelta(minutes=minutes),
                     score=score, is_pick=pick)


def sets_in(slots):
    return [s.artist for s in slots if s.kind == 'SET']


def test_a_day_may_start_before_anything_came_before_it():
    """The first day of a festival has no previous night to recover from."""
    day = [band('Opener', 10), band('Second', 12), band('Third', 14)]
    assert 'Opener' in sets_in(build_day(day, not_before=None))


def test_the_morning_after_a_late_finish_starts_later():
    """
    A schedule that lists a 09:00 set after a 02:00 finish is not advice. The
    early sets are dropped rather than flagged, because the alternative is
    printing a plan and leaving the hard part to the reader.
    """
    day = [band('Breakfast Band', 9), band('Midday', 13), band('Evening', 18)]
    rested = build_day(day, not_before=DAY.replace(hour=11, minute=0))
    assert 'Breakfast Band' not in sets_in(rested)
    assert 'Midday' in sets_in(rested)


def test_a_sleep_floor_never_empties_a_day():
    """
    Better a tired morning than a blank page: if the floor would remove
    everything, the day is scheduled anyway and the person can judge.
    """
    day = [band('Only Act', 9)]
    kept = build_day(day, not_before=DAY.replace(hour=20, minute=0))
    assert sets_in(kept) == ['Only Act']


def test_a_day_will_not_hold_more_music_than_the_cap():
    """Nine hours of music in a row is an endurance event, not a festival."""
    day = [band('Act %d' % i, 9 + i, minutes=60, score=0.5 - i * 0.01)
           for i in range(12)]
    full = build_day(day, music_cap_minutes=10000)
    capped = build_day(day, music_cap_minutes=300)
    minutes = lambda slots: sum(
        (s.ends_at - s.starts_at).total_seconds() / 60 for s in slots if s.kind == 'SET')
    assert minutes(full) > 300
    assert minutes(capped) <= 300
    assert len(sets_in(capped)) < len(sets_in(full))


def test_the_cap_cuts_the_weakest_and_keeps_your_own_picks():
    """
    Someone who came for one band gets to stand through the day for it. Being
    told you are tired by software is not help.
    """
    day = [band('Act %d' % i, 9 + i, minutes=60, score=0.9) for i in range(8)]
    day.append(band('The One', 21, minutes=60, score=0.0, pick=True))
    capped = build_day(day, music_cap_minutes=240)
    assert 'The One' in sets_in(capped)


def test_the_cap_leaves_a_sane_day_alone():
    """It is a limit, not a target: a day under it is untouched."""
    day = [band('A', 12), band('B', 14), band('C', 16)]
    assert sets_in(build_day(day, music_cap_minutes=450)) == sets_in(build_day(day))
