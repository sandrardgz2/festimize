# Is there a signal on a new artist?

The first backtest found nothing that beat recency on artists with one or
two years of history — and that is 85%% of the corpus. This asks whether a
new name carries information outside its own history. Method and reasoning
in `docs/evaluation/newcomer_signals.py`.

- trained on: 2015, 2016, 2017, 2018, 2019, 2022
- judged on: 2023, 2024, 2025
- cohort: 2325 artists with at most 2 years of history, not already arrived,
  **all of them booked in 2022** — so none of them wins on being recent and the
  question is which of two equally recent new acts is the one to watch

| signal | rank correlation | strongest quarter in the top decile | lift over chance | strongest quarter booked at all |
|---|---|---|---|---|
| share of the last training year (baseline) | 0.221 | 18% | 1.8x | 48% |
| breadth (distinct festivals) | 0.209 | 18% | 1.9x | 53% |
| company (calibre of the bills) | 0.142 | 15% | 1.6x | 47% |
| company (direction of the bills) | -0.031 | 9% | 0.9x | 36% |
| asked back by the same festival | 0.041 | 11% | 1.1x | 40% |
| selectivity (bills of established acts) | 0.143 | 15% | 1.6x | 48% |
| stage (played the main stage) | 0.096 | 12% | 1.2x | 43% |
| all of them, ranked and averaged | 0.161 | 17% | 1.7x | 49% |

Nothing beats the 0.221 baseline. Within a cohort this tightly matched on
recency, none of these tells one new act from another.

## Asking it as a breakout instead

Mean share of the test years is noisy for a small artist, and it is not what
a badge claims. So: of these new names, which went on to three or more
bookings in 2023-2025? 255 of 2325 did, 11%, against 39% who were booked at
all. A badge on the strongest quarter is right as often as the last column
says, against a 11% base rate.

| signal | AUC | strongest quarter that broke out | lift over chance |
|---|---|---|---|
| share of the last training year | 0.635 | 20% | 1.8x |
| breadth (distinct festivals) | 0.633 | 20% | 1.9x |
| company (calibre of the bills) | 0.618 | 17% | 1.5x |
| company (direction of the bills) | 0.516 | 11% | 1.0x |
| asked back by the same festival | 0.511 | 11% | 1.0x |
| selectivity (bills of established acts) | 0.621 | 17% | 1.5x |
| stage (played the main stage) | 0.536 | 14% | 1.2x |

An AUC of 0.5 is a coin flip and 1.0 is perfect. Nothing here reaches 0.64.
The best signal available on a new artist takes a badge from being right
about one name in nine to about one in five — and it is **breadth**, which
is to say the number of festivals they played, which is a fact the page can
simply show. The model adds nothing the user could not read for themselves.

