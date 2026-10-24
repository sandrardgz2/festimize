"""
Must-see artists: the tier above an ordinary pick.

Every saved artist used to carry the same bonus, so a clash between two of
them was settled on match score — the software deciding which band you lose.
Measured on the demo data 2026-10-23, one account had four such pairs on a
single bill. A festival-goer has two or three bands they came for; these are
the rules that follow from saying so.
"""
from datetime import datetime, timedelta

from app.scheduler import Candidate, build_day, choose_best

DAY = datetime(2027, 8, 13, 10, 0)


def band(name, start_hour, minutes=60, score=0.5, pick=False, must_see=False,
         stage='Main Stage'):
    start = DAY.replace(hour=0, minute=0) + timedelta(hours=start_hour)
    return Candidate(performance_id=abs(hash((name, start_hour))) % 100000,
                     artist_id=abs(hash(name)) % 100000, artist=name,
                     stage=stage, starts_at=start,
                     ends_at=start + timedelta(minutes=minutes),
                     score=score, is_pick=pick, must_see=must_see)


def sets_in(slots):
    return [s.artist for s in slots if s.kind == 'SET']


def test_a_must_see_wins_a_clash_against_a_better_matching_pick():
    """
    The whole point. Two saved artists at the same hour, the must-see scoring
    worse — which is exactly the case the old flat bonus got wrong, because
    with nothing to separate them the higher score took it.
    """
    day = [band('Came For This', 14, score=0.60, pick=True, must_see=True),
           band('Also Nice', 14, score=0.95, pick=True),
           band('Filler', 17)]
    chosen = sets_in(build_day(day))
    assert 'Came For This' in chosen
    assert 'Also Nice' not in chosen


def test_a_must_see_is_kept_whole_rather_than_joined_late():
    """
    A flat bonus is banked on arrival, so the solver would walk you in late to
    the band you came for in order to fit another beside it. Scaling by the
    share attended is what stops that: Headliner runs 18:00-19:00 and Support
    17:30-18:30, and taking both means missing forty minutes of one of them.
    """
    day = [band('Headliner', 18, score=0.7, pick=True, must_see=True),
           band('Support', 17, minutes=90, score=0.9, stage='Second Stage')]
    taken = {c.artist: arrive for c, arrive in choose_best(day)}
    assert 'Headliner' in taken
    assert taken['Headliner'] == day[0].starts_at, 'walked in late to a must-see'


def test_two_must_sees_that_only_graze_each_other_are_both_caught():
    """
    The scaling must not harden into "whole set or nothing". Where the choice
    is between missing the first quarter of one and losing it outright, the
    quarter costs twenty-five points and the whole set costs a hundred, so
    both are taken and one is joined late.

    This is the one case where a must-see is allowed to be partial: the
    alternative is not a better day, it is one fewer band you came for.
    """
    earlier = band('Earlier', 16, minutes=65, score=0.5, pick=True, must_see=True)
    wanted = band('Wanted', 17, score=0.4, pick=True, must_see=True,
                  stage='Second Stage')
    taken = {c.artist: arrive for c, arrive in choose_best([earlier, wanted])}
    assert set(taken) == {'Earlier', 'Wanted'}
    assert taken['Wanted'] > wanted.starts_at


def test_a_must_see_outranks_a_strong_recommendation_rather_than_shortening():
    """
    The other side of the same rule: when the clash is against an artist the
    person never named, the recommendation is what gives way. Missing fifteen
    minutes of the band you came for to fit a 0.9 suggestion beside it is the
    trade the flat bonus used to make.
    """
    earlier = band('Suggested', 16, minutes=65, score=0.9)
    wanted = band('Wanted', 17, score=0.4, pick=True, must_see=True)
    taken = {c.artist: arrive for c, arrive in choose_best([earlier, wanted])}
    assert taken['Wanted'] == wanted.starts_at
    assert 'Suggested' not in taken


def test_the_daily_cap_never_takes_a_must_see():
    """
    The cap is a budget for the scheduler's own choices. A set it had to pick
    because the person came for it is not one of those, even when they have
    asked for the day to be fitted inside the limit.
    """
    day = [band('One', 11, minutes=120, score=0.95),
           band('Two', 14, minutes=120, score=0.94),
           band('Must See', 18, minutes=60, score=0.30, pick=True, must_see=True)]
    chosen = sets_in(build_day(day, music_cap_minutes=240, fit_inside=True))
    assert 'Must See' in chosen
    assert len(chosen) < 3, 'the cap should still have bitten something'


def test_two_must_sees_that_clash_still_leave_one_behind():
    """
    No rule can fix this one — you cannot be in two places — so the honest
    result is one of them and a named alternative the page can offer as a
    swap, not a silent drop.
    """
    day = [band('Both At Eight A', 20, score=0.5, pick=True, must_see=True),
           band('Both At Eight B', 20, score=0.9, pick=True, must_see=True)]
    chosen = sets_in(build_day(day))
    assert len(chosen) == 1
