"""
Check what the festivals in festivals.txt would actually give us.

Edit corpus/festivals.txt, run this, and read the table. For each festival it
finds the Wikipedia article, looks at a sample of years, and reports how many
artists it can read out of each. The point is to choose the corpus on evidence:
the famous festivals are often the thin ones, and a name on a list is not data.

    python3 corpus/coverage.py              # a three-year sample, quick
    python3 corpus/coverage.py --full       # every year, slow

Nothing here writes to the database.
"""
import re
import sys
import json
import urllib.parse
import urllib.request

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from corpus.wikipedia import collect, search, year_sections   # noqa: E402

HERE = __file__.rsplit('/', 1)[0]


def wanted():
    """
    The festivals listed in festivals.txt.

    A line is `Name`, optionally `| 2015-2026` to limit the years, optionally
    `| article: Exact Wikipedia Title` when the search picks the wrong page —
    which it does for festivals whose lineups live in a separate article.
    """
    out = []
    for line in open(HERE + '/festivals.txt'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split('|')]
        name, first, last = parts[0], 1990, 2026
        how = {}
        for part in parts[1:]:
            key, sep, value = part.partition(':')
            if sep:
                how[key.strip().lower()] = value.strip()
            else:
                years = re.findall(r'(?:19|20)\d\d', part)
                if len(years) == 2:
                    first, last = int(years[0]), int(years[1])
        out.append((name, first, last, how))
    return out


def article_for(name: str):
    """The Wikipedia article this festival name resolves to, if any."""
    hits = search(name)
    if not hits:
        return None
    # a dedicated line-ups article beats the main one when both exist
    for title in hits:
        if re.search(r'line-?ups?', title, re.I):
            return title
    return hits[0]


def main():
    full = '--full' in sys.argv
    print('%-34s %-34s %6s %7s %7s  %s' % ('festival', 'article', 'years', 'sample', 'artists', 'verdict'))
    print('-' * 108)
    for name, first, last, how in wanted():
        try:
            if 'setlistfm' in how:
                from corpus.setlistfm import collect as setlist_collect
                city = how['setlistfm']
                rows = setlist_collect(city, first, last)
                years = sorted({r['year'] for r in rows})
                average = round(len(rows) / len(years)) if years else 0
                print('%-34s %-34s %6d %7s %7d  %s'
                      % (name[:34], 'setlist.fm: ' + city, len(years),
                         '%d-%d' % (years[0], years[-1]) if years else '-', average,
                         'good' if average >= 30 else 'thin'))
                continue
            page = how.get('article') or article_for(name)
            if not page:
                print('%-34s %-34s %6s %7s %7s  no article' % (name[:34], '—', '-', '-', '-'))
                continue
            years = sorted(y for y in year_sections(page) if first <= y <= last)
            if not years:
                print('%-34s %-34s %6d %7s %7s  no year sections' % (name[:34], page[:34], 0, '-', '-'))
                continue
            sample = years if full else years[-3:]
            everything = collect(page, sample[0], sample[-1])
            counts = [sum(1 for r in everything if r['year'] == y) for y in sample]
            best = max(counts) if counts else 0
            average = round(sum(counts) / len(counts)) if counts else 0
            verdict = ('good' if average >= 30 else
                       'thin' if average >= 8 else
                       'unusable — needs setlist.fm')
            print('%-34s %-34s %6d %7s %7d  %s'
                  % (name[:34], page[:34], len(years),
                     '%d-%d' % (sample[0], sample[-1]), average, verdict))
        except Exception as error:
            print('%-34s %-34s %6s %7s %7s  failed: %s' % (name[:34], '?', '-', '-', '-', error))


if __name__ == '__main__':
    main()
