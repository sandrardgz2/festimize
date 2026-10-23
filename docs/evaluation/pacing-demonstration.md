# What the pacing rules actually do to a day

The pacing rules are the hard part of the enhanced phase to show, because the
demonstration festivals are programmed sanely: Sick New World runs 11:45 to
23:15 on one day, and Bloodstock finishes at 20:15 and starts again at 10:30.
Neither the nine-hour sleep floor nor the daily music cap fires on them at the
default setting. A rule nobody can see still has to be shown to work, so it is
shown two ways: six tests in `analytics/tests/test_pacing.py` that construct
the days the demo lineups do not contain, and this — the same bill and the
same saved artists, re-solved at three different settings.

Measured 23 October 2026 against the `demo@festimize.app` account (14 saved
artists), by writing the pace to `app_user` and calling `POST /plan/{user}`.
The account was restored to its original settings afterwards and the restore
verified field by field.

| Your pace | Sick New World (1 day) | Bloodstock (3 days) |
|---|---|---|
| Moderate — 7.5 h a day | 9 sets, 7 h 25 m | 21 sets, 21 h 50 m |
| Light — 5 h a day | 5 sets, 4 h 55 m | 14 sets, 13 h 45 m |
| Light, and nothing before 13:00 | 5 sets, 4 h 55 m | 11 sets, 12 h 05 m |

## Reading it

**The cap is doing the work, not a filter.** Going from moderate to light does
not remove the last four sets of the day; it re-solves the day to fit five
hours, and the five it keeps are not the first five it had. The scheduler is
choosing the best day inside a smaller budget.

**A rule that changes nothing is reported as changing nothing.** Adding "no
sets before 13:00" to the light setting makes no difference at all to Sick New
World, because at five hours the day the solver already preferred starts after
13:00 anyway. It costs three sets at Bloodstock, which has mornings worth
attending. Neither number is rounded toward the story.

**Your own picks are never cut.** Every rule that removes a set — the cap, the
meal break, the breathers — passes over an artist the person named, and over a
set they asked for by name. Someone who came for one band stands through the
day for it. See `_carve` and the cap block in `analytics/app/scheduler.py`.

## What this does not show

These are three points on one person's taste against two bills. It is a
demonstration that the settings reach the solver and change its answer, not a
study of whether the resulting days are nicer to walk. That question needs
people, and belongs to the user study, not here.
