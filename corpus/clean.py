"""
One definition of what counts as an artist name.

Rows reach the dataset from four readers — year sections, per-year articles,
matrix tables and setlist.fm — plus a carry-over path that reuses what an
earlier run found when a source is unavailable. Each of those used to decide
for itself what a name was, which is how "000" survived: it was filtered out
of one reader and let back in by another.

So every row passes through here on its way to the file, no matter where it
came from. The rules are deliberately conservative about unlinked names and
permissive about linked ones, because a wiki link or a MusicBrainz id is
evidence that a human decided this was an artist.
"""
import re

MONTHS = (r'january|february|march|april|may|june|july|august|september|october|'
          r'november|december')
DATE_START = re.compile(r'^(?:%s)\s*\d' % MONTHS, re.I)      # "April 10 & 17"
DIGIT_RUN = re.compile(r'\d{3}')                              # "000", "000 to 75"
PROSE = re.compile(r'\b(over|next|about|approximately|between|around|during|after|'
                   r'before|including|featuring|were|was|are|has|had|would|will|'
                   r'their|which|who|when|while|because|however|also|than|from)\b')


# Venues that appear in the tour-date tables of travelling festivals, read as
# acts because they sit in the same column shape as a lineup. Curated by hand
# rather than matched by a pattern: "Flux Pavilion", "Magnolia Park", "Theme
# Park", "Kyle Hall" and "Orchard Lounge" are real artists, and no rule
# separates them from "Molson Park" and "Tinley Park" without losing one side.
VENUES = {
    'bicentennial park', 'blockbuster desert sky pavilion', 'blockbuster pavilion',
    'capital theatre', 'desert sky pavilion', 'houston raceway park',
    'los angeles state historic park', 'meadows music theater', 'molson park',
    'new world music theatre', 'pine knob music theatre', 'raceway park',
    'ray street park', 'south park meadows', 'tinley park', 'world music theater',
    'world music theatre', "world's first cinema", 'world’s first cinema',
    'places to park',
}


def looks_like_artist(name, identified=False):
    """
    Is this a plausible artist name?

    `identified` means the row carries a wiki link or a MusicBrainz id, which
    earns it the benefit of the doubt: "Fever 333" and "311" are real bands and
    would fail the digit rule otherwise.
    """
    name = (name or '').strip()
    if not name or len(name) > 50:
        return False
    if name.lower() in VENUES:
        return False
    if DATE_START.match(name):
        return False
    if identified:
        return True
    if name.replace(' ', '').isdigit():          # "000", "311" when nothing vouches for it
        return False
    if DIGIT_RUN.search(name):                   # "000 to 75", "12 000 people"
        return False
    if PROSE.search(name):                       # a fragment of a sentence
        return False
    if len(name.split()) > 6:
        return False
    return True


# Several festivals run a comedy or spoken-word tent and list it with the music
# stages, so the reader picks it up as a bill: Rock on the Range's lineup names
# Andrew Dice Clay, Jay Mohr and Brian Posehn on the Rolling Rock Comedy Tent.
# They are performers and the article is right about them; they are not musical
# appearances, and a recommender built on tags would have nothing to say about
# them. The stage is what gives them away, and it is already recorded per row.
NON_MUSIC_STAGE = re.compile(
    r'\b(comedy|comedian|spoken word|poetry|cinema|film|literature|wrestl|'
    r'circus|kids|workshop|q\s*&\s*a|signing)\b', re.I)


def is_music(row) -> bool:
    """Whether a row is a musical performance rather than something else billed."""
    return not NON_MUSIC_STAGE.search(row.get('stage') or '')
