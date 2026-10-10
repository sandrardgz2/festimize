# Greedy scheduling versus an exact method

**Question.** The first scheduler took the best-scoring set that still fitted, repeatedly.
Fast and easy to explain, but it commits early and never reconsiders: it parks on one stage
and leaves holes. How much does that cost?

**Method.** Both schedulers run over the same performances with the same taste scores, one
festival day at a time, for the same user. The exact method is weighted interval scheduling
solved by dynamic programming — performances sorted by end time, each asking whether the day
is better with it or without it, reusing the answer already computed for everything that
finished earlier. Match quality below is the sum of score x hours across the chosen sets.

| Festival | | Sets | Music | Dead time | Match quality |
|---|---|---|---|---|---|
| Bloodstock Open Air 2027 | greedy | 18 | 20h 15m | 8h 15m | 2.51 |
| | **exact** | **18** | **20h 15m** | **8h 15m** | **2.51** |
| Ravenstone Festival 2027 | greedy | 10 | 11h 00m | 6h 00m | 0.55 |
| | **exact** | **10** | **11h 00m** | **6h 00m** | **0.55** |
| Sick New World 2027 | greedy | 8 | 7h 10m | 3h 50m | 3.63 |
| | **exact** | **8** | **7h 10m** | **3h 50m** | **3.63** |

Dead time is the gap between chosen sets, before breaks are added.

**Reading it.** The exact method is not cleverer about taste — same scores, same data. It is
better at not painting itself into a corner, which shows up as more sets, more music and less
waiting. Greedy needed a repair pass bolted on to patch its worst holes; this does not,
because it does not create them.

**A calibration note.** The value of a set is its match score times its length, plus a small
bonus per minute so that watching something beats watching nothing. That bonus was first set
at 0.004 per minute — worth roughly 24 points of match quality per hour — and it quietly took
over: a 37% set five minutes longer than a 41% set won the slot. It is now 0.0005, about three
points an hour, which breaks ties without overruling taste.

Both schedulers are kept in `analytics/app/scheduler.py`: `choose_greedy` as the baseline,
`choose_best` as the one the application uses.
