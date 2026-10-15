# Moving up the bill, against playing more festivals

The original design measured rising as stage promotion. What shipped measures
a growing share of festivals, and the substitution was never tested. This
tests it: trained on 2015, 2016, 2017, 2018, 2019, 2022, judged on 2023, 2024, 2025.
Method, and the circularity it has to avoid, in `docs/evaluation/stage_backtest.py`.

- artists with a readable billing position in the training years: **5321**
- of those, enough years to see a direction: **1272**
- artists the share measure can speak about at all: **1615**

## Artists with three or more years of history

| measure | artists judged | rank correlation | strongest quarter in the top decile | lift over chance | strongest quarter booked at all |
|---|---|---|---|---|---|
| fame (baseline) | 669 | -0.032 | 4% | 0.5x | 34% |
| recency (baseline) | 669 | 0.296 | 16% | 1.6x | 56% |
| share growth — what shipped | 669 | 0.278 | 18% | 1.9x | 59% |
| billing position now | 364 | 0.040 | 14% | 1.3x | 48% |
| moving up the bill | 229 | 0.079 | 14% | 1.3x | 57% |

Moving up the bill (0.079) does not beat recency (0.296), so on this
population it carries no information that knowing they played lately
does not already carry.

## Every artist the measures can reach

| measure | artists judged | rank correlation | strongest quarter in the top decile | lift over chance | strongest quarter booked at all |
|---|---|---|---|---|---|
| fame (baseline) | 9666 | 0.095 | 20% | 1.6x | 31% |
| recency (baseline) | 9666 | 0.319 | 27% | 2.2x | 41% |
| share growth — what shipped | 9666 | 0.276 | 26% | 2.1x | 40% |
| billing position now | 4518 | 0.117 | 17% | 1.3x | 29% |
| moving up the bill | 756 | 0.079 | 15% | 1.3x | 43% |

Moving up the bill (0.079) does not beat recency (0.319), so on this
population it carries no information that knowing they played lately
does not already carry.

