"""
Give every name in the corpus a MusicBrainz identity.

    python3 corpus/resolve.py                 # resolve, then enrich from MusicBrainz
    python3 corpus/resolve.py --no-search      # skip the slow per-name search
    python3 corpus/resolve.py --report         # read what is cached, fetch nothing

A name is not an identity. "Bring Me the Horizon" and "Bring Me The Horizon"
are one band written twice; "Clutch" is two different bands. Counting how often
an artist appears — which is the whole point of the rising-artist measure — is
wrong in both directions until the names are resolved to something stable, and
MusicBrainz ids are the stable thing the database is already keyed on.

Three routes, in order of how much they can be trusted:

  1. setlist.fm hands back an id with every setlist, logged by the person who
     was there and corrected by the site's editors. 80% of rows arrive resolved.
  2. A Wikipedia link resolves through Wikidata: the article is the sitelink,
     and the artist's MusicBrainz id is property P434 on the item. Fifty titles
     per request, so the whole corpus costs a few dozen calls.
  3. A bare name has to be searched for, one call a second, and is accepted
     only when MusicBrainz returns a name that matches exactly once the
     punctuation and accents are stripped. Anything less is left unresolved,
     because a wrong id is worse than no id: it merges two artists silently.

Nothing is guessed. A name that none of the three routes settles keeps its own
identity, flagged so the loader can see it is a name and not an artist.
"""
import collections
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'corpus')
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
ROWS = os.path.join(DATA, 'appearances.jsonl')

AGENT = 'Festimize/1.0 (IST 440W capstone; neku113@gmail.com)'
WIKIDATA = 'https://www.wikidata.org/w/api.php'
MUSICBRAINZ = 'https://musicbrainz.org/ws/2/artist'
MB_PAUSE = 1.1          # MusicBrainz asks for one request a second, at most
TITLES_PER_CALL = 50    # the Wikidata API's limit for anonymous callers
ARIDS_PER_CALL = 40     # keeps the Lucene query inside a sane URL length


def _digest(parts):
    """A short stable name for a batch, so a cached answer is never the wrong one."""
    return hashlib.sha1('|'.join(parts).encode('utf-8')).hexdigest()[:16]


def flatten(name):
    """A name with accents, case and punctuation removed, for comparison only."""
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    return re.sub(r'[^0-9a-z]+', '', name.lower())


def _get(url, headers=None):
    """One GET, retried twice, returning parsed JSON."""
    last = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=dict(
                {'User-Agent': AGENT, 'Accept': 'application/json'}, **(headers or {})))
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            last = error
            if error.code == 404:
                return {}
            time.sleep(2.0 * (attempt + 1))
        except Exception as error:                              # noqa: BLE001
            last = error
            time.sleep(2.0 * (attempt + 1))
    raise last


def _cached(name, build):
    """Whatever `build()` returns, kept on disk so a re-run costs nothing."""
    path = os.path.join(CACHE, name)
    if os.path.exists(path):
        return json.load(open(path, encoding='utf-8'))
    os.makedirs(CACHE, exist_ok=True)
    made = build()
    partial = path + '.partial'
    json.dump(made, open(partial, 'w', encoding='utf-8'), ensure_ascii=False)
    os.replace(partial, path)
    return made


# ------------------------------------------------------------------ the rows
def names_in_corpus():
    """
    Every distinct name, with what the corpus already knows about it.

    `mbids` is a count rather than a single id on purpose: when setlist.fm
    has logged one name against two ids, that is either two artists sharing a
    name or an editing mistake, and the difference matters.
    """
    found = {}
    for line in open(ROWS, encoding='utf-8'):
        if not line.strip():
            continue
        row = json.loads(line)
        about = found.setdefault(row['artist'], {
            'name': row['artist'], 'appearances': 0,
            'mbids': collections.Counter(), 'titles': collections.Counter(),
            'festivals': set()})
        about['appearances'] += 1
        about['festivals'].add(row['festival'])
        if row.get('musicbrainz_id'):
            about['mbids'][row['musicbrainz_id']] += 1
        if row.get('wikipedia_title'):
            about['titles'][row['wikipedia_title']] += 1
    return found


# -------------------------------------------------------------- the routes
def from_wikidata(titles):
    """
    {Wikipedia title: MusicBrainz id} for the titles that carry one.

    Wikidata holds the mapping as property P434 on the item the article is
    the English sitelink of, which makes this a bulk lookup rather than one
    call per artist.
    """
    out = {}
    titles = sorted(set(titles))
    for start in range(0, len(titles), TITLES_PER_CALL):
        batch = titles[start:start + TITLES_PER_CALL]
        tag = 'wikidata-mbid-%s.json' % _digest(batch)

        def fetch(batch=batch):
            url = WIKIDATA + '?' + urllib.parse.urlencode({
                'action': 'wbgetentities', 'sites': 'enwiki',
                'titles': '|'.join(batch), 'props': 'claims',
                'format': 'json', 'formatversion': '2'})
            answer = _get(url)
            held = {}
            for item in (answer.get('entities') or {}).values():
                if not isinstance(item, dict):
                    continue
                claim = (item.get('claims') or {}).get('P434') or []
                ids = [c['mainsnak']['datavalue']['value'] for c in claim
                       if c.get('mainsnak', {}).get('datavalue')]
                # The title asked for is not echoed back per entity, so the
                # item's own id is the key and the titles are matched after.
                held[item.get('id')] = ids[0] if ids else None
            return {'ids': held, 'asked': batch}

        answer = _cached(tag, fetch)
        # One more call, cached with the same batch, to map titles to items.
        def sitelinks(batch=batch):
            url = WIKIDATA + '?' + urllib.parse.urlencode({
                'action': 'wbgetentities', 'sites': 'enwiki',
                'titles': '|'.join(batch), 'props': 'sitelinks',
                'sitefilter': 'enwiki', 'format': 'json', 'formatversion': '2'})
            got = _get(url)
            pairs = {}
            for item in (got.get('entities') or {}).values():
                if not isinstance(item, dict):
                    continue
                link = ((item.get('sitelinks') or {}).get('enwiki') or {}).get('title')
                if link:
                    pairs[link] = item.get('id')
            return pairs

        where = _cached('wikidata-titles-%s.json' % _digest(batch), sitelinks)
        for title, item in where.items():
            mbid = answer['ids'].get(item)
            if mbid:
                out[title] = mbid
        print('  wikidata %5d/%d titles' % (min(start + TITLES_PER_CALL, len(titles)),
                                            len(titles)))
    return out


def search_musicbrainz(name):
    """
    The MusicBrainz id for a bare name, or None when nothing matches exactly.

    An exact match on the flattened name is the whole test. MusicBrainz scores
    its results, but a high score on a near-miss ("Alleycvtt" for "ALLEYCVT")
    is exactly the mistake that would merge two artists, so the score is only
    used to order the candidates.
    """
    tag = 'mb-search-%s.json' % (flatten(name)[:50] or 'blank')

    def fetch():
        url = MUSICBRAINZ + '?' + urllib.parse.urlencode({
            'query': 'artist:"%s"' % name.replace('"', ''), 'fmt': 'json', 'limit': 5})
        time.sleep(MB_PAUSE)
        return _get(url)

    answer = _cached(tag, fetch)
    wanted = flatten(name)
    for found in answer.get('artists') or []:
        if flatten(found.get('name') or '') == wanted:
            return found.get('id')
        for alias in found.get('aliases') or []:
            if flatten(alias.get('name') or '') == wanted:
                return found.get('id')
    return None


def describe(mbids):
    """
    {id: {name, disambiguation, country, began}} straight from MusicBrainz.

    Asked in batches through the search index, which accepts `arid:` — the
    read endpoint takes one id at a time and this corpus has twelve thousand.
    """
    out = {}
    mbids = sorted(set(m for m in mbids if m))
    for start in range(0, len(mbids), ARIDS_PER_CALL):
        batch = mbids[start:start + ARIDS_PER_CALL]
        tag = 'mb-artists-%s.json' % _digest(batch)

        def fetch(batch=batch):
            query = ' OR '.join('arid:%s' % m for m in batch)
            url = MUSICBRAINZ + '?' + urllib.parse.urlencode({
                'query': query, 'fmt': 'json', 'limit': len(batch)})
            time.sleep(MB_PAUSE)
            return _get(url)

        for found in (_cached(tag, fetch).get('artists') or []):
            out[found['id']] = {
                'name': found.get('name'),
                'disambiguation': found.get('disambiguation') or None,
                'country': found.get('country'),
                'began': (found.get('life-span') or {}).get('begin'),
                'type': found.get('type'),
            }
        print('  musicbrainz %5d/%d ids' % (min(start + ARIDS_PER_CALL, len(mbids)),
                                            len(mbids)))
    return out


# ------------------------------------------------------------------ the merge
def resolve(found, search=True):
    """
    An id for each name, and how it was arrived at.

    Route order is trust order. A name already carrying an id keeps it even
    when Wikidata disagrees, because setlist.fm's id came from the show and
    Wikidata's from an article that may be about a different act of the name.
    """
    settled = {}
    for name, about in found.items():
        if about['mbids']:
            best, count = about['mbids'].most_common(1)[0]
            rival = sum(about['mbids'].values()) - count
            settled[name] = (best, 'setlistfm', rival)

    titles = {title for name, about in found.items()
              if name not in settled for title in about['titles']}
    print('%d names carry a Wikipedia title' % len(titles))
    by_title = from_wikidata(titles) if titles else {}
    for name, about in found.items():
        if name in settled:
            continue
        for title, _ in about['titles'].most_common():
            if title in by_title:
                settled[name] = (by_title[title], 'wikidata', 0)
                break

    bare = [name for name in found if name not in settled]
    print('%d names need a name search' % len(bare))
    if search:
        bare.sort(key=lambda n: -found[n]['appearances'])
        for done, name in enumerate(bare, 1):
            mbid = search_musicbrainz(name)
            if mbid:
                settled[name] = (mbid, 'musicbrainz-search', 0)
            if done % 200 == 0:
                print('  searched %5d/%d names' % (done, len(bare)))
    return settled


def artists(found, settled, detail):
    """
    One record per artist, with every name the corpus called them.

    Two names collapse into one artist when they resolve to the same id. Names
    that resolve to nothing are kept as artists in their own right, keyed on
    the flattened name so that at least the spelling variants of an unresolved
    name count as one thing.
    """
    by_key = {}
    for name, about in sorted(found.items()):
        mbid = settled.get(name, (None,))[0]
        key = mbid or 'name:' + flatten(name)
        record = by_key.setdefault(key, {
            'artist_key': key, 'mbid': mbid, 'name': None,
            'name_normalized': flatten(name), 'disambiguation': None,
            'country': None, 'formed_year': None, 'aliases': [],
            'appearances': 0, 'festivals': 0, 'resolved_by': None})
        known = detail.get(mbid or '', {})
        record['name'] = known.get('name') or record['name'] or name
        record['name_normalized'] = flatten(record['name'])
        record['disambiguation'] = known.get('disambiguation')
        record['country'] = known.get('country')
        began = known.get('began') or ''
        record['formed_year'] = int(began[:4]) if began[:4].isdigit() else None
        record['appearances'] += about['appearances']
        record['resolved_by'] = settled.get(name, (None, 'unresolved'))[1]
        if name not in record['aliases']:
            record['aliases'].append(name)
    for record in by_key.values():
        record['aliases'].sort()
    return by_key


def main():
    search = '--no-search' not in sys.argv
    report_only = '--report' in sys.argv
    found = names_in_corpus()
    rows = sum(a['appearances'] for a in found.values())
    print('%d distinct names over %d appearance rows' % (len(found), rows))

    settled = resolve(found, search=search and not report_only)
    detail = describe({mbid for mbid, _, _ in settled.values()}) if not report_only else {}
    records = artists(found, settled, detail)

    path = os.path.join(DATA, 'artists.jsonl')
    partial = path + '.partial'
    with open(partial, 'w', encoding='utf-8') as out:
        for record in sorted(records.values(), key=lambda r: -r['appearances']):
            out.write(json.dumps(record, ensure_ascii=False) + '\n')
    os.replace(partial, path)

    keys = {name: settled.get(name, (None,))[0] or 'name:' + flatten(name) for name in found}
    key_path = os.path.join(DATA, 'artist-keys.json')
    json.dump(keys, open(key_path + '.partial', 'w', encoding='utf-8'),
              ensure_ascii=False, sort_keys=True)
    os.replace(key_path + '.partial', key_path)

    by_route = collections.Counter(r['resolved_by'] for r in records.values())
    resolved_rows = sum(a['appearances'] for n, a in found.items() if n in settled)
    print()
    print('%d artists after merging names' % len(records))
    print('%d of %d names resolved (%.1f%%); %d of %d rows (%.1f%%)' % (
        len(settled), len(found), 100.0 * len(settled) / len(found),
        resolved_rows, rows, 100.0 * resolved_rows / rows))
    for route, count in by_route.most_common():
        print('  %-20s %d artists' % (route, count))
    print('%d names were merged into an artist of another name' % (len(found) - len(records)))
    print()
    print('written to %s' % path)
    print('written to %s' % key_path)


if __name__ == '__main__':
    main()
