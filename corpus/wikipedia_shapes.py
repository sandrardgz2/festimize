"""
Two article shapes that one-article-per-festival parsing cannot read.

corpus/wikipedia.py assumes a festival keeps every year in one article, under
one heading per year. Two festivals in festivals.txt do not, and between them
they hold more years of lineup than any other entry in the list, so skipping
them would cost the rising-artist measure most of its history:

  * **An article per year.** Bonnaroo has no lineup section at all on its main
    article; each year lives in "2015 Bonnaroo Music Festival" and so on. The
    year is in the title rather than in a heading, so there is nothing for
    year_blocks to find. Here the title supplies the year and the run rule
    reads the whole article.
  * **A band-by-year matrix.** "List of Warped Tour lineups by year" is one
    wikitable with a row per band and a column per year, and a mark in the
    cell where the two meet. No run of names exists anywhere in it: every
    name sits alone in a cell, so _runs sees ones and twos and discards them
    all. Here the grid itself is the lineup, and the column heading is the
    year.

Both reuse the helpers in wikipedia.py rather than reimplementing them, and
both go through page_wikitext, which throttles and caches. Nothing here calls
the API directly.

What this does not do:

  * It does not read prose. A per-year article is mostly prose, and a year
    whose lineup was only ever written as a sentence comes out empty. That is
    the right answer: a count of names mined out of paragraphs cannot be
    checked against anything.
  * It does not know a stage from an act. A per-year article usually carries
    the full daily schedule, and in a schedule grid a small venue's name sits
    in exactly the cell an artist would. Obvious non-performances are dropped
    by name (comedy, burlesque, yoga, a beard competition), but the filter is
    a short list of words, not knowledge, and a few venue names survive it.
  * It does not trust the matrix beyond the mark. The Warped Tour table says
    a band played a year and nothing else, so stage is always empty and no
    row is ever flagged a headliner. A missing mark is read as "not listed",
    which is not the same as "did not play".
  * It does not record empty years. A title that does not exist, or that
    cannot be fetched, is skipped, so a gap in the output is a gap in
    Wikipedia or in the network and the two look alike from here.
"""
import re
import sys
from typing import Dict, List, Optional

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from corpus.wikipedia import (MONTHS, NOT_ARTIST, QUALIFIER,         # noqa: E402
                              _name_of, _runs, page_wikitext)

# Things a schedule grid lists in the artist column that nobody performs: the
# tents themselves, and the parts of the festival that are not music. Applied
# only to names with no wiki link, because a link is an article about a band
# and worth more than any guess made from the name.
NOT_PERFORMANCE = re.compile(
    r'\b(?:comedy|theat(?:re|er)|burlesque|cabaret|sideshow|breakdancing|'
    r'belly\s?dance|tribal dance|silent disco|yoga|buskers?|competition|'
    r'contest|interview|workshop|short movies|lounge|caf[eé])\b', re.I)
# A prose lead-in that reads as a name: "On March 12, [[band]], [[band]]..."
# puts the first clause of the sentence in the first comma-separated slot. The
# lead-in has to be followed by a date, or the rule eats the band ON an ON.
DATED_PROSE = re.compile(r'\b(?:19|20)\d\d\b'
                         r'|^(?:on|in|as of|by|during)\s+(?:the\s+)?'
                         r'(?:mid-|early |late )?(?:\d|%s)' % MONTHS, re.I)

MARK = re.compile(r'^(?:\{\{\s*(?:y|yes|ya|tick|check\s?mark)\s*\}\}|y|yes|✓|✔)$', re.I)
YEAR = re.compile(r'\b(19[5-9]\d|20[0-4]\d)\b')
# A stage is named after one, and a schedule's section headings are days, so
# requiring the word keeps "Which Stage" and drops "Friday, June 14".
STAGE_WORD = re.compile(r'\b(?:stage|tent|arena|cinema|pavilion)\b', re.I)


def _usable(name: str, title: Optional[str]) -> bool:
    """Whether a name read out of a schedule is worth recording as an artist."""
    if NOT_ARTIST.match(name):
        return False
    if title is None and (NOT_PERFORMANCE.search(name) or DATED_PROSE.search(name)):
        return False
    return True


def _stage(label: Optional[str]) -> Optional[str]:
    """The stage a run was listed under, or nothing when the label is not one."""
    if not label:
        return None
    label = re.sub(r"[\[\]']", '', label).strip(' *:|!')
    if ',' in label or '=' in label or len(label) > 40:
        return None                       # a day heading, or markup that got loose
    return label if STAGE_WORD.search(label) else None


def _row(page: str, year: int, name: str, title: Optional[str],
         stage: Optional[str], bold: bool) -> dict:
    return {
        'page': page, 'year': year, 'artist': QUALIFIER.sub('', name).strip(),
        'wikipedia_title': title, 'stage': stage, 'headliner': bold,
        'linked': title is not None,
    }


def _unique(rows: List[dict]) -> List[dict]:
    """One row per artist per year; a schedule repeats an act for every day."""
    seen, found = set(), []
    for row in rows:
        key = (row['year'], row['artist'].lower())
        if not row['artist'] or key in seen:
            continue
        seen.add(key)
        found.append(row)
    return found


def per_year_articles(pattern: str, first: int, last: int) -> List[dict]:
    """
    Every artist named in a run, for festivals with one article per year.

    `pattern` holds the title with the year left out, as in
    "{year} Bonnaroo Music Festival". A year whose article does not exist is
    skipped: the pattern is a guess about how the editors named things, and
    the gaps at either end of the range are where the guess runs out.
    """
    rows: List[dict] = []
    for year in range(first, last + 1):
        page = pattern.format(year=year)
        try:
            text = page_wikitext(page)
        except Exception:                 # no such article, or the fetch failed
            continue
        for names, stage in _runs(text):
            label = _stage(stage)
            for name, title, bold in names:
                if _usable(name, title):
                    rows.append(_row(page, year, name, title, label, bold))
    return _unique(rows)


def _tables(text: str):
    """The wikitext of each table on the page, refs and comments removed."""
    text = re.sub(r'<ref[^>]*/>', '', text)
    text = re.sub(r'<ref.*?</ref>', '', text, flags=re.S | re.I)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    table: Optional[List[str]] = None
    depth = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('{|'):
            depth += 1
            if depth == 1:
                table = []
                continue
        if table is None:
            continue
        if stripped.startswith('|}'):
            depth -= 1
            if depth == 0:
                yield table
                table = None
                continue
        table.append(line)
    if table:
        yield table


def _content(cell: str) -> str:
    """
    A cell without its styling.

    `| align="center" | {{Y}}` is one cell with attributes; the pipe that
    separates them is the first one not inside a link or a template, and the
    left half is attributes only when it reads like them.
    """
    cell = cell.lstrip('|').strip()
    depth = 0
    for index, char in enumerate(cell):
        if cell.startswith(('[[', '{{'), index):
            depth += 1
        elif cell.startswith((']]', '}}'), index):
            depth = max(0, depth - 1)
        elif char == '|' and depth == 0:
            head, tail = cell[:index], cell[index + 1:]
            if '=' in head and '[' not in head and '{' not in head:
                return tail.strip()
            break
    return cell


def _band(cell: str):
    """
    (name, wikipedia title, False) for the band named in a row's first cell.

    More forgiving than _name_of, because in this table the column heading
    already says what the cell is. Three shapes turn up that _name_of refuses
    and that are bands all the same: a cell naming a collaboration, where the
    first link is the act that was billed; a name with punctuation in it, like
    "Zero 9:36" or "Survive This!"; and a name that starts lower case. None of
    the guesswork in _name_of is needed here, and the date guard is actively
    wrong: Thursday and June are both bands that played this tour.
    """
    found = _name_of(cell)
    if found:
        return found
    link = re.search(r'\[\[([^|\]]+)(?:\|([^\]]+))?\]\]', cell)
    if link:
        title = link.group(1).strip()
        return (link.group(2) or title).strip(), title, False
    text = re.sub(r"<[^>]*>|'{2,}|\{\{[^{}]*\}\}", '', cell).strip(' |')
    return (text, None, False) if 0 < len(text) <= 60 else None


def _cells(lines: List[str]) -> List[str]:
    """The cells of one table row, in order, as written."""
    found: List[str] = []
    for line in lines:
        for piece in re.split(r'\|\|', line.lstrip('|')):
            found.append(_content('|' + piece))
    return found


def matrix_article(page: str) -> List[dict]:
    """
    One row per marked cell of a band-by-year table, as on the Warped Tour list.

    The first column is the band and the headings name the years, so a row is
    a band and a column is a year and a {{Y}} where they cross is an
    appearance. Columns are matched from the left, because editors leave the
    trailing empty cells off a row and sometimes leave a few spare ones on.
    Any cell holding something other than a mark is read as unmarked rather
    than guessed at.
    """
    rows: List[dict] = []
    for table in _tables(page_wikitext(page)):
        body, header = [], []
        for line in table:
            if line.lstrip().startswith('!'):
                header.extend(_content('|' + piece)
                              for piece in re.split(r'!!', line.lstrip().lstrip('!')))
            else:
                body.append(line)
        years: Dict[int, int] = {}
        for index, cell in enumerate(header):
            match = YEAR.search(cell)
            if match and index:                     # column 0 is the band itself
                years[index] = int(match.group(1))
        if not years:
            continue

        group: Optional[List[str]] = None
        groups: List[List[str]] = []
        for line in body:
            if line.lstrip().startswith('|-'):
                if group:
                    groups.append(group)
                group = []
            elif group is not None and line.lstrip().startswith('|'):
                group.append(line)
        if group:
            groups.append(group)

        for lines in groups:
            cells = _cells(lines)
            if not cells:
                continue
            band = _band(cells[0])
            if not band:
                continue
            name, title, _ = band
            for index, year in years.items():
                if index < len(cells) and MARK.match(cells[index]):
                    rows.append(_row(page, year, name, title, None, False))
    return _unique(rows)
