"""
Turn the evaluation reports into one page you can read in a browser.

    analytics/.venv/bin/python docs/evaluation/render.py        # write and open it
    analytics/.venv/bin/python docs/evaluation/render.py --quiet # write only

The reports are written as Markdown because that is what git diffs well and
what pastes into a document. Markdown is not something to read in a terminal,
and there is no viewer on this machine, so this renders them locally. It writes
a file and opens it; nothing is uploaded anywhere.
"""
import glob
import html
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'reports.html')

# Newest first is the wrong order for reading: the corpus reports say what the
# data is, and the momentum reports argue about what to do with it.
ORDER = ['corpus-quality', 'corpus-fidelity', 'corpus-audit',
         'momentum-backtest', 'newcomer-signals',
         'scheduler-comparison', 'profile-clustering']

STYLE = """
:root {
  --ink: #241b2e; --soft: #6b5b7b; --line: #e7dff0; --paper: #fffdfe;
  --accent: #b5338a; --accent-soft: #f7edf6; --mark: #7c3aed;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ink: #ece6f2; --soft: #a99bb8; --line: #352a42; --paper: #17121d;
    --accent: #f08fcf; --accent-soft: #241b2e; --mark: #c4a6ff;
  }
}
:root[data-theme="dark"] {
  --ink: #ece6f2; --soft: #a99bb8; --line: #352a42; --paper: #17121d;
  --accent: #f08fcf; --accent-soft: #241b2e; --mark: #c4a6ff;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--paper); color: var(--ink);
  font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  padding: 0 16px;
}
.wrap { max-width: 50rem; margin: 0 auto; padding: 3rem 0 6rem; }
h1.page { font-size: 1.1rem; letter-spacing: .08em; text-transform: uppercase;
          color: var(--soft); font-weight: 600; margin: 0 0 2.5rem; }
nav { display: flex; flex-wrap: wrap; gap: .5rem; margin: 0 0 3rem; }
nav a { font-size: .85rem; text-decoration: none; color: var(--accent);
        border: 1px solid var(--line); border-radius: 2rem; padding: .3rem .85rem; }
nav a:hover { background: var(--accent-soft); }
section { border-top: 1px solid var(--line); padding-top: 2.5rem; margin-top: 3.5rem; }
section:first-of-type { border-top: 0; margin-top: 0; padding-top: 0; }
h1 { font-size: 1.75rem; line-height: 1.25; margin: 0 0 1.25rem; letter-spacing: -.02em; }
h2 { font-size: 1.15rem; margin: 2.5rem 0 .75rem; color: var(--accent); }
h3 { font-size: .95rem; margin: 1.75rem 0 .5rem; color: var(--soft);
     text-transform: uppercase; letter-spacing: .06em; }
p { margin: 0 0 1rem; }
ul { margin: 0 0 1rem; padding-left: 1.25rem; }
li { margin: .2rem 0; }
code { font: .875em ui-monospace, SFMono-Regular, Menlo, monospace;
       background: var(--accent-soft); padding: .1em .35em; border-radius: 3px; }
strong { color: var(--mark); }
.scroll { overflow-x: auto; margin: 0 0 1.5rem; }
table { border-collapse: collapse; font-size: .9rem; min-width: 100%; }
th, td { text-align: left; padding: .5rem .75rem; border-bottom: 1px solid var(--line);
         white-space: nowrap; }
th { font-size: .75rem; text-transform: uppercase; letter-spacing: .05em;
     color: var(--soft); font-weight: 600; }
td:first-child, th:first-child { white-space: normal; }
tr:hover td { background: var(--accent-soft); }
.when { font-size: .8rem; color: var(--soft); margin: -.75rem 0 2rem; }
"""


def inline(text):
    """Bold, code and the rest of what these reports actually use."""
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\w)\*([^*]+)\*(?!\w)', r'<em>\1</em>', text)
    return text


def convert(body):
    """Markdown to HTML, for the small part of Markdown these reports use."""
    out, rows, bullets, para = [], [], [], []

    def shut_table():
        if not rows:
            return
        head, body_rows = rows[0], [r for r in rows[1:]
                                    if not re.match(r'^[\s|:-]+$', '|'.join(r))]
        out.append('<div class="scroll"><table><thead><tr>'
                   + ''.join('<th>%s</th>' % inline(c) for c in head)
                   + '</tr></thead><tbody>')
        for row in body_rows:
            out.append('<tr>' + ''.join('<td>%s</td>' % inline(c) for c in row) + '</tr>')
        out.append('</tbody></table></div>')
        rows[:] = []

    def shut_list():
        if bullets:
            out.append('<ul>' + ''.join('<li>%s</li>' % inline(b) for b in bullets) + '</ul>')
            bullets[:] = []

    def shut_para():
        if para:
            out.append('<p>%s</p>' % inline(' '.join(para)))
            para[:] = []

    for line in body.split('\n'):
        bare = line.strip()
        if bare.startswith('|'):
            shut_para(); shut_list()
            rows.append([c.strip() for c in bare.strip('|').split('|')])
            continue
        shut_table()
        if not bare:
            shut_para(); shut_list()
        elif bare.startswith('### '):
            shut_para(); shut_list(); out.append('<h3>%s</h3>' % inline(bare[4:]))
        elif bare.startswith('## '):
            shut_para(); shut_list(); out.append('<h2>%s</h2>' % inline(bare[3:]))
        elif bare.startswith('# '):
            shut_para(); shut_list(); out.append('<h1>%s</h1>' % inline(bare[2:]))
        elif bare.startswith(('- ', '* ')):
            shut_para(); bullets.append(bare[2:])
        else:
            shut_list(); para.append(bare)
    shut_table(); shut_list(); shut_para()
    return '\n'.join(out)


def main():
    import datetime
    found = {os.path.splitext(os.path.basename(p))[0]: p
             for p in glob.glob(os.path.join(HERE, '*.md'))}
    names = [n for n in ORDER if n in found] + sorted(n for n in found if n not in ORDER)

    pieces, links = [], []
    for name in names:
        body = open(found[name], encoding='utf-8').read()
        when = datetime.datetime.fromtimestamp(os.path.getmtime(found[name]))
        title = re.search(r'^#\s+(.+)$', body, re.M)
        links.append('<a href="#%s">%s</a>' % (name, html.escape(
            title.group(1) if title else name)))
        pieces.append('<section id="%s">%s<p class="when">%s · written %s</p>%s</section>'
                      % (name,
                         '' if title else '<h1>%s</h1>' % html.escape(name),
                         html.escape(name + '.md'),
                         when.strftime('%-d %B %Y, %H:%M'),
                         convert(body)))

    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Festimize evaluation</title><style>%s</style></head><body>'
            '<div class="wrap"><h1 class="page">Festimize &middot; evaluation reports</h1>'
            '<nav>%s</nav>%s</div></body></html>'
            % (STYLE, ''.join(links), ''.join(pieces)))
    open(OUT, 'w', encoding='utf-8').write(page)
    print('%d reports -> %s' % (len(names), OUT))
    if '--quiet' not in sys.argv:
        subprocess.run(['open', OUT])


if __name__ == '__main__':
    sys.exit(main())
