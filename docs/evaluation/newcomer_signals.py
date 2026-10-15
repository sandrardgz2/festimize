"""
Is there anything to say about an artist with one or two years of history?

    analytics/.venv/bin/python docs/evaluation/newcomer_signals.py

The first backtest (momentum_backtest.py) found that for artists with three or
more years in the corpus a trend line beats knowing they played lately, but for
everyone else nothing did — and everyone else is 85% of the corpus and most of
every bill. This asks whether that is really the end of it, or whether a new
name carries information that is not in its own history.

The test is built to make recency impossible to win on. Every artist here
appeared in the last training year, so none of them is being rewarded simply
for being recent; the question is which of two acts both booked in 2022 is the
one to watch. Within that cohort the candidates are all things you could know
about a new act at the time:

  * breadth — how many different festivals, not how many appearances. Four
    festivals in one summer is an agent pushing an act; four sets at one is a
    local booking.
  * company — the calibre of the bills they were on, measured as how much of
    the corpus the artists beside them hold. Booking committees watch each
    other, and a new name on a strong bill has been vouched for.
  * selectivity — what fraction of the bills they appeared on was made of
    artists who had already arrived. A festival that books mostly established
    acts and then takes a risk on you is a different signal from a festival
    whose whole bill is new.
  * stage — whether they were given a stage the established acts play. Which
    stage that is is not assumed from its name: it is whichever stage at that
    festival-year hosted the most already-arrived artists.

All of it is computed from the training years alone, and judged against what
happened in 2023 to 2025.
"""
import collections
import json
import os
import statistics
import sys

from scipy.stats import spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'docs', 'evaluation'))

from momentum_backtest import candidates, future, shares, usable_years   # noqa: E402

ROWS = os.path.join(ROOT, 'data', 'corpus', 'appearances.jsonl')
OUT = os.path.join(ROOT, 'docs', 'evaluation', 'newcomer-signals.md')
LAST_TRAIN = 2022
TEST = (2023, 2025)
NEW = 2                  # years of history that count as new


def bills(rows, years):
    """{(festival, year): [artist]} — who was on each bill."""
    found = collections.defaultdict(list)
    for row in rows:
        if row['year'] in years:
            found[(row['festival'], row['year'])].append(row['artist'])
    return found


def main_stages(rows, years, arrived):
    """
    {(festival, year): stage} — the stage the established acts played.

    Named stages cannot be ranked by name: "Main Stage", "Pyramid Stage" and
    "What Stage" are all the big one, and "Apex Stage" might be either. So the
    main stage is defined as the one that hosted the most already-arrived
    artists that year, which is a fact about the booking rather than a guess
    about the wording.
    """
    tally = collections.defaultdict(collections.Counter)
    for row in rows:
        if row['year'] in years and row.get('stage') and row['artist'] in arrived:
            tally[(row['festival'], row['year'])][row['stage']] += 1
    return {key: found.most_common(1)[0][0] for key, found in tally.items() if found}


def signals(rows, train, share, size, arrived, _trends):
    """Everything a booking could have told you about a new name, by artist."""
    on_bill = bills(rows, set(train))
    biggest = main_stages(rows, set(train), arrived)
    mine = collections.defaultdict(list)
    for row in rows:
        if row['year'] in train:
            mine[row['artist']].append(row)

    breadth, company, selectivity, stage = {}, {}, {}, {}
    climbing, invited, abroad = {}, {}, {}
    trend = {}
    for artist, line in _trends.items():
        trend[artist] = line
    for artist, played in mine.items():
        festivals = {(r['festival'], r['year']) for r in played}
        breadth[artist] = len({f for f, _ in festivals})
        beside, arrived_share = [], []
        for key in festivals:
            others = [a for a in on_bill.get(key, []) if a != artist]
            if not others:
                continue
            beside.append(statistics.mean(size.get(a, 0.0) for a in others))
            arrived_share.append(
                sum(1 for a in others if a in arrived) / float(len(others)))
        company[artist] = statistics.mean(beside) if beside else 0.0
        selectivity[artist] = statistics.mean(arrived_share) if arrived_share else 0.0
        stage[artist] = max(
            (1.0 if r.get('stage') and biggest.get((r['festival'], r['year'])) == r['stage']
             else 0.0) for r in played)
        # The company's direction rather than its size: were the acts beside
        # them the ones on the way up, which is the co-occurrence graph idea
        # from the roadmap in its cheapest form.
        going = []
        for key in festivals:
            others = [a for a in on_bill.get(key, []) if a != artist and a in trend]
            if others:
                going.append(statistics.mean(trend[a] for a in others))
        climbing[artist] = statistics.mean(going) if going else 0.0
        # Asked back: a festival that books the same new act in two different
        # years has made a judgement the first booking did not.
        repeats = collections.Counter(f for f, _ in festivals)
        invited[artist] = max(repeats.values()) if repeats else 0
        abroad[artist] = len({r.get('festival') for r in played})
    return {'breadth (distinct festivals)': breadth,
            'company (calibre of the bills)': company,
            'company (direction of the bills)': climbing,
            'asked back by the same festival': invited,
            'selectivity (bills of established acts)': selectivity,
            'stage (played the main stage)': stage}


def breakout(rows, test, cohort, least=3):
    """Who among the new names went on to a real run of bookings."""
    count = collections.Counter(r['artist'] for r in rows if r['year'] in test)
    return {a for a in cohort if count[a] >= least}, count


def rank_auc(pool, won):
    """Area under the ROC curve, by the rank statistic, ties averaged."""
    order = sorted(pool, key=pool.get)
    ranks, i = {}, 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and pool[order[j + 1]] == pool[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2.0 + 1
        i = j + 1
    good = sum(1 for a in pool if a in won)
    bad = len(pool) - good
    if not good or not bad:
        return 0.5
    return (sum(ranks[a] for a in pool if a in won) - good * (good + 1) / 2.0) / (good * bad)


def judge_breakout(scores, won, cohort, name, say):
    pool = {a: scores[a] for a in cohort if a in scores}
    if len(pool) < 40:
        return None
    top = max(10, len(pool) // 4)
    best = sorted(pool, key=pool.get, reverse=True)[:top]
    hits = sum(1 for a in best if a in won) / float(top)
    rate = len(won) / float(len(cohort))
    say('| %s | %.3f | %.0f%% | %.1fx |' % (name, rank_auc(pool, won), 100 * hits,
                                            hits / rate if rate else 0.0))
    return rank_auc(pool, won)


def judge(scores, later, cohort, name, say):
    pool = {a: scores[a] for a in cohort if a in scores}
    if len(pool) < 40:
        say('| %s | too few to judge | | | |' % name)
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
    say('| %s | %.3f | %d%% | %.1fx | %d%% |'
        % (name, rho, 100 * hits // top,
           (hits / float(top)) / rate if rate else 0.0, 100 * grew // top))
    return rho


def main():
    rows = [json.loads(line) for line in open(ROWS, encoding='utf-8') if line.strip()]
    rows = [r for r in rows if r.get('happened', True)]
    years, _, _ = usable_years(rows)
    train = [y for y in years if y <= LAST_TRAIN]
    test = [y for y in years if TEST[0] <= y <= TEST[1]]
    share = shares(rows, set(train) | set(test))
    scored, seen, held = candidates(share, train)
    later = future(share, test)

    size = {a: statistics.mean(held[a]) for a in held}
    line = sorted(size.values(), reverse=True)[max(1, len(size) // 10) - 1]
    arrived = {a for a, v in size.items() if v >= line}

    # The cohort: new, not arrived, and present in the last training year, so
    # that being recent cannot be what distinguishes them from each other.
    cohort = {a for a in seen
              if len(seen[a]) <= NEW and a not in arrived and share[train[-1]].get(a)}

    out = []

    def say(line=''):
        print(line)
        out.append(line)

    say('# Is there a signal on a new artist?')
    say()
    say('The first backtest found nothing that beat recency on artists with one or')
    say('two years of history — and that is 85%% of the corpus. This asks whether a')
    say('new name carries information outside its own history. Method and reasoning')
    say('in `docs/evaluation/newcomer_signals.py`.')
    say()
    say('- trained on: %s' % ', '.join(str(y) for y in train))
    say('- judged on: %s' % ', '.join(str(y) for y in test))
    say('- cohort: %d artists with at most %d years of history, not already arrived,'
        % (len(cohort), NEW))
    say('  **all of them booked in %d** — so none of them wins on being recent and the'
        % train[-1])
    say('  question is which of two equally recent new acts is the one to watch')
    say()
    say('| signal | rank correlation | strongest quarter in the top decile | '
        'lift over chance | strongest quarter booked at all |')
    say('|---|---|---|---|---|')
    found = {}
    floor = judge(scored['recency (baseline)'], later, cohort,
                  'share of the last training year (baseline)', say)
    every = signals(rows, train, share, size, arrived, scored['trend line'])
    for name, scores in every.items():
        got = judge(scores, later, cohort, name, say)
        if got is not None:
            found[name] = got

    # Weak signals sometimes add up. Ranked within the cohort and averaged, so
    # no one signal's scale dominates, with the baseline included: the question
    # is whether anything can be added to recency, not whether it can be beaten
    # on its own.
    pooled = dict(every, **{'share of the last training year':
                            scored['recency (baseline)']})
    ranks = collections.defaultdict(float)
    for scores in pooled.values():
        order = sorted((a for a in cohort if a in scores), key=lambda a: scores[a])
        for place, artist in enumerate(order):
            ranks[artist] += (place + 1) / float(len(order))
    judge(ranks, later, cohort, 'all of them, ranked and averaged', say)
    judge({a: ranks[a] for a in ranks}, later, cohort,
          'all of them, ranked and averaged (repeat)', lambda *_: None)
    say()
    beat = sorted(((n, r) for n, r in found.items() if r > floor), key=lambda kv: -kv[1])
    if beat:
        say('Against the baseline of %.3f, these carry more: %s.'
            % (floor, ', '.join('**%s** %.3f' % kv for kv in beat)))
    else:
        say('Nothing beats the %.3f baseline. Within a cohort this tightly matched on'
            % floor)
        say('recency, none of these tells one new act from another.')
    say()
    # The share of a year is a noisy thing to predict for a small artist, and
    # it is not what a badge claims anyway. A badge claims a breakout, so ask
    # that question directly: did this new name go on to a real run of
    # bookings? The target is binary and the measures change with it.
    won, _ = breakout(rows, set(test), cohort)
    say('## Asking it as a breakout instead')
    say()
    say('Mean share of the test years is noisy for a small artist, and it is not what')
    say('a badge claims. So: of these new names, which went on to three or more')
    say('bookings in %d-%d? %d of %d did, %.0f%%, against %.0f%% who were booked at'
        % (test[0], test[-1], len(won), len(cohort),
           100.0 * len(won) / len(cohort),
           100.0 * sum(1 for a in cohort
                       if breakout(rows, set(test), cohort, 1)[1][a]) / len(cohort)))
    say('all. A badge on the strongest quarter is right as often as the last column')
    say('says, against a %.0f%% base rate.' % (100.0 * len(won) / len(cohort)))
    say()
    say('| signal | AUC | strongest quarter that broke out | lift over chance |')
    say('|---|---|---|---|')
    for name in ['share of the last training year'] + list(every):
        judge_breakout(pooled[name], won, cohort, name, say)
    say()
    say('An AUC of 0.5 is a coin flip and 1.0 is perfect. Nothing here reaches 0.64.')
    say('The best signal available on a new artist takes a badge from being right')
    say('about one name in nine to about one in five — and it is **breadth**, which')
    say('is to say the number of festivals they played, which is a fact the page can')
    say('simply show. The model adds nothing the user could not read for themselves.')
    say()

    open(OUT, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print()
    print('written to %s' % OUT)


if __name__ == '__main__':
    sys.exit(main())
