"""
Which festivals go into the corpus, and where their lineups live.

Taken from the audit in data/lineup-audit/ (30 September 2026), which checked
twenty rock and metal festivals against English Wikipedia and recorded, for
each, whether the lineups are listed year by year and how many artists appear.

The famous festivals are not the useful ones: Wacken's article names five bands
for a year it says had two hundred, and Hellfest names none. They are marked
`setlistfm` here and come from a different source.

`page` is the English Wikipedia title. `first` and `last` bound the years worth
asking for. `cancelled` years are recorded as cancellations rather than left
missing, because a gap and a cancellation mean different things to the
rising-artist measure.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Festival:
    key: str
    name: str
    country: str
    source: str                       # 'wikipedia' | 'setlistfm'
    page: Optional[str] = None
    first: int = 2010
    last: int = 2026
    cancelled: List[int] = field(default_factory=list)
    note: str = ""


WIKIPEDIA = [
    Festival('bloodstock', 'Bloodstock Open Air', 'GB', 'wikipedia',
             'Bloodstock Open Air', 2001, 2026, [2020]),
    Festival('reading-leeds', 'Reading and Leeds Festivals', 'GB', 'wikipedia',
             'Reading and Leeds Festivals line-ups', 2001, 2026, [2020],
             note='lineups live in a separate article, not the main one'),
    Festival('graspop', 'Graspop Metal Meeting', 'BE', 'wikipedia',
             'Graspop Metal Meeting', 1996, 2026, [2020, 2021]),
    Festival('resurrection', 'Resurrection Fest', 'ES', 'wikipedia',
             'Resurrection Fest', 2006, 2026, [2020, 2021],
             note='no lineup section for 2014, 2017 or 2018'),
    Festival('summer-breeze', 'Summer Breeze Open Air', 'DE', 'wikipedia',
             'Summer Breeze Open Air', 2004, 2026, [2020],
             note='format changes three times between 2004 and 2019'),
    Festival('tuska', 'Tuska Open Air Metal Festival', 'FI', 'wikipedia',
             'Tuska Open Air Metal Festival', 1998, 2026, [2020, 2021]),
    Festival('louder-than-life', 'Louder Than Life', 'US', 'wikipedia',
             'Louder Than Life', 2014, 2026, [2018, 2020],
             note='2018 cancelled for weather, 2020 for COVID'),
    Festival('aftershock', 'Aftershock Festival', 'US', 'wikipedia',
             'Aftershock Festival', 2012, 2026, [2020]),
    Festival('rockville', 'Welcome to Rockville', 'US', 'wikipedia',
             'Welcome to Rockville', 2011, 2026, [2020],
             note='moved city and renamed every stage in 2021; the two eras do not merge'),
    Festival('sonic-temple', 'Sonic Temple Art & Music Festival', 'US', 'wikipedia',
             'Sonic Temple (festival)', 2019, 2026, [2020, 2021, 2022]),
    Festival('download', 'Download Festival', 'GB', 'wikipedia',
             'Download Festival', 2003, 2026, [2020],
             note='2003-2009 list properly, later years thin out into prose'),
    Festival('copenhell', 'Copenhell', 'DK', 'wikipedia',
             'Copenhell', 2010, 2026, [2020, 2021]),
    Festival('maryland-deathfest', 'Maryland Deathfest', 'US', 'wikipedia',
             'Maryland Deathfest', 2003, 2016, [],
             note='infobox claims 2003-2026 but only 2003-2016 have lineup sections'),
]

# Festivals whose Wikipedia articles name a handful of headliners and nothing
# else. These need setlist.fm, which records who actually played on the day.
SETLISTFM = [
    Festival('wacken', 'Wacken Open Air', 'DE', 'setlistfm', None, 1999, 2026, [2020, 2021]),
    Festival('hellfest', 'Hellfest', 'FR', 'setlistfm', None, 2006, 2026, [2020, 2021]),
    Festival('brutal-assault', 'Brutal Assault', 'CZ', 'setlistfm', None, 2006, 2026, [2020, 2021],
             note='German Wikipedia also has a full lineups subpage if setlist.fm falls short'),
    Festival('psycho-las-vegas', 'Psycho Las Vegas', 'US', 'setlistfm', None, 2016, 2026, [2020]),
]

ALL = WIKIPEDIA + SETLISTFM
BY_KEY = {f.key: f for f in ALL}
