"""
Check the corpus before anyone builds anything on it.

A lineup corpus fails quietly. A wrong year does not crash a query, it just
makes an artist look like it was booked earlier than it was; a stage name read
as a band adds an act that never existed; a festival missing from one year
looks like a career gap. None of that shows up until a conclusion is already
drawn from it, so it gets checked here instead.

    python3 corpus/validate.py            # report to the terminal
    python3 corpus/validate.py --write    # also write docs/evaluation/corpus-quality.md

Every check prints what it found, not just whether it passed, because "17
names look like venues" is a number worth watching across runs.
"""
import collections
import json
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'corpus', 'appearances.jsonl')
REPORT = os.path.join(ROOT, 'docs', 'evaluation', 'corpus-quality.md')

REQUIRED = ('festival', 'year', 'artist', 'source', 'confidence', 'commercial_use')
VENUE_WORDS = re.compile(r'\b(stage|tent|arena|pavilion|field|park|hall|room|lounge|bar|'
                         r'camp|cinema|theatre|theater|disco|workshop|market)\b', re.I)
PROSE_WORDS = re.compile(r'\b(over|next|about|approximately|between|around|during|after|'
                         r'before|including|featuring|were|was|are|has|had|would|will|'
                         r'their|which|who|when|while|because|however|also|than|from)\b')
# A month followed by a number is a date; "April Art" and "August Burns Red"
# are bands, so the digit is what makes the difference.
DATE_LIKE = re.compile(r'^(january|february|march|april|may|june|july|august|september|'
                       r'october|november|december)\s*\d', re.I)

# Things known to be true, used as a smoke test on the finished corpus. If one
# of these fails, something upstream broke even when every count looks sane.
# Facts asserted from outside the data and then looked for in it. This is the
# only check here that tests truth rather than shape, and it is the one that
# earned its keep: Beyoncé went missing from Coachella 2018 for days because a
# comma inside [[Tyler, the Creator]] broke the line above her, and nothing
# else noticed. They are spread across both sources and both readers on
# purpose, so a break in one path cannot hide behind the other.
KNOWN = [
    ('Slipknot', 'Download Festival', 2019),          # wikipedia, year sections
    ('Iron Maiden', 'Download Festival', 2016),
    ('Metallica', 'Download Festival', 2023),
    ('Beyoncé', 'Coachella', 2018),                   # wikipedia, line-ups article
    ('Billie Eilish', 'Coachella', 2019),
    ('Odesza', 'Suwannee Hulaween', 2018),            # wikipedia, lineup in prose
    ('Arch Enemy', 'Wacken Open Air', 2026),          # setlist.fm, city search
    ('Judas Priest', 'Hellfest', 2022),               # setlist.fm, city search
    ('Slipknot', 'Knotfest', 2021),
    # Rock am Ring and Rock im Park are twin festivals, same weekend and very
    # nearly the same bill, in two cities. Rammstein's Rock am Ring set was lost
    # to the evacuation on 2 June 2017 but they played Rock im Park at the
    # Zeppelinfeld on the 4th, so under the merged name this is a fact that must
    # be here. It sat in FORBIDDEN until the Nuremberg half of the festival was
    # added and then failed, which is the check doing its job in both directions.
    ('Rammstein', 'Rock am Ring and Rock im Park', 2017),
    ('The Chemical Brothers', 'Creamfields', 2019),   # wikipedia, separate list article
]

# Facts that must NOT be in the data. Every one of these was produced by a real
# bug, so each is a regression test for a whole class of error rather than a
# single row. These checks have twice contradicted an assertion rather than the
# data, which is the other thing they are for: see the Rammstein note in KNOWN.
FORBIDDEN = [
    ('The Sword', 'Download Festival', 2015, 'pulled out; named only in a paragraph about it'),
    ('King 810', 'Download Festival', 2015, 'pulled out'),
    ('Leicestershire Police', 'Download Festival', 2015, 'a police force in a prose paragraph'),
    # Psycho Las Vegas was parked on 14 October, so this one now passes because
    # the festival is absent rather than because the rule works. It stays as a
    # record of how the comedian arrived; is_music is what keeps him out, and
    # the Sonic Temple case below exercises that rule on a festival still here.
    ('Max Amini', 'Psycho Las Vegas', 2026, 'a comedian; a city search picked up a club show'),
    ('Celeste', 'Glastonbury Festival', 2020, 'announced for an edition that was cancelled'),
    ('Andrew Dice Clay', 'Sonic Temple Art & Music Festival', 2019, 'a comedian in the spoken-word tent'),
    ('Gogol Bordello', 'CRSSD Festival', 2015,
     'Gasparilla Music Festival in Tampa; a venue search for Waterfront Park '
     'matched any park with a shared word, in any city'),
    ('Davido', 'Riot Fest', 2023,
     'an Afrobeats festival at Doug Jennings Park on the Gold Coast, '
     'matched by a search for Chicago\'s Douglass Park'),
]


def load():
    return [json.loads(line) for line in open(DATA, encoding='utf-8')]


def main():
    rows = load()
    out = []

    def say(line=''):
        print(line)
        out.append(line)

    festivals = collections.Counter(r['festival'] for r in rows)
    artists = collections.Counter(r['artist'] for r in rows)
    years = collections.Counter(r['year'] for r in rows)

    say('# Corpus quality')
    say()
    say('%d appearances, %d distinct artists, %d festivals, %d-%d.'
        % (len(rows), len(artists), len(festivals), min(years), max(years)))
    say()

    # --- structure
    missing = [r for r in rows if any(field not in r for field in REQUIRED)]
    say('## Structure')
    say()
    say('- rows missing a required field: **%d**' % len(missing))
    bad_year = [r for r in rows if not isinstance(r['year'], int) or not 1960 <= r['year'] <= 2027]
    say('- rows with an impossible year: **%d**' % len(bad_year))
    duplicates = [key for key, count in
                  collections.Counter((r['festival'], r['year'], r['artist'].lower())
                                      for r in rows).items() if count > 1]
    say('- duplicate (festival, year, artist) rows: **%d**' % len(duplicates))
    say()

    # --- names
    say('## Names that do not look like artists')
    say()
    suspects = {
        'contain a three-digit run': [r for r in rows if re.search(r'\d{3}', r['artist'])
                                      and not r.get('linked')],
        'read like a venue or stage': [r for r in rows if VENUE_WORDS.search(r['artist'])
                                       and not (r.get('linked') or r.get('musicbrainz_id'))],
        'read like a sentence': [r for r in rows if PROSE_WORDS.search(r['artist'])],
        'start with a date': [r for r in rows if DATE_LIKE.match(r['artist'])],
        'longer than 45 characters': [r for r in rows if len(r['artist']) > 45],
    }
    for label, found in suspects.items():
        sample = ', '.join(sorted({r['artist'] for r in found})[:4])
        say('- %s: **%d** %s' % (label, len(found), ('— e.g. %s' % sample) if found else ''))
    say()

    # --- identity
    resolvable = sum(1 for r in rows if r.get('linked') or r.get('musicbrainz_id'))
    say('## Identity')
    say()
    say('- rows resolvable to a MusicBrainz id: **%d (%.0f%%)**'
        % (resolvable, 100.0 * resolvable / len(rows)))
    say('- artists appearing once only: **%d of %d (%.0f%%)**'
        % (sum(1 for c in artists.values() if c == 1), len(artists),
           100.0 * sum(1 for c in artists.values() if c == 1) / len(artists)))
    say()

    # --- per festival
    say('## Per festival')
    say()
    say('| festival | rows | years | span | per year | source | commercial |')
    say('|---|---|---|---|---|---|---|')
    for name, count in festivals.most_common():
        mine = [r for r in rows if r['festival'] == name]
        ys = sorted({r['year'] for r in mine})
        say('| %s | %d | %d | %d-%d | %d | %s | %s |'
            % (name, count, len(ys), ys[0], ys[-1], round(count / len(ys)),
               mine[0]['source'], 'yes' if mine[0].get('commercial_use') else 'no'))
    say()

    # --- volumes
    # A fixed ceiling asks the wrong question. Tomorrowland really does book
    # five hundred DJs across sixteen stages and two weekends, and flagging it
    # every run teaches us to ignore the flag; Psycho Las Vegas' 1,349 was
    # contamination because its other years are nothing like it. So each year is
    # compared with what that festival normally does, and only an absurd
    # absolute number is blocking on its own.
    per_year = collections.Counter((r['festival'], r['year']) for r in rows)
    sizes = collections.defaultdict(list)
    for (festival, _year), count in per_year.items():
        sizes[festival].append(count)
    typical = {festival: statistics.median(counts) for festival, counts in sizes.items()}
    thin = [key for key, count in per_year.items() if count <= 3]
    uneven = [key for key, count in per_year.items()
              if count > max(60, 3 * typical[key[0]])]
    fat = [key for key, count in per_year.items() if count > 1000]
    say('## Volume')
    say()
    say('- festival-years with three acts or fewer: **%d**%s'
        % (len(thin), (' — e.g. %s' % ', '.join('%s %d' % k for k in sorted(thin)[:4])) if thin else ''))
    say('- festival-years more than three times that festival\'s usual size: **%d**%s'
        % (len(uneven), (' — %s' % ', '.join('%s %d (usual %d)' % (k[0], k[1], typical[k[0]])
                                             for k in sorted(uneven))) if uneven else ''))
    say('- festival-years above a thousand acts, which no festival books: **%d**%s'
        % (len(fat), (' — %s' % ', '.join('%s %d' % k for k in sorted(fat))) if fat else ''))
    say('- largest festival-years: %s'
        % ', '.join('%s %d (%d acts)' % (f, y, c)
                    for (f, y), c in per_year.most_common(3)))
    say()

    # --- known answers
    # Which festivals are worth keeping is a judgement, and it needs the shape
    # of the series rather than a single total: five years of a hundred acts
    # supports a trend, ten years swinging between five and eighty does not.
    say('## Coverage')
    say()
    # One bad year does not condemn a festival: Hellfest has ten good years and a
    # 2021 with twenty acts in it. What matters is how many years are properly
    # covered, because that is how many points a trend has to be drawn through.
    say('What this column does not ask is whether the rows are any good. A festival')
    say('with two complete bills in it cannot show its own trend, and still adds two')
    say('real points to the career of every artist on those bills — which is what the')
    say('rising-artist score is measured over. Sick New World is kept on exactly that')
    say('reasoning; Defqon.1 was cut on the opposite one, because six acts out of a')
    say('hundred is a fragment of a bill rather than a short history.')
    say()
    say('| festival | years | usable | median | smallest | largest | enough for a trend |')
    say('|---|---|---|---|---|---|---|')
    rank = sorted(sizes, key=lambda f: (-sum(1 for c in sizes[f]
                                             if c >= max(8, 0.25 * typical[f])),
                                        statistics.median(sizes[f])))
    for festival in rank:
        counts = sorted(sizes[festival])
        floor = max(8, 0.25 * typical[festival])
        usable = sum(1 for count in counts if count >= floor)
        say('| %s | %d | %d | %d | %d | %d | %s |'
            % (festival, len(counts), usable, typical[festival], counts[0], counts[-1],
               'yes' if usable >= 5 else '**no**'))
    say()

    say('## Known-answer checks')
    say()
    index = {(r['artist'].lower(), r['festival'], r['year']) for r in rows}
    failures = 0
    for artist, festival, year in KNOWN:
        ok = (artist.lower(), festival, year) in index
        failures += 0 if ok else 1
        say('- %s %s at %s %d' % ('PASS' if ok else 'FAIL', artist, festival, year))
    say()
    say('## Things that must not be here')
    say()
    # A row that is counted as an appearance. An announced lineup for a
    # cancelled edition is kept on purpose and flagged, so it is not a failure.
    happened = {(r['artist'].lower(), r['festival'], r['year'])
                for r in rows if r.get('happened', True)}
    for artist, festival, year, why in FORBIDDEN:
        gone = (artist.lower(), festival, year) not in happened
        failures += 0 if gone else 1
        say('- %s %s at %s %d — %s'
            % ('PASS' if gone else 'FAIL', artist, festival, year, why))
    say()

    # Sentence-sounding names are reviewed by eye, not counted against the run:
    # Rocket from the Crypt and Fall from Grace are bands.
    # Blocking means the dataset is wrong: a missing field, an impossible year,
    # a duplicate, a year that read hundreds of acts, or a fact we know and
    # cannot find. The name heuristics are a review queue, not a verdict —
    # Rocket from the Crypt and Flux Pavilion both trip them and both are real.
    review = sum(len(found) for found in suspects.values())
    problems = len(missing) + len(bad_year) + len(duplicates) + len(fat) + failures
    say('**%d blocking problems**, %d names queued for review (%.2f%% of rows).'
        % (problems, review, 100.0 * review / len(rows)))
    if '--write' in sys.argv:
        os.makedirs(os.path.dirname(REPORT), exist_ok=True)
        open(REPORT, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
        print('\nwritten to', REPORT)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
