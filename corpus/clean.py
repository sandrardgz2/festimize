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


# A heading above a block of names is usually a stage, and sometimes it is a
# day, a region, the festival's own name, or a row of table markup that the
# stripper left behind. The stage is not decoration: dim_stage.size_rank is
# what tells a main-stage booking from a tent at noon, which is the difference
# the rising-artist measure is looking for. So a stage name is either cleaned
# into something a person would recognise, or dropped — never kept as it fell
# out of the markup.
TABLE_ATTRS = re.compile(
    r'^[^|]*?\b(?:colspan|rowspan|style|align|scope|class|width|bgcolor)\s*=\s*'
    r'"[^"]*"[^|]*\|', re.I)
STAGE_LIST = re.compile(r'^([^:]{2,40}?(?:stage|tent|arena))\s*:\s*\S', re.I)
DAY_OR_PART = re.compile(
    r'^(?:mon|tues?|wednes|thurs?|fri|satur|sun)day$|^day \d+$|^weekend \d+$|'
    r'^(?:early|late) \w+$', re.I)
NOT_A_STAGE = re.compile(
    r'^(?:line-?up|line-?up by stage|headliners?|artists?|acts?|performers?|'
    r'bands?|additional artists?\b.*|artists? appearing\b.*|also appearing\b.*|'
    r'other artists?\b.*|more\b.*|tbа|tba|various)$', re.I)
# A stage is named after a place you can stand in. Requiring one of these words
# is what tells a stage from a region or an edition: Knotfest files its bills
# under "California" and "Knotfest Roadshow USA & Canada", which are neither.
# The non-music words are in the list so that a comedy tent survives cleaning
# and is still caught by is_music below — dropping its name would let the
# comedians back in.
VENUE_WORD = re.compile(
    r'\b(stage|tent|arena|theatre|theater|amphitheat\w*|bandshell|pavilion|'
    r'ballroom|warehouse|canopy|grid|gallery|terrace|shed|pond|pit|lock ?up|'
    r'holts|field|dome|hall|club|room|tower|barn|bowl|garden|bar|forest|'
    r'comedy|comedian|spoken word|poetry|cinema|film|literature|wrestl\w*|'
    r'circus|kids|workshop|signing)\b', re.I)
QUIRKY = re.compile(r'^(?:the|that|this|what|which|who)\b', re.I)


def stage_name(raw, festival=None):
    """
    A stage name fit to key a table on, or None when the heading is not a stage.

    Four things go wrong in the markup and all four are fixed here rather than
    in each reader, because the same heading reaches this function from year
    sections, per-year articles and matrix tables alike:

      * table attributes survive the strip — 'colspan="3" style="..."| White
        Stage' is the White Stage
      * wiki emphasis and links cling to the name — "[[HeartSupport]] Stage",
        "'''Apex Stage'''"
      * a stage heading sometimes carries its own bill — '**EDM Stage: AN21,
        Ftampa, Wax Motif' names one stage and four artists
      * spacing and case drift year to year — 'Monster Energy Stage(Pond)' and
        'Monster Energy Stage (Pond)' are one stage written twice

    What is dropped is a heading that is not a stage at all: a day of the week,
    a region, the festival's own name, or a bare 'Lineup'. Those rows keep
    their artist, year and festival; they simply have no stage, which is the
    truth about them.
    """
    name = (raw or '').strip()
    if not name:
        return None
    name = TABLE_ATTRS.sub('', name)
    name = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', name)   # [[A|B]] -> B
    name = re.sub(r"'{2,}", '', name)                               # wiki bold/italic
    name = re.sub(r'<[^>]+>', ' ', name)
    listed = STAGE_LIST.match(name)
    if listed:                                  # a stage heading with its bill attached
        name = listed.group(1)
    name = name.replace('"', ' ')
    name = name.strip(' \t|!*;:+-–—.,“”')
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'\s*\(\s*', ' (', name)      # 'Stage(Pond)' -> 'Stage (Pond)'
    name = re.sub(r'\s*\)\s*', ')', name).strip()
    if len(name) < 2 or len(name) > 60:
        return None
    if DAY_OR_PART.match(name) or NOT_A_STAGE.match(name):
        return None
    if festival and name.lower() in (festival.lower(), festival.lower() + ' festival'):
        return None
    if not VENUE_WORD.search(name) and not QUIRKY.match(name):
        return None
    return name
