"""
Pull festival lineups out of English Wikipedia.

There is no single format. Bloodstock keeps its lineup in a table of stages
with the artists separated by line breaks; Tuska writes the whole bill as one
comma-separated run of links; others use bullet lists, and most mix prose in
around it. Writing a parser per festival would mean thirteen parsers to keep
working, so this looks for the one thing every shape has in common.

**A lineup is a run of names.** Three or more artist links in a row, separated
only by commas or line breaks, is a bill. A sentence about the weather may
contain a link or two, but it does not contain six of them in a row with
nothing but commas between. That one rule reads every shape in the audit, and
it leaves prose alone, which is the point: a paragraph saying "Metallica
headlined" is not a lineup, and mining names out of sentences invents data that
nobody can check.

Two things are recorded beyond the name:

  * **Bold means top of the bill.** Articles bold the headliners, consistently
    enough to be worth keeping as a billing signal and never enough to be
    trusted on its own, so it is stored as a flag rather than a rank.
  * **The wiki link.** A link resolves to a Wikidata item and from there to a
    MusicBrainz id, which is a far better identity than a name that might be
    "Sleep" or "Sleep Token".

Years that are only prose come out empty, and empty is recorded rather than
quietly skipped: a year with no lineup on Wikipedia is a fact about the source,
and the rising-artist measure needs to tell that apart from a year off.
"""
import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

CACHE = os.path.join(os.path.dirname(__file__), '.cache')

API = 'https://en.wikipedia.org/w/api.php'
AGENT = 'Festimize/0.1 (IST 440W student project; github.com/sandrardgz2/festimize)'

SKIP_NAMESPACE = re.compile(r'^(File|Image|Category|Template|Wikipedia|Help|Portal):', re.I)
QUALIFIER = re.compile(r'\s*\((?:band|musician|singer|rapper|DJ|duo|group|American|British|'
                       r'Swedish|Finnish|German|Norwegian|French|Danish|Dutch|Australian|'
                       r'Canadian|[A-Z]{2})\s*(?:band|musician|singer|duo|group)?\)\s*$', re.I)
# Things that turn up inside lineup runs but are not artists. Dates matter
# most: a table of days puts "October 2" in exactly the position a name goes.
MONTHS = (r'january|february|march|april|may|june|july|august|september|october|november|december'
          r'|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec')
NOT_ARTIST = re.compile(
    r'^(?:'
    r'stage|main stage|second stage|third stage|day \d+|friday|saturday|sunday|thursday|'
    r'monday|tuesday|wednesday|tba|tbc|to be announced|cancell?ed|headliners?|and more|'
    r'hurricane .*|covid-19 pandemic|heavy metal|death metal|black metal|rock music|'
    r'(?:19|20)\d\d|\d{1,2}(?::\d\d)?(?:am|pm)?|'
    r'(?:%s)\s*\d{0,2}(?:st|nd|rd|th)?|'          # October 2
    r'\d{1,2}(?:st|nd|rd|th)?\s+(?:%s)'            # 2 October
    r')$' % (MONTHS, MONTHS), re.I)
# Words that belong to sentences, not to band names.
PROSE = re.compile(r'\b(over|next|about|approximately|between|around|during|after|before|'
                   r'including|featuring|were|was|is|are|has|had|would|will|their|its|'
                   r'which|who|when|while|because|however|also|more|than|from)\b')
# A sentence that is announcing a bill, as opposed to one that merely mentions
# bands. Only these are mined for links, and only their links are taken.
LINEUP_SENTENCE = re.compile(
    r'\b(line-?up|bands?|artists?|performers?|acts?|featur\w*|headlin\w*)\b', re.I)
# The dangerous paragraphs are not the ones that say nothing — they are the ones
# that say the opposite. Download's 2015 section names The Sword, King 810,
# Ghost Town and Antemasque in a paragraph about bands that *pulled out*, so
# mining it records four appearances that never happened. A sentence carrying
# any of this vocabulary is narrative about the festival, not its bill.
WITHDRAWN = re.compile(
    r'\b(pulled out|pull out|due to play|were to play|was to play|withdrew|withdrawn|'
    r'cancell?ed|replaced|removed|dropped out|rescheduled|postponed|instead of|'
    r'police|surveillance|arrest\w*|died|death|injur\w*|lawsuit|refund\w*)\b', re.I)
# A bill is mostly names; a story is mostly words. Below this the links are
# incidental to whatever the paragraph is actually about.
LINK_SHARE = 0.15
# Download and Knotfest both run several national editions and Wikipedia files
# them as subsections of one year: the 2019 Download section holds a UK table
# and an Australian one. Merged, they make one festival that looks twice its
# size and put bands at a festival on the wrong continent. The heading is the
# only thing that says which edition a table belongs to, and it has to be
# tracked separately from the stage, because a stage heading inside the section
# overwrites it — which is how RedHook ended up on a UK stage.
# The place comes last in the heading, whether the heading is the place on its
# own ("Australia", as Download writes it) or the brand and the place together
# ("Lollapalooza Argentina", as Lollapalooza writes it). Matching only the start
# missed every Lollapalooza edition, which is how a Puerto Rican reggaetón
# singer ended up at the Chicago festival.
EDITION = re.compile(
    r'(?i)(?:^|\s)(australia|japan|france|spain|germany|italy|chile|brazil|brasil|'
    r'argentina|mexico|india|portugal|madrid|lisbon|paris|berlin|melbourne|sydney|'
    r'santiago|s\u00e3o paulo|sao paulo|rio de janeiro|buenos aires|united states|'
    r'usa|las vegas|los angeles|porto|stockholm|uk|united kingdom|england|chicago)'
    # a trailing note stays part of the heading: Lollapalooza's 2020 sections
    # read "Lollapalooza Berlin (Canceled)", and requiring the place to be the
    # very last word filed five cancelled overseas bills as the Chicago one
    r'(?:\s*\([^)]*\))?\s*$')
STAGE_LINE = re.compile(r"(?:'''|\|\s*)?\s*\[?\[?([^|\]']{2,60}?)\]?\]?\s*(?:'''\s*)?(?:stage|tent|arena)\b", re.I)


_last_call = [0.0]
MIN_GAP = 1.2          # Wikipedia starts returning 429 well before you expect it to


def _api(**params) -> dict:
    params.setdefault('format', 'json')
    params.setdefault('formatversion', '2')
    url = API + '?' + urllib.parse.urlencode(params)
    last = None
    for attempt in range(5):
        wait = MIN_GAP - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()
        try:
            request = urllib.request.Request(url, headers={'User-Agent': AGENT})
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            last = error
            retry_after = error.headers.get('Retry-After') if error.headers else None
            if retry_after:
                time.sleep(float(retry_after))
            elif error.code == 429:
                time.sleep(10.0 * (attempt + 1))     # a burst earns a long cool-off
            else:
                time.sleep(2.0 * (attempt + 1))
        except Exception as error:
            last = error
            time.sleep(2.0 * (attempt + 1))
    raise last


def search(name: str, limit: int = 3) -> List[str]:
    """Article titles matching this festival name, cached on disk."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, 'search-' + hashlib.sha1(name.encode()).hexdigest() + '.json')
    if os.path.exists(path):
        return json.load(open(path))
    found = [hit['title'] for hit in
             _api(action='query', list='search', srsearch=name, srlimit=limit)['query']['search']]
    json.dump(found, open(path, 'w'))
    return found


def page_wikitext(page: str) -> str:
    """
    The whole article, fetched once and kept on disk.

    One request per article rather than one per year: a festival with twenty
    years of lineups is twenty requests the polite way and one this way, and
    Wikipedia starts refusing long before twenty festivals are done.
    """
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, hashlib.sha1(page.encode()).hexdigest() + '.wikitext')
    if os.path.exists(path):
        return open(path, encoding='utf-8').read()
    text = _api(action='parse', page=page, prop='wikitext', redirects='1')['parse']['wikitext']
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)
    return text


def year_blocks(page: str) -> Dict[int, str]:
    """Each year heading on the page, with the wikitext underneath it."""
    text = page_wikitext(page)
    blocks: Dict[int, List[str]] = {}
    current, depth = None, 0
    for line in text.splitlines():
        heading = re.match(r'^(={2,})\s*(.+?)\s*\1\s*$', line)
        if heading:
            level, title = len(heading.group(1)), heading.group(2)
            match = re.search(r'\b(19[5-9]\d|20[0-4]\d)\b', title)
            if match:
                current, depth = int(match.group(1)), level
                blocks.setdefault(current, [])
                continue
            if current is not None and level <= depth:
                current = None                  # a new section at the same level ends the year
                continue
        if current is not None:
            blocks[current].append(line)
    return {year: '\n'.join(lines) for year, lines in blocks.items()}


def year_sections(page: str) -> Dict[int, str]:
    """Kept for callers that only want to know which years exist."""
    return year_blocks(page)


# Templates whose whole purpose is to wrap content: a collapsible box, a
# multi-column list. Deleting them took the lineup with them — Lollapalooza
# writes every Chicago bill inside {{hidden}}, so the Chicago lineups were
# silently absent for years while the overseas editions, which are not wrapped,
# came through. Their scaffolding goes and what they contain stays.
WRAPPERS = ('hidden', 'columns-list', 'column', 'collapse top', 'cot')
SCAFFOLD = re.compile(
    r'^\s*\|\s*(headercss|contentcss|header|title|titlestyle|style|bodystyle|'
    r'expanded|border|frame\w*|colwidth|col\d*|cols|width|fw\d|ta\d|align)\s*=.*$',
    re.I)
CONTENT_PARAM = re.compile(r'^\s*\|\s*content\s*=\s*', re.I)


def _unwrap(text: str) -> str:
    """Keep what a content-wrapping template holds and drop the template."""
    for name in WRAPPERS:
        opening = re.compile(r'\{\{\s*' + re.escape(name) + r'\b', re.I)
        while True:
            found = opening.search(text)
            if not found:
                break
            # walk to the matching close so a nested template cannot end it early
            depth, cursor = 0, found.start()
            while cursor < len(text):
                if text.startswith('{{', cursor):
                    depth += 1
                    cursor += 2
                elif text.startswith('}}', cursor):
                    depth -= 1
                    cursor += 2
                    if depth == 0:
                        break
                else:
                    cursor += 1
            inner = text[found.end():cursor - 2]
            kept = [CONTENT_PARAM.sub('', line) for line in inner.splitlines()
                    if not SCAFFOLD.match(line)]
            text = text[:found.start()] + '\n'.join(kept) + text[cursor:]
    return text


def _strip(text: str) -> str:
    """Remove everything that is not content: refs, templates, comments, images."""
    text = re.sub(r'<ref[^>]*/>', '', text)
    text = re.sub(r'<ref.*?</ref>', '', text, flags=re.S | re.I)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = _unwrap(text)
    text = re.sub(r'\{\{[^{}]*\}\}', '', text)
    text = re.sub(r'\[\[(?:File|Image):[^\]]*\]\]', '', text, flags=re.I)
    return text


def _name_of(token: str):
    """(name, wikipedia title, was bold) for one token, or None if it is not a name."""
    bold = "'''" in token
    token = re.sub(r"'{2,}", '', token).strip()
    token = re.sub(r'<[^>]+>', ' ', token).strip(' \t|*:;.')
    if not token:
        return None
    link = re.match(r'^\[\[([^|\]]+)(?:\|([^\]]+))?\]\]$', token)
    if link:
        title = link.group(1).strip()
        if SKIP_NAMESPACE.match(title):
            return None
        name = (link.group(2) or title).strip()
        return name, title, bold
    # An unlinked name has to look like a name. Prose with commas in it reads
    # as a list of three or more "names" otherwise, and a figure like "12,000"
    # splits at its own comma into fragments. Linked tokens skip these checks:
    # a wiki link is evidence in itself.
    if (len(token) <= 50 and not token.endswith(('.', ':', '!', '?'))
            and len(token.split()) <= 6
            and not re.search(r'\d{3}', token)              # "000 in 1995 and 18"
            and re.match(r"^[A-Z0-9!][\w\s&'’.\-+!/×]*$", token)):
        return token, None, bold
    return None


def _runs(text: str):
    """
    Yield (names, stage) for every run of three or more names.

    A run is either several names on one line separated by commas, or several
    consecutive lines holding one name each — which is how a table cell lists a
    stage's bill. Anything shorter than three is prose and is dropped.
    """
    stage = None
    edition = None
    edition_depth = [None]          # which heading level the editions sit at
    buffer: List[tuple] = []

    def flush():
        nonlocal buffer
        found = buffer
        buffer = []
        return (found, stage, edition) if len(found) >= 3 else None

    for line in _strip(text).splitlines():
        line = line.rstrip()
        heading = re.match(r'^={3,}\s*(.+?)\s*={3,}$', line)
        if heading:
            run = flush()
            if run:
                yield run
            title = heading.group(1).strip()
            depth = len(heading.group(0)) - len(heading.group(0).lstrip('='))
            if EDITION.search(title):
                # Editions sit at one level of the year's subheadings, and the
                # home edition is a heading at that same level with no place in
                # it — Lollapalooza lists Argentina, Chile, Paris, then plain
                # "Lollapalooza", then Berlin. Remembering the level is what
                # lets the home section clear the previous country instead of
                # inheriting it.
                edition, stage, edition_depth[0] = title, None, depth
            elif depth == edition_depth[0]:
                edition, stage = None, None
            else:
                stage = title
            continue
        if line.startswith('!'):
            run = flush()
            if run:
                yield run
            label = re.sub(r"[!\[\]']", ' ', line).strip()
            if re.search(r'\b(stage|tent|arena|theatre|theater)\b', label, re.I) and len(label) < 60:
                stage = label
            continue
        if not line or line.startswith(('|-', '|}', '{|')):
            run = flush()
            if run:
                yield run
            continue
        # a short cell naming a stage sets the context for what follows it
        if (re.search(r'\b(stage|tent)\b', line, re.I) and len(line) < 120
                and not re.search(r'\[\[.*\]\].*\[\[.*\]\]', line)):
            run = flush()
            if run:
                yield run
            stage = re.sub(r"[\[\]']", '', line).strip(' |!').strip() or stage
            continue
        # Prose is where the junk comes from: a sentence with commas reads as a
        # list of names, and a figure like "12,000" splits at its own comma.
        # Judging the whole line is better than judging each piece, because
        # "Aphex Twin" looks like a name whichever sentence it was lifted from.
        if PROSE.search(line):
            run = flush()
            if run:
                yield run
            # Some festivals write the bill as a sentence rather than a list:
            # Hulaween's every year reads "The bands featured were [[A]], [[B]],
            # [[C]]...". Throwing the line away loses the whole lineup, and
            # reading it like a list lets sentence fragments in. Only the linked
            # names are taken, and only when the sentence says it is announcing
            # a bill — a band with its own article is not a stray phrase, and
            # LINEUP_SENTENCE keeps out prose that merely mentions three bands.
            if LINEUP_SENTENCE.search(line) and not WITHDRAWN.search(line):
                # A link inside quotation marks is a song, not an act:
                # Babymetal joined DragonForce to perform "[[Gimme Chocolate!!]]".
                plain = re.sub(r'["\u201c\u201d]\s*\[\[[^\]]*\]\]\s*["\u201c\u201d]', ' ', line)
                inners = re.findall(r'\[\[([^\]]*)\]\]', plain)
                share = (sum(len(i.split('|')[-1]) for i in inners)
                         / float(max(len(plain), 1)))
                linked = [_name_of('[[%s]]' % inner) for inner in inners]
                linked = [found for found in linked if found
                          and not NOT_ARTIST.match(found[0])]
                if len(linked) >= 3 and share >= LINK_SHARE:
                    yield linked, stage, edition
            continue
        # A comma inside a link belongs to the name — [[Tyler, the Creator]],
        # [[Earth, Wind & Fire]], [[Crosby, Stills & Nash]]. Splitting on it
        # breaks the link, the line then yields nothing, and the names already
        # collected from the cell above are thrown away with it. So links are
        # hidden before the split and put back afterwards.
        held = []

        def hide(match):
            held.append(match.group(0))
            return '\x00%d\x00' % (len(held) - 1)

        masked = re.sub(r'\[\[[^\]]*\]\]', hide, line)
        tokens = [re.sub(r'\x00(\d+)\x00', lambda m: held[int(m.group(1))], piece)
                  for piece in re.split(r'<br\s*/?>|,|•|\u2022', masked)]
        names = [found for found in (_name_of(t) for t in tokens) if found]
        names = [n for n in names if not NOT_ARTIST.match(n[0])]
        if len(names) >= 3:
            run = flush()
            if run:
                yield run
            yield names, stage, edition
        elif names:
            buffer.extend(names)
        else:
            run = flush()
            if run:
                yield run
    run = flush()
    if run:
        yield run


MOST_IN_A_YEAR = 400          # no single festival year lists more acts than this


def collect(page: str, first: int, last: int) -> List[dict]:
    """
    Every artist listed under a year heading on this page, within those years.

    Two sanity rules, because a wrong year is worse than a missing one: an
    article whose only year heading covers the whole page cannot date anything
    (Time Warp's article puts fifteen thousand characters under "1994", which
    would file every DJ it mentions under the festival's first edition), and a
    year that appears to list hundreds of acts is reading something that is not
    a lineup.
    """
    rows: List[dict] = []
    blocks = year_blocks(page)
    if len(blocks) == 1 and len(next(iter(blocks.values()))) > 6000:
        print('   %s: one year heading covers the whole article; years cannot be '
              'trusted, skipping' % page)
        return []
    for year, text in sorted(blocks.items()):
        if not first <= year <= last:
            continue
        for names, stage, edition in _runs(text):
            for name, title, bold in names:
                rows.append({
                    'page': page, 'year': year, 'artist': QUALIFIER.sub('', name).strip(),
                    'wikipedia_title': title, 'stage': stage, 'edition': edition,
                    'headliner': bold, 'linked': title is not None,
                })
    rows.sort(key=lambda r: r.get('edition') is not None)   # home edition wins a tie
    seen, unique = set(), []
    for row in rows:                      # an artist may appear on two stages in a year
        key = (row['year'], row['artist'].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)

    # Counted per edition, not per year. Lollapalooza runs eight festivals in a
    # year and reading all of them put 2023 over the cap, which would have
    # thrown away the Chicago bill because Argentina and Chile were in the same
    # tally. Only the edition that reads as hundreds of acts is dropped.
    counts = {}
    for row in unique:
        key = (row['year'], row.get('edition'))
        counts[key] = counts.get(key, 0) + 1
    overfull = {key for key, count in counts.items() if count > MOST_IN_A_YEAR}
    if overfull:
        print('   %s: %s read as hundreds of acts, dropping as unreliable'
              % (page, ', '.join('%d%s' % (y, ' ' + e if e else '')
                                 for y, e in sorted(overfull, key=lambda k: (k[0], k[1] or '')))))
        unique = [row for row in unique
                  if (row['year'], row.get('edition')) not in overfull]
    return unique
