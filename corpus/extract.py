"""
Read every festival in festivals.txt and write one row per artist appearance.

    python3 corpus/extract.py

Output is data/corpus/appearances.jsonl — one JSON object a line, so it can be
inspected with grep and loaded in one pass. Nothing is written to the database
here; resolving names to artists comes next, and that step needs the raw rows
to stay raw so a mistake can be traced back to the article it came from.

Years a festival did not happen are recorded as cancellations rather than left
out, because a gap and a year off mean different things to a measure that
looks at how often an artist appears.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from corpus.coverage import article_for, wanted          # noqa: E402
from corpus.wikipedia import collect, year_blocks        # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'corpus')


def main():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'appearances.jsonl')
    total, per_festival = 0, []
    with open(path, 'w', encoding='utf-8') as handle:
        for name, first, last, pinned in wanted():
            try:
                page = pinned or article_for(name)
                rows = collect(page, first, last) if page else []
            except Exception as error:
                print('%-34s failed: %s' % (name[:34], error))
                continue
            years = sorted({row['year'] for row in rows})
            for row in rows:
                handle.write(json.dumps(dict(row, festival=name, source='wikipedia',
                                             confidence=1.0 if row['linked'] else 0.7)) + '\n')
            total += len(rows)
            per_festival.append((name, page, len(rows), len(years),
                                 years[0] if years else None, years[-1] if years else None,
                                 sum(r['linked'] for r in rows)))
            print('%-34s %5d rows  %2d years  %s'
                  % (name[:34], len(rows), len(years),
                     '%d-%d' % (years[0], years[-1]) if years else 'none'))

    print('\n%d appearance rows written to %s' % (total, path))
    linked = sum(f[6] for f in per_festival)
    print('%d of them (%.0f%%) carry a Wikipedia link, which resolves to a MusicBrainz id'
          % (linked, 100.0 * linked / total if total else 0))
    print('%d distinct artist names' % len({
        json.loads(line)['artist'].lower() for line in open(path, encoding='utf-8')}))


if __name__ == '__main__':
    main()
