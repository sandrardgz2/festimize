"""
Building a day.

Greedy, by design: take the best remaining set that still fits, repeat. A
constraint solver would find a better optimum, but greedy is explainable —
when someone asks why an artist was left out, the answer is always "something
better overlapped it" or "a rule blocked it".

Three things shape the result beyond raw taste score:

  * Your own picks outrank everything. You said you love them; a 0.9
    recommendation should not beat an artist you named yourself.
  * A discovery quota. Without it, someone who saves thirty artists gets a
    weekend of only those thirty and never hears anyone new — which is the
    whole point of the product. One set in three is reserved for artists the
    user did not name.
  * Rest, in realistic amounts. People come for a full day of music, so the
    day is filled first and breaks are then carved out of it: one 45-minute
    meal break and at most two 30-minute breathers, each placed where it costs
    the least. Earlier versions dropped weak matches and then labelled the
    resulting holes "rest", which produced three-set days with two-hour gaps —
    an empty schedule wearing a flattering name.

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
                minute_value: float = 0.004) -> List[Candidate]:
    """
    Choose the best possible set of non-overlapping performances.

    This is weighted interval scheduling, solved exactly rather than greedily.
    Sort every performance by when it ends. Work through them in that order and
    ask one question of each: is the day better with this set, or without it?

      * without it — the best day already worked out from everything that
        finished earlier
      * with it — this set's value, plus the best day that finished before this
        set starts, which is already known because the list is sorted by end time

    Keep whichever is larger and move on. The final entry is the best day
    available, and walking the choices backwards recovers which sets it used.

    Greedy cannot find this. Taking a 41% set at 19:30 locks out a 37% set at
    20:00 that would have led to a better evening, and greedy never reconsiders.

    Value of a set = match score x hours, plus minute_value per minute so a full
    day beats an empty one, plus pick_bonus for an artist the user chose, which
    is large enough that picks are never traded for recommendations.
    """
    if not candidates:
        return []

    sets = sorted(candidates, key=lambda c: c.ends_at)
    changeover = timedelta(minutes=changeover_minutes)

    def value(c: Candidate) -> float:
        minutes = (c.ends_at - c.starts_at).total_seconds() / 60
        return c.score * (minutes / 60) + minute_value * minutes + (pick_bonus if c.is_pick else 0.0)

    # last_compatible[i] = index of the latest set that finishes early enough
    # to still get to set i, or -1 if there is none.
    last_compatible = []
    for i, c in enumerate(sets):
        j = i - 1
        while j >= 0 and sets[j].ends_at + changeover > c.starts_at:
            j -= 1
        last_compatible.append(j)

    best = [0.0] * (len(sets) + 1)      # best[i] = best value using the first i sets
    for i, c in enumerate(sets, start=1):
        take = value(c) + best[last_compatible[i - 1] + 1]
        best[i] = max(best[i - 1], take)

    chosen: List[Candidate] = []
    i = len(sets)
    while i > 0:
        c = sets[i - 1]
        if best[i] != best[i - 1]:      # this set is in the best schedule
            chosen.append(c)
            i = last_compatible[i - 1] + 1
        else:
            i -= 1
    return sorted(chosen, key=lambda c: c.starts_at)


def build_day(candidates: Sequence[Candidate],
              discovery_quota: float = 1 / 3,
              meal_minutes: int = 45,
              breather_minutes: int = 30,
              max_breathers: int = 2,
              max_run_minutes: int = 180,
              changeover_minutes: int = 10,
              swap_tolerance: float = 0.10) -> List[Slot]:
    """
    Fill a day with music, then carve breaks out of it.

    discovery_quota is the share of chosen sets that must be artists the user
    did not name. max_run_minutes is how long someone goes without a break
    before one is worth taking — three hours on site, which on an eleven-hour
    day means a meal break and two or three breathers.

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

    ranked = sorted(candidates, key=lambda c: (not c.is_pick, -c.score, c.starts_at))
    best_score = max((c.score for c in candidates if not c.is_pick), default=0.0)

    # Choose the best possible non-overlapping set of performances. See
    # choose_best: greedy used to do this and needed a repair pass afterwards
    # to patch the holes it left; this does not.
    chosen = list(choose_best(candidates, changeover_minutes=changeover_minutes))

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
               taken: Optional[List[Slot]] = None, may_drop_a_pick: bool = False):
        """
        Place one break of `minutes` as soon as possible after `after`.

        Prefers an existing gap. Failing that, drops the weakest unprotected set
        and rests instead.

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

    rests: List[Slot] = []
    day_start = chosen[0].starts_at
    day_end = chosen[-1].ends_at

    # One meal break in the second half of the day, where meals happen. This is
    # the only break allowed to cost a set: everyone has to eat, and on a packed
    # bill there is no free 45 minutes to eat in.
    midpoint = day_start + (day_end - day_start) / 2
    meal, dropped = _carve(chosen, midpoint, meal_minutes, "meal break", rests, may_drop_a_pick=True)
    if meal:
        rests.append(meal)
        if dropped:
            chosen.remove(dropped)

    # Breathers come out of gaps that already exist. Giving up a set you would
    # have enjoyed, to stand somewhere else doing nothing, is not pacing.
    def gaps(sets: List[Candidate]):
        for a, b in zip(sets, sets[1:]):
            if b.starts_at - a.ends_at >= timedelta(minutes=breather_minutes):
                yield a.ends_at, b.starts_at

    for gap_start, gap_end in gaps(chosen):
        if len([r for r in rests if r.reason.startswith("breather")]) >= max_breathers:
            break
        if any(_overlaps(gap_start, gap_end, r.starts_at, r.ends_at) for r in rests):
            continue
        covered = [r for r in rests if r.ends_at <= gap_start]
        since = max([r.ends_at for r in covered], default=day_start)
        if (gap_start - since) >= timedelta(minutes=max_run_minutes) or not covered:
            length = min(gap_end - gap_start, timedelta(minutes=breather_minutes))
            rests.append(Slot("REST", gap_start, gap_start + length, reason="breather"))

    # A long day with no gaps still needs more than lunch. If the lineup leaves
    # no room, take it from the weakest set — the alternative is ten hours on
    # your feet with one sit-down, which is the thing this product exists to stop.
    long_day = (day_end - day_start) >= timedelta(hours=8)
    if long_day and len(rests) < 2:
        gap_starts = [r.ends_at for r in rests] or [day_start]
        after = max(gap_starts)
        breather, dropped = _carve(chosen, after, breather_minutes, "breather", rests,
                                   may_drop_a_pick=True)
        if not breather:
            breather, dropped = _carve(chosen, day_start, breather_minutes, "breather", rests,
                                       may_drop_a_pick=True)
        if breather:
            rests.append(breather)
            if dropped:
                chosen.remove(dropped)

    # What each choice cost. A schedule that simply appears is hard to trust;
    # one that says what it turned down can be argued with, which is better.
    def displaced(c: Candidate) -> Optional[Candidate]:
        rivals = [o for o in candidates
                  if o not in chosen
                  and _overlaps(c.starts_at, c.ends_at,
                                o.starts_at - timedelta(minutes=changeover_minutes),
                                o.ends_at + timedelta(minutes=changeover_minutes))]
        return max(rivals, key=lambda o: o.score) if rivals else None

    def describe(c: Candidate) -> str:
        if c.is_pick:
            return "your pick"
        pct = round(c.score * 100)
        # Below 5% there is no meaningful tag overlap. Saying "2% match" implies a
        # precision the number does not have; it is filling the slot, and should say so.
        base = "%d%% match" % pct if pct >= 5 else "no close match — fills the slot"
        return base

    slots = []
    for c in chosen:
        reason = describe(c)
        rival = displaced(c)
        if rival is not None and (rival.score > 0.05 or rival.is_pick):
            minutes = int((rival.ends_at - rival.starts_at).total_seconds() // 60)
            mine = int((c.ends_at - c.starts_at).total_seconds() // 60)
            rival_label = "also your pick" if rival.is_pick else "%d%%" % round(rival.score * 100)
            reason += " · chosen over %s (%s, %d min against %d)" % (
                rival.artist, rival_label, minutes, mine)
        slots.append(Slot("SET", c.starts_at, c.ends_at, c.performance_id, c.artist, c.stage, reason))
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
            if minutes >= 15:
                slots.append(Slot("REST", f_start, f_end,
                                  reason="gap — %d minutes between sets" % minutes))

    slots.sort(key=lambda s: s.starts_at)
    return slots
