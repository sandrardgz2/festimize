"""
Fetch what each artist sounds like, from MusicBrainz.

    analytics/.venv/bin/python corpus/tags.py
    analytics/.venv/bin/python corpus/tags.py --limit 200    # a sample first

Taste matching runs on tags, and after the corpus load the database held
15,799 artists of which 139 had any — the 139 entered by hand for the demo. So
the recommender could not score a single artist the corpus brought in, and a
historical lineup showed no match percentages at all. The dataset was sitting
beside the product rather than feeding it.

MusicBrainz rather than Last.fm on purpose. Last.fm's tags are richer and its
API is licensed for non-commercial use only; MusicBrainz core data is CC0, so
these rows can be used commercially and the corpus keeps that option open.
Last.fm can be layered on top later for the artists MusicBrainz is thin about,
tagged as its own source so a commercial build can drop it in one query.

One request a second, cached per artist, so this can be stopped and restarted.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'corpus')
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
AGENT = 'Festimize/1.0 (IST 440W capstone; neku113@gmail.com)'
PAUSE = 1.1
OUT = os.path.join(DATA, 'artist-tags.jsonl')

# A tag has to be about the music. MusicBrainz lets anyone write anything, so
# the lists carry nationalities, moods and opinions alongside genres, and a
# taste profile built on "french" or "heavy" matches on the wrong thing.
NOT_A_GENRE = {
    'seen live', 'favourites', 'favorites', 'awesome', 'good', 'bad', 'heavy',
    'groovy', 'catchy', 'cool', 'love', 'male vocalists', 'female vocalists',
    'female vocalist', 'male vocalist', 'band', 'artist', 'composer', 'duo',
    'trio', 'quartet', 'solo', 'live', 'radio', 'spotify', 'youtube', 'seen',
    # "modern" is on 33 of the 139 hand-seeded artists and separates none of
    # them from each other. Moods that do separate taste — aggressive, melodic,
    # atmospheric — are deliberately kept: a beatdown fan and a melodic
    # metalcore fan differ on exactly those.
    'modern', 'contemporary', 'new',
}
PLACES = {
    'american', 'british', 'english', 'french', 'german', 'swedish', 'finnish',
    'norwegian', 'danish', 'dutch', 'belgian', 'canadian', 'australian',
    'japanese', 'brazilian', 'spanish', 'italian', 'polish', 'russian', 'irish',
    'scottish', 'welsh', 'usa', 'uk', 'us', 'europe', 'european',
}


def wanted(tag):
    """Whether a tag says something about the music rather than the artist."""
    tag = tag.strip().lower()
    if len(tag) < 3 or len(tag) > 40:
        return False
    return tag not in NOT_A_GENRE and tag not in PLACES


def fetch(mbid):
    """The tags and genres MusicBrainz holds for one artist, cached on disk."""
    path = os.path.join(CACHE, 'mb-tags-%s.json' % mbid)
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding='utf-8'))
        except ValueError:
            pass
    url = ('https://musicbrainz.org/ws/2/artist/%s?' % mbid
           + urllib.parse.urlencode({'inc': 'tags+genres', 'fmt': 'json'}))
    last = None
    for attempt in range(5):
        try:
            time.sleep(PAUSE)
            request = urllib.request.Request(url, headers={
                'User-Agent': AGENT, 'Accept': 'application/json'})
            with urllib.request.urlopen(request, timeout=45) as response:
                held = json.load(response)
            break
        except urllib.error.HTTPError as error:
            last = error
            if error.code == 404:
                held = {}
                break
            # 503 is MusicBrainz asking for patience, not a failure.
            time.sleep((8.0 if error.code in (429, 503) else 2.0) * (attempt + 1))
        except Exception as error:                              # noqa: BLE001
            last = error
            time.sleep(2.0 * (attempt + 1))
    else:
        print('  could not read %s: %s' % (mbid, last))
        return None

    found = {}
    # A genre is a curated tag, so it is trusted over a free one of the same
    # name; the vote count becomes the weight, which is what makes a tag
    # eight people agreed on count for more than one somebody typed once.
    for group in ('tags', 'genres'):
        for tag in (held.get(group) or []):
            name = (tag.get('name') or '').strip().lower()
            if wanted(name):
                found[name] = max(found.get(name, 0), int(tag.get('count') or 1))
    os.makedirs(CACHE, exist_ok=True)
    json.dump(found, open(path + '.partial', 'w', encoding='utf-8'), ensure_ascii=False)
    os.replace(path + '.partial', path)
    return found


def main():
    limit = None
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])

    artists = [json.loads(line) for line in
               open(os.path.join(DATA, 'artists.jsonl'), encoding='utf-8') if line.strip()]
    # Busiest first, so an interrupted run has still covered the artists most
    # likely to be on a lineup somebody is looking at.
    artists = [a for a in artists if a.get('mbid')]
    artists.sort(key=lambda a: -a['appearances'])
    if limit:
        artists = artists[:limit]
    print('%d artists with a MusicBrainz id to tag' % len(artists))

    written = tagged = empty = 0
    partial = OUT + '.partial'
    with open(partial, 'w', encoding='utf-8') as handle:
        for artist in artists:
            found = fetch(artist['mbid'])
            if found is None:
                continue
            if found:
                tagged += 1
            else:
                empty += 1
            handle.write(json.dumps({
                'mbid': artist['mbid'],
                'name': artist['name'],
                'appearances': artist['appearances'],
                'tags': sorted(found.items(), key=lambda kv: -kv[1]),
                'source': 'musicbrainz',
                'commercial_use': True,
                'attribution': 'MusicBrainz, CC0',
            }, ensure_ascii=False) + '\n')
            written += 1
            if written % 250 == 0:
                print('  %5d/%d artists (%d with tags)' % (written, len(artists), tagged))
    os.replace(partial, OUT)
    print()
    print('%d artists written, %d carry tags, %d have none in MusicBrainz'
          % (written, tagged, empty))
    print('written to %s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
