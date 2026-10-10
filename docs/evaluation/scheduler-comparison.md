# Greedy scheduling versus an exact method

**Question.** The first scheduler took the best-scoring set that still fitted, repeatedly.
Fast and easy to explain, but it commits early and never reconsiders: it parks on one stage
and leaves holes. How much does that cost?

**Method.** Both schedulers run over the same performances with the same taste scores, one
festival day at a time, for the same user. The exact method is weighted interval scheduling
solved by dynamic programming — performances sorted by end time, each asking whether the day
is better with it or without it, reusing the answer already computed for everything that
finished earlier. Match quality below is the sum of score x hours actually watched. Dead time
is the gap between chosen sets, before breaks are added.

| Festival | | Sets | Music | Dead time | Match quality |
|---|---|---|---|---|---|
| Bloodstock Open Air 2027 | greedy | 18 | 20h 15m | 8h 15m | 2.51 |
| | **exact** | **21** | **22h 05m** | **7h 10m** | **2.55** |
| Ravenstone Festival 2027 | greedy | 10 | 11h 00m | 6h 00m | 0.55 |
| | **exact** | **11** | **12h 05m** | **4h 55m** | **0.55** |
| Sick New World 2027 | greedy | 8 | 7h 10m | 3h 50m | 3.63 |
| | **exact** | **9** | **7h 55m** | **3h 05m** | **3.99** |

**Reading it.** The exact method wins a set and 35–65 minutes of music on five of the six
festival days, and never loses one. But the reason is not the search strategy, and saying so
takes one more measurement.

**Where the win actually comes from.** Run the exact method with late joining switched off —
every set must be caught from its first minute, exactly as greedy requires — and the two
methods tie on all six days, set for set and minute for minute:

| | Sets per day (Bloodstock / Ravenstone / Sick New World) |
|---|---|
| greedy | 6, 6, 6 / 5, 5 / 8 |
| exact, no late joining | 6, 6, 6 / 5, 5 / 8 |
| exact | 7, 7, 7 / 5, 6 / 9 |

So the gain is entirely from being allowed to walk in on a set already in progress, which the
dynamic program can weigh (it asks what each set is worth *given where you already are*) and
the greedy loop cannot express. On these lineups, with whole sets only, greedy finds the
optimum every time.

A concrete case, Sick New World, Saturday 24 April. Greedy takes Deftones at 19:30 because it
is the best-scoring set available at that moment, and that single choice costs it both Bring
Me the Horizon and Slipknot. The exact method gives up Deftones, takes those two instead, and
ends the day a set ahead.

**Why keep the exact method.** It cannot be beaten, by construction, so no future lineup will
embarrass it — whereas greedy's success here is a property of this data, not of the algorithm.
It also made late joining expressible at all, and it removed the repair pass that greedy
needed to patch the holes it left, which is less code and one fewer thing to explain.

**The calibration mattered more than the algorithm.** The value of a set is its match score
times its length, plus a small bonus per minute so that watching something beats watching
nothing. That bonus was first set at 0.004 per minute — worth roughly 24 points of match
quality per hour — and it quietly took over the objective: a 37% set five minutes longer than
a 41% set won the slot. Measured at that setting the exact method appeared to win for the
wrong reason: it was exploiting a bad objective, not scheduling better. At 0.0005 per minute,
about three points an hour, the bonus breaks ties without overruling taste. Every number above
is measured at the calibrated setting.

Both schedulers are kept in `analytics/app/scheduler.py`: `choose_greedy` as the baseline,
`choose_best` as the one the application uses. `docs/evaluation/compare_schedulers.py`
reproduces this table.
