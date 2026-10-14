"""
Finish the corpus without anyone watching.

Written because an assistant is not a daemon: this session only runs when
something invokes it, so work that has to continue unattended has to live in a
process of its own. This is that process. It waits out the setlist.fm daily
quota, collects what is left, validates the result, and writes a report that
can be read whenever someone comes back.

    caffeinate -dis python3 corpus/overnight.py &

It commits a clean result locally and never pushes: publishing is a decision
for a person, and a validation pass is not the same as a review.
"""
import datetime
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(ROOT, 'analytics', '.venv', 'bin', 'python')
REPORT = os.path.join(ROOT, 'data', 'corpus', 'overnight-report.txt')
PATIENCE = 14                      # hours to keep trying before giving up
BETWEEN_TRIES = 45 * 60


def log(handle, message):
    stamp = datetime.datetime.now().strftime('%H:%M')
    line = '%s  %s' % (stamp, message)
    print(line, flush=True)
    handle.write(line + '\n')
    handle.flush()


def run(script, *args):
    result = subprocess.run([PYTHON, '-u', os.path.join(ROOT, 'corpus', script)] + list(args),
                            cwd=ROOT, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def main():
    deadline = time.time() + PATIENCE * 3600
    with open(REPORT, 'w', encoding='utf-8') as handle:
        log(handle, 'started; will keep trying until %s'
            % datetime.datetime.fromtimestamp(deadline).strftime('%H:%M'))

        while True:
            code, output = run('extract.py')
            handle.write(output + '\n')
            blocked = [line for line in output.splitlines() if 'quota is exhausted' in line]
            log(handle, 'extract finished; %d festivals still blocked by the quota' % len(blocked))
            if not blocked or time.time() > deadline:
                break
            log(handle, 'sleeping %d minutes before trying those again' % (BETWEEN_TRIES // 60))
            time.sleep(BETWEEN_TRIES)

        code, output = run('validate.py', '--write')
        handle.write(output + '\n')
        clean = code == 0
        log(handle, 'validation %s' % ('passed' if clean else 'found blocking problems'))

        # Every row traced back to the source text it came from. Run after the
        # crawl because the festivals that were blocked cannot be checked until
        # their searches are in the cache.
        _, output = run('fidelity.py')
        handle.write(output + '\n')
        unsupported = [line for line in output.splitlines() if 'does not support' in line]
        log(handle, 'fidelity: %s' % (unsupported[0].strip('- ') if unsupported else 'not reported'))

        if clean:
            subprocess.run(['git', 'add', 'data/corpus', 'docs/evaluation', 'corpus'], cwd=ROOT)
            message = ('Corpus: overnight run, validated\n\n'
                       'Collected by corpus/overnight.py while nobody was at the machine. '
                       'Committed only because every blocking check passed; not pushed, '
                       'because publishing is a decision for a person.\n\n'
                       'Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>\n')
            subprocess.run(['git', 'commit', '-q', '-m', message], cwd=ROOT)
            log(handle, 'committed locally, not pushed')
        else:
            log(handle, 'left uncommitted on purpose — the working tree holds the result')
        log(handle, 'done')


if __name__ == '__main__':
    sys.exit(main())
