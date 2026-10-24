"""
Apply every migration in db/migrations to one database, in order.

    python3 db/migrate.py                     # the URL in analytics/.env
    python3 db/migrate.py "postgresql+psycopg://..."
    python3 db/migrate.py --dry-run           # say what would run, change nothing
    python3 db/migrate.py --yes               # skip the prompt, having decided

Needed because there has never been a migration runner: the local database
is brought up by hand with psql, and anything else — the hosted one in
analytics/.env, and whatever task 7.1 deploys to — silently falls behind.
Audited 24 October, the hosted database was missing ten of the eleven
migrations and still held the pre-corpus data.

Every migration is written to be safe to re-run (CREATE TABLE IF NOT
EXISTS, ADD COLUMN IF NOT EXISTS), so this applies all of them rather than
tracking which have run. That is the right trade at eleven files: a version
table is one more thing to get out of step with the directory it describes.

Run against a remote database this writes to it, so it asks before it does.
"""
import pathlib
import sys

from sqlalchemy import create_engine, text

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOCAL = 'postgresql+psycopg://festimize:festimize@localhost:5432/festimize'


def url_from_env():
    env = ROOT / 'analytics' / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith('DATABASE_URL='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    return LOCAL


def shown(url):
    """The host, without the password."""
    tail = url.split('@')[-1]
    return tail.split('?')[0]


def main(argv):
    dry = '--dry-run' in argv
    rest = [a for a in argv[1:] if not a.startswith('--')]
    url = rest[0] if rest else url_from_env()
    files = sorted((ROOT / 'db' / 'migrations').glob('*.sql'))
    if not files:
        sys.exit('no migrations found')

    print('database : %s' % shown(url))
    print('migrations: %d' % len(files))
    if dry:
        for f in files:
            print('  would apply', f.name)
        return 0

    local = 'localhost' in url or '127.0.0.1' in url
    if not local and '--yes' not in argv:
        # Typing the host is the speed bump, not a security measure. --yes is
        # for a caller who has already decided, including one with no stdin.
        print('\nThis is not localhost. It will be written to.')
        try:
            answer = input('Type the host to confirm: ').strip()
        except EOFError:
            sys.exit('no stdin to confirm on; re-run with --yes if you meant it')
        if answer != shown(url).split('/')[0]:
            sys.exit('not confirmed; nothing was changed')

    engine = create_engine(url, connect_args={'connect_timeout': 30})
    failed = 0
    for f in files:
        try:
            with engine.begin() as c:
                c.execute(text(f.read_text()))
            print('  applied %s' % f.name)
        except Exception as exc:
            failed += 1
            print('  FAILED  %s -> %s' % (f.name, str(exc).splitlines()[0][:160]))
    print('\n%d applied, %d failed' % (len(files) - failed, failed))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
