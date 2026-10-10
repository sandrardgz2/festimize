# Greedy scheduling versus an exact method

**Question.** The first scheduler took the best-scoring set that still fitted, repeatedly.
That is fast and easy to explain, but it commits early: a 41% set ending at 20:40 can lock out
a 37% set running to 21:15 and leave an hour of standing around. How much does that cost?

**Method.** Both schedulers run over the same performances with the same taste scores, one
festival day at a time. The exact method is weighted interval scheduling solved by dynamic
programming — sets sorted by end time, each one asking whether the day is better with it or
without it, reusing the answer already computed for everything that finished earlier.

| Festival | | Sets | Music | Dead time | Picks kept |
|---|---|---|---|---|---|
| Bloodstock Open Air 2027 | greedy | 18 | 20h 15m | 8h 15m | 1 |
| | **exact** | **20** | **21h 15m** | **8h 00m** | **1** |
| Ravenstone Festival 2027 | greedy | 10 | 11h 00m | 6h 00m | 0 |
| | **exact** | **11** | **12h 00m** | **5h 00m** | **0** |
| Sick New World 2027 | greedy | 8 | 7h 10m | 3h 50m | 3 |
| | **exact** | **8** | **7h 15m** | **3h 45m** | **3** |

Dead time is the gap between chosen sets, before any breaks are added.

**Reading it.** The exact method is not cleverer about taste — it uses the same scores. It is
better at not painting itself into a corner, which shows up as more sets and less waiting.
Greedy needed a repair pass bolted on afterwards to patch the worst holes; the exact method
does not, because it does not create them.

Both are kept in `analytics/app/scheduler.py`: `choose_greedy` as the baseline, `choose_best`
as the one the application uses.
