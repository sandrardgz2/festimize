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
  * Rest. A long unbroken run on your feet is what ruins the last day of a
    festival, so the scheduler inserts a break once you pass the limit — and
    it will drop a set to make room. On a packed day every gap is fifteen
    minutes, so a break that only fits into existing gaps never happens,
    which makes the whole pacing idea decorative. Resting has to cost
    something or it is not a constraint.

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
              max_run_minutes: int = 210,
              rest_minutes: int = 40,
              changeover_minutes: int = 10,
              min_score_ratio: float = 0.25,
              min_score_floor: float = 0.02) -> List[Slot]:
    """
    Choose sets for one day and slot rest around them.

    discovery_quota is the share of chosen sets that must be artists the user
    did not name. max_run_minutes is how long they can be on their feet before
    a break is forced in — three and a half hours of standing, which is long
    enough to matter and short enough to be realistic.

    Weak recommendations are dropped, but the bar is relative: a quarter of the
    best score on the day, never below the floor. An absolute threshold does
    not survive contact with real data — when the strongest match on a lineup
    is 16%, a fixed 5% bar is meaningless, and on a lineup full of 80% matches
    it is far too generous.
    """
    if not candidates:
        return []
    best_score = max((c.score for c in candidates if not c.is_pick), default=0.0)
    bar = max(min_score_floor, best_score * min_score_ratio)
    candidates = [c for c in candidates if c.is_pick or c.score >= bar]
    if not candidates:
        return []

    # Your own picks first, then best match. Ties break earlier-first so the
    # day fills from the front rather than leaving awkward gaps.
    ranked = sorted(candidates, key=lambda c: (not c.is_pick, -c.score, c.starts_at))

    chosen: List[Candidate] = []
    for cand in ranked:
        if any(_overlaps(cand.starts_at, cand.ends_at,
                         c.starts_at - timedelta(minutes=changeover_minutes),
                         c.ends_at + timedelta(minutes=changeover_minutes)) for c in chosen):
            continue
        chosen.append(cand)

    # Enforce the discovery quota: if too few of the chosen sets are new
    # artists, swap the weakest picks out for the best discoveries that fit.
    def discoveries(sets): return sum(1 for c in sets if not c.is_pick)

    needed = int(len(chosen) * discovery_quota)
    if discoveries(chosen) < needed:
        pool = [c for c in ranked if c not in chosen and not c.is_pick]
        for new in pool:
            if discoveries(chosen) >= needed:
                break
            # Drop the lowest-value pick this discovery would collide with.
            clashing = [c for c in chosen
                        if _overlaps(new.starts_at, new.ends_at,
                                     c.starts_at - timedelta(minutes=changeover_minutes),
                                     c.ends_at + timedelta(minutes=changeover_minutes))]
            if len(clashing) == 1 and clashing[0].is_pick and clashing[0].score <= new.score + 0.15:
                chosen.remove(clashing[0])
                chosen.append(new)
            elif not clashing:
                chosen.append(new)

    chosen.sort(key=lambda c: c.starts_at)

    # Walk the day, forcing a break once the run gets too long. If no gap is
    # long enough, the next set is given up for the break: the weakest match
    # loses, and a pick is only sacrificed when there is nothing else to drop.
    slots: List[Slot] = []
    run_start: Optional[datetime] = None
    hours = timedelta(minutes=max_run_minutes)
    rest = timedelta(minutes=rest_minutes)

    queue = list(chosen)
    while queue:
        cand = queue.pop(0)
        if run_start is None:
            run_start = cand.starts_at
        elif slots and (cand.starts_at - slots[-1].ends_at) >= rest:
            # A long gap between sets is already a break. Show it as one: the
            # point of the schedule is to tell someone when they are off their
            # feet, and free time counts.
            slots.append(Slot("REST", slots[-1].ends_at, cand.starts_at,
                              reason="break in the lineup"))
            run_start = cand.starts_at
        elif (cand.ends_at - run_start) > hours:
            gap_start = slots[-1].ends_at
            if (cand.starts_at - gap_start) >= rest:
                slots.append(Slot("REST", gap_start, gap_start + rest,
                                  reason="%d hours on your feet" % (max_run_minutes // 60)))
                run_start = cand.starts_at
            elif cand.is_pick or cand.score >= 0.8 * best_score or not queue:
                # Never give up a set they asked for, the strongest match of the
                # day, or the last set of the day, just to rest. The break waits.
                pass
            else:
                # Sacrifice this set so the break can happen: the weakest thing
                # standing between them and a sit down.
                slots.append(Slot("REST", gap_start, max(gap_start + rest, cand.ends_at),
                                  reason="%d hours on your feet — %s dropped to rest"
                                         % (max_run_minutes // 60, cand.artist)))
                run_start = None
                continue
        slots.append(Slot("SET", cand.starts_at, cand.ends_at, cand.performance_id, cand.artist,
                          cand.stage,
                          "your pick" if cand.is_pick else "%d%% match" % round(cand.score * 100)))
    return slots
