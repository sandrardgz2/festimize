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


def _strip(text: str) -> str:
    """Remove everything that is not content: refs, templates, comments, images."""
    text = re.sub(r'<ref[^>]*/>', '', text)
    text = re.sub(r'<ref.*?</ref>', '', text, flags=re.S | re.I)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
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
    # an unlinked name: short, no sentence punctuation, not a stray word of prose
    if (len(token) <= 50 and not token.endswith(('.', ':', '!', '?'))
            and len(token.split()) <= 6 and re.match(r"^[A-Z0-9][\w\s&'’.\-+!/]*$", token)):
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
    buffer: List[tuple] = []

    def flush():
        nonlocal buffer
        found = buffer
        buffer = []
        return (found, stage) if len(found) >= 3 else None

    for line in _strip(text).splitlines():
        line = line.rstrip()
        heading = re.match(r'^={3,}\s*(.+?)\s*={3,}$', line)
        if heading:
            run = flush()
            if run:
                yield run
            stage = heading.group(1).strip()
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
        tokens = re.split(r'<br\s*/?>|,|•|\u2022', line)
        names = [found for found in (_name_of(t) for t in tokens) if found]
        names = [n for n in names if not NOT_ARTIST.match(n[0])]
        if len(names) >= 3:
            run = flush()
            if run:
                yield run
            yield names, stage
        elif names:
            buffer.extend(names)
        else:
            run = flush()
            if run:
                yield run
    run = flush()
    if run:
        yield run


def collect(page: str, first: int, last: int) -> List[dict]:
    """Every artist listed under a year heading on this page, within those years."""
    rows: List[dict] = []
    for year, text in sorted(year_blocks(page).items()):
        if not first <= year <= last:
            continue
        for names, stage in _runs(text):
            for name, title, bold in names:
                rows.append({
                    'page': page, 'year': year, 'artist': QUALIFIER.sub('', name).strip(),
                    'wikipedia_title': title, 'stage': stage, 'headliner': bold,
                    'linked': title is not None,
                })
    seen, unique = set(), []
    for row in rows:                      # an artist may appear on two stages in a year
        key = (row['year'], row['artist'].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique
