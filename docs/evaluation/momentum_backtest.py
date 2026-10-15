"""
Which definition of "rising" actually predicts who gets booked?

    analytics/.venv/bin/python docs/evaluation/momentum_backtest.py

The rising-artist score is the centre of the enhanced build, and there are
several defensible ways to compute it. Rather than choose by argument, this
holds back the last three years of the corpus, computes every candidate from
the years before them, and asks which candidate best picks the artists who
went on to be booked more.

Three decisions shape the test and each is worth stating:

  * 2020 and 2021 are excluded. The corpus holds 2 and 14 festivals in those
    years against a median of 30, so an artist's share of them is noise. They
    are not a quiet pair of years in music history; they are a hole in the
    panel, and treating them as data is how a pandemic becomes a career.
  * 2026 is excluded from the target. Those rows are announced lineups, not
    finished festivals, so a festival that has not announced yet looks like a
    festival nobody was booked at.
  * Everything is a share of its year, never a count. The corpus does not hold
    the same festivals every year — Bonnaroo's article stops in 2019, Lost
    Lands joins in 2022 — so counts rise and fall with our coverage. A share
    asks the only question that survives that: how much of the year was this
    artist?

Two baselines, both deliberately stupid, and the second one matters more than
the first. "Fame" is how many times they played before. "Recency" is how much
of the last training year they held — nothing about a direction of travel at
all. A first run of this test put a trend line and a newcomer score at the top
and both returned the identical eighteen names, every one of them an artist who
appeared in 2022 and no earlier year. They were not measuring ascent; they were
measuring who was booked lately, which predicts next year perfectly well and
tells a user nothing. Any candidate here has to beat recency to be worth having.

And each candidate is judged on the artists it is for. Pooling a band with six
years of history and a name that appeared once last summer lets recency win by
sheer numbers, because two thirds of the corpus is the second kind. So the
table is split: a trajectory is judged on artists with three or more years, a
newcomer measure on those with one or two.
"""
import collections
import json
import os
import statistics
import sys

from scipy.stats import spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROWS = os.path.join(ROOT, 'data', 'corpus', 'appearances.jsonl')
OUT = os.path.join(ROOT, 'docs', 'evaluation', 'momentum-backtest.md')

LAST_TRAIN = 2022          # the model sees nothing after this
TEST = (2023, 2025)        # and is judged on these
ANNOUNCED_ONLY = 2026      # lineups published but not yet played
TOP = 100                  # how many of each candidate's picks to inspect
# A year holding less than this much of the usual festival count is too thin to
# compare. Half was the first threshold and 2021 scraped past it at exactly the
# cut — 15 festivals against a median of 30 — so every pandemic booking counted
# double. The shipped measure uses seven tenths and so must the evidence for it.
THIN = 0.7
SMALL = 1e-6


def usable_years(rows):
    """
    The years the corpus covers well enough to compare.

    A year with a third of the usual festivals in it cannot be compared with a
    full one, whatever happened in music that year.
    """
    festivals = collections.defaultdict(set)
    for row in rows:
        festivals[row['year']].add(row['festival'])
    typical = statistics.median(len(f) for f in festivals.values())
    return (sorted(year for year, found in festivals.items()
                   if len(found) >= typical * THIN and year != ANNOUNCED_ONLY),
            {year: len(found) for year, found in festivals.items()}, typical)


def shares(rows, years):
    """share[year][artist] — the fraction of that year's bookings they held."""
    counts = collections.defaultdict(collections.Counter)
    for row in rows:
        if row['year'] in years:
            counts[row['year']][row['artist']] += 1
    return {year: {artist: n / float(sum(found.values()))
                   for artist, n in found.items()}
            for year, found in counts.items()}


# --------------------------------------------------------------- candidates
def candidates(share, train):
    """
    {name: {artist: score}} — every definition of rising, on the train years.

    Each is computed for every artist present at all; whether an artist has
    enough history for a given definition is the point of the comparison, so
    nothing is filtered out here.
    """
    artists = {a for year in train for a in share[year]}
    held = {a: [share[year].get(a, 0.0) for year in train] for a in artists}
    seen = {a: [year for year in train if share[year].get(a)] for a in artists}

    popularity, recency, slope, recent, newcomer, both = {}, {}, {}, {}, {}, {}
    middle = sum(range(len(train))) / float(len(train))
    spread = sum((i - middle) ** 2 for i in range(len(train)))
    for artist in artists:
        line = held[artist]
        popularity[artist] = sum(line)
        recency[artist] = line[-1]
        slope[artist] = sum((i - middle) * value
                            for i, value in enumerate(line)) / spread
        last_two = statistics.mean(line[-2:])
        prior_two = statistics.mean(line[-4:-2]) if len(line) >= 4 else 0.0
        recent[artist] = (last_two + SMALL) / (prior_two + SMALL)
        age = len(train) - train.index(seen[artist][0]) if seen[artist] else len(train)
        newcomer[artist] = line[-1] / float(age)
        # The two-case definition: a trajectory where there is one, and how
        # hard a new name is booking where there is not. Both halves are put on
        # one scale by ranking within their own half and splicing the ranks, so
        # the badge means the same thing wherever it appears.
        both[artist] = ('trajectory', recent[artist]) if len(seen[artist]) >= 3 \
            else ('newcomer', newcomer[artist])

    spliced = {}
    for half in ('trajectory', 'newcomer'):
        group = {a: v for a, (kind, v) in both.items() if kind == half}
        order = sorted(group, key=group.get)
        for rank, artist in enumerate(order):
            spliced[artist] = (rank + 1) / float(len(order))
    return {
        'fame (baseline)': popularity,
        'recency (baseline)': recency,
        'trend line': slope,
        'recent vs prior': recent,
        'newcomer intensity': newcomer,
        'two-case (trajectory or newcomer)': spliced,
    }, seen, held


def future(share, test):
    """mean share per test year — what actually happened next."""
    artists = {a for year in test for a in share[year]}
    return {a: statistics.mean(share[year].get(a, 0.0) for year in test)
            for a in artists}


def judge(scores, later, eligible, name, say):
    """How well one candidate picked the artists who went on to be booked."""
    pool = {a: s for a, s in scores.items() if a in eligible}
    if len(pool) < 40:
        say('| %s | too few artists to judge | | | |' % name)
        return None
    outcome = {a: later.get(a, 0.0) for a in pool}
    rho, _ = spearmanr([pool[a] for a in pool], [outcome[a] for a in pool])
    top = min(TOP, max(10, len(pool) // 4))
    ranked = sorted(pool, key=pool.get, reverse=True)[:top]
    cut = sorted(outcome.values(), reverse=True)[max(1, len(outcome) // 10) - 1]
    hits = sum(1 for a in ranked if outcome[a] >= cut and outcome[a] > 0)
    base = sum(1 for a in outcome if outcome[a] >= cut and outcome[a] > 0)
    rate = base / float(len(outcome))
    grew = sum(1 for a in ranked if outcome[a] > 0)
    say('| %s | %.3f | %d%% | %.1fx | %d%% |'
        % (name, rho, 100 * hits // top,
           (hits / float(top)) / rate if rate else 0.0, 100 * grew // top))
    return rho


def main():
    rows = [json.loads(line) for line in open(ROWS, encoding='utf-8') if line.strip()]
    rows = [r for r in rows if r.get('happened', True)]
    years, coverage, typical = usable_years(rows)
    train = [y for y in years if y <= LAST_TRAIN]
    test = [y for y in years if TEST[0] <= y <= TEST[1]]
    share = shares(rows, set(train) | set(test))

    out = []

    def say(line=''):
        print(line)
        out.append(line)

    say('# What "rising" should mean')
    say()
    say('Several definitions of a rising artist are defensible. This holds back the')
    say('last three years of the corpus, computes each definition from the years')
    say('before them, and asks which one picked the artists who were in fact booked')
    say('more afterwards. The method and its exclusions are in')
    say('`docs/evaluation/momentum_backtest.py`.')
    say()
    say('- trained on: %s' % ', '.join(str(y) for y in train))
    say('- judged on: %s' % ', '.join(str(y) for y in test))
    say('- excluded: %s'
        % ', '.join('%d (%d festivals against a median of %d)' % (y, coverage[y], typical)
                    for y in sorted(coverage)
                    if y not in years and y != ANNOUNCED_ONLY)
        + ', and %d (announced lineups, not finished festivals)' % ANNOUNCED_ONLY)
    say()

    scored, seen, held = candidates(share, train)
    later = future(share, test)

    # "Not yet arrived": an artist in the top tenth of the train years is
    # already a name the user knows, and a badge on them tells nobody anything.
    size = {a: statistics.mean(held[a]) for a in held}
    line = sorted(size.values(), reverse=True)[max(1, len(size) // 10) - 1]
    arrived = {a for a, v in size.items() if v >= line}
    say('## Who is eligible')
    say()
    say('A rising badge means *ascending and not yet arrived*, so the %d artists in'
        % len(arrived))
    say('the top tenth of the training years are held out of every candidate below.')
    say('Metallica is booked more now than in 2015 and is not news to anybody.')
    say()

    say('## Which definition predicts who gets booked')
    say('## Which definition predicts who gets booked')
    say()
    say('Each definition is judged on the artists it is for, and against both')
    say('baselines. The strongest picks are the top quarter of the eligible group or')
    say('a hundred artists, whichever is fewer.')
    say()
    for label, established, wanted in (
            ('Artists with three or more years of history', True,
             ('fame (baseline)', 'recency (baseline)', 'trend line',
              'recent vs prior')),
            ('Artists with one or two years of history', False,
             ('fame (baseline)', 'recency (baseline)', 'newcomer intensity',
              'trend line'))):
        eligible = {a for a in seen
                    if a not in arrived and (len(seen[a]) >= 3) == established}
        say('### %s' % label)
        say()
        say('%d eligible, after holding out the %d already arrived.'
            % (len(eligible), len(arrived)))
        say()
        say('| definition | rank correlation | strongest picks in the top decile | '
            'lift over chance | strongest picks booked at all |')
        say('|---|---|---|---|---|')
        found = {}
        for name in wanted:
            got = judge(scored[name], later, eligible, name, say)
            if got is not None:
                found[name] = got
        say()
        floor = found.get('recency (baseline)', 0.0)
        beat = sorted(((n, r) for n, r in found.items()
                       if 'baseline' not in n and r > floor),
                      key=lambda kv: -kv[1])
        if beat:
            say('Beats recency (%.3f): %s. Strongest is **%s** at %.3f.'
                % (floor, ', '.join('%s %.3f' % kv for kv in beat),
                   beat[0][0], beat[0][1]))
        else:
            say('**Nothing here beats recency** (%.3f). On this population, how much'
                % floor)
            say('of last year an artist held predicts next year better than any')
            say('direction of travel computed out of their history.')
        say()
    say('### The two-case definition, over everyone it would apply to')
    say()
    say('| definition | rank correlation | strongest picks in the top decile | '
        'lift over chance | strongest picks booked at all |')
    say('|---|---|---|---|---|')
    everyone = {a for a in seen if a not in arrived}
    for name in ('recency (baseline)', 'two-case (trajectory or newcomer)'):
        judge(scored[name], later, everyone, name, say)
    say()
    say()
    say('## How many artists each definition can speak about')
    say()
    say('| years of history in the training window | artists | share |')
    say('|---|---|---|')
    spread = collections.Counter(len(seen[a]) for a in seen)
    total = sum(spread.values())
    for count in sorted(spread):
        say('| %d | %d | %.1f%% |' % (count, spread[count],
                                      100.0 * spread[count] / total))
    say()
    say('A trend line needs four points, recent-against-prior needs three, and most')
    say('artists have fewer. That is the reason the two-case definition exists: not')
    say('because it scores better, but because the alternative is a badge that is')
    say('silent on most of a lineup.')

    open(OUT, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print()
    print('written to %s' % OUT)


if __name__ == '__main__':
    sys.exit(main())
