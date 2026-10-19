"""
Load the historical corpus into PostgreSQL.

    analytics/.venv/bin/python db/load_corpus.py
    analytics/.venv/bin/python db/load_corpus.py --dry-run

Reads data/corpus/appearances.jsonl and artists.jsonl — the raw crawl and the
MusicBrainz identities resolved from it — and fills the star schema the
analytics side reads: dim_artist, dim_festival, dim_festival_edition,
dim_stage, dim_date and fact_performance.

Run db/migrations/001_corpus.sql first. Safe to run repeatedly: the dimension
tables are upserts keyed on something stable, and the historical performances
are deleted and rewritten, so a second run leaves the same database behind.

Three things about this load are worth knowing before reading the code.

**It merges rather than replaces.** The database already holds 139 artists and
three festivals, hand-entered for the demo and carrying the Last.fm tags the
recommender runs on. Those rows have no MusicBrainz id, so a corpus artist is
matched to them by lowercased name — the convention the existing rows actually
use — and the id is adopted onto the row that is already there. Getting this
wrong would not fail loudly; it would quietly double every artist in the table
and leave the recommender reading one copy and the lineup page the other.

**A cancelled edition is loaded, and flagged.** Rows for a lineup that was
announced and then called off are kept, with dim_festival_edition.happened set
false, because the booking happened even though the festival did not.

**Stage rank is measured, not read off the name.** dim_stage.size_rank drives
the rising measure, and no rule on the wording can find the main stage:
Glastonbury's is the Pyramid Stage, Bonnaroo's is What Stage, and plenty of
sponsor-named stages are the biggest thing at their festival. So the stages of
a festival are ranked by the standing of the artists who played them — the
stage with the most-booked names is rank 1. That is a fact about the booking
rather than a guess about the wording.
"""
import collections
import datetime
import json
import os
import re
import sys

import psycopg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'corpus')
DSN = os.environ.get('FESTIMIZE_DSN',
                     'postgresql://festimize:festimize@localhost:5432/festimize')


def normalise(name):
    """
    Lowercased, as the rows already in dim_artist are.

    The schema comment says punctuation is stripped as well, and the seeds do
    not do it — "harm's way" and "static-x" are in there with their
    punctuation. The convention that exists wins over the one that was
    documented, because matching the rows already in the table is the whole
    point of normalising.
    """
    return re.sub(r'\s+', ' ', (name or '').strip()).lower()


def read(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        sys.exit('%s is missing — run corpus/resolve.py first' % path)
    if name.endswith('.jsonl'):
        return [json.loads(line) for line in open(path, encoding='utf-8') if line.strip()]
    return json.load(open(path, encoding='utf-8'))


def places(rows):
    """
    {festival: (country, city)} for the festivals read from setlist.fm.

    Every setlist carries its venue's city and country, so the festivals read
    that way can say where they are. The ones read from Wikipedia cannot, and
    are left null rather than guessed at.
    """
    import glob
    seen = collections.defaultdict(collections.Counter)
    dated = {(row['festival'], row.get('date')) for row in rows if row.get('date')}
    by_date = collections.defaultdict(set)
    for festival, date in dated:
        by_date[date].add(festival)
    for path in glob.glob(os.path.join(ROOT, 'corpus', '.cache', 'setlistfm-*.json')):
        try:
            held = json.load(open(path, encoding='utf-8'))
        except ValueError:
            continue
        for entry in (held.get('setlists', held) if isinstance(held, dict) else held):
            date = entry.get('eventDate') or ''
            parts = date.split('-')
            if len(parts) != 3:
                continue
            iso = '%s-%s-%s' % (parts[2], parts[1], parts[0])
            city = ((entry.get('venue') or {}).get('city') or {})
            where = (((city.get('country') or {}).get('code')), city.get('name'))
            for festival in by_date.get(iso, ()):
                seen[festival][where] += 1
    return {festival: found.most_common(1)[0][0] for festival, found in seen.items()}


def stage_ranks(rows):
    """
    {(festival, stage): rank} — 1 is the stage with the biggest names on it.

    Standing is an artist's total appearances across the whole corpus, which is
    a reasonable stand-in for how big a name they were at the time and needs no
    outside data. A stage's rank is the mean standing of everyone who played
    it, biggest first.
    """
    standing = collections.Counter(row['artist'] for row in rows)
    weight = collections.defaultdict(list)
    for row in rows:
        if row.get('stage'):
            weight[(row['festival'], row['stage'])].append(standing[row['artist']])
    by_festival = collections.defaultdict(list)
    for (festival, stage), found in weight.items():
        by_festival[festival].append((sum(found) / float(len(found)), stage))
    ranks = {}
    for festival, stages in by_festival.items():
        for place, (_, stage) in enumerate(sorted(stages, reverse=True), 1):
            ranks[(festival, stage)] = place
    return ranks


def main():
    dry = '--dry-run' in sys.argv
    rows = read('appearances.jsonl')
    artists = read('artists.jsonl')
    keys = read('artist-keys.json')
    print('%d appearance rows, %d artists, %d names mapped'
          % (len(rows), len(artists), len(keys)))

    where = places(rows)
    ranks = stage_ranks(rows)
    print('%d festivals located from setlist.fm, %d stages ranked'
          % (len(where), len(ranks)))

    if dry:
        print('dry run — nothing written')
        return 0

    with psycopg.connect(DSN, autocommit=False) as db:
        cur = db.cursor()

        # ------------------------------------------------------------ artists
        # Adopt a MusicBrainz id onto an existing row of the same name before
        # inserting anything, so the demo artists and their tags keep their
        # identity and gain a history rather than being shadowed by a copy.
        cur.execute('SELECT artist_id, name_normalized, mbid FROM dim_artist')
        held = {}
        for artist_id, name, mbid in cur.fetchall():
            held[name] = (artist_id, mbid)
        adopted = inserted = 0
        for record in sorted(artists, key=lambda r: -r['appearances']):
            name = normalise(record['name'])
            mbid = record.get('mbid')
            if name in held and held[name][1] is None and mbid:
                cur.execute("""UPDATE dim_artist
                                  SET mbid = %s,
                                      disambiguation = COALESCE(disambiguation, %s),
                                      country = COALESCE(country, %s),
                                      formed_year = COALESCE(formed_year, %s)
                                WHERE artist_id = %s
                                  AND NOT EXISTS (SELECT 1 FROM dim_artist
                                                   WHERE mbid = %s)""",
                            (mbid, record.get('disambiguation'), record.get('country'),
                             record.get('formed_year'), held[name][0], mbid))
                if cur.rowcount:
                    held[name] = (held[name][0], mbid)
                    adopted += 1
                    continue
            if name in held:
                continue
            cur.execute("""INSERT INTO dim_artist
                               (mbid, name, name_normalized, disambiguation,
                                country, formed_year)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           ON CONFLICT DO NOTHING
                           RETURNING artist_id""",
                        (mbid, record['name'], name, record.get('disambiguation'),
                         record.get('country'), record.get('formed_year')))
            got = cur.fetchone()
            if got:
                held[name] = (got[0], mbid)
                inserted += 1
        print('artists: %d new, %d existing rows adopted a MusicBrainz id'
              % (inserted, adopted))

        cur.execute('SELECT name_normalized, artist_id FROM dim_artist')
        artist_id = dict(cur.fetchall())
        by_key = {record['artist_key']: record['name'] for record in artists}

        # ---------------------------------------------------------- festivals
        cur.execute('SELECT name, festival_id FROM dim_festival')
        festival_id = dict(cur.fetchall())
        for festival in sorted({row['festival'] for row in rows}):
            country, city = where.get(festival, (None, None))
            if festival in festival_id:
                cur.execute("""UPDATE dim_festival
                                  SET country = COALESCE(country, %s),
                                      city = COALESCE(city, %s)
                                WHERE festival_id = %s""",
                            (country, city, festival_id[festival]))
                continue
            cur.execute("""INSERT INTO dim_festival (name, country, city)
                           VALUES (%s, %s, %s) RETURNING festival_id""",
                        (festival, country, city))
            festival_id[festival] = cur.fetchone()[0]
        print('festivals: %d in the table' % len(festival_id))

        # ----------------------------------------------------------- editions
        spans = collections.defaultdict(list)
        cancelled = {}
        for row in rows:
            key = (row['festival'], row['year'])
            cancelled[key] = cancelled.get(key, True) and row.get('happened', True)
            if row.get('date'):
                spans[key].append(row['date'])
        for (festival, year) in sorted(spans.keys() | cancelled.keys()):
            dates = sorted(spans.get((festival, year), []))
            cur.execute("""INSERT INTO dim_festival_edition
                               (festival_id, year, start_date, end_date, happened)
                           VALUES (%s, %s, %s, %s, %s)
                           ON CONFLICT (festival_id, year) DO UPDATE
                               SET start_date = COALESCE(dim_festival_edition.start_date,
                                                         EXCLUDED.start_date),
                                   end_date = COALESCE(dim_festival_edition.end_date,
                                                       EXCLUDED.end_date),
                                   happened = EXCLUDED.happened""",
                        (festival_id[festival], year,
                         dates[0] if dates else None, dates[-1] if dates else None,
                         cancelled[(festival, year)]))
        cur.execute("""SELECT f.name, e.year, e.edition_id
                         FROM dim_festival_edition e
                         JOIN dim_festival f USING (festival_id)""")
        edition_id = {(name, year): eid for name, year, eid in cur.fetchall()}
        print('editions: %d in the table' % len(edition_id))

        # ------------------------------------------------------------- stages
        for (festival, stage), rank in sorted(ranks.items()):
            cur.execute("""INSERT INTO dim_stage (festival_id, name, size_rank)
                           VALUES (%s, %s, %s)
                           ON CONFLICT (festival_id, name) DO UPDATE
                               SET size_rank = EXCLUDED.size_rank""",
                        (festival_id[festival], stage, rank))
        cur.execute("""SELECT f.name, s.name, s.stage_id
                         FROM dim_stage s JOIN dim_festival f USING (festival_id)""")
        stage_id = {(festival, stage): sid for festival, stage, sid in cur.fetchall()}
        print('stages: %d in the table' % len(stage_id))

        # -------------------------------------------------------------- dates
        days = {row['date'] for row in rows if row.get('date')}
        for day in sorted(days):
            when = datetime.date(*(int(p) for p in day.split('-')))
            cur.execute("""INSERT INTO dim_date (date_id, date, year, month, day,
                                                 day_of_week)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           ON CONFLICT (date_id) DO NOTHING""",
                        (int(day.replace('-', '')), when, when.year, when.month,
                         when.day, when.isoweekday()))
        print('dates: %d days' % len(days))

        # ------------------------------------------------------- performances
        # One row per artist per edition per stage. The corpus can hold the
        # same artist twice in a year — two stages, or two sources agreeing —
        # so the key is formed here rather than left to the database, whose
        # unique index cannot see two NULL set times as equal.
        want, skipped = {}, collections.Counter()
        for row in rows:
            name = normalise(keys.get(row['artist']) and by_key.get(keys[row['artist']])
                             or row['artist'])
            who = artist_id.get(name) or artist_id.get(normalise(row['artist']))
            if not who:
                skipped['no artist row'] += 1
                continue
            edition = edition_id.get((row['festival'], row['year']))
            if not edition:
                skipped['no edition'] += 1
                continue
            stage = stage_id.get((row['festival'], row.get('stage')))
            key = (who, edition, stage or 0)
            best = want.get(key)
            if best is None or row.get('confidence', 0) > best.get('confidence', 0):
                want[key] = dict(row, _artist=who, _edition=edition, _stage=stage)
        print('performances: %d unique of %d rows%s'
              % (len(want), len(rows),
                 '' if not skipped else ', skipped ' + ', '.join(
                     '%d %s' % (n, why) for why, n in skipped.most_common())))

        # The historical rows are replaced wholesale rather than merged. COPY
        # cannot skip a conflict, and the unique index added for these rows
        # means a second run otherwise dies on the first duplicate — which it
        # did, the first time this was run twice. Deleting by "has no set time"
        # is exactly the corpus: every hand-entered demonstration row has one,
        # so the demo lineups and any plan built on them are untouched. It also
        # clears rows a re-read no longer supports, which a merge would leave
        # behind for ever.
        cur.execute('DELETE FROM fact_performance WHERE starts_at IS NULL')
        print('performances: %d historical rows cleared before the load' % cur.rowcount)

        with cur.copy("""COPY fact_performance
                             (artist_id, edition_id, stage_id, date_id, is_headliner,
                              source, confidence)
                         FROM STDIN""") as copy:
            for row in want.values():
                copy.write_row((row['_artist'], row['_edition'], row['_stage'],
                                int(row['date'].replace('-', '')) if row.get('date') else None,
                                bool(row.get('headliner')), row['source'],
                                row.get('confidence', 1.0)))
        db.commit()

        for table in ('dim_artist', 'dim_festival', 'dim_festival_edition',
                      'dim_stage', 'dim_date', 'fact_performance'):
            cur.execute('SELECT count(*) FROM ' + table)
            print('  %-22s %d rows' % (table, cur.fetchone()[0]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
