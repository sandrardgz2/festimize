"""
Does moving up the bill predict who gets booked, better than playing more?

    analytics/.venv/bin/python docs/evaluation/stage_backtest.py

The original design of this project said the rising measure would be stage
promotion: db/schema.sql still carries the comment "1 = main stage. Drives the
rising-artist measure." What shipped instead measures an artist's growing share
of the festivals in the corpus. The substitution was never tested — the first
backtest compared five candidates and stage promotion was not among them — so
this tests it properly, the same way: trained on 2015-2022, judged on who was
booked in 2023-2025, against the same two baselines.

Two problems have to be solved before the question can even be asked.

**Which stage is the big one.** Not something the name can answer: Glastonbury's
is the Pyramid Stage, Bonnaroo's is What Stage, and plenty of sponsor-named
stages are the biggest thing at their festival. So a stage's standing is the
mean standing of the artists who played it, and an artist's standing is how
much of the corpus they hold.

**That definition is circular**, and the circularity flatters exactly the
artists being scored: if a rising act plays the Dogtooth Stage, their own
presence is part of why Dogtooth ranks where it does. So every stage is ranked
twice — once normally, and once for each artist with that artist's own
appearances removed. A measure that only works when it can see itself is not
measuring anything.

And one thing that cannot be solved here: rank 1 at Furnace Fest and rank 1 at
Glastonbury are both rank 1. Billing is therefore read as a position within its
own festival — the top of a small bill is the top of a small bill — which
measures promotion through a festival rather than between festivals. An artist
who moves from Download's second stage to a village festival's main stage will
read as promoted, and that is a real limitation of this measure rather than a
bug in this script.
"""
import collections
import json
import os
import statistics
import sys

from scipy.stats import spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'docs', 'evaluation'))
sys.path.insert(0, os.path.join(ROOT, 'analytics'))

from app.momentum import slope                                          # noqa: E402
from momentum_backtest import candidates, future, shares, usable_years  # noqa: E402

ROWS = os.path.join(ROOT, 'data', 'corpus', 'appearances.jsonl')
OUT = os.path.join(ROOT, 'docs', 'evaluation', 'stage-backtest.md')
LAST_TRAIN = 2022
TEST = (2023, 2025)
ENOUGH = 3


def billing(rows, years, standing):
    """
    How high up the bill each artist was, per year, as 0..1 with 1 the top.

    A stage's standing is the mean standing of everyone on it. The stages of
    one festival-year are then ordered, and an artist's position is where the
    best stage they played sits in that order — so the top of any bill is 1.0
    and the bottom is near 0, whatever the festival is called.

    Each stage is scored without the artist being asked about, because
    including them would let a big name raise the stage that makes them look
    promoted.
    """
    weight = collections.defaultdict(lambda: [0.0, 0])          # stage -> sum, count
    mine = collections.defaultdict(lambda: [0.0, 0])            # (artist, stage) -> sum, count
    played = collections.defaultdict(set)                       # (artist, year) -> stages
    stages = collections.defaultdict(set)                       # (festival, year) -> stages
    for row in rows:
        if row['year'] not in years or not row.get('stage'):
            continue
        key = (row['festival'], row['year'], row['stage'])
        value = standing.get(row['artist'], 0.0)
        weight[key][0] += value
        weight[key][1] += 1
        mine[(row['artist'], key)][0] += value
        mine[(row['artist'], key)][1] += 1
        played[(row['artist'], row['year'])].add(key)
        stages[(row['festival'], row['year'])].add(key)

    def without(key, artist):
        """A stage's standing with this artist's own appearances taken out."""
        total, count = weight[key]
        taken, times = mine.get((artist, key), (0.0, 0))
        left = count - times
        return (total - taken) / left if left > 0 else None

    out = collections.defaultdict(dict)
    for (artist, year), found in played.items():
        best = None
        for key in found:
            here = sorted(
                (s for s in stages[(key[0], key[1])]),
                key=lambda s: (without(s, artist) if without(s, artist) is not None else -1.0))
            if len(here) < 2:
                continue                      # a one-stage festival says nothing
            where = here.index(key) / float(len(here) - 1)
            best = where if best is None else max(best, where)
        if best is not None:
            out[artist][year] = best
    return out


def main():
    rows = [json.loads(line) for line in open(ROWS, encoding='utf-8') if line.strip()]
    rows = [r for r in rows if r.get('happened', True)]
    years, _, _ = usable_years(rows)          # the backtest's version takes the raw rows
    train = [y for y in years if y <= LAST_TRAIN]
    test = [y for y in years if TEST[0] <= y <= TEST[1]]
    share = shares(rows, set(train) | set(test))
    scored, seen, held = candidates(share, train)
    later = future(share, test)

    standing = collections.Counter(r['artist'] for r in rows if r['year'] in train)
    level = billing([r for r in rows if r['year'] in train], set(train), standing)

    # Two ways to read a billing history: where they ended up, and which way
    # they were going. The first is the honest baseline for the second.
    where_now, which_way = {}, {}
    for artist, found in level.items():
        line = [found[y] for y in train if y in found]
        if not line:
            continue
        where_now[artist] = line[-1]
        if len(line) >= 2:
            which_way[artist] = slope([found.get(y, 0.0) for y in train])

    size = {a: statistics.mean(held[a]) for a in held}
    ceiling = sorted(size.values(), reverse=True)[max(1, int(len(size) * 0.1)) - 1]
    arrived = {a for a, v in size.items() if v >= ceiling}

    out = []

    def say(line=''):
        print(line)
        out.append(line)

    say('# Moving up the bill, against playing more festivals')
    say()
    say('The original design measured rising as stage promotion. What shipped measures')
    say('a growing share of festivals, and the substitution was never tested. This')
    say('tests it: trained on %s, judged on %s.'
        % (', '.join(str(y) for y in train), ', '.join(str(y) for y in test)))
    say('Method, and the circularity it has to avoid, in `docs/evaluation/stage_backtest.py`.')
    say()
    say('- artists with a readable billing position in the training years: **%d**'
        % len(where_now))
    say('- of those, enough years to see a direction: **%d**' % len(which_way))
    say('- artists the share measure can speak about at all: **%d**'
        % sum(1 for a in seen if len(seen[a]) >= ENOUGH))
    say()

    pool_all = {a for a in seen if a not in arrived}
    pool_old = {a for a in pool_all if len(seen[a]) >= ENOUGH}

    def judge(scores, name, eligible, say):
        pool = {a: scores[a] for a in eligible if a in scores}
        if len(pool) < 40:
            say('| %s | only %d artists — too few to judge | | | |' % (name, len(pool)))
            return None
        outcome = {a: later.get(a, 0.0) for a in pool}
        rho, _ = spearmanr([pool[a] for a in pool], [outcome[a] for a in pool])
        top = max(10, len(pool) // 4)
        ranked = sorted(pool, key=pool.get, reverse=True)[:top]
        cut = sorted(outcome.values(), reverse=True)[max(1, len(outcome) // 10) - 1]
        hits = sum(1 for a in ranked if outcome[a] >= cut and outcome[a] > 0)
        base = sum(1 for a in outcome if outcome[a] >= cut and outcome[a] > 0)
        rate = base / float(len(outcome))
        grew = sum(1 for a in ranked if outcome[a] > 0)
        say('| %s | %d | %.3f | %d%% | %.1fx | %d%% |'
            % (name, len(pool), rho, 100 * hits // top,
               (hits / float(top)) / rate if rate else 0.0, 100 * grew // top))
        return rho

    for label, eligible in (('Artists with three or more years of history', pool_old),
                            ('Every artist the measures can reach', pool_all)):
        say('## %s' % label)
        say()
        say('| measure | artists judged | rank correlation | strongest quarter in the '
            'top decile | lift over chance | strongest quarter booked at all |')
        say('|---|---|---|---|---|---|')
        found = {}
        for name, scores in (('fame (baseline)', scored['fame (baseline)']),
                             ('recency (baseline)', scored['recency (baseline)']),
                             ('share growth — what shipped', scored['trend line']),
                             ('billing position now', where_now),
                             ('moving up the bill', which_way)):
            got = judge(scores, name, eligible, say)
            if got is not None:
                found[name] = got
        say()
        floor = found.get('recency (baseline)', 0.0)
        shipped = found.get('share growth — what shipped', 0.0)
        stage = found.get('moving up the bill')
        if stage is None:
            say('Stage movement cannot be judged on this population.')
        elif stage > shipped and stage > floor:
            say('**Moving up the bill wins** (%.3f), against share growth at %.3f and'
                % (stage, shipped))
            say('recency at %.3f. The measure this project originally specified is the')
            say('better one.')
        elif stage > floor:
            say('Moving up the bill (%.3f) beats recency (%.3f) but not share growth'
                % (stage, floor))
            say('(%.3f). It measures something real and the shipped measure measures it'
                % shipped)
            say('better.')
        else:
            say('Moving up the bill (%.3f) does not beat recency (%.3f), so on this'
                % (stage, floor))
            say('population it carries no information that knowing they played lately')
            say('does not already carry.')
        say()

    open(OUT, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print()
    print('written to %s' % OUT)


if __name__ == '__main__':
    sys.exit(main())
