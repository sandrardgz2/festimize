"""
Fetching what an artist sounds like, on demand.

The corpus holds 15,799 artists and 139 of them carry tags, because tagging
the whole history was work nobody needed: every artist on a schedulable
festival already had them. That was the right call and it left one gap — a
search box over the other 15,660 would let someone pick an artist the
recommender then cannot score, which is worse than not offering them.

So the tags are fetched when somebody actually picks the artist. One request,
about a second, and only for artists that reach a taste profile.

MusicBrainz rather than Last.fm: core data is CC0, so these rows stay usable
commercially, and Last.fm's API is licensed for non-commercial use only.

The vocabulary below is the single definition — corpus/tags.py imports it from
here rather than keeping its own copy.

Targets Python 3.9 syntax.
"""
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List

log = logging.getLogger(__name__)

AGENT = 'Festimize/1.0 (IST 440W capstone; neku113@gmail.com)'
ENDPOINT = 'https://musicbrainz.org/ws/2/artist/'

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


def wanted(tag: str) -> bool:
    """Whether a tag says something about the music rather than the artist."""
    tag = tag.strip().lower()
    if len(tag) < 3 or len(tag) > 40:
        return False
    return tag not in NOT_A_GENRE and tag not in PLACES


def fetch(mbid: str, timeout: float = 8.0) -> Dict[str, int]:
    """
    {tag: weight} for one artist, or {} if MusicBrainz has nothing or is down.
    
    Deliberately forgiving. This runs while somebody waits for a page, and an
    artist saved without tags is a recoverable state — they simply score
    nothing until the tags arrive — whereas a failed save is not.
    """
    url = ENDPOINT + mbid + '?' + urllib.parse.urlencode({'inc': 'tags+genres',
                                                          'fmt': 'json'})
    try:
        request = urllib.request.Request(url, headers={
            'User-Agent': AGENT, 'Accept': 'application/json'})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            held = json.load(response)
    except Exception as error:                                  # noqa: BLE001
        log.warning('could not read tags for %s: %s', mbid, error)
        return {}

    found: Dict[str, int] = {}
    # A genre is a curated tag, so it wins over a free one of the same name;
    # the vote count becomes the weight, which is what makes a tag eight people
    # agreed on count for more than one somebody typed once.
    for group in ('tags', 'genres'):
        for tag in (held.get(group) or []):
            name = (tag.get('name') or '').strip().lower()
            if wanted(name):
                found[name] = max(found.get(name, 0), int(tag.get('count') or 1))
    return found


def as_rows(artist_id: int, tags: Dict[str, int]) -> List[dict]:
    """Tag rows ready for artist_tag, weighted and attributed."""
    return [{'artist_id': artist_id, 'tag': tag, 'weight': float(max(1, weight)),
             'source': 'musicbrainz'}
            for tag, weight in tags.items()]
