# Festimize — Adversarial Testing Findings

Authorized robustness testing of Festimize against its own author, for IST 440W
(testing deliverable, due 1 November 2026). Every attack below was run against a
local `docker compose up` stack: web app on `:8080`, analytics on `:8000`,
Postgres on `:5432`. A throwaway account `attack@festimize.app` (user 10) is
used so the demo accounts are never corrupted.

Each case records the attack, what happened, a severity, and the fix — **noted,
not yet applied.** Fixes are a separate pass, after this document is reviewed.

Severity: **High** = reachable by anyone on the network / data loss or
disclosure · **Medium** = needs a logged-in user or crashes a request ·
**Low** = no breakage, but confusing or unpolished.

---

## Group A — Security

### Case 1 — The analytics service requires no authentication · **High**

**Attack.** With no login and no token, call the planning API directly:

```
POST http://localhost:8000/plan/2?edition_id=3        -> HTTP 200
GET  http://localhost:8000/plan/2/cost?edition_id=3   -> HTTP 200
```

**Outcome.** The first call **rebuilds user 2's saved schedule** — an attacker
who has never logged in can overwrite any account's plan by user id. The second
discloses what every set on the bill would cost that user. The service has no
authentication of any kind (confirmed: no `Security`, `Depends(...auth)`,
`HTTPBearer`, or API-key check anywhere in `analytics/app`).

**Why it is reachable.** `docker-compose.yml` publishes `8000:8000`, so the API
is bound to all interfaces, not just localhost. The web app is the only
intended caller, but nothing enforces that.

**Fix (noted).** Require a shared secret between the web app and the analytics
service (header checked in a FastAPI dependency), and in `docker-compose.yml`
publish the analytics port only to the web container, not the host.

### Case 2 — Postgres is published to the network with a known password · **High**

**Attack.** From a separate client container (i.e. not over Docker's internal
network — the published host port):

```
docker run --rm -e PGPASSWORD=festimize postgres:17 \
  psql -h host.docker.internal -p 5432 -U festimize -d festimize \
  -c "select count(*) from app_user"
-> connected — 4 accounts, 15799 artists readable
```

**Outcome.** The database is reachable from off-box with the `festimize` /
`festimize` credentials that are written in plain text in `docker-compose.yml`.
All user accounts (including bcrypt password hashes) and the whole corpus are
readable and writable.

**Why it is reachable.** `docker-compose.yml` publishes `5432:5432`. The
database never needs to be reachable from the host at all — only the two
services talk to it, over the internal compose network.

**Fix (noted).** Remove the `5432:5432` publish (or bind it to `127.0.0.1`
only), and move the credentials to an `.env` file that is git-ignored, so the
password is not committed. The app already reads its DB settings from the
environment.

---

## Group B — Robustness

### Case 7 — Can hostile edits make the scheduler emit a false day? · held, **Low** note

This is the case that matters most for the product: the whole claim is that the
schedule is trustworthy. Attack the *schedule*, not the server. After every
hostile edit, three invariants were checked on the built plan:

- no two sets overlap in time,
- no performance appears twice,
- no artist appears in two rows.

| Scenario | What was forced | Invariants | Day produced |
|---|---|---|---|
| 7a | Pin two fully-overlapping sets (Knocked Loose + Spiritbox) | 0 violations | clean |
| 7b | Pin **all 25** sets on the bill (heavily overlapping) | 0 violations | 10 sets, clean |
| 7c | **Decline every** set | 0 violations | 1 set (never empty) |
| 7d | Arrival window that excludes the whole day (23:00–23:30) | 0 violations | 10 sets (window ignored) |

**Outcome.** The scheduler never produced an invalid day. Pinning conflicting
sets is resolved by its pin-trimming pass (a clashing set is clamped or
dropped, never double-booked). Declining or excluding everything falls back to
a non-empty day rather than erroring, via `out[day] = kept or found` in
`planning.py:150`.

**The one observation (Low).** An impossible time window (7d) is **silently
ignored** — the user asked to attend only 23:00–23:30, there are no sets then,
and the app shows the full 10-set day with no note that the window did nothing.
Not a crash and not an invalid schedule, but the user gets no feedback that
their input had no effect.

**Fix (noted).** When a day's hours exclude every set, keep the non-empty
fallback but surface a line on the schedule ("Your hours for this day exclude
every set — showing the full day instead").

---

## Still to run

- Case 3 — one logged-in user acting on another's plan (IDOR)
- Case 4 — standard web surface: CSRF, SQLi, XSS, signed-out access
- Case 5 — malformed and oversized parameters
- Case 6 — invalid times in both pace forms
- Case 8 — two-runtime boundary across shared column types
- Case 9 — analytics service and database killed mid-use
- Case 10 — two sessions editing one plan
- Case 11 — 50 simultaneous schedule builds
- Case 12 — clean docker build on an empty volume

---

## Group A (continued) — Access control and web surface

### Case 3 — Can one logged-in user act on another's plan? (IDOR) · held

**Attack.** Every schedule/plan endpoint on the web app was checked for a
user id or plan id taken from the request. The only `@PathVariable` in the web
layer is `artistId` on the public artist page, which carries no user data.

**Outcome.** All plan, pin, decline, hours and meal endpoints derive the acting
user from the session `Principal`, never from a request parameter. A logged-in
user cannot target another account through the web app. (The analytics API is
the exception — that is Case 1, and it is the hole.)

### Case 4 — Standard web attack surface · held

| Sub-test | Attack | Result |
|---|---|---|
| CSRF | `POST /schedule/add` with no `_csrf` token | **403** — rejected |
| Signed-out access | `GET /schedule` with no session | **302 → /login** |
| SQL injection | login `username = ' OR '1'='1' --` | **302 → /login?error**, no auth |
| Stored XSS | display name `<script>alert(1)</script>`, read back | rendered as `&lt;script&gt;…` |

**Outcome.** All four held. CSRF protection is on for every state-changing POST,
every page except the public ones requires authentication, every query uses
bind parameters (so injection is inert — the literal string is treated as a
username and fails), and Thymeleaf HTML-escapes interpolated text by default so
stored markup is shown, not executed.

---

## Group B (continued) — Bad input

### Case 5 — Malformed request parameters · mostly held, **Low** note

**Attack.** Garbage `editionId` values on the schedule page and the analytics API.

```
editionId=abc                    -> 400      editionId=1e9   -> 400
editionId=9223372036854775808    -> 400      editionId=%00   -> 400
editionId=-1                     -> 200  (accepted)
analytics POST edition_id=9.2e18 -> 404  (handled, not a crash)
```

**Outcome.** Non-numeric, overflowing and null-byte values are rejected with a
clean 400; the analytics service returns 404 for an unknown edition rather than
crashing. **The one note (Low):** `editionId=-1` is accepted and silently falls
through to the default festival (via `EditionChoice`) rather than being
rejected. Harmless — no negative edition exists, so the user just sees the
default — but it is an unvalidated value reaching the picker.

### Case 6 — Invalid times crash two schedule endpoints · **Medium**

**Attack.** Impossible time strings into each form that takes a time.

```
/schedule/hours   arriveAt=25:00 | 99:99 | ab:cd | :::   -> HTTP 500 (all)
/schedule/eat-here startsAt=not-a-timestamp               -> HTTP 500
/profile          earliestStart=25:00                      -> HTTP 302 (rejected cleanly)
```

**Outcome.** The profile form validates times (it parses them in a try/catch and
drops anything that will not parse — `ProfileController.valid()`), so a bad value
there is handled. But `/schedule/hours` and `/schedule/eat-here` pass the raw
string straight into a Postgres cast (`cast(nullif(:arriveAt,'') as time)`,
`cast(:startsAt as timestamptz)`), and an invalid value throws an unhandled
exception — the user gets a **500 error page**.

**Severity Medium, not High:** the cast fails inside the transaction, so it
rolls back — **no data is corrupted** (confirmed: 0 `plan_day` rows written, the
column stayed null). And the values come from `<input type="time">`, which most
browsers will not let submit a bad value. But any browser that does not enforce
it, or a hidden-field timestamp (`eat-here`), or a direct POST, crashes the
request.

**Fix (noted).** Give the two schedule endpoints the same validation the profile
form already has — parse-and-reject before the cast, falling back the way a
blank value already does. One shared helper for all three.

---

## Group C — Dependencies, concurrency and platform

### Case 8 — The two-runtime boundary, deliberately provoked · held

Festimize's worst recurring bug class: the Java web app and the Python analytics
service read the same Postgres columns with different conversion rules. It has
cost two real bugs — a five-hour pace-time shift and a four-hour set-time shift.

**Attack.** Write a pace time through the Java app, read it back through the
Python service; and check a `timestamptz` set time end to end.

```
wrote earliest_start = 11:00 via the web app
  raw in Postgres:        11:00:00
  read by Python planner: 11:00:00      (no shift)
set time stored 2027-04-24 11:45 UTC -> web app shows 11:45  (consistent)
```

**Outcome.** Held. The pace columns are moved as text so Postgres does the only
cast, and the global timezone handling renders set times in the festival clock.
The boundary that caused both historical bugs is closed.

### Case 9 — Kill the dependencies mid-use · one held, one **Medium**

**9a — analytics service killed.** With `:8000` down: read-only pages still serve
(HTTP 200); a rebuild fast-fails in **5 ms**, logs `Connection refused`, and
redirects to `…?error=analytics` instead of crashing. **Graceful.** The
`PlanningClient` catches the connection failure rather than propagating a 500.

**9b — database stopped.** The **web app hangs** — a page request blocked for the
full 20 s test timeout (HTTP 000) rather than failing fast, because the
connection pool waits for a connection that will not come. The **analytics
service degrades cleanly** (`{"database":"unreachable"}`, the startup/health
check added last week). Both **recover automatically** once the database is
back — no restart needed.

**Finding (Medium):** a web request against a dead database hangs for the
connection timeout (HikariCP default ~30 s) instead of returning a fast error.
Availability, not data loss.

**Fix (noted).** Lower `spring.datasource.hikari.connection-timeout` to a few
seconds and add a friendly error page, so an outage shows an error promptly
rather than a hung tab.

### Case 10 — Two sessions editing one plan · held

**Attack.** Two logged-in sessions for one account pin different sets
simultaneously (`Code Orange` and `Slipknot`, fired in parallel).

**Outcome.** Both pins were recorded, the plan rebuilt consistently, invariants
clean. No lost update — the delete-then-insert of `plan_item` is transactional,
so the interleaved rebuilds did not leave duplicate or missing rows.

### Case 11 — Fifty simultaneous schedule builds · held

**Attack.** 50 parallel `POST /plan/10` against the O(n²) solver.

**Outcome.** All **50 returned HTTP 200** in **0.77 s** total; the plan stayed
consistent (0 invariant violations), no duplicate rows from interleaved
rebuilds, and the service remained healthy. The solver is small enough
(≤25 sets per day) that O(n²) is trivial, and concurrent rebuilds of one plan
serialize correctly at the database.

### Case 12 — Clean Docker build on an empty volume · held

**Attack.** Load `schema.sql` and all five seed files into a fresh Postgres (the
exact files `docker compose` mounts on first start), checking for any error.

```
init errors (ERROR/FATAL): none
loaded: 18 tables, 139 artists, 95 timed sets
```

**Outcome.** Clean load, zero errors. This confirms the `schema.sql` repair from
the previous week holds — a marker running `docker compose up --build` on an
empty machine gets a working database with all 18 tables. A fresh build has no
user accounts, which is correct: both `README.md` and `SETUP.md` tell the user
to **register**, not to use a demo login, so the documented path is honest.

---

## Summary

12 cases. Nothing produced data loss or a corrupted schedule. The scheduler —
the heart of the product — held every invariant under every hostile input.

| # | Case | Result |
|---|---|---|
| 1 | Analytics API unauthenticated | **High** — overwrite any plan |
| 2 | Postgres published with known password | **High** — full DB read/write off-box |
| 3 | IDOR via the web layer | held |
| 4 | CSRF / SQLi / XSS / signed-out | held (all four) |
| 5 | Malformed parameters | held; `editionId=-1` accepted (Low) |
| 6 | Invalid times | **Medium** — 500 on two schedule endpoints |
| 7 | Hostile pins/declines vs. scheduler invariants | held; impossible window silent (Low) |
| 8 | Two-runtime boundary | held |
| 9 | Dependencies killed mid-use | 9a held; 9b **Medium** — web hangs on dead DB |
| 10 | Two sessions, one plan | held |
| 11 | 50 concurrent builds | held |
| 12 | Clean build on empty volume | held |

**To fix (next pass):** 2 High (1, 2 — deployment exposure), 2 Medium (6 — time
validation; 9b — fast-fail on DB outage), 2 Low (5, 7 — input feedback).
Everything else is a mitigation already in place, documented here as evidence it
works.

---

## Fixes applied, and the re-attacks that confirm them

Each fix was re-attacked with the exact command that first broke it.

### Case 1 — analytics API authentication · fixed

A shared secret now gates every planning route (`app/auth.py`, keyed on the
`API_KEY` env var); `/health` stays open. The web app presents it as
`X-Analytics-Key` (`PlanningClient`). In `docker-compose.yml` the analytics
port is also bound to `127.0.0.1` only.

```
POST /plan/2  no key          -> 401   (was 200)
GET  /plan/2/cost  no key     -> 401   (was 200)
POST /plan/2  wrong key       -> 401
POST /plan/2  correct key     -> 200
the web app (which now sends the key) still builds plans -> 302, 11 sets
```

### Case 2 — Postgres network exposure · fixed

`docker-compose.yml` now binds `127.0.0.1:5432:5432` (loopback only) and reads
the password from a git-ignored `.env` (`.env.example` committed as the
template). Proven on a throwaway container:

```
old binding: 0.0.0.0:5432->5432/tcp   (every interface — LAN reachable)
new binding: 127.0.0.1:5434           (loopback only — not reachable off-box)
```

### Case 6 — invalid times · fixed

`/schedule/hours` and `/schedule/eat-here` now validate the time before the
cast (shared `goodTime` / `goodStamp` helpers), the way the profile form
already did, and show a notice.

```
/schedule/hours arriveAt=25:00 | 99:99 | ab:cd   -> 302   (was 500)
/schedule/eat-here startsAt=garbage              -> 302   (was 500)
/schedule/hours arriveAt=16:00 (valid)           -> 302   (still works)
page shows: "That time was not valid, so nothing was changed."
```

### Case 9b — database outage · improved

`spring.datasource.hikari.connection-timeout` lowered to 4 s.

```
GET /schedule with the database stopped -> HTTP 500 in 8 s   (was a 20 s+ hang)
recovers automatically when the database returns
```

A definite error in a few seconds rather than a hung tab. (8 s, not 4 s,
because the security filter and the page each wait once; acceptable, and far
better than indefinite.)

### Cases 5 and 7 (Low) · accepted, documented

`editionId=-1` falls to the default festival and `EditionChoice` never yields a
negative edition, so it is harmless; an impossible time window is never allowed
to empty the day. Both are left as-is — neither breaks anything — and recorded
here so the decision is explicit rather than an oversight.

---

## A pre-existing issue the testing surfaced (not caused by these fixes)

Running the DB-backed quality tests against the **full local corpus** (rather
than the pre-corpus Neon database `analytics/.env` points at) fails two
invariant tests:

```
test_no_break_runs_longer_than_an_hour  -> Sick New World: 84 minutes of rest in a row
test_the_scheduler_adds_at_most_one_long_break
```

The 84-minute block is a meal break that absorbed a genuine ~100-minute hole in
the Sick New World lineup (16:05–17:45), where only Code Orange plays and it is
not one of this user's stronger picks. It is visible in the app's own demo
(the `16:07–17:45 meal break`), so it is real behaviour, not a test artifact.

This is **pre-existing** — confirmed by stashing all of this week's changes and
re-running: the two tests fail identically, because nothing here touches the
scheduler. It is recorded because the testing is what exposed it: the suite
passes against one database and fails against another, which is the same
"two databases, one stale" hazard noted during deployment prep. A fix (cap the
meal break, or fill the hole) belongs with the scheduler work, not this pass.
