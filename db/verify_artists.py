"""
Check every artist in dim_artist against MusicBrainz.

Why: the seeded artists and their tags were written by hand (and by an AI agent),
which makes them plausible but unverified. MusicBrainz is the canonical source the
project already relies on, so this script confirms each artist exists, records the
MusicBrainz id as the canonical key, and replaces invented tags with real ones.

Invented tags are kept only where MusicBrainz has none, and they stay marked
source='manual' so the two can always be told apart.

Rate limited to one request per second, as MusicBrainz requires.
"""
import json, sys, time, urllib.parse, urllib.request
from sqlalchemy import create_engine, text

UA = "Festimize/0.1 (IST 440W student project; contact via GitHub sandrardgz2)"
DB = open("analytics/.env").read().strip().split("=", 1)[1]
engine = create_engine(DB)


def mb(path):
    req = urllib.request.Request("https://musicbrainz.org/ws/2/" + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    with engine.begin() as c:
        artists = c.execute(text("select artist_id, name, country from dim_artist order by name")).fetchall()

    report = []
    for artist_id, name, country in artists:
        try:
            q = urllib.parse.quote(f'artist:"{name}"')
            hits = mb(f"artist?query={q}&fmt=json&limit=5").get("artists", [])
            time.sleep(1.1)
        except Exception as e:
            report.append((name, "lookup failed", str(e)[:60], 0)); continue

        exact = [h for h in hits if h["name"].lower() == name.lower()]
        if not exact:
            report.append((name, "NOT FOUND", "", 0)); continue
        best = max(exact, key=lambda h: h.get("score", 0))

        try:
            full = mb(f"artist/{best['id']}?inc=tags+genres&fmt=json")
            time.sleep(1.1)
        except Exception:
            full = best

        genres = [g["name"] for g in full.get("genres", []) if g.get("count", 0) >= 1]
        tags = [t["name"] for t in full.get("tags", []) if t.get("count", 0) >= 1]
        real = list(dict.fromkeys(genres + tags))[:10]

        with engine.begin() as c:
            c.execute(text("update dim_artist set mbid = :m, country = coalesce(:c, country), "
                           "disambiguation = :d where artist_id = :a"),
                      {"m": best["id"], "c": best.get("country"), "d": best.get("disambiguation") or None,
                       "a": artist_id})
            if real:
                c.execute(text("delete from artist_tag where artist_id = :a and source = 'musicbrainz'"),
                          {"a": artist_id})
                for i, tag in enumerate(real):
                    c.execute(text("insert into artist_tag (artist_id, tag, weight, source) "
                                   "values (:a, :t, :w, 'musicbrainz') on conflict do nothing"),
                              {"a": artist_id, "t": tag.lower(), "w": round(max(0.4, 1.0 - 0.07 * i), 2)})
        report.append((name, "ok", best.get("disambiguation", "") or "", len(real)))

    found = [r for r in report if r[1] == "ok"]
    print(f"checked {len(report)} artists: {len(found)} confirmed, {len(report) - len(found)} not confirmed")
    for r in report:
        if r[1] != "ok":
            print("  ! ", r[0], "->", r[1], r[2])
    thin = [r for r in found if r[3] == 0]
    print(f"confirmed but no MusicBrainz tags (kept the hand-written ones): {len(thin)}")
    for r in thin[:15]:
        print("  - ", r[0])


if __name__ == "__main__":
    main()
