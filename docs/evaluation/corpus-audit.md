# Corpus audit

A random sample of 100 rows from data/corpus/appearances.jsonl, read one
by one. Drawn with `--sample 100 --seed 440`, so the same rows come back.

## What this does and does not establish

Each row was judged on three things: whether the name is a musical act at
all, whether the festival is one that act would plausibly play, and whether
the year is right. Where a row could be settled against a second source it
was — seven rows were read back against the article or the cached setlists
they came from, which is how both of the errors below were found.

For small acts the evidence is the festival's own lineup table and nothing
more. That table is where the error we found was *not*: corpus-fidelity.md
shows every row is a faithful reading of its source, so what is left here is
the question of whether the source is right, and for an uncontroversial list
copied off a poster it usually is. A row that could not be settled is
recorded as unknown and left out of the figure rather than counted as
correct — with a sample this size one such row moves the number by a point.

- rows drawn: **100**
- rows decided: **100**
- correct: **98**
- precision: **98%** (95% interval 93-99%)

## What was wrong

| festival | year | artist | source | verdict | note |
|---|---|---|---|---|---|
| Lollapalooza | 2020 | Sofia Portanet | wikipedia | wrong-festival | "Lollapalooza Berlin 2020, not Chicago; the heading read ""Lollapalooza Berlin (Canceled)"" and the trailing note defeated the edition test — found by this audit, now fixed" |
| Sick New World | 2022 | Snoop Dogg | setlistfm | wrong-festival | Lovers & Friends, 30 April 2022, at the same Las Vegas field; Sick New World did not exist until 2023 — found by this audit, now scoped to 2023-2026 |

