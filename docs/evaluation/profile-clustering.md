# Does clustering the taste profile help?

**Question.** The first version averaged every saved artist into one profile. Does that
misrepresent someone whose taste splits across styles?

**Test profile.** Three doom and stoner artists (Electric Wizard, Windhand, Sleep) and three
thrash artists (Slayer, Megadeth, Testament) — a deliberate split, scored against the other
95 artists in the database using their MusicBrainz tags.

| Rank | One averaged profile | score | Two clustered profiles | score |
|---|---|---|---|---|
| 1 | Trivium | 0.30 | Grave Lines | 0.41 |
| 2 | DevilDriver | 0.30 | Trivium | 0.37 |
| 3 | Machine Head | 0.29 | DevilDriver | 0.36 |
| 4 | High on Fire | 0.29 | Machine Head | 0.35 |
| 5 | Lamb of God | 0.25 | Body Void | 0.35 |
| 6 | Grave Lines | 0.24 | High on Fire | 0.35 |
| 7 | Pantera | 0.22 | Lamb of God | 0.31 |
| 8 | Black Label Society | 0.20 | Pantera | 0.27 |
| 9 | Body Void | 0.20 | YOB | 0.26 |
| 10 | Khemmis | 0.19 | Black Label Society | 0.25 |

**Average score change across all candidates: +0.023.**

**Reading it.** Averaging pulls every score toward the middle, because no artist in the
database is simultaneously doom and thrash. Clustering scores each candidate against the side
of the profile it actually belongs to, so strong single-style matches rise and the ranking
stops rewarding artists that are vaguely both.

**Why it matters beyond this test.** Any user with range hits this — the metal and electronic
case is the obvious one, but doom versus thrash is the same mechanism at smaller scale.

Method: `analytics/app/recommender.py`, `clustered=True` (k-means over the saved artists,
one to three profiles by picks saved, each candidate keeping its best score).
