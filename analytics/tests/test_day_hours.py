"""
Arrival and departure, a day at a time.

app_user.earliest_start and latest_end are one window applied to every day of
every festival. Nobody attends a weekend that way: people drive up after work
on the Friday and are on site from ten on the Saturday. With only the
account-wide setting, somebody arriving late on day one had to either lose the
mornings of every other day or lie to the app about the first.
"""
from datetime import date, datetime, time, timedelta

from app.routes.planning import within_hours
from app.scheduler import Candidate

FRIDAY = date(2027, 8, 13)
SATURDAY = date(2027, 8, 14)


def band(name, day, start_hour, minutes=60):
    start = datetime(day.year, day.month, day.day, start_hour, 0)
    return Candidate(performance_id=abs(hash((name, day))) % 100000,
                     artist_id=abs(hash(name)) % 100000, artist=name,
                     stage='Main Stage', starts_at=start,
                     ends_at=start + timedelta(minutes=minutes),
                     score=0.5, is_pick=False)


def names(by_day, day):
    return [c.artist for c in by_day[day]]


def two_days():
    return {FRIDAY: [band('Friday Morning', FRIDAY, 11),
                     band('Friday Evening', FRIDAY, 18)],
            SATURDAY: [band('Saturday Morning', SATURDAY, 11),
                       band('Saturday Evening', SATURDAY, 18)]}


def test_one_day_arriving_late_leaves_the_others_alone():
    """The case the account-wide window could not express."""
    kept = within_hours(two_days(), default=(None, None),
                        day_hours={FRIDAY: (time(16, 0), None)})
    assert names(kept, FRIDAY) == ['Friday Evening']
    assert names(kept, SATURDAY) == ['Saturday Morning', 'Saturday Evening']


def test_a_day_with_its_own_hours_ignores_the_profile_window():
    """
    The more specific answer wins outright. Holding a Friday that says "from
    16:00" to the profile's "not after 19:00" as well would mean the person
    has to restate their whole profile to describe one evening.
    """
    kept = within_hours(two_days(), default=(time(11, 0), time(12, 30)),
                        day_hours={FRIDAY: (time(16, 0), None)})
    assert names(kept, FRIDAY) == ['Friday Evening']
    assert names(kept, SATURDAY) == ['Saturday Morning']


def test_leaving_early_drops_only_what_runs_past_the_departure():
    kept = within_hours(two_days(), default=(None, None),
                        day_hours={SATURDAY: (None, time(17, 0))})
    assert names(kept, SATURDAY) == ['Saturday Morning']


def test_the_profile_window_still_applies_where_a_day_says_nothing():
    kept = within_hours(two_days(), default=(time(16, 0), None), day_hours={})
    assert names(kept, FRIDAY) == ['Friday Evening']
    assert names(kept, SATURDAY) == ['Saturday Evening']


def test_hours_that_would_empty_a_day_are_ignored_for_that_day():
    """
    Someone whose hours exclude every set on the Sunday has mistyped
    something. An empty day explains neither the mistake nor the festival.
    """
    kept = within_hours(two_days(), default=(None, None),
                        day_hours={FRIDAY: (time(23, 0), None)})
    assert len(kept[FRIDAY]) == 2
