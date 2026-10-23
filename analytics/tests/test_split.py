"""
Leaving one set early to catch another.

choose_best can join a set late but never leave one early, so two overlapping
sets were always a choice between them — the solver would drop a band outright
rather than take half of one and all of the other. That is not what anybody
does at a festival, and the app already lets a person ask for it by hand one
gap at a time. These are the limits on the solver proposing it unasked.
"""
from datetime import datetime, timedelta

from app.scheduler import Candidate, build_day

DAY = datetime(2027, 8, 13, 10, 0)


def band(name, start_hour, start_min=0, minutes=60, score=0.5, pick=False,
         must_see=False, stage='Main Stage'):
    start = DAY.replace(hour=start_hour, minute=start_min)
    return Candidate(performance_id=abs(hash((name, start_hour, start_min))) % 100000,
                     artist_id=abs(hash(name)) % 100000, artist=name,
                     stage=stage, starts_at=start,
                     ends_at=start + timedelta(minutes=minutes),
                     score=score, is_pick=pick, must_see=must_see)


def sets_in(slots):
    return [s.artist for s in slots if s.kind == 'SET']


def slot_for(slots, artist):
    return next(s for s in slots if s.kind == 'SET' and s.artist == artist)


def test_two_overlapping_picks_are_both_caught():
    """
    The whole point. Both at 14:00 and 15:00 with an hour each, overlapping by
    half an hour: the solver used to take one and drop the other.
    """
    day = [band('Early Pick', 14, minutes=90, score=0.6, pick=True),
           band('Late Pick', 15, minutes=60, score=0.5, pick=True,
                stage='Second Stage'),
           band('Evening', 18)]
    built = build_day(day)
    assert 'Early Pick' in sets_in(built)
    assert 'Late Pick' in sets_in(built)


def test_the_first_set_is_cut_short_by_the_walk_and_says_so():
    """
    You leave in time to get there, not when the next band starts, and the
    schedule says what it cost — the figure a person needs to decide whether
    they would rather not.
    """
    day = [band('Early Pick', 14, minutes=90, score=0.6, pick=True),
           band('Late Pick', 15, minutes=60, score=0.5, pick=True,
                stage='Second Stage')]
    built = build_day(day)
    cut = slot_for(built, 'Early Pick')
    assert cut.ends_at == DAY.replace(hour=14, minute=50), 'left ten minutes before 15:00'
    assert 'left 40 min early to catch Late Pick' in cut.reason


def test_the_second_set_is_caught_whole():
    """
    Half of one and half of the other reads well in a sentence, but the only
    reason to leave early is to be somewhere. Arriving late as well means
    missing the middle of both for no gain.
    """
    day = [band('Early Pick', 14, minutes=90, score=0.6, pick=True),
           band('Late Pick', 15, minutes=60, score=0.5, pick=True,
                stage='Second Stage')]
    whole = slot_for(build_day(day), 'Late Pick')
    assert whole.starts_at == DAY.replace(hour=15, minute=0)
    assert whole.ends_at == DAY.replace(hour=16, minute=0)


def test_a_recommendation_never_cuts_your_own_pick_short():
    """Giving up part of an artist you named for one you did not is not a trade
    anybody asked for."""
    day = [band('My Pick', 14, minutes=90, score=0.6, pick=True),
           band('Suggested', 15, minutes=60, score=0.99, stage='Second Stage')]
    built = build_day(day)
    assert slot_for(built, 'My Pick').ends_at == DAY.replace(hour=15, minute=30)
    assert 'Suggested' not in sets_in(built)


def test_a_must_see_is_never_left_early():
    """The tier above a pick exists to keep those whole."""
    day = [band('Came For This', 14, minutes=90, score=0.6, pick=True, must_see=True),
           band('Other Pick', 15, minutes=60, score=0.9, pick=True,
                stage='Second Stage')]
    built = build_day(day)
    assert slot_for(built, 'Came For This').ends_at == DAY.replace(hour=15, minute=30)
    assert 'Other Pick' not in sets_in(built)


def test_a_pinned_set_is_never_left_early():
    """They said where they wanted to be. This is not the place to shorten it."""
    pinned = band('Asked For This', 14, minutes=90, score=0.3, pick=True)
    other = band('Other Pick', 15, minutes=60, score=0.9, pick=True,
                 stage='Second Stage')
    built = build_day([pinned, other], pinned=[pinned.performance_id])
    assert slot_for(built, 'Asked For This').ends_at == DAY.replace(hour=15, minute=30)


def test_too_little_of_the_first_set_is_not_worth_turning_up_for():
    """
    Overlapping by almost all of it. Twenty minutes of the first, less the
    walk, is below the floor, so the pair is not split and the solver makes
    the straight choice it always made.
    """
    day = [band('Early Pick', 14, minutes=90, score=0.6, pick=True),
           band('Late Pick', 14, 15, minutes=75, score=0.9, pick=True,
                stage='Second Stage')]
    built = build_day(day)
    assert len(sets_in(built)) == 1


def test_the_set_after_the_pair_still_has_time_to_walk_to():
    """
    A split that lands you somewhere you cannot leave is not a split. Nothing
    here is dropped to make room for one.
    """
    day = [band('Early Pick', 14, minutes=90, score=0.6, pick=True),
           band('Late Pick', 15, minutes=60, score=0.5, pick=True,
                stage='Second Stage'),
           band('Right After', 16, minutes=45, score=0.95, pick=True,
                stage='Third Stage')]
    built = build_day(day)
    chosen = sets_in(built)
    assert 'Right After' in chosen
    assert 'Late Pick' not in chosen, 'would have left no time to walk out'


def test_never_give_up_more_music_than_the_split_gains():
    """
    Without this the floor is all there is, so an hour of one band could be
    given up for a ten-minute set and counted as a second artist — a net loss
    of music dressed up as variety.
    """
    day = [band('Long Pick', 14, minutes=120, score=0.6, pick=True),
           band('Brief Pick', 15, minutes=15, score=0.9, pick=True,
                stage='Second Stage')]
    built = build_day(day)
    assert slot_for(built, 'Long Pick').ends_at == DAY.replace(hour=16, minute=0)
    assert 'Brief Pick' not in sets_in(built)


def test_an_even_trade_is_still_taken():
    """The guard must not become "only when you come out ahead" — giving up
    twenty-five minutes for a thirty-minute set is the Deftones/Currents case
    on the real bill, and it is worth taking."""
    day = [band('Early Pick', 19, 30, minutes=70, score=0.6, pick=True),
           band('Late Pick', 20, 25, minutes=30, score=0.5, pick=True,
                stage='Second Stage')]
    built = build_day(day)
    assert sets_in(built) == ['Early Pick', 'Late Pick']
    assert slot_for(built, 'Early Pick').ends_at == DAY.replace(hour=20, minute=15)
