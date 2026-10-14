"""
Check every row against the source text it claims to come from.

    python3 corpus/fidelity.py

Every error this project has found has been an extraction error rather than a
source error: a comma inside [[Tyler, the Creator]] that split a line and took
the artists above it with it, table header cells read as bands, a whole article
filed under its first year, a paragraph about bands who pulled out read as a
bill. None of those were Wikipedia being wrong. They were the reader being
wrong, and none of them were caught by checking that fields were present.

So this asks a narrower question than "is this true", and asks it of every row
rather than a sample: does the source actually say this? A Wikipedia row has to
have its artist named inside the year block it was attributed to, and a
setlist.fm row has to match a logged setlist with that artist on that date.
A row that fails cannot be defended by pointing at its source, whatever else
is true about it.

What it does not establish: whether the source itself is right. A festival that
mis-states its own 2017 bill will pass here. That is what the hand audit in
corpus/audit.py is for. The two measure different things and both are needed.
"""
import collections
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from corpus.coverage import article_for, wanted           # noqa: E402
from corpus.setlistfm import _pages, _terms               # noqa: E402
from corpus.wikipedia import page_wikitext, year_blocks    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROWS = os.path.join(ROOT, 'data', 'corpus', 'appearances.jsonl')
REPORT = os.path.join(ROOT, 'docs', 'evaluation', 'corpus-fidelity.md')


def flatten(name):
    """
    Compare names the way a reader would, not the way bytes do.

    Wikipedia writes RÜFÜS DU SOL, Rüfüs Du Sol and [[Rüfüs Du Sol|RÜFÜS DU
    SOL]] for one band, and a check that called those three different things
    would report its own strictness as a data problem.
    """
    plain = unicodedata.normalize('NFKD', name or '')
    plain = ''.join(c for c in plain if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '', plain.lower())


def wikipedia_sources(rows):
    """
    Source text per (festival, year), read from the cache.

    Three article shapes, checked as tightly as each allows. A festival with
    year headings gives that year's section. A festival with one article a year
    gives that article, which is the same strength. A matrix article — one table
    of bands against years — can only give the whole table, so a phantom name is
    caught there but a name moved between columns is not; `weak` says which.
    """
    text, weak = {}, set()
    for name, first, last, how in wanted():
        if 'setlistfm' in how:
            continue
        try:
            if 'pattern' in how:
                for year in range(first, last + 1):
                    try:
                        body = page_wikitext(how['pattern'].replace('{year}', str(year)))
                    except Exception:
                        continue
                    text[(name, year)] = body
                continue
            page = how.get('article') or article_for(name)
            if not page:
                continue
            if 'matrix' in how:
                body = page_wikitext(page)
                for year in range(first, last + 1):
                    text[(name, year)] = body
                    weak.add(name)
                continue
            for year, body in year_blocks(page).items():
                text[(name, year)] = body
        except Exception:
            continue
    return text, weak


def setlistfm_sources(rows):
    """(artist, date) pairs per festival, read from the cached searches."""
    found = collections.defaultdict(set)
    for name, first, last, how in wanted():
        if 'setlistfm' not in how:
            continue
        try:
            for part in how['setlistfm'].split('+'):
                for entry in _pages(_terms(part), first, last):
                    artist = (entry.get('artist') or {}).get('name')
                    date = entry.get('eventDate', '')
                    if artist and date:
                        day, month, year = date.split('-')
                        found[name].add((flatten(artist),
                                         '%s-%s-%s' % (year, month, day)))
        except Exception:
            continue
    return found


def main():
    rows = [json.loads(line) for line in open(ROWS, encoding='utf-8') if line.strip()]
    wiki, weak = wikipedia_sources(rows)
    sets = setlistfm_sources(rows)

    checked = collections.Counter()
    failed = collections.defaultdict(list)
    unchecked = collections.Counter()

    for row in rows:
        festival, year, artist = row['festival'], row['year'], row['artist']
        if row['source'] == 'setlistfm':
            known = sets.get(festival)
            if not known:
                unchecked['setlist.fm search not in the cache'] += 1
                continue
            checked[festival] += 1
            if (flatten(artist), row.get('date', '')) not in known:
                failed[festival].append((year, artist, 'no setlist with that artist on that date'))
        else:
            body = wiki.get((festival, year))
            if body is None:
                unchecked['no cached year block for that festival-year'] += 1
                continue
            checked[festival] += 1
            if flatten(artist) not in flatten(body):
                failed[festival].append((year, artist, 'not named in that year of the article'))

    total_checked = sum(checked.values())
    total_failed = sum(len(f) for f in failed.values())
    out = []
    say = out.append
    say('# Corpus fidelity')
    say('')
    say('Does the source say what the row claims? Asked of every row that can be')
    say('traced back to cached source text. This does not ask whether the source')
    say('is right — see corpus-audit.md for that.')
    say('')
    say('- rows checked: **%d of %d**' % (total_checked, len(rows)))
    if weak:
        say('- of those, **%d** are checked for the name only, not the year: %s'
            % (sum(count for festival, count in checked.items() if festival in weak),
               ', '.join(sorted(weak)) + ' list bands against years in one table, so the'
               ' article cannot say which column a name sat in'))
    say('- rows the source does not support: **%d (%.2f%%)**'
        % (total_failed, 100.0 * total_failed / total_checked if total_checked else 0))
    say('')
    if unchecked:
        say('## Not checkable')
        say('')
        for reason, count in unchecked.most_common():
            say('- %s: **%d**' % (reason, count))
        say('')
    if failed:
        say('## Where the source does not support the row')
        say('')
        say('| festival | checked | unsupported | rate | example |')
        say('|---|---|---|---|---|')
        for festival in sorted(failed, key=lambda f: -len(failed[f])):
            bad = failed[festival]
            example = '%d %s — %s' % bad[0]
            say('| %s | %d | %d | %.1f%% | %s |'
                % (festival, checked[festival], len(bad),
                   100.0 * len(bad) / checked[festival] if checked[festival] else 0, example))
        say('')
    clean = [f for f in checked if f not in failed]
    say('%d of %d checkable festivals have every row supported by their source.'
        % (len(clean), len(checked)))
    say('')
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    open(REPORT, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('\n'.join(out))
    print('written to', REPORT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
