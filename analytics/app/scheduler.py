"""
Building a day.

The day is filled first and breaks are carved out of it afterwards. Filling is
weighted interval scheduling: every set is worth its match score, and the day
is worth the sum of the sets in it, so the best day is the highest-scoring set
of performances that do not overlap. That is solved exactly by dynamic
programming — sets sorted by finishing time, each asking whether the day is
better with it or without it. An earlier version took the best remaining set
repeatedly and needed a repair pass to patch the holes that left; see
docs/evaluation/scheduler-comparison.md for the two measured against each
other.

Three things shape the result beyond raw taste score:

  * Your own picks outrank everything. You said you love them; a 0.9
    recommendation should not beat an artist you named yourself.
  * A discovery quota. Without it, someone who saves thirty artists gets a
    weekend of only those thirty and never hears anyone new — which is the
    whole point of the product. One set in three is reserved for artists the
    user did not name.
  * Rest, in realistic amounts. People come for a full day of music, so the
    day is filled first and breaks are then carved out of it: one meal break,
    and a breather only when the lineup does not already break the day up,
    never more than an hour of arranged break in a day. Earlier versions
    dropped weak matches and then labelled the resulting holes "rest", which
    produced three-set days with two-hour gaps — an empty schedule wearing a
    flattering name.

A set may also be joined late rather than skipped, when enough of it remains
to be worth walking in on: ten minutes missed beats an hour of nothing.

Targets Python 3.9 syntax.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence


@dataclass
class Candidate:
    performance_id: int
    artist_id: int
    artist: str
    stage: str
    starts_at: datetime
    ends_at: datetime
    score: float          # 0..1 taste match
    is_pick: bool         # the user named this artist themselves


@dataclass
class Slot:
    kind: str             # SET | REST
    starts_at: datetime
    ends_at: datetime
    performance_id: Optional[int] = None
    artist: Optional[str] = None
    stage: Optional[str] = None
    reason: str = ""
    # Which performance this set displaced, so the page can offer it as a
    # swap. The explanation sentence has the artist's name in it and nothing
    # a form could post back.
    alternative_id: Optional[int] = None


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


def choose_greedy(candidates: Sequence[Candidate],
                  discovery_quota: float = 1 / 3,
                  changeover_minutes: int = 10,
                  swap_tolerance: float = 0.10) -> List[Candidate]:
    """
    The original chooser, kept as a baseline to measure against.

    Takes the best-scoring set that still fits, repeatedly, then tries single
    swaps to patch the holes that approach leaves. Superseded by choose_best,
    which does not need patching because it does not make the mistake.
    """
    if not candidates:
        return []
    ranked = sorted(candidates, key=lambda c: (not c.is_pick, -c.score, c.starts_at))
    chosen: List[Candidate] = []
    for cand in ranked:
        if not any(_overlaps(cand.starts_at, cand.ends_at,
                             c.starts_at - timedelta(minutes=changeover_minutes),
                             c.ends_at + timedelta(minutes=changeover_minutes)) for c in chosen):
            chosen.append(cand)
    return sorted(chosen, key=lambda c: c.starts_at)


def choose_best(candidates: Sequence[Candidate],
                changeover_minutes: int = 10,
                pick_bonus: float = 10.0,
                minute_value: float = 0.0005,
                least_worth_catching: int = 25,
                least_fraction: float = 0.6) -> List[tuple]:
    """
    Choose the best possible set of performances, allowing late arrivals.

    This is weighted interval scheduling solved exactly. Sort every performance
    by when it ends, then work through them asking one question of each: is the
    day better with this set, or without it? "With it" means this set's value
    plus the best day that could have come before it, which is already known
    because the list is in end-time order.

    Two sets no longer have to be strictly sequential. If one ends as another
    starts, you can still walk over and catch most of the second — missing ten
    minutes of a band beats standing in a field for an hour. A set counts only
    if at least `least_worth_catching` minutes of it remain once you arrive,
    and it is valued by the part you would actually see.

    Returns (candidate, arrive_at) pairs, where arrive_at may be later than the
    set's advertised start.
    """
    if not candidates:
        return []

    sets = sorted(candidates, key=lambda c: c.ends_at)
    changeover = timedelta(minutes=changeover_minutes)
    least = timedelta(minutes=least_worth_catching)
    n = len(sets)

    def arrival(prev_index: int, i: int):
        """When they could get to set i, having come from set prev_index (-1 = start of day)."""
        earliest = sets[i].starts_at
        if prev_index >= 0:
            earliest = max(earliest, sets[prev_index].ends_at + changeover)
        full = sets[i].ends_at - sets[i].starts_at
        enough = max(least, full * least_fraction)
        return earliest if (sets[i].ends_at - earliest) >= enough else None

    def value(i: int, arrive) -> float:
        minutes = (sets[i].ends_at - arrive).total_seconds() / 60
        return (sets[i].score * (minutes / 60) + minute_value * minutes
                + (pick_bonus if sets[i].is_pick else 0.0))

    # best[i] = best achievable value considering the first i sets, and the
    # choice that produced it. O(n^2), which at festival size is nothing.
    best = [0.0] * (n + 1)
    took = [None] * (n + 1)
    for i in range(1, n + 1):
        best[i], took[i] = best[i - 1], None
        for j in range(i):                      # j = number of earlier sets used
            arrive = arrival(j - 1, i - 1)
            if arrive is None:
                continue
            if j > 0 and sets[j - 1].ends_at + changeover > sets[i - 1].ends_at:
                continue                        # cannot have finished the earlier one
            total = best[j] + value(i - 1, arrive)
            if total > best[i]:
                best[i], took[i] = total, (j, arrive)

    chosen = []
    i = n
    while i > 0:
        if took[i] is None:
            i -= 1
            continue
        j, arrive = took[i]
        chosen.append((sets[i - 1], arrive))
        i = j
    return sorted(chosen, key=lambda pair: pair[1])


def build_day(candidates: Sequence[Candidate],
              discovery_quota: float = 1 / 3,
              meal_minutes: int = 45,
              breather_minutes: int = 30,
              max_breathers: int = 2,
              max_run_minutes: int = 180,
              changeover_minutes: int = 10,
              swap_tolerance: float = 0.10,
              not_before: Optional[datetime] = None,
              music_cap_minutes: int = 450,
              meal_by: Optional[object] = None,
              pinned: Optional[Sequence[int]] = None) -> List[Slot]:
    """
    Fill a day with music, then carve breaks out of it.

    discovery_quota is the share of chosen sets that must be artists the user
    did not name. max_run_minutes is how long someone goes without a break
    before one is worth taking — three hours on site, which on an eleven-hour
    day means a meal break and two or three breathers.

    not_before is the earliest this day may start: the sleep floor, passed in
    by the caller, which knows when the previous day ended. music_cap_minutes
    is how much music one day may hold before the rest stops being a festival
    and starts being an endurance event — seven and a half hours, which on a
    nine-hour site day already means standing through five sixths of it.

    Neither rule fires on the demonstration festivals. They are programmed
    sanely: the days end at 20:15 and the next begins at 10:30, and no day
    offers more music than the cap allows. They exist because a real lineup
    does not promise that, and they are covered by tests rather than by the
    demo.

    swap_tolerance is how much match quality may be given up to remove dead
    time: a set scoring within ten points of the one it replaces may take its
    place when doing so buys back at least twenty minutes of standing around.

    Breaks are taken from existing gaps wherever possible. Where no gap is long
    enough, the weakest set in the window is given up, because a break that
    only happens when it is free is not a constraint. The user's own picks, the
    strongest match of the day and the final set are never given up.
    """
    if not candidates:
        return []

    # Sets the person asked for by name. Everything clashing with one is taken
    # off the table before the solver runs, so the pin is honoured rather than
    # competed with — otherwise the day it produces is the day it preferred,
    # which is the thing being overruled.
    if pinned:
        wanted = [c for c in candidates if c.performance_id in set(pinned)]
        for keep in wanted:
            candidates = [c for c in candidates
                          if c is keep
                          or not _overlaps(keep.starts_at, keep.ends_at,
                                           c.starts_at - timedelta(minutes=changeover_minutes),
                                           c.ends_at + timedelta(minutes=changeover_minutes))]

    # The sleep floor. Dropping the sets rather than warning about them is the
    # point: a schedule that lists a 09:00 set after a 02:00 finish is not
    # advice, it is a timetable with the hard part left to the reader.
    if not_before is not None:
        rested = [c for c in candidates if c.starts_at >= not_before]
        if rested:
            candidates = rested

    ranked = sorted(candidates, key=lambda c: (not c.is_pick, -c.score, c.starts_at))
    best_score = max((c.score for c in candidates if not c.is_pick), default=0.0)

    # Choose the best possible set of performances. See choose_best: greedy
    # used to do this and needed a repair pass to patch the holes it left.
    # The advertised times, kept before the late-arrival handling below rewrites
    # them. The counterfactual at the end of this function has to reason about
    # the day as published, not as walked.
    advertised = {id(c): (c.starts_at, c.ends_at) for c in candidates}

    picked = choose_best(candidates, changeover_minutes=changeover_minutes)

    # Some sets are joined late, having walked from somewhere else. Record how
    # much is missed, then treat the arrival as the start for everything that
    # follows — the gaps, the breaks and the timeline are all about where the
    # person actually is.
    missed = {}
    chosen = []
    for cand, arrive in picked:
        if arrive > cand.starts_at:
            missed[id(cand)] = int((arrive - cand.starts_at).total_seconds() // 60)
            cand.starts_at = arrive
        chosen.append(cand)

    # Discovery quota: swap the weakest picks out for the best new artists.
    def discoveries(sets): return sum(1 for c in sets if not c.is_pick)

    needed = int(len(chosen) * discovery_quota)
    if discoveries(chosen) < needed:
        for new in [c for c in ranked if c not in chosen and not c.is_pick]:
            if discoveries(chosen) >= needed:
                break
            clashing = [c for c in chosen
                        if _overlaps(new.starts_at, new.ends_at,
                                     c.starts_at - timedelta(minutes=changeover_minutes),
                                     c.ends_at + timedelta(minutes=changeover_minutes))]
            if not clashing:
                chosen.append(new)
            elif len(clashing) == 1 and not clashing[0].is_pick and clashing[0].score < new.score:
                # Only ever displace a weaker recommendation. An artist the user
                # named is never traded away to hit a discovery target — that is
                # the quota overruling the person it is supposed to serve.
                chosen.remove(clashing[0])
                chosen.append(new)

    chosen.sort(key=lambda c: c.starts_at)
    if not chosen:
        return []

    protected = {id(c) for c in chosen if c.is_pick or c.score >= 0.95 * best_score}
    protected.add(id(chosen[-1]))           # never trade the last set of the day for a break

    def _carve(sets: List[Candidate], after: datetime, minutes: int, label: str,
               taken: Optional[List[Slot]] = None, may_drop_a_pick: bool = False,
               shortest_acceptable: Optional[int] = None, may_drop: bool = True,
               prefer_latest_before: Optional[datetime] = None):
        """
        Place one break of `minutes` as soon as possible after `after`.

        Prefers an existing gap, and will take a shorter one rather than give up
        a set: eating in half an hour beats missing a band to eat in
        three-quarters of one. Only when nothing usable exists does a set go.

        may_drop_a_pick is for the meal break only. Someone whose whole day is
        artists they chose still has to eat, and protecting every pick means
        they would get no break at all. In that case the weakest pick goes —
        never the strongest set of the day, and never the last one.

        Returns (slot, dropped_candidate) or (None, None).
        """
        need = timedelta(minutes=minutes)
        taken = taken or []

        def free(start, end):
            return not any(_overlaps(start, end, r.starts_at, r.ends_at) for r in taken)

        for i in range(len(sets) - 1):
            if sets[i].ends_at < after:
                continue
            gap = sets[i + 1].starts_at - sets[i].ends_at
            if gap >= need and free(sets[i].ends_at, sets[i].ends_at + need):
                return Slot("REST", sets[i].ends_at, sets[i].ends_at + need, reason=label), None

        # Nothing long enough: take the longest gap that is still usable before
        # considering dropping a set for it.
        if shortest_acceptable is not None:
            usable = []
            for i in range(len(sets) - 1):
                if sets[i].ends_at < after:
                    continue
                gap = sets[i + 1].starts_at - sets[i].ends_at
                if gap >= timedelta(minutes=shortest_acceptable) and free(sets[i].ends_at, sets[i + 1].starts_at):
                    usable.append((gap, sets[i].ends_at, sets[i + 1].starts_at))
            if usable:
                # For a meal: the latest gap that still lands before evening.
                # Quarter to three is early to eat at a festival, and holding
                # out for the very last gap pushed dinner to quarter past six.
                in_window = [u for u in usable
                             if prefer_latest_before is None or u[1] <= prefer_latest_before]
                gap, start, end = (max(in_window, key=lambda u: u[1]) if in_window
                                   else min(usable, key=lambda u: u[1]))
                return Slot("REST", start, min(end, start + need), reason=label), None

        if not may_drop:
            return None, None

        droppable = [c for c in sets
                     if c.starts_at >= after and id(c) not in protected
                     and (c.ends_at - c.starts_at) >= need - timedelta(minutes=15)
                     and free(c.starts_at, c.starts_at + need)]
        if not droppable and may_drop_a_pick:
            keep = {id(max(sets, key=lambda c: c.score)), id(sets[-1])}
            droppable = [c for c in sets
                         if c.starts_at >= after and id(c) not in keep
                         and (c.ends_at - c.starts_at) >= need - timedelta(minutes=15)
                         and free(c.starts_at, c.starts_at + need)]
        if droppable:
            victim = min(droppable, key=lambda c: c.score)
            return (Slot("REST", victim.starts_at, victim.starts_at + need,
                         reason="%s — %s skipped" % (label, victim.artist)), victim)
        return None, None

    # The day's music cap. Cut from the weakest end, and never from the user's
    # own picks: someone who came for one band gets to stand through the day
    # for it, and being told they are tired by software is not help.
    total = sum((c.ends_at - c.starts_at).total_seconds() / 60 for c in chosen)
    capped: List[Candidate] = []
    if total > music_cap_minutes:
        for c in sorted(chosen, key=lambda c: (c.is_pick, c.score), reverse=True):
            minutes = (c.ends_at - c.starts_at).total_seconds() / 60
            if sum((x.ends_at - x.starts_at).total_seconds() / 60
                   for x in capped) + minutes <= music_cap_minutes or c.is_pick:
                capped.append(c)
        chosen = sorted(capped, key=lambda c: c.starts_at)

    rests: List[Slot] = []
    day_start = chosen[0].starts_at
    day_end = chosen[-1].ends_at

    # One meal break, somewhere in the middle of the day. Restricting it to the
    # second half meant ignoring a perfectly good gap at two in the afternoon
    # and then giving up a set at five to eat — the worst of both. Forty per
    # cent in is mid-afternoon on a festival day.
    meal_window = day_start + (day_end - day_start) * 0.4
    # Six in the evening unless this person said otherwise on their profile.
    dinner_by = day_start.replace(hour=18, minute=0, second=0, microsecond=0)
    if meal_by is not None:
        dinner_by = day_start.replace(hour=meal_by.hour, minute=meal_by.minute,
                                      second=0, microsecond=0)
    meal, dropped = _carve(chosen, meal_window, meal_minutes, "meal break", rests,
                           may_drop_a_pick=True, shortest_acceptable=30,
                           prefer_latest_before=dinner_by)
    if meal:
        rests.append(meal)
        if dropped:
            chosen.remove(dropped)

    # A breather is only worth adding when the day does not already provide
    # one. These lineups leave half an hour between sets; calling one of those
    # a "breather" tells the user nothing they cannot see. So: find the longest
    # stretch with no usable gap in it, and only then make room.
    RESTFUL = timedelta(minutes=20)       # a gap this long is already a sit down

    def longest_unbroken(sets: List[Candidate]) -> tuple:
        """Returns (start, end, minutes) of the longest stretch without a real gap."""
        if not sets:
            return None, None, 0
        worst = (sets[0].starts_at, sets[0].ends_at, 0)
        run_start = sets[0].starts_at
        for a, b in zip(sets, sets[1:]):
            breaks_here = (b.starts_at - a.ends_at) >= RESTFUL or any(
                r.starts_at >= a.ends_at and r.ends_at <= b.starts_at for r in rests)
            if breaks_here:
                length = int((a.ends_at - run_start).total_seconds() // 60)
                if length > worst[2]:
                    worst = (run_start, a.ends_at, length)
                run_start = b.starts_at
        length = int((sets[-1].ends_at - run_start).total_seconds() // 60)
        if length > worst[2]:
            worst = (run_start, sets[-1].ends_at, length)
        return worst

    for _ in range(max_breathers):
        run_start, run_end, length = longest_unbroken(chosen)
        if length <= max_run_minutes:
            break                          # the day already breaks itself up
        # Breathers only ever use time the lineup already leaves free. Giving
        # up a set to stand still is not pacing, and the user can always take
        # their own break — the schedule is advice, not a cage.
        breather, dropped = _carve(chosen, run_start, breather_minutes, "breather", rests,
                                   shortest_acceptable=20, may_drop=False)
        if not breather:
            break
        rests.append(breather)
        if dropped:
            chosen.remove(dropped)

    # What each choice cost. A schedule that simply appears is hard to trust;
    # one that says what it turned down can be argued with, which is better.
    def _clash_minutes(a: Candidate, b: Candidate) -> float:
        """Minutes two sets genuinely overlap, ignoring the walk between them."""
        start, end = max(a.starts_at, b.starts_at), min(a.ends_at, b.ends_at)
        return max(0.0, (end - start).total_seconds() / 60)

    # Each set that missed out belongs to one choice, not to every choice it
    # brushes against. Without this a single casualty is reported by several
    # slots at once, and the worst of those readings is actively false: a pick
    # that genuinely lost to another pick was also printed against an unrelated
    # set it merely finished five minutes before, which read as "this 84% match
    # beat an artist you chose". The schedule was right; the sentence was not.
    blamed: dict = {}
    for other in candidates:
        if other in chosen:
            continue
        conflicts = [c for c in chosen
                     if _overlaps(c.starts_at, c.ends_at,
                                  other.starts_at - timedelta(minutes=changeover_minutes),
                                  other.ends_at + timedelta(minutes=changeover_minutes))]
        if not conflicts:
            continue
        # The one that actually takes its place: the biggest true overlap, and
        # only failing that the neighbour whose changeover made it unreachable.
        against = max(conflicts, key=lambda c: (_clash_minutes(c, other), c.score))
        kept = blamed.get(id(against))
        if kept is None or other.score > kept.score:
            blamed[id(against)] = other

    def displaced(c: Candidate) -> Optional[Candidate]:
        return blamed.get(id(c))

    def instead(winner: Candidate, rival: Candidate) -> Optional[str]:
        """
        What the day costs if the rival is taken in the winner's place.

        Answered by solving the day again without the winner rather than by
        reasoning about the clash, because the scheduler never decides a clash
        on its own terms: it compares the best possible day containing each.
        Two of someone's own picks are worth the same, so the real answer to
        "why this one" is always something about the rest of the day.

        Usually the answer is smaller than it looks. The first version of this
        only reported whole sets lost and stayed silent otherwise, which hid
        the common case: you can join a set late, so the cost of the swap is
        often a few minutes of music rather than a band.
        """
        import dataclasses
        pristine = []
        for c in candidates:
            if c is winner:
                continue
            start, end = advertised[id(c)]
            pristine.append(dataclasses.replace(c, starts_at=start, ends_at=end))
        other = {c.artist: arrive for c, arrive
                 in choose_best(pristine, changeover_minutes=changeover_minutes)}
        if rival.artist not in other:
            return None                    # the rival still does not get in
        lost = [c.artist for c in chosen if c is not winner and c.artist not in other]
        if lost:
            return "taking %s instead would cost you %s" % (
                rival.artist,
                lost[0] if len(lost) == 1 else ", ".join(lost[:-1]) + " and " + lost[-1])
        advertised_start = advertised[id(rival)][0]
        late = int((other[rival.artist] - advertised_start).total_seconds() // 60)
        if late > 0:
            return ("%s would fit just as well, but you would join it %d minutes late"
                    % (rival.artist, late))
        return None                        # genuinely interchangeable; say nothing

    def describe(c: Candidate) -> str:
        if c.is_pick:
            return "your pick"
        pct = round(c.score * 100)
        # Below 5% there is no meaningful tag overlap. Saying "2% match" implies a
        # precision the number does not have; it is filling the slot, and should say so.
        return "%d%% match" % pct if pct >= 5 else "no close match — fills the slot"

    slots = []
    for c in chosen:
        reason = describe(c)
        rival = displaced(c)
        if rival is not None and (rival.score > 0.05 or rival.is_pick):
            minutes = int((rival.ends_at - rival.starts_at).total_seconds() // 60)
            mine = int((c.ends_at - c.starts_at).total_seconds() // 60)
            # No percentage on a pick. Every saved artist is now one of the
            # profiles taste is scored against, so it matches itself perfectly
            # and reads "100%" — a tautology dressed as a measurement. That it
            # was chosen is the entire reason it was in contention.
            rival_label = ("also your pick" if rival.is_pick
                           else "%d%%" % round(rival.score * 100))
            reason += " · chosen over %s (%s, %d min against %d)" % (
                rival.artist, rival_label, minutes, mine)
            # Between two of their own picks the numbers are identical, so the
            # only honest reason is what else the day can then hold.
            if rival.is_pick and c.is_pick:
                why = instead(c, rival)
                if why:
                    reason += " — " + why
        if id(c) in missed:
            reason += " · joined %d min late, walking from the last set" % missed[id(c)]
        slots.append(Slot("SET", c.starts_at, c.ends_at, c.performance_id, c.artist, c.stage,
                          reason, rival.performance_id if rival is not None else None))
    slots += rests

    # Account for every minute. A gap left blank on a timeline looks like a
    # mistake, so short ones are shown as what they are — changeover time —
    # while the breaks the scheduler chose stay visually distinct.
    chosen_sorted = sorted(chosen, key=lambda c: c.starts_at)
    for earlier, later in zip(chosen_sorted, chosen_sorted[1:]):
        # Subtract any breaks already placed, and show whatever is left over.
        free = [(earlier.ends_at, later.starts_at)]
        for r in sorted(rests, key=lambda r: r.starts_at):
            carved = []
            for f_start, f_end in free:
                if r.ends_at <= f_start or r.starts_at >= f_end:
                    carved.append((f_start, f_end))
                    continue
                if r.starts_at > f_start:
                    carved.append((f_start, r.starts_at))
                if r.ends_at < f_end:
                    carved.append((r.ends_at, f_end))
            free = carved
        for f_start, f_end in free:
            minutes = int((f_end - f_start).total_seconds() // 60)
            if minutes < 15:
                continue
            reason = "gap — %d minutes between sets" % minutes
            # Say what is on during a long gap. Standing around for an hour is
            # one thing; standing around while an artist you might like plays
            # is another, and the user should be the one deciding.
            if minutes >= 40:
                playing = [o for o in candidates
                           if o not in chosen and o.score > 0.05
                           and _overlaps(f_start, f_end, o.starts_at, o.ends_at)]
                if playing:
                    best_other = max(playing, key=lambda o: o.score)
                    reason += " · %s plays %s–%s (%d%%) if you would rather" % (
                        best_other.artist,
                        best_other.starts_at.strftime("%H:%M"),
                        best_other.ends_at.strftime("%H:%M"),
                        round(best_other.score * 100))
            slots.append(Slot("REST", f_start, f_end, reason=reason))

    slots.sort(key=lambda s: s.starts_at)
    return slots
