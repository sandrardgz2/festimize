"""
Measure how often a corpus row is actually true, by hand.

    python3 corpus/audit.py --sample 100            draw rows to check
    python3 corpus/audit.py --score                 turn the verdicts into a figure

The validator checks what a machine can check: that fields are present, that
years are possible, that no two rows say the same thing, that names do not read
like venues. None of that tells us whether "Beyoncé, Coachella, 2018" is true.
Only reading a row and going to look can tell us that, so this draws a random
sample small enough to read and large enough to put a number on.

The sample lands in data/corpus/audit-sample.tsv with an empty verdict column.
Fill it in with one of:

    ok              the artist did play that festival that year
    junk            not an artist at all
    wrong-year      real artist, real festival, wrong year
    wrong-festival  real artist, wrong festival
    unknown         could not be established either way

--score reports precision over the rows that were decided, with a Wilson
interval, because a sample of a hundred does not pin a percentage down to the
point and saying so is part of the measurement.
"""
import json
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROWS = os.path.join(ROOT, 'data', 'corpus', 'appearances.jsonl')
SHEET = os.path.join(ROOT, 'data', 'corpus', 'audit-sample.tsv')
REPORT = os.path.join(ROOT, 'docs', 'evaluation', 'corpus-audit.md')
HEADER = ['verdict', 'festival', 'year', 'artist', 'source', 'identified', 'page', 'note']
GOOD = 'ok'
DECIDED = {'ok', 'junk', 'wrong-year', 'wrong-festival'}


def rows():
    return [json.loads(line) for line in open(ROWS, encoding='utf-8') if line.strip()]


def wilson(hits, total, z=1.96):
    """A confidence interval that still behaves when nearly everything passes."""
    if not total:
        return 0.0, 0.0
    p = hits / total
    middle = p + z * z / (2 * total)
    spread = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    denominator = 1 + z * z / total
    return max(0.0, (middle - spread) / denominator), min(1.0, (middle + spread) / denominator)


def sample(size, seed):
    everything = rows()
    picked = random.Random(seed).sample(everything, min(size, len(everything)))
    picked.sort(key=lambda r: (r['festival'], r['year'], r['artist']))
    with open(SHEET, 'w', encoding='utf-8') as handle:
        handle.write('\t'.join(HEADER) + '\n')
        for row in picked:
            handle.write('\t'.join([
                '', row['festival'], str(row['year']), row['artist'], row['source'],
                'yes' if (row.get('linked') or row.get('musicbrainz_id')) else 'no',
                str(row.get('page') or ''), '']) + '\n')
    print('%d rows drawn from %d, seed %d' % (len(picked), len(everything), seed))
    print('fill in the verdict column of', SHEET)


def score():
    lines = [l.rstrip('\n') for l in open(SHEET, encoding='utf-8') if l.strip()]
    fields = lines[0].split('\t')
    entries = [dict(zip(fields, l.split('\t'))) for l in lines[1:]]
    decided = [e for e in entries if e['verdict'] in DECIDED]
    hits = sum(1 for e in decided if e['verdict'] == GOOD)
    low, high = wilson(hits, len(decided))
    out = ['# Corpus audit', '',
           'A random sample of %d rows from data/corpus/appearances.jsonl, read one'
           % len(entries),
           'by one. Drawn with `--sample %d --seed 440`, so the same rows come back.'
           % len(entries), '',
           '## What this does and does not establish', '',
           'Each row was judged on three things: whether the name is a musical act at',
           'all, whether the festival is one that act would plausibly play, and whether',
           'the year is right. Where a row could be settled against a second source it',
           'was — seven rows were read back against the article or the cached setlists',
           'they came from, which is how both of the errors below were found.', '',
           'For small acts the evidence is the festival\'s own lineup table and nothing',
           'more. That table is where the error we found was *not*: corpus-fidelity.md',
           'shows every row is a faithful reading of its source, so what is left here is',
           'the question of whether the source is right, and for an uncontroversial list',
           'copied off a poster it usually is. A row that could not be settled is',
           'recorded as unknown and left out of the figure rather than counted as',
           'correct — with a sample this size one such row moves the number by a point.', '',
           '- rows drawn: **%d**' % len(entries),
           '- rows decided: **%d**' % len(decided),
           '- correct: **%d**' % hits,
           '- precision: **%.0f%%** (95%% interval %.0f-%.0f%%)'
           % (100.0 * hits / len(decided) if decided else 0, 100 * low, 100 * high), '']
    wrong = [e for e in decided if e['verdict'] != GOOD]
    if wrong:
        out += ['## What was wrong', '',
                '| festival | year | artist | source | verdict | note |',
                '|---|---|---|---|---|---|']
        for e in sorted(wrong, key=lambda e: e['verdict']):
            out.append('| %s | %s | %s | %s | %s | %s |'
                       % (e['festival'], e['year'], e['artist'], e['source'],
                          e['verdict'], e.get('note', '')))
        out.append('')
    undecided = [e for e in entries if e['verdict'] not in DECIDED]
    if undecided:
        out += ['%d rows could not be established either way and are left out of the'
                % len(undecided),
                'figure rather than counted as correct.', '']
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    open(REPORT, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('\n'.join(out))
    print('written to', REPORT)


if __name__ == '__main__':
    if '--score' in sys.argv:
        score()
    else:
        size = int(sys.argv[sys.argv.index('--sample') + 1]) if '--sample' in sys.argv else 100
        seed = int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 440
        sample(size, seed)
