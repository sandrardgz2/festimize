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


def build_day(candidates: Sequence[Candidate],
              discovery_quota: float = 1 / 3,
              meal_minutes: int = 45,
              breather_minutes: int = 30,
              max_breathers: int = 2,
              max_run_minutes: int = 150,
              changeover_minutes: int = 10) -> List[Slot]:
    """
    Fill a day with music, then carve breaks out of it.

    discovery_quota is the share of chosen sets that must be artists the user
    did not name. max_run_minutes is how long someone stays on their feet
    before a breather is worth taking — two and a half hours of standing.

    Breaks are taken from existing gaps wherever possible. Where no gap is long
    enough, the weakest set in the window is given up, because a break that
    only happens when it is free is not a constraint. The user's own picks, the
    strongest match of the day and the final set are never given up.
    """
    if not candidates:
        return []

    # Pick order: your own artists first, then best match, earliest as a tiebreak.
    ranked = sorted(candidates, key=lambda c: (not c.is_pick, -c.score, c.starts_at))
    best_score = max((c.score for c in candidates if not c.is_pick), default=0.0)

    chosen: List[Candidate] = []
    for cand in ranked:
        if any(_overlaps(cand.starts_at, cand.ends_at,
                         c.starts_at - timedelta(minutes=changeover_minutes),
                         c.ends_at + timedelta(minutes=changeover_minutes)) for c in chosen):
            continue
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
            elif len(clashing) == 1 and clashing[0].is_pick and clashing[0].score <= new.score + 0.15:
                chosen.remove(clashing[0])
                chosen.append(new)

    chosen.sort(key=lambda c: c.starts_at)
    if not chosen:
        return []

    protected = {id(c) for c in chosen if c.is_pick or c.score >= 0.95 * best_score}
    protected.add(id(chosen[-1]))           # never trade the last set of the day for a break

    def _carve(sets: List[Candidate], after: datetime, minutes: int, label: str):
        """
        Place one break of `minutes` as soon as possible after `after`.

        Prefers an existing gap. Failing that, drops the weakest unprotected set
        and rests instead. Returns (slot, dropped_candidate) or (None, None).
        """
        need = timedelta(minutes=minutes)
        for i in range(len(sets) - 1):
            if sets[i].ends_at < after:
                continue
            gap = sets[i + 1].starts_at - sets[i].ends_at
            if gap >= need:
                return Slot("REST", sets[i].ends_at, sets[i].ends_at + need, reason=label), None
        droppable = [c for c in sets
                     if c.starts_at >= after and id(c) not in protected
                     and (c.ends_at - c.starts_at) >= need - timedelta(minutes=15)]
        if droppable:
            victim = min(droppable, key=lambda c: c.score)
            return (Slot("REST", victim.starts_at, victim.starts_at + need,
                         reason="%s — %s skipped" % (label, victim.artist)), victim)
        return None, None

    rests: List[Slot] = []
    day_start = chosen[0].starts_at

    # One meal break, in the second half of the day where meals actually happen.
    midpoint = day_start + (chosen[-1].ends_at - day_start) / 2
    meal, dropped = _carve(chosen, midpoint, meal_minutes, "meal break")
    if meal:
        rests.append(meal)
        if dropped:
            chosen.remove(dropped)

    # Breathers once standing time runs long, up to the cap.
    for _ in range(max_breathers):
        run_start = day_start
        trigger = None
        for i, c in enumerate(chosen):
            resting = [r for r in rests if r.starts_at >= run_start and r.ends_at <= c.starts_at]
            gap_before = (c.starts_at - chosen[i - 1].ends_at) if i else timedelta(0)
            if resting or gap_before >= timedelta(minutes=breather_minutes):
                run_start = c.starts_at
                continue
            if (c.ends_at - run_start) > timedelta(minutes=max_run_minutes):
                trigger = c.starts_at
                break
        if trigger is None:
            break
        breather, dropped = _carve(chosen, trigger - timedelta(minutes=90), breather_minutes, "breather")
        if not breather:
            break
        rests.append(breather)
        if dropped:
            chosen.remove(dropped)

    def describe(c: Candidate) -> str:
        if c.is_pick:
            return "your pick"
        pct = round(c.score * 100)
        # Below 5% there is no meaningful tag overlap. Saying "2% match" implies a
        # precision the number does not have; it is filling the slot, and should say so.
        return "%d%% match" % pct if pct >= 5 else "no close match — fills the slot"

    slots = [Slot("SET", c.starts_at, c.ends_at, c.performance_id, c.artist, c.stage, describe(c))
             for c in chosen] + rests

    # Show the real gaps, but only ones worth sitting down for. Marking every
    # fifteen-minute changeover as a break turns the page into a list of waiting.
    # Anything longer than an hour and a half is a hole in the lineup, not a break.
    chosen_sorted = sorted(chosen, key=lambda c: c.starts_at)
    for earlier, later in zip(chosen_sorted, chosen_sorted[1:]):
        gap = later.starts_at - earlier.ends_at
        if timedelta(minutes=45) <= gap <= timedelta(minutes=90):
            if not any(_overlaps(r.starts_at, r.ends_at, earlier.ends_at, later.starts_at) for r in rests):
                slots.append(Slot("REST", earlier.ends_at, later.starts_at, reason="break between sets"))

    slots.sort(key=lambda s: s.starts_at)
    return slots
