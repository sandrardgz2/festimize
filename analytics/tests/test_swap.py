"""
Swapping a set has to be reversible.

Asking for one act instead of another used to be a one-way door. The pin took
every clashing set off the table before the solver ran — which is right, a pin
should not be competed with — but it took them out of `candidates` too, and
`candidates` is what the schedule reads afterwards to work out what each slot
was chosen over. So the new slot named no alternative, offered no button, and
the only way back was to put every decision back.

Task 5.4.
"""
from datetime import datetime, timedelta

from app.scheduler import Candidate, build_day

DAY = datetime(2027, 4, 24, 10, 0)


def band(name, start_hour, minutes=60, score=0.5, pick=False):
    start = DAY.replace(hour=0, minute=0) + timedelta(hours=start_hour)
    return Candidate(performance_id=abs(hash((name, start_hour))) % 100000,
                     artist_id=abs(hash(name)) % 100000, artist=name,
                     stage='Main Stage', starts_at=start,
                     ends_at=start + timedelta(minutes=minutes),
                     score=score, is_pick=pick)


def slot_for(slots, artist):
    return next(s for s in slots if s.kind == 'SET' and s.artist == artist)


def sets_in(slots):
    return [s.artist for s in slots if s.kind == 'SET']


# Two acts at the same hour, and one the day can hold either way.
HEADLINER = band('Slipknot', 20, minutes=75, score=0.42)
RIVAL = band('Currents', 20, minutes=30, score=0.77)
EARLIER = band('Code Orange', 16, score=0.40)


def a_day():
    return [EARLIER, HEADLINER, RIVAL]


def test_without_a_pin_the_solver_takes_the_longer_set():
    """
    Slipknot wins on its own merits despite the lower percentage: seventy-five
    minutes at 42% is worth more than thirty at 77%, and the solver is scoring
    the day rather than ranking the artists. Worth stating, because the
    opposite was assumed while writing this file and the test said otherwise.
    """
    chosen = sets_in(build_day(a_day()))
    assert 'Slipknot' in chosen and 'Currents' not in chosen


def test_a_pin_is_honoured_over_the_solver_preference():
    chosen = sets_in(build_day(a_day(), pinned=[RIVAL.performance_id]))
    assert 'Currents' in chosen and 'Slipknot' not in chosen


def test_a_pinned_set_still_names_what_it_displaced():
    """The whole bug: without this the slot named nothing and had no way back."""
    slots = build_day(a_day(), pinned=[RIVAL.performance_id])
    slot = slot_for(slots, 'Currents')
    assert slot.alternative_id == HEADLINER.performance_id
    assert 'Slipknot' in slot.reason


def test_the_pin_says_who_asked_rather_than_claiming_it_chose():
    """
    "Chosen over" would be a lie on a pinned set: nothing chose it, the person
    did. The sentence has to say so, or the page takes credit for their edit.

    Nor "instead of", which claims the rival is what they gave up. All this
    function knows is that the two collide; what the day actually lost comes
    from re-solving without the pin, which happens elsewhere.
    """
    slots = build_day(a_day(), pinned=[RIVAL.performance_id])
    reason = slot_for(slots, 'Currents').reason
    assert 'you asked for this, which clashes with' in reason
    assert 'chosen over' not in reason
    assert 'instead of' not in reason


def test_the_swap_goes_back_the_way_it_came():
    """Pin either one and the other is offered: the door opens from both sides."""
    there = slot_for(build_day(a_day(), pinned=[RIVAL.performance_id]), 'Currents')
    back = slot_for(build_day(a_day(), pinned=[HEADLINER.performance_id]), 'Slipknot')
    assert there.alternative_id == HEADLINER.performance_id
    assert back.alternative_id == RIVAL.performance_id


def test_a_pin_does_not_blame_a_set_it_never_touched():
    """Code Orange plays at 16:00 and is in the schedule; it is not a casualty."""
    slots = build_day(a_day(), pinned=[RIVAL.performance_id])
    assert 'Code Orange' in sets_in(slots)
    assert 'Code Orange' not in slot_for(slots, 'Currents').reason


def test_two_pins_do_not_cancel_each_other():
    """
    Clashing pins are prevented in the web layer, which lifts the old pin
    before setting the new one. Should a pair reach the scheduler anyway, the
    second must not remove the first: honouring neither is the worst answer.
    """
    both = [HEADLINER.performance_id, RIVAL.performance_id]
    assert 'Slipknot' in sets_in(build_day(a_day(), pinned=both))


def test_a_pin_is_not_blamed_for_what_another_pin_also_removes():
    """
    Adding Jesus Piece (11:45-12:20) reported "instead of Zulu", a 28% match
    overlapping it by five minutes. Zulu was never in the day and could not
    have been: it also runs under Drain, which was pinned too. The set
    actually given up was Vended at 58%, elsewhere in the afternoon.

    Naming the wrong one is worse than naming none — it says you traded away
    something you never had, and says nothing about what you did lose.
    """
    from datetime import datetime, timedelta

    def at(hour, minute, mins, name, score):
        start = datetime(2027, 4, 24, hour, minute)
        return Candidate(performance_id=abs(hash(name)) % 100000,
                         artist_id=abs(hash(name)) % 100000, artist=name,
                         stage='Main Stage', starts_at=start,
                         ends_at=start + timedelta(minutes=mins),
                         score=score, is_pick=False)

    first = at(11, 45, 35, 'Jesus Piece', 0.43)
    second = at(12, 30, 40, 'Drain', 0.30)
    caught_between = at(12, 15, 35, 'Zulu', 0.28)      # clashes with both pins
    later = at(14, 30, 40, 'Dying Wish', 0.50)
    day = [first, second, caught_between, later]

    slots = build_day(day, pinned=[first.performance_id, second.performance_id])
    pinned_slot = slot_for(slots, 'Jesus Piece')
    assert 'Zulu' not in pinned_slot.reason
    assert pinned_slot.alternative_id is None


def test_a_meal_never_carves_out_a_set_the_person_asked_for():
    """
    Pinning Code Orange on the demo plan accepted the pin, rebuilt the day,
    and the set was gone: its 16:30-17:20 slot was the only room left for the
    45-minute meal, and the meal's last-resort rule kept only the strongest
    set and the last one.

    That relaxation exists because somebody whose whole day is artists they
    chose still has to eat — an argument about picks, which the scheduler
    inferred a day from. A pin is an instruction. Where honouring it leaves
    nowhere to eat, no meal is arranged.
    """
    from datetime import datetime, timedelta

    def at(hour, minute, mins, name, score, pick=False):
        start = datetime(2027, 4, 24, hour, minute)
        return Candidate(performance_id=abs(hash(name)) % 100000,
                         artist_id=abs(hash(name)) % 100000, artist=name,
                         stage='Main Stage', starts_at=start,
                         ends_at=start + timedelta(minutes=mins),
                         score=score, is_pick=pick)

    # Back to back all afternoon: no gap anywhere long enough to eat in.
    day = [at(12, 0, 60, 'Noon', 0.9, pick=True),
           at(13, 10, 60, 'One', 0.8, pick=True),
           at(14, 20, 50, 'Asked For This', 0.41),
           at(15, 20, 60, 'Three', 0.7, pick=True),
           at(16, 30, 60, 'Four', 0.6, pick=True)]
    asked_for = day[2]
    slots = build_day(day, pinned=[asked_for.performance_id])
    assert 'Asked For This' in [s.artist for s in slots if s.kind == 'SET']
    assert not any('Asked For This' in (s.reason or '')
                   for s in slots if s.kind == 'REST'), 'carved out for a break'
