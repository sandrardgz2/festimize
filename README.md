# Festimize

Personalized, health-aware festival scheduling. A festival lineup runs to a hundred or more
artists across overlapping stages; Festimize scores every one of them against your taste —
including artists you have never heard of — and builds a schedule that accounts for the fact
that you are a person standing in a field for three days.

IST 440W capstone, Penn State.

---

## Running it

You need Docker. Nothing else — no Java, no Python, no database.

If Docker is not already installed, get **Docker Desktop** (macOS, Windows, or Linux) from
<https://www.docker.com/products/docker-desktop/> and start it before running the commands
below. Confirm it is running with `docker info` (it should print server details, not an error).

```bash
git clone https://github.com/sandrardgz2/festimize.git
cd festimize
docker compose up --build
```

The first build takes a few minutes (it compiles the Java application, installs the Python
dependencies inside the images, and loads the full dataset into PostgreSQL on first start).
When it finishes, open **http://localhost:8080**.

Then:

1. **Register** an account — any email, nothing is sent anywhere.
2. **Setup** — tick artists you like. Ten is plenty. The page lists the artists the
   recommender can actually score (the ones that carry tags), not all 15,799 in the corpus.
3. **Lineup** — every artist at the festival, scored against your taste, best match first.
   Artists you chose yourself are marked "Your pick" rather than given a percentage.
4. **Schedule** — press *Build my schedule* for a day-by-day plan with breaks.

To stop: `docker compose down`. To wipe the database too: `docker compose down -v`.

### Checking it works

With the stack running, this registers an account, saves some artists, and builds a schedule
for all three festivals, printing what it found:

```bash
python3 smoke_test.py
```

It needs only the Python standard library. Every line should read `ok`.

### What gets created

The database loads itself on first start from `db/`: the schema (`schema.sql`), then the full
corpus (`seed_corpus.sql`). That is the entire dataset the report describes — **15,799 artists
and 39,778 performances across 36 festivals and 334 editions**, bounded to 2015–2026, assembled
from Wikipedia/Wikidata, MusicBrainz, Last.fm, and setlist.fm, and validated against
MusicBrainz — together with the artist tags and the precomputed rising-artist measure. (The
corpus is the 36 festivals listed in `corpus/festivals.txt`. The database also holds two
demonstration festivals that are not part of the corpus — Bloodstock Open Air's fabricated 2027
bill and the fictional Ravenstone — so a plain `count(*)` of the festival table returns 38.)

Most of those 334 editions are historical and can only be browsed. **Three** of them are
demonstration editions that carry hand-entered set times, so they are the ones the scheduler
can actually plan: Bloodstock Open Air 2027, Sick New World 2027, and a fictional Ravenstone
Festival 2027. They are deliberately different in character — a classic British metal bill, a
nu-metal and alternative-metal bill, and a small fictional one — so the recommender can be seen
working, and failing, against different tastes.

**The 2027 lineups are fabricated.** The artists are real and their tags come from MusicBrainz,
but these three festivals' lineups and set times were written by hand for demonstration.
Bloodstock Open Air and Sick New World are real festivals; these are not their announced
lineups, and no festival has published a 2027 bill. Set times are not machine-readable anywhere
— see `data/lineup-audit/summary.md`, which surveys twenty festivals and what their data
actually looks like.

### Reproducing the results in the report

Everything the report states can be shown from this running stack:

| Claim in the report | How to show it |
|---|---|
| Corpus scale: 15,799 artists, 39,778 performances, 36 festivals, 334 editions | `docker compose exec db psql -U festimize -d festimize -c "select (select count(*) from dim_artist) artists, (select count(*) from fact_performance) performances, (select count(*) from dim_festival) festivals, (select count(*) from dim_festival_edition) editions;"` — artists/performances/editions match the report; the festival count reads **38** because it includes the two demonstration festivals on top of the 36-festival corpus |
| Taste scoring, best match first, discoveries you did not name | the **Lineup** page, after setup |
| The rising-artist measure (15,737 artists measured) | the **Rising** badges on the lineup, and an artist's page; `select count(*) from artist_momentum;` |
| A conflict-free, paced, three-day schedule | the **Schedule** page, *Build my schedule* |
| Every behaviour the schedule tests guard | from the repo root: `docker compose run --rm --no-deps -v "$(pwd)/analytics:/srv" analytics python -m pytest tests/ -q` (54 pass, 1 skip — needs only Docker) |
| The measured design choices (clustering, exact vs. greedy) | `docs/evaluation/` — `profile-clustering.md`, `scheduler-comparison.md` |

The whole happy path can also be checked in one command (see **Checking it works** above):
`python3 smoke_test.py` registers an account, scores every demo lineup, and builds a schedule
for each, printing `ok` on every line.

---

## What is in here

| Path | What it is |
|---|---|
| `app/` | Spring Boot + Thymeleaf web application: accounts, lineup, schedule |
| `analytics/` | Python FastAPI service: taste matching and schedule building |
| `db/` | PostgreSQL schema and seed data |
| `data/lineup-audit/` | Survey of lineup data availability across twenty festivals |
| `docs/evaluation/` | Measured comparisons of design choices |
| `ROADMAP.md` | What was deliberately left out, and why |

### How the two services split

The web application never does any modelling. It asks the analytics service to score a user or
build a plan; the service writes its results to the database, and the web tier reads them back.
If the analytics service is down the pages still render — the lineup simply appears without
match percentages, with a note saying why.

**Taste matching** (`analytics/app/recommender.py`): artists become vectors over their tags,
TF-IDF weights rare tags above common ones, and a user's saved artists are clustered into one
to three taste profiles. Each artist keeps its best score across those profiles — a single
averaged profile misrepresents anyone whose taste spans styles. Measured in
`docs/evaluation/profile-clustering.md`.

**Scheduling** (`analytics/app/scheduler.py`): the best set of non-overlapping sets, solved
exactly as weighted interval scheduling by dynamic programming — every set is worth its match
score and the day is worth the sum of the sets in it, so the chosen day is provably the
highest-scoring one possible. Your own picks outrank any recommendation, one set in three is
reserved for artists you did not name, and the day is filled with music before breaks are
carved out of it: one 45-minute meal break and up to two 30-minute breathers, taken from
existing gaps where possible and from the weakest set in the window where not. An earlier
version selected greedily and needed a repair pass to patch the holes that left; the two are
measured against each other in `docs/evaluation/scheduler-comparison.md`.

---

## Running it without Docker

For development. You need JDK 21+, Python 3.9+, and a PostgreSQL database (a free
[Neon](https://neon.com) project works).

```bash
# 1. Create the tables and load the full corpus
psql "$DATABASE_URL" -f db/schema.sql
psql "$DATABASE_URL" -f db/seed_corpus.sql
# (Or, for just the 139-artist demo subset: db/seed_demo.sql + db/seed_artists_*.sql.)

# 2. Analytics service
cd analytics
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
echo "DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require" > .env
.venv/bin/python -m uvicorn app.main:app --port 8000

# 3. Web application, in another terminal
cd app
DATABASE_URL='jdbc:postgresql://HOST/DBNAME?sslmode=require' \
DB_USER=... DB_PASSWORD=... ./mvnw spring-boot:run
```

Run without Docker and the analytics service starts keyless (it is bound to `127.0.0.1`); under
Docker the two containers share an `X-Analytics-Key`. Both are handled automatically.
