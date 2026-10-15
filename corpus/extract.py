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
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from corpus.clean import is_music, looks_like_artist, stage_name   # noqa: E402
from corpus.coverage import article_for, wanted          # noqa: E402
from corpus.wikipedia import collect, year_blocks        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'corpus')

# What each source allows, recorded per row rather than assumed later. Facts
# about who played where are not copyrightable and Wikipedia asks only for
# attribution; MusicBrainz core data is CC0. setlist.fm's API is licensed for
# non-commercial use, so those rows have to be droppable in one query if this
# is ever more than coursework.
# Festival/source combinations proven wrong, kept out however they arrive —
# including through the carry-over path. Time Warp's article files every DJ it
# mentions under 1994, its first edition, so the names are real and the years
# are fiction; it waits for setlist.fm instead.
QUARANTINE = {('Time Warp Festival', 'wikipedia')}

LICENSING = {
    'wikipedia': {'commercial_use': True, 'attribution': 'English Wikipedia, CC BY-SA'},
    'setlistfm': {'commercial_use': False, 'attribution': 'setlist.fm, non-commercial API terms'},
}


def previous(path):
    """
    What we already had, keyed by festival.

    Both the file on disk and the last committed version are read, and the
    richer of the two wins per festival. A run that failed for a festival
    writes nothing for it, so without this a second failed run would turn a
    temporary rate limit into permanent data loss.
    """
    def read(lines):
        found = {}
        for line in lines:
            if line.strip():
                row = json.loads(line)
                found.setdefault(row['festival'], []).append(row)
        return found

    on_disk = read(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    committed = {}
    try:
        import subprocess
        result = subprocess.run(['git', 'show', 'HEAD:data/corpus/appearances.jsonl'],
                                cwd=ROOT, capture_output=True, text=True)
        if result.returncode == 0:
            committed = read(result.stdout.splitlines())
    except Exception:
        pass

    best = {}
    for name in set(on_disk) | set(committed):
        rows = max(on_disk.get(name, []), committed.get(name, []), key=len)
        best[name] = rows
    return best


def in_window(row, months):
    """Whether a carried row falls in the months the festival now runs in."""
    if not months:
        return True
    date = row.get('date') or ''
    match = re.match(r'\d{4}-(\d{2})', date)
    # A row with no date cannot be placed in or out of the window; the festivals
    # that have a window are all setlist.fm, where every row carries a date.
    return int(match.group(1)) in months if match else True


def main():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'appearances.jsonl')
    before = previous(path)
    # write beside the real file and rename at the end, so a crawl that is
    # interrupted leaves the last good dataset intact rather than half of a new one
    partial = path + '.partial'
    total, per_festival = 0, []
    with open(partial, 'w', encoding='utf-8') as handle:
        for name, first, last, how in wanted():
            try:
                rows, page, source = [], None, 'wikipedia'
                if 'setlistfm' in how:
                    from corpus.setlistfm import collect as setlist_collect
                    page = how['setlistfm']            # "city=Wacken" or "venue=Douglass Park"
                    months = [int(m) for m in re.findall(r'\d+', how.get('months', ''))]
                    least_days = int(how.get('days', 1) or 1)
                    per_day = int(how.get('per_day', 5) or 5)
                    rows = setlist_collect(page, first, last, months=months or None,
                                           least_days=least_days, least_per_day=per_day)
                    source = 'setlistfm'
                elif 'pattern' in how:
                    from corpus.wikipedia_shapes import per_year_articles
                    page = how['pattern']
                    rows = per_year_articles(page, first, last)
                elif 'matrix' in how:
                    from corpus.wikipedia_shapes import matrix_article
                    page = how.get('article') or article_for(name)
                    rows = [r for r in matrix_article(page) if first <= r['year'] <= last]
                else:
                    page = how.get('article') or article_for(name)
                    rows = collect(page, first, last) if page else []
                # An article that stops before the festival did leaves a hole
                # that reads as every artist on its bills retiring that year:
                # Wikipedia has a per-year Bonnaroo article through 2019 and
                # none after, though the festival ran on. `fill:` closes the
                # gap with a setlist.fm search used only for the years the
                # article does not reach, so the editorial lineup still wins
                # where it exists and the commercially usable rows are not
                # traded away for the years it covers. Its own try: a rate
                # limit on the fill must not cost us the article as well.
                if 'fill' in how and source != 'setlistfm':
                    try:
                        from corpus.setlistfm import collect as setlist_collect
                        held = {row['year'] for row in rows}
                        months = [int(m) for m in re.findall(r'\d+', how.get('months', ''))]
                        filled = [row for row in setlist_collect(
                                      how['fill'], first, last, months=months or None,
                                      least_days=int(how.get('days', 1) or 1),
                                      least_per_day=int(how.get('per_day', 5) or 5))
                                  if row['year'] not in held]
                        for row in filled:
                            row['source'] = 'setlistfm'
                        rows = rows + filled
                        print('%-34s %d rows added for %s from setlist.fm'
                              % ('', len(filled),
                                 ', '.join(str(y) for y in
                                           sorted({r['year'] for r in filled})) or 'no year'))
                    except Exception as gap:
                        print('%-34s gap not filled: %s' % ('', gap))
            except Exception as error:
                # A rate limit is not evidence that a festival has no lineup.
                # Keep what the last run found rather than quietly dropping it.
                # Carried rows have to obey the current list, not the one that
                # fetched them: narrowing a festival to 2015-2026 must not be
                # undone by a rate limit handing back its 1995 rows.
                # Every current rule is re-applied, not just the year range.
                # Roadburn's carried rows were read before there was a month
                # window, so without this a rate limit quietly reinstates the
                # year-round Tilburg club gigs that window exists to remove.
                window = [int(m) for m in re.findall(r'\d+', how.get('months', ''))]
                kept = [row for row in before.get(name, [])
                        if (name, row.get('source', 'wikipedia')) not in QUARANTINE
                        and first <= row.get('year', 0) <= last
                        and in_window(row, window)
                        and is_music(row)
                        and looks_like_artist(row.get('artist'),
                                             row.get('linked') or row.get('musicbrainz_id'))]
                for row in kept:
                    row.setdefault('source', 'wikipedia')
                    if row['source'] != 'setlistfm':
                        row['stage'] = stage_name(row.get('stage'), name)
                    # Flagged so the report can say which festivals are serving
                    # an older crawl rather than what this run actually read.
                    row['carried'] = True
                    for field, value in LICENSING[row['source']].items():
                        row.setdefault(field, value)
                    handle.write(json.dumps(row) + '\n')
                total += len(kept)
                print('%-34s failed: %s%s'
                      % (name[:34], error,
                         ' (kept %d rows from the last run)' % len(kept) if kept else ''))
                continue
            # one gate for every reader and for anything carried over
            if (name, source) in QUARANTINE:
                print('%-34s quarantined: known-bad year attribution' % name[:34])
                continue
            # A festival brand with editions in several countries is several
            # festivals. Wikipedia files them under one year, so merged they
            # make Knotfest look like a 47-act festival when its home editions
            # are nearer 19, and they put bands at a festival on the wrong
            # continent. The edition is kept on the row, so this is one line to
            # reverse if the overseas bills are ever wanted in their own right.
            abroad = [row for row in rows if row.get('edition')]
            if abroad:
                where = collections.Counter(row['edition'] for row in abroad)
                print('%-34s %d rows dropped as other editions: %s'
                      % ('', len(abroad),
                         ', '.join('%s %d' % kv for kv in where.most_common())))
            rows = [row for row in rows
                    if not row.get('edition')
                    and is_music(row)
                    and looks_like_artist(row.get('artist'),
                                          row.get('linked') or row.get('musicbrainz_id'))]
            # The heading above a block of names is cleaned only now, after
            # is_music has judged the raw text: a comedy tent must not be
            # renamed out of reach of that test. setlist.fm rows hold a venue
            # in this field rather than a stage, and are left as they are.
            for row in rows:
                if row.get('source', source) != 'setlistfm':
                    row['stage'] = stage_name(row.get('stage'), name)
            # An announced lineup for an edition that never happened is still
            # information, but it is not an appearance: counting it would show
            # an artist's career continuing through a year nobody played.
            called_off = {int(y) for y in re.findall(r'(?:19|20)\d\d', how.get('cancelled', ''))}
            for row in rows:
                row['happened'] = row['year'] not in called_off
            years = sorted({row['year'] for row in rows})
            for row in rows:
                # an editorial lineup is firmer evidence than a crowd-sourced
                # setlist, and an unlinked name is firmer than neither. The
                # source is read off the row, because a festival read from its
                # article can have later years filled in from setlist.fm, and
                # the two do not carry the same licence.
                came_from = row.get('source', source)
                confidence = (0.85 if came_from == 'setlistfm' else
                              1.0 if row.get('linked') else 0.7)
                handle.write(json.dumps(dict(row, festival=name, source=came_from,
                                             confidence=confidence,
                                             **LICENSING[came_from])) + '\n')
            total += len(rows)
            per_festival.append((name, page, len(rows), len(years),
                                 years[0] if years else None, years[-1] if years else None,
                                 sum(r['linked'] for r in rows)))
            print('%-34s %5d rows  %2d years  %s'
                  % (name[:34], len(rows), len(years),
                     '%d-%d' % (years[0], years[-1]) if years else 'none'))

    os.replace(partial, path)
    print('\n%d appearance rows written to %s' % (total, path))
    linked = sum(f[6] for f in per_festival)
    print('%d of them (%.0f%%) carry a Wikipedia link, which resolves to a MusicBrainz id'
          % (linked, 100.0 * linked / total if total else 0))
    print('%d rows are announced lineups for editions that were cancelled'
          % sum(1 for line in open(path, encoding='utf-8') if '"happened": false' in line))
    print('%d distinct artist names' % len({
        json.loads(line)['artist'].lower() for line in open(path, encoding='utf-8')}))


if __name__ == '__main__':
    main()
