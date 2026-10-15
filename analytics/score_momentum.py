"""
Recompute the rising-artist measure and store it.

    analytics/.venv/bin/python analytics/score_momentum.py
    analytics/.venv/bin/python analytics/score_momentum.py --show 25

Reads the historical performances out of the database, scores every artist
with app.momentum, and writes one row per artist into artist_momentum. A batch
job rather than something the web app computes: the measure needs every
artist's whole history to rank one of them, so it cannot be done per request,
and a lineup page has to be a read.

Cancelled editions are excluded here rather than in the measure. An announced
lineup for a festival that never happened is a real fact about who was booked,
which is why those rows are kept, and it is not an appearance — counting it
would show a career continuing through a year nobody played.

Targets Python 3.9 syntax.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text          # noqa: E402

from app.momentum import RISING, score              # noqa: E402

DSN = os.environ.get('FESTIMIZE_DSN',
                     'postgresql+psycopg://festimize:festimize@localhost:5432/festimize')

HISTORY = text("""
    SELECT e.year, f.name AS festival, a.name AS artist, a.artist_id,
           a.formed_year
      FROM fact_performance p
      JOIN dim_festival_edition e USING (edition_id)
      JOIN dim_festival f USING (festival_id)
      JOIN dim_artist a USING (artist_id)
     WHERE e.happened
       AND p.starts_at IS NULL            -- historical rows; demo lineups have times
""")

STORE = text("""
    INSERT INTO artist_momentum (artist_id, momentum_score, appearances, festivals,
                                 first_year, last_year, basis, computed_at)
    VALUES (:artist_id, :score, :appearances, :festivals,
            :first_year, :last_year, :basis, now())
    ON CONFLICT (artist_id) DO UPDATE
       SET momentum_score = EXCLUDED.momentum_score,
           appearances = EXCLUDED.appearances,
           festivals = EXCLUDED.festivals,
           first_year = EXCLUDED.first_year,
           last_year = EXCLUDED.last_year,
           basis = EXCLUDED.basis,
           computed_at = EXCLUDED.computed_at
""")


def main():
    show = 0
    if '--show' in sys.argv:
        show = int(sys.argv[sys.argv.index('--show') + 1])

    engine = create_engine(DSN, pool_pre_ping=True)
    with engine.begin() as db:
        found = db.execute(HISTORY).fetchall()
        if not found:
            sys.exit('no historical performances in the database — run '
                     'db/load_corpus.py first')
        rows = [(r.year, r.festival, r.artist) for r in found]
        ids = {r.artist: r.artist_id for r in found}
        formed = {r.artist: r.formed_year for r in found if r.formed_year}
        print('%d performances, %d artists, %d with a formation year'
              % (len(rows), len(ids), len(formed)))

        scored = score(rows, formed)
        for artist, about in scored.items():
            if artist not in ids:
                continue
            db.execute(STORE, dict(about, artist_id=ids[artist],
                                   score=about['score']))

        counts = db.execute(text("""SELECT basis, count(*),
                                           count(*) FILTER (WHERE momentum_score >= :cut)
                                      FROM artist_momentum GROUP BY basis
                                     ORDER BY 2 DESC"""), {'cut': RISING}).fetchall()
        print()
        for basis, total, strong in counts:
            print('  %-12s %6d artists, %d above the badge threshold'
                  % (basis, total, strong))

        if show:
            print()
            top = db.execute(text("""
                SELECT a.name, m.momentum_score, m.appearances, m.festivals,
                       m.first_year, m.last_year, m.basis, a.formed_year
                  FROM artist_momentum m JOIN dim_artist a USING (artist_id)
                 WHERE m.basis = 'trajectory' AND m.festivals >= 3
                 ORDER BY m.momentum_score DESC LIMIT :n"""), {'n': show}).fetchall()
            print('%-28s %6s %5s %5s %-10s %s'
                  % ('rising', 'score', 'appr', 'fest', 'years', 'formed'))
            for r in top:
                print('%-28s %6.3f %5d %5d %-10s %s'
                      % (r.name[:28], r.momentum_score, r.appearances, r.festivals or 0,
                         '%d-%d' % (r.first_year, r.last_year), r.formed_year or '?'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
