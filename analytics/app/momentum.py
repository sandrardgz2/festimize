"""
The rising-artist measure.

An artist is rising when they are taking up more of the festival circuit each
year than they used to, and are not at the top of it yet. Both halves matter:
without the second, the measure flags the acts everyone has already heard of,
and a badge that says "Metallica is rising" tells a user nothing they can use.

What the measure is, and why it is this and not something else, was decided by
holding back the last three years of the corpus and testing five candidates
against what actually happened — see docs/evaluation/momentum-backtest.md. The
findings that shaped this code:

  * **Counts are unusable; shares are not.** The corpus does not hold the same
    festivals every year. An artist who played Bonnaroo every year appears to
    have stopped in 2019, which is when Wikipedia's per-year articles stop. So
    every year is measured as a share of itself.
  * **Thin years have to go.** 2020 holds two festivals and 2021 holds
    fourteen, against a median of thirty. An artist's share of those years is
    noise, and treating it as data turns a pandemic into a career.
  * **Past bookings predict future ones worse than chance** for established
    artists: -0.03 rank correlation, 0.6x lift. Fame is not momentum, which is
    the clearest justification this measure has for existing.
  * **A trajectory needs three years, and most artists do not have them.** For
    an artist with one or two, eight different signals were tested — breadth,
    the calibre of the bills they were on, whether they were asked back, the
    stage they played, the direction of the careers beside them — and none beat
    simply knowing how much of last year they held. So no prediction is made
    for them at all. They are marked `new` and the page shows the fact instead.

Targets Python 3.9 syntax.
"""
import collections
import statistics
from typing import Dict, List, Sequence, Tuple

# A year holding less than seven tenths of the usual festivals is too thin to
# compare. Half was the first threshold and it was a knife edge: 2021 holds 15
# festivals against a median of 30, so it scraped in at exactly the cut and
# every pandemic booking counted double. Seven tenths puts it clearly out and
# keeps every ordinary year, which hold 28 or more.
THIN = 0.7
ENOUGH = 3             # years of presence a trajectory needs
ARRIVED = 0.1          # the top tenth of the circuit is not rising, it is there
RISING = 0.75          # a badge goes on the strongest quarter of the trajectories
# A badge also needs breadth. Nina Black and Luna & Lenthe both score in the
# top ten without it, on Tomorrowland and Rock Werchter every year since 2023 —
# two Belgian festivals, which is a local residency rather than an ascent.
SPREAD = 3
# And an artist who has been going for decades is not rising when they turn up
# again, they are returning. Hoobastank scores top of the list on six festivals
# in four years, and formed in 1994. Scored the same way, named differently.
VETERAN = 15
# A gradient fitted across the whole window is positive for an artist who
# started mid-window and has since stopped: 070 Shake's shares run
# 0,0,0,0,5.5,2.3,12.1,2.5,0 — a peak in 2023 and nothing in 2025 — and the
# early zeros tilt the line upwards. Rising has to mean still here, so a badge
# requires a booking in the most recent year the corpus covers properly.


def usable_years(rows: Sequence[Tuple[int, str, str]]) -> List[int]:
    """
    The years the corpus covers well enough to compare with each other.

    `rows` is (year, festival, artist). A year with a third of the usual
    festivals in it cannot be compared with a full one, whatever happened in
    music that year, and the most recent year is left out because its lineups
    are still being announced — a festival that has not published yet would
    otherwise look like a festival nobody was booked at.
    """
    festivals: Dict[int, set] = collections.defaultdict(set)
    for year, festival, _ in rows:
        festivals[year].add(festival)
    if not festivals:
        return []
    typical = statistics.median(len(f) for f in festivals.values())
    newest = max(festivals)
    return sorted(year for year, found in festivals.items()
                  if len(found) >= typical * THIN and year != newest)


def shares(rows: Sequence[Tuple[int, str, str]],
           years: Sequence[int]) -> Dict[int, Dict[str, float]]:
    """
    share[year][artist] — the fraction of that year's bookings they held.

    A booking is one artist at one festival in one year, counted once however
    many stages they appeared on. Two sets at the same festival is a detail of
    that festival's programme; it is not twice as much of the circuit, and
    counting rows instead of bookings would say it was.
    """
    booked: Dict[int, set] = collections.defaultdict(set)
    for year, festival, artist in rows:
        if year in years:
            booked[year].add((festival, artist))
    counts = {year: collections.Counter(artist for _, artist in found)
              for year, found in booked.items()}
    return {year: {artist: n / float(len(booked[year]))
                   for artist, n in found.items()}
            for year, found in counts.items()}


def slope(line: Sequence[float]) -> float:
    """
    Least-squares gradient of a share across the years, absence counted as zero.

    Counting an absent year as zero is deliberate: not being booked is a fact
    about a career, not a missing measurement. The years themselves have
    already been filtered to ones the corpus covers, which is what stops this
    from reading our own gaps as somebody's decline.
    """
    middle = (len(line) - 1) / 2.0
    spread = sum((i - middle) ** 2 for i in range(len(line))) or 1.0
    return sum((i - middle) * value for i, value in enumerate(line)) / spread


def score(rows: Sequence[Tuple[int, str, str]],
          formed: Dict[str, int] = None) -> Dict[str, dict]:
    """
    {artist: {score, basis, appearances, festivals, first_year, last_year}}.

    The score is a percentile within the artists who have a trajectory at all,
    so it reads as "stronger than this fraction of rising artists" and can be
    thresholded without knowing anything about the distribution of gradients.
    An artist with no trajectory keeps a score of zero and says why in `basis`:
    `new` for too little history, `arrived` for already being at the top. An
    artist with a trajectory who has been going for decades is `returning`
    rather than `trajectory`, which needs `formed` — {artist: year} from
    MusicBrainz — and falls back to `trajectory` where that is unknown.
    """
    formed = formed or {}
    years = usable_years(rows)
    held = shares(rows, years)

    seen: Dict[str, set] = collections.defaultdict(set)
    counted: collections.Counter = collections.Counter()
    festivals: Dict[str, set] = collections.defaultdict(set)
    span: Dict[str, List[int]] = {}
    for year, festival, artist in rows:
        counted[artist] += 1
        festivals[artist].add(festival)
        if year in held and held[year].get(artist):
            seen[artist].add(year)
        low, high = span.get(artist, (9999, 0))
        span[artist] = (min(low, year), max(high, year))

    everyone = {artist for year in held for artist in held[year]}
    size = {artist: statistics.mean(held[year].get(artist, 0.0) for year in years)
            for artist in everyone}
    ceiling = (sorted(size.values(), reverse=True)[max(1, int(len(size) * ARRIVED)) - 1]
               if size else 0.0)

    gradients = {}
    for artist in everyone:
        if len(seen[artist]) < ENOUGH or size[artist] >= ceiling:
            continue
        gradients[artist] = slope([held[year].get(artist, 0.0) for year in years])

    ordered = sorted(gradients, key=gradients.get)
    place = {artist: (rank + 1) / float(len(ordered))
             for rank, artist in enumerate(ordered)} if ordered else {}

    out = {}
    newest = max(years) if years else 0
    for artist in counted:
        first, last = span[artist]
        if artist in place:
            began = formed.get(artist)
            basis = ('returning' if began and newest - began > VETERAN
                     else 'trajectory')
            value = place[artist]
        elif artist in size and size[artist] >= ceiling:
            basis, value = 'arrived', 0.0
        else:
            basis, value = 'new', 0.0
        still_here = bool(held.get(newest, {}).get(artist))
        out[artist] = {
            'score': round(value, 4),
            'basis': basis,
            'rising': (basis == 'trajectory' and value >= RISING
                       and len(festivals[artist]) >= SPREAD and still_here),
            'appearances': counted[artist],
            'festivals': len(festivals[artist]),
            'first_year': first,
            'last_year': last,
        }
    return out
