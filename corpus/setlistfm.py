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
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

BASE = 'https://api.setlist.fm/rest/1.0/'
AGENT = 'Festimize/0.1 (IST 440W student project; github.com/sandrardgz2/festimize)'
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
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
            time.sleep(5.0 * (attempt + 1) if error.code == 429 else 2.0 * (attempt + 1))
        except Exception as error:
            last = error
            time.sleep(2.0 * (attempt + 1))
    raise last


def _pages(city: str, first: int, last: int) -> List[dict]:
    """Every setlist recorded in this city, cached so a re-run costs nothing."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, 'setlistfm-%s-%d-%d.json' % (city.lower().replace(' ', '-'), first, last))
    if os.path.exists(path):
        return json.load(open(path, encoding='utf-8'))
    found, page = [], 1
    while True:
        result = _api('search/setlists', cityName=city, p=page)
        batch = result.get('setlist') or []
        found.extend(batch)
        total = result.get('total', 0)
        if not batch or len(found) >= total or page >= 250:
            break
        page += 1
    json.dump(found, open(path, 'w', encoding='utf-8'))
    return found


def collect(city: str, first: int, last: int, least_per_day: int = 5) -> List[dict]:
    """
    One row per artist per festival year, from the setlists logged in this city.

    A date is treated as a festival day only when several different artists
    played it, which is what separates a festival from a Tuesday night gig in
    the same town.
    """
    setlists = _pages(city, first, last)
    by_date: Dict[str, List[dict]] = collections.defaultdict(list)
    for entry in setlists:
        by_date[entry.get('eventDate', '')].append(entry)

    rows, seen = [], set()
    for date, entries in by_date.items():
        try:                                   # setlist.fm writes dates dd-mm-yyyy
            day, month, year = (int(part) for part in date.split('-'))
        except ValueError:
            continue
        if not first <= year <= last:
            continue
        artists = {e['artist']['name'] for e in entries if e.get('artist')}
        if len(artists) < least_per_day:
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
                'page': 'setlist.fm/%s' % city,
            })
    return rows
