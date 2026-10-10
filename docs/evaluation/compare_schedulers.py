import sys
sys.path.insert(0, '/Users/sandra/PennState/festimize/analytics')
from collections import defaultdict
from sqlalchemy import create_engine, text
from app.scheduler import Candidate, choose_greedy, choose_best

url = open('/Users/sandra/PennState/festimize/analytics/.env').read().strip().split('=', 1)[1]
SQL = """
select p.performance_id, a.artist_id, p.starts_at, p.ends_at, a.name, s.name as stage,
       coalesce(sc.match_score, 0) as score,
       exists(select 1 from user_artist ua where ua.user_id=:u and ua.artist_id=a.artist_id) as is_pick
from fact_performance p join dim_artist a using (artist_id) join dim_stage s using (stage_id)
left join artist_score sc on sc.artist_id=a.artist_id and sc.user_id=:u
where p.edition_id=:e order by p.starts_at"""

with create_engine(url).begin() as c:
    u = c.execute(text("select user_id from app_user order by user_id limit 1")).scalar()
    for e, label in ((1, 'Bloodstock Open Air 2027'), (2, 'Ravenstone Festival 2027'), (3, 'Sick New World 2027')):
        days = defaultdict(list)
        for r in c.execute(text(SQL), {'u': u, 'e': e}):
            days[r.starts_at.date()].append(Candidate(r.performance_id, r.artist_id, r.name, r.stage,
                                                      r.starts_at, r.ends_at, float(r.score), r.is_pick))
        out = {}
        for name, sel in (('greedy', lambda cs: [(x, x.starts_at) for x in choose_greedy(cs)]),
                          ('exact', choose_best)):
            sets = mins = dead = 0
            quality = 0.0
            for day, cs in sorted(days.items()):
                chosen = sorted(sel(cs), key=lambda t: t[1])
                sets += len(chosen)
                for cand, arrive in chosen:
                    m = (cand.ends_at - arrive).total_seconds() / 60
                    mins += m
                    quality += cand.score * m / 60
                if chosen:
                    span = (chosen[-1][0].ends_at - chosen[0][1]).total_seconds() / 60
                    dead += span - sum((x.ends_at - a).total_seconds() / 60 for x, a in chosen)
            out[name] = (sets, mins, dead, quality)
        for name in ('greedy', 'exact'):
            s, m, d, q = out[name]
            print('%-26s %-7s sets %2d  music %2dh %02dm  dead %2dh %02dm  quality %.2f'
                  % (label, name, s, m // 60, m % 60, d // 60, d % 60, q))
