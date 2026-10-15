"""
Lineups for the festivals Wikipedia will not give us.

Wacken's article names five bands for a year it says had two hundred, and
Hellfest's names none. setlist.fm has the opposite problem and the opposite
strength: no editorial lineup at all, but a setlist for every performance
somebody in the crowd bothered to write down, each already carrying the
artist's MusicBrainz id. For a festival that is a lineup, arrived at from the
other direction.

Searching by city rather than by venue: festivals rename their stages and
their venue records, and these festivals happen in villages — everything
playing in Wacken in August is Wacken. Where that is not safe, a day with only
a handful of acts is dropped, because a real festival day has dozens and a
pub gig has one.

What this gives up: setlist.fm only knows about performances somebody logged,
so coverage thins with age and with how small the stage was. Rows are marked
with lower confidence than Wikipedia's editorial lineups for that reason.
"""
import collections
import datetime
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

BASE = 'https://api.setlist.fm/rest/1.0/'


class QuotaExhausted(RuntimeError):
    """The daily request allowance is gone; nothing more will work until it resets."""
AGENT = 'Festimize/0.1 (IST 440W student project; github.com/sandrardgz2/festimize)'
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
CAP = 250 * 20                     # the API pages no further than this
MIN_GAP = 0.6                      # their limit is about two a second; stay under it
_last_call = [0.0]


def _key() -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    for line in open(path):
        name, _, value = line.strip().partition('=')
        if name == 'SETLISTFM_API_KEY':
            return value
    raise RuntimeError('SETLISTFM_API_KEY missing from corpus/.env')


def _api(path: str, **params) -> dict:
    url = BASE + path + '?' + urllib.parse.urlencode(params)
    last = None
    for attempt in range(5):
        wait = MIN_GAP - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()
        try:
            request = urllib.request.Request(url, headers={
                'x-api-key': _key(), 'Accept': 'application/json', 'User-Agent': AGENT})
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return {'setlist': [], 'total': 0}
            last = error
            if error.code == 429:
                # A free key allows about 1,440 requests a day. Past that, every
                # call fails until it resets, so retrying wastes a minute each
                # time and tells us nothing we do not already know.
                if attempt >= 1:
                    raise QuotaExhausted(
                        'setlist.fm daily quota is exhausted; this festival needs a later run')
                time.sleep(5.0)
            else:
                time.sleep(2.0 * (attempt + 1))
        except Exception as error:
            last = error
            time.sleep(2.0 * (attempt + 1))
    raise last


def _terms(where: str) -> Dict[str, str]:
    """
    "city=Wacken", "venue=Douglass Park", or the two joined with & as the API
    wants them.

    Pairing a city with a venue is what a generic venue name needs. setlist.fm
    matches a venue name loosely, so "Waterfront Park" on its own also returns
    the Waterfront Parks in Louisville, Portland and Burlington — and parks
    that merely share a word, like St. Petersburg's Vinoy Park — along with
    whatever festival each of them holds.
    """
    found = {}
    for pair in where.split('&'):
        key, _, value = pair.partition('=')
        found['cityName' if key.strip() == 'city' else 'venueName'] = value.strip()
    return found


def _in_city(entry: dict, city: str) -> bool:
    """Whether a setlist was logged in this city, which a loose match needs asked."""
    where = ((entry.get('venue') or {}).get('city') or {}).get('name') or ''
    return where.strip().lower() == city.strip().lower()


def _pages(where: Dict[str, str], first: int, last: int) -> List[dict]:
    """
    Every setlist matching this search, cached so a re-run costs nothing.

    The cache is keyed on the search alone and not on the years asked for,
    because the request does not carry the years — narrowing a festival from
    1999-2026 to 2015-2026 is a filter applied here, and it must not throw away
    a crawl that already cost a day's allowance to fetch.
    """
    os.makedirs(CACHE, exist_ok=True)
    tag = '-'.join('%s=%s' % kv for kv in sorted(where.items())).lower().replace(' ', '-')
    path = os.path.join(CACHE, 'setlistfm-%s.json' % tag)
    sliced = os.path.join(CACHE, 'setlistfm-%s-by-year.json' % tag)
    if os.path.exists(sliced):
        held = json.load(open(sliced, encoding='utf-8'))
        if held['from'] <= first and held['to'] >= last:
            return held['setlists']
        first, last = min(first, held['from']), max(last, held['to'])
    elif os.path.exists(path):
        held = json.load(open(path, encoding='utf-8'))
        if len(held) < CAP:
            return held
    else:
        found = _search(where)
        if len(found) < CAP:
            json.dump(found, open(path, 'w', encoding='utf-8'))
            return found
    # The API stops paging at 250 pages of 20. A search that reaches the cap has
    # been silently truncated to whatever sorts first, which for a large city is
    # the last two years: Budapest came back with 5,000 setlists and not one
    # from before 2024. Asking year by year keeps each search small enough to
    # come back whole, and the answer is stored with the span it covers so a
    # later, narrower run reuses it instead of paying for it again.
    whole, seen = [], set()
    for year in range(first, last + 1):
        for entry in _search(dict(where, year=year)):
            key = entry.get('id') or json.dumps(entry, sort_keys=True)
            if key not in seen:
                seen.add(key)
                whole.append(entry)
    json.dump({'from': first, 'to': last, 'setlists': whole},
              open(sliced, 'w', encoding='utf-8'))
    return whole


def _search(where: Dict[str, object]) -> List[dict]:
    """One paged search, however many pages it runs to."""
    found, page = [], 1
    while True:
        result = _api('search/setlists', p=page, **where)
        batch = result.get('setlist') or []
        found.extend(batch)
        total = result.get('total', 0)
        if not batch or len(found) >= total or page >= 250:
            break
        page += 1
    return found


def _run_length(day, days) -> int:
    """How many consecutive days the run containing this day is."""
    length, step = 1, datetime.timedelta(days=1)
    back = day - step
    while back in days:
        length += 1
        back -= step
    forward = day + step
    while forward in days:
        length += 1
        forward += step
    return length


def collect(where, first: int, last: int, least_per_day: int = 5,
            months: Optional[List[int]] = None, least_days: int = 1) -> List[dict]:
    """
    One row per artist per festival year, from the setlists logged at a place.

    `where` is "city=Wacken" or "venue=Douglass Park" — a village name is
    enough for a festival that is the only thing happening there, and a big
    city needs the venue or it picks up every club gig in town. A common venue
    name needs both, joined with &, or it also finds the parks of that name in
    other cities.

    A date counts as a festival day only when several different artists played
    it, which is what separates a festival from a Tuesday night in the same
    place. In a city that is never quiet that test is not enough on its own:
    `months` narrows the search to the weeks the festival actually occupies,
    which is the one thing about a festival that does not change year to year.
    Riot Fest and Summer Smash share a park and are told apart only this way.

    `least_days` is how many days in a row the festival runs. Werchter also
    hosts TW Classic and Werchter Boutique, one-day shows on the same field in
    the same weeks, and a four-day festival is told from a one-day show by the
    length of the run — not by anything either of them is called.
    """
    if isinstance(where, str):
        # Several searches may be joined with +. A venue search matches on a
        # prefix, which only works in one direction: Riot Fest's park gained an
        # s in 2020, so "Douglas Park" finds the editions up to 2019 and
        # "Douglass Park" finds the ones after, and the festival needs both.
        where = [_terms(part) for part in where.split('+')]
    elif isinstance(where, dict):
        where = [where]
    setlists, where_tags = [], []
    for search in where:
        found = _pages(search, first, last)
        # A search that names both is asking for one park in one city, so the
        # loose venue match is held to it; a city or a venue on its own is
        # trusted as given, because a festival site can straddle a boundary
        # (Primavera's Parc del Forum is half in Sant Adria de Besos).
        if 'cityName' in search and 'venueName' in search:
            found = [entry for entry in found if _in_city(entry, search['cityName'])]
        setlists.extend(found)
        where_tags.extend(search.values())
    by_date: Dict[str, List[dict]] = collections.defaultdict(list)
    for entry in setlists:
        by_date[entry.get('eventDate', '')].append(entry)

    # Which dates are festival days, decided before any row is written: a day
    # with several different artists on it, inside the months the festival runs,
    # and part of a long enough run of consecutive days.
    days = set()
    for date, entries in by_date.items():
        try:
            day, month, year = (int(part) for part in date.split('-'))
        except ValueError:
            continue
        if not first <= year <= last or (months and month not in months):
            continue
        if len({e['artist']['name'] for e in entries if e.get('artist')}) >= least_per_day:
            days.add(datetime.date(year, month, day))
    if least_days > 1:
        days = {day for day in days if _run_length(day, days) >= least_days}

    rows, seen = [], set()
    for date, entries in by_date.items():
        try:                                   # setlist.fm writes dates dd-mm-yyyy
            day, month, year = (int(part) for part in date.split('-'))
        except ValueError:
            continue
        if not first <= year <= last:
            continue
        if datetime.date(year, month, day) not in days:
            continue
        for entry in entries:
            artist = entry.get('artist') or {}
            name = (artist.get('name') or '').strip()
            if not name or (year, name.lower()) in seen:
                continue
            seen.add((year, name.lower()))
            rows.append({
                'artist': name,
                'musicbrainz_id': artist.get('mbid'),
                'year': year,
                'date': '%04d-%02d-%02d' % (year, month, day),
                'stage': (entry.get('venue') or {}).get('name'),
                'headliner': False,
                'linked': bool(artist.get('mbid')),
                'page': 'setlist.fm/' + '/'.join(where_tags),
            })
    return rows
