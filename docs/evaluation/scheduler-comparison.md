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

**Reading it: they tie.** On all three festivals, with the value function calibrated correctly,
greedy and the exact method choose the same schedule. That is an honest negative result and
worth stating plainly rather than burying.

Why they tie: these lineups are forgiving. Sets are short relative to the gaps between them,
so taking the best-scoring set rarely blocks a better combination later — the case where
greedy fails. It does exist (one long mediocre set shutting out two good short ones), but it
does not arise often enough in this data to separate the two.

Why keep the exact method anyway. It cannot be beaten, by construction, so no future lineup
will embarrass it — whereas greedy's failure is a property of the data, not of the algorithm,
and denser festivals with longer sets would expose it. It also removed the repair pass that
greedy needed to patch the holes it left, which is less code and one fewer thing to explain.

**The calibration mattered more than the algorithm.** The value of a set is its match score
times its length, plus a small bonus per minute so that watching something beats watching
nothing. That bonus was first set at 0.004 per minute — worth roughly 24 points of match
quality per hour — and it quietly took over the objective: a 37% set five minutes longer than
a 41% set won the slot. Measured against greedy at that setting, the exact method appeared to
win by two sets and an hour of music. It was not winning; it was exploiting a bad objective.

At 0.0005 per minute, about three points an hour, the bonus breaks ties without overruling
taste, and the two methods agree. The lesson is that the objective function deserved more
scrutiny than the search strategy.

Both schedulers are kept in `analytics/app/scheduler.py`: `choose_greedy` as the baseline,
`choose_best` as the one the application uses.
