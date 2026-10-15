# What "rising" should mean

Several definitions of a rising artist are defensible. This holds back the
last three years of the corpus, computes each definition from the years
before them, and asks which one picked the artists who were in fact booked
more afterwards. The method and its exclusions are in
`docs/evaluation/momentum_backtest.py`.

- trained on: 2015, 2016, 2017, 2018, 2019, 2022
- judged on: 2023, 2024, 2025
- excluded: 2020 (2 festivals against a median of 30), 2021 (14 festivals against a median of 30), and 2026 (announced lineups, not finished festivals)

## Who is eligible

A rising badge means *ascending and not yet arrived*, so the 1073 artists in
the top tenth of the training years are held out of every candidate below.
Metallica is booked more now than in 2015 and is not news to anybody.

## Which definition predicts who gets booked
## Which definition predicts who gets booked

Each definition is judged on the artists it is for, and against both
baselines. The strongest picks are the top quarter of the eligible group or
a hundred artists, whichever is fewer.

### Artists with three or more years of history

666 eligible, after holding out the 1073 already arrived.

| definition | rank correlation | strongest picks in the top decile | lift over chance | strongest picks booked at all |
|---|---|---|---|---|
| fame (baseline) | -0.028 | 6% | 0.6x | 28% |
| recency (baseline) | 0.295 | 14% | 1.4x | 56% |
| trend line | 0.272 | 23% | 2.3x | 64% |
| recent vs prior | 0.212 | 10% | 1.0x | 45% |

**Nothing here beats recency** (0.295). On this population, how much
of last year an artist held predicts next year better than any
direction of travel computed out of their history.

### Artists with one or two years of history

9000 eligible, after holding out the 1073 already arrived.

| definition | rank correlation | strongest picks in the top decile | lift over chance | strongest picks booked at all |
|---|---|---|---|---|
| fame (baseline) | 0.046 | 26% | 2.3x | 35% |
| recency (baseline) | 0.308 | 61% | 5.4x | 74% |
| newcomer intensity | 0.298 | 61% | 5.4x | 71% |
| trend line | 0.282 | 63% | 5.5x | 78% |

**Nothing here beats recency** (0.308). On this population, how much
of last year an artist held predicts next year better than any
direction of travel computed out of their history.

### The two-case definition, over everyone it would apply to

| definition | rank correlation | strongest picks in the top decile | lift over chance | strongest picks booked at all |
|---|---|---|---|---|
| recency (baseline) | 0.317 | 62% | 5.0x | 76% |
| two-case (trajectory or newcomer) | 0.222 | 59% | 4.7x | 78% |


## How many artists each definition can speak about

| years of history in the training window | artists | share |
|---|---|---|
| 1 | 7334 | 68.3% |
| 2 | 1793 | 16.7% |
| 3 | 796 | 7.4% |
| 4 | 452 | 4.2% |
| 5 | 239 | 2.2% |
| 6 | 125 | 1.2% |

A trend line needs four points, recent-against-prior needs three, and most
artists have fewer. That is the reason the two-case definition exists: not
because it scores better, but because the alternative is a badge that is
silent on most of a lineup.
