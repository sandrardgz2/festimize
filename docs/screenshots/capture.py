"""
Capture the screenshots in this folder from a running stack.

    docker compose up --build        # in another terminal
    pip install playwright
    python3 docs/screenshots/capture.py

It drives a real Chrome, so what it saves is what the pages look like. The
two files that are not here — the terminal and the Neon console — were taken
by hand; terminal-output.txt holds that output as text.
"""
import pathlib, re, sys
from playwright.sync_api import sync_playwright

OUT = pathlib.Path('/Users/sandra/PennState/festimize/docs/screenshots')
OUT.mkdir(parents=True, exist_ok=True)
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
EMAIL, PASSWORD = 'sandra.demo@festimize.app', 'festimize123'
WANTED = ['Gojira', 'Deftones', 'Korn', 'System of a Down', 'Evanescence', 'Spiritbox',
          'Slipknot', 'Tool', 'Mastodon', 'Opeth', 'Lamb of God', 'Metallica']

def shot(page, name, full=True):
    path = OUT / name
    page.screenshot(path=str(path), full_page=full)
    print('  wrote', name)

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME)
    page = browser.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=2)

    page.goto('http://localhost:8080/register')
    page.fill('#email', EMAIL)
    page.fill('#displayName', 'Sandra')
    page.fill('#password', PASSWORD)
    shot(page, '01-register.png', full=False)
    page.click('button[type=submit]')
    page.wait_for_load_state('networkidle')

    if '/login' in page.url or page.locator('text=Sign in').count() and '/setup' not in page.url:
        page.goto('http://localhost:8080/login')
        page.fill('input[name=username]', EMAIL)
        page.fill('input[name=password]', PASSWORD)
        page.click('button[type=submit]')
        page.wait_for_load_state('networkidle')

    page.goto('http://localhost:8080/setup')
    for name in WANTED:
        box = page.locator('label.card', has_text=re.compile(r'^\s*%s\b' % re.escape(name)))
        if box.count():
            checkbox = box.first.locator('input[type=checkbox]')
            if not checkbox.is_checked():
                checkbox.check()
    page.locator('button:has-text("Save my artists")').first.click()
    page.wait_for_load_state('networkidle')
    page.goto('http://localhost:8080/setup')
    shot(page, '02-setup.png')

    for edition, slug in ((3, 'sick-new-world'), (1, 'bloodstock')):
        page.goto('http://localhost:8080/lineup?editionId=%d' % edition)
        shot(page, '03-lineup-%s.png' % slug)
        page.goto('http://localhost:8080/schedule?editionId=%d' % edition)
        page.locator('form[action$="/schedule/build"] button').first.click()
        page.wait_for_load_state('networkidle')
        shot(page, '04-schedule-%s.png' % slug)

    browser.close()
print('done')
