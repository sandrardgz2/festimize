"""
What the rising measure must not say.

Every case here is a mistake the measure made on the real corpus before it was
corrected, so these are regression tests rather than illustrations. No database
is needed: the measure is a function of a list of bookings, which is most of
the reason it is written that way.

The reasoning behind each rule, and the backtest that chose the measure in the
first place, is in docs/evaluation/momentum-backtest.md.
"""
from app.momentum import ARRIVED, SPREAD, score, shares, usable_years

FULL = list(range(2015, 2026))
THIN_YEAR = 2021
ORDINARY = [y for y in FULL if y != THIN_YEAR]


def circuit(years=ORDINARY, festivals=33, slots=40, regulars=400, each=10):
    """
    A plausible corpus to test against.

    The shape matters more than the size, and two versions of this fixture
    failed before this one, both for the same reason: the measure's idea of
    "already arrived" is the top tenth of the circuit, and a percentile means
    nothing through a flat distribution. A first version gave every artist one
    booking a year, so the top-tenth cut landed on the only value there was
    and every artist came back `arrived`. The second spread the tail out but
    still had nobody at the top, so the cut landed on the tail again.

    So this has three layers, like the real corpus: `regulars` who are on
    every other bill and occupy the top tenth, a long tail of acts who play
    one festival in some years and not others, and whatever a test adds. The
    real corpus's cut sits at about half a booking a year; this one's sits
    well above anything a test climbs to, which is what makes the assertions
    about a mid-table artist mean something.
    """
    rows = []
    for k, year in enumerate(years):
        for n in range(festivals):
            for slot in range(slots):
                i = n * slots + slot
                if (i + k) % ((i % 9) + 1) == 0:
                    rows.append((year, 'Festival %d' % n, 'Filler %d' % i))
        for big in range(regulars):
            for n in range(each):
                rows.append((year, 'Festival %d' % ((big + n) % festivals),
                             'Regular %d' % big))
    return rows


def test_a_thin_year_is_left_out():
    """
    2021 held 15 festivals against a median of 30 and scraped past a half
    threshold, which made every pandemic booking count double.
    """
    rows = circuit() + [(THIN_YEAR, 'Festival 0', 'Someone')]
    assert THIN_YEAR not in usable_years(rows)
    assert 2015 in usable_years(rows)


def test_the_newest_year_is_left_out():
    """Its lineups are still being announced, so it is not a year yet."""
    assert max(ORDINARY) not in usable_years(circuit())


def test_a_booking_counts_once_however_many_stages():
    """
    Two sets at one festival is that festival's programme, not twice as much
    of the circuit.
    """
    rows = [(2015, 'Festival 0', 'Once'),
            (2015, 'Festival 0', 'Twice'), (2015, 'Festival 0', 'Twice')]
    held = shares(rows, [2015])
    assert held[2015]['Twice'] == held[2015]['Once'] == 0.5


def test_a_local_residency_is_not_a_badge():
    """
    Nina Black and Luna & Lenthe scored in the top ten on Tomorrowland and
    Rock Werchter every year — two Belgian festivals, which is a residency.
    """
    rows = circuit()
    for year in (2022, 2023, 2024, 2025):
        rows += [(year, 'Festival 0', 'Local DJ'), (year, 'Festival 1', 'Local DJ')]
    found = score(rows)['Local DJ']
    assert found['festivals'] < SPREAD
    assert not found['rising']


def test_a_veteran_is_returning_not_rising():
    """Hoobastank topped the list on six festivals in four years, formed 1994."""
    rows = circuit()
    for year in (2022, 2023, 2024, 2025):
        for n in range(6):
            rows.append((year, 'Festival %d' % n, 'Old Band'))
    assert score(rows)['Old Band']['basis'] == 'trajectory'
    assert score(rows, {'Old Band': 1994})['Old Band']['basis'] == 'returning'


def test_an_artist_at_the_top_is_not_rising():
    """A badge on an artist everyone has heard of tells the user nothing."""
    rows = circuit()
    for year in ORDINARY:
        for n in range(33):
            rows.append((year, 'Festival %d' % n, 'Headliner'))
    assert score(rows)['Headliner']['basis'] == 'arrived'
    assert not score(rows)['Headliner']['rising']


def test_two_years_of_history_gets_no_prediction():
    """
    Eight signals were tested on artists this new and none beat knowing how
    much of last year they held, so the measure says nothing about them.
    """
    rows = circuit()
    for year in (2024, 2025):
        for n in range(5):
            rows.append((year, 'Festival %d' % n, 'Newcomer'))
    found = score(rows)['Newcomer']
    assert found['basis'] == 'new'
    assert found['score'] == 0.0
    assert found['appearances'] == 10


def test_a_climbing_artist_is_found():
    """The measure has to actually fire, which is easy to lose while tightening."""
    rows = circuit()
    for year, many in ((2019, 1), (2022, 2), (2023, 3), (2024, 4), (2025, 5)):
        for n in range(many):
            rows.append((year, 'Festival %d' % n, 'Climber'))
    found = score(rows)['Climber']
    assert found['basis'] == 'trajectory', found
    assert found['rising'], found


def test_an_artist_who_has_stopped_is_not_rising():
    """
    070 Shake's shares run 0,0,0,0,5.5,2.3,12.1,2.5,0 — a peak in 2023 and
    nothing in the most recent year. The early zeros tilt a fitted line
    upwards, so the gradient alone would call that rising.
    """
    rows = circuit()
    for year, many in ((2018, 1), (2022, 3), (2023, 5)):
        for n in range(many):
            rows.append((year, 'Festival %d' % n, 'Stopped'))
    found = score(rows)['Stopped']
    assert found['last_year'] == 2023
    assert not found['rising'], found
