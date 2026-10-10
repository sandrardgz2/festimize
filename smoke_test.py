"""
End-to-end check that a freshly started stack actually works.

Run it after `docker compose up --build`:

    python3 smoke_test.py

It registers an account, saves a handful of artists, then builds and reads a
schedule for every demonstration festival, printing what it found. No
dependencies beyond the standard library, so it runs on a clean machine.
"""
import http.cookiejar
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

WEB = "http://localhost:8080"
ANALYTICS = "http://localhost:8000"
WANTED = [
    "Gojira", "Slipknot", "Deftones", "Korn", "System of a Down",
    "Evanescence", "Spiritbox", "Metallica", "Lamb of God", "Mastodon",
    "Opeth", "Tool",
]

jar = http.cookiejar.CookieJar()
browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
failures = []


def token_from(page):
    """Spring Security puts a CSRF token in every form; posts are rejected without it."""
    found = re.search(r'name="_csrf" value="([^"]+)"', page)
    return found.group(1) if found else ""


def visit(path, data=None, base=WEB, token=None):
    """GET, or POST when data is given. Returns (status, body)."""
    if data is not None and token:
        data = dict(data, _csrf=token)
    body = urllib.parse.urlencode(data, doseq=True).encode() if data else None
    try:
        with browser.open(base + path, body) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")


def check(label, condition, detail=""):
    print(("  ok   " if condition else "  FAIL ") + label + (" — " + detail if detail else ""))
    if not condition:
        failures.append(label)


print("Festimize smoke test")

status, body = visit("/health", base=ANALYTICS)
check("analytics health", status == 200 and '"database":"connected"' in body.replace(" ", ""), body.strip()[:60])

_, page = visit("/register")
status, _ = visit("/register", {
    "email": "smoke-test@example.com", "displayName": "Smoke Test", "password": "festimize123",
}, token=token_from(page))
if status == 200:  # already registered from an earlier run: sign in instead
    _, page = visit("/login")
    status, _ = visit("/login", {"username": "smoke-test@example.com", "password": "festimize123"},
                      token=token_from(page))
check("register and sign in", status in (200, 302), "HTTP %d" % status)

status, setup = visit("/setup")
offered = dict((name, artist_id) for artist_id, name in
               re.findall(r'name="artistIds" value="(\d+)"[^>]*>\s*<span>([^<]+)</span>', setup))
picks = [offered[name] for name in WANTED if name in offered]
check("setup page lists artists", len(offered) > 50, "%d offered" % len(offered))
check("test artists are available", len(picks) >= 10, "%d of %d found" % (len(picks), len(WANTED)))

if picks:
    status, _ = visit("/setup", {"artistIds": picks}, token=token_from(setup))
    check("saving picks", status in (200, 302), "HTTP %d" % status)

for edition_id, name in ((1, "Bloodstock Open Air"), (2, "Ravenstone Festival"), (3, "Sick New World")):
    print(name)
    status, lineup = visit("/lineup?editionId=%d" % edition_id)
    matches = len(re.findall(r"% match", lineup))
    mine = lineup.count("badge-pick")
    check("lineup scores artists", status == 200 and matches > 0,
          "%d scored, %d of them my picks" % (matches, mine))

    _, page = visit("/schedule?editionId=%d" % edition_id)
    status, _ = visit("/schedule/build", {"editionId": edition_id}, token=token_from(page))
    check("schedule builds", status in (200, 302), "HTTP %d" % status)

    status, schedule = visit("/schedule?editionId=%d" % edition_id)
    sets = schedule.count("slot-set")
    breaks = schedule.count("slot-rest")
    check("schedule has sets", status == 200 and sets > 0, "%d sets, %d breaks" % (sets, breaks))

print()
if failures:
    print("%d check(s) failed: %s" % (len(failures), ", ".join(failures)))
    sys.exit(1)
print("Everything passed.")
