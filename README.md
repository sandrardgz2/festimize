# Festimize

Personalized, health-aware festival scheduling. A festival lineup runs to a hundred or more
artists across overlapping stages; Festimize scores every one of them against your taste —
including artists you have never heard of — and builds a schedule that accounts for the fact
that you are a person standing in a field for three days.

IST 440W capstone, Penn State.

---

## Running it

You need Docker. Nothing else — no Java, no Python, no database.

```bash
git clone https://github.com/sandrardgz2/festimize.git
cd festimize
docker compose up --build
```

The first build takes a few minutes (it compiles the Java application and installs the Python
dependencies inside the images). When it finishes, open **http://localhost:8080**.

Then:

1. **Register** an account — any email, nothing is sent anywhere.
2. **Setup** — tick artists you like. Ten is plenty; 139 are loaded.
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

The database loads itself on first start from `db/`: the schema, three demonstration festival
editions with set times, and 139 real artists with tags verified against MusicBrainz.

The three editions are deliberately different in character — a classic British metal bill, a
small fictional one, and a nu-metal and alternative-metal bill — so the recommender can be
seen working, and failing, against different tastes.

**The 2027 lineups are fabricated.** The artists are real and their tags come from MusicBrainz,
but the festival lineups and set times were written by hand for demonstration. Bloodstock Open
Air and Sick New World are real festivals; these are not their announced lineups, and no
festival has published a 2027 bill. Set times are not machine-readable anywhere — see
`data/lineup-audit/summary.md`, which surveys twenty festivals and what their data actually
looks like.

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

**Scheduling** (`analytics/app/scheduler.py`): greedy selection of non-overlapping sets, where
your own picks outrank any recommendation, one set in three is reserved for artists you did not
name, and the day is filled with music before breaks are carved out of it: one 45-minute meal
break and up to two 30-minute breathers, taken from existing gaps where possible and from the
weakest set in the window where not. Greedy
rather than optimal on purpose: when someone asks why an artist was left out, the answer is
always "something better overlapped it" or "a rule blocked it".

---

## Running it without Docker

For development. You need JDK 21+, Python 3.9+, and a PostgreSQL database (a free
[Neon](https://neon.com) project works).

```bash
# 1. Create the tables and load the data
psql "$DATABASE_URL" -f db/schema.sql
psql "$DATABASE_URL" -f db/seed_demo.sql
psql "$DATABASE_URL" -f db/seed_artists_us.sql

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

`SETUP.md` has the same steps with more hand-holding.
