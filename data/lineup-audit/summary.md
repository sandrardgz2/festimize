# Festival lineup data audit

Twenty rock and metal festivals checked against English Wikipedia on 30 September 2026.

| Festival | Verdict | Where the lineups live | Years | Artists/year | Stages | Set times |
|---|---|---|---|---|---|---|
| Bloodstock Open Air | **include** | in_article_tables | 2001-2027 (2027 shown as an announced/forthcoming lineup) ['2020 (canc | ~45-50 artists for 2019 Counted distinct band names listed u | True | False |
| Reading and Leeds Festivals | **include** | mixed | 1961-2026 (on the line-ups article); main article separately gives onl | ~35-40 artists for 2019, across roughly six stages WebFetch  | True | partial |
| Graspop Metal Meeting | **include** | in_article_tables | 1996 through the most recent edition (2026 mentioned in current articl | Not independently verified per-year by fetching two individu | True | partial |
| Resurrection Fest | **include** | in_article_tables | 2006–2022, with gaps: no lineup section for 2014, 2017, or 2018, and 2 | Varies a lot by year, counted directly from bullet lists: 20 | partial | False |
| Summer Breeze Open Air | **include** | in_article_tables | Founded 1997; 'Lineup history' section runs 2004–2021 (subsections 1.1 | Not independently counted; estimated at roughly 60-100 per y | partial | False |
| Tuska Open Air Metal Festival | **include** | in_article_tables | Essentially complete: a year section for every year 1998–2026, plus a  | ~60 artist names for 2023, counted directly from the bullet  | partial | False |
| Louder Than Life | **include** | in_article_tables | 2014-2026 continuously, except 2018 (cancelled: rain/weather) and 2020 | Roughly 95-100 artist names for 2024, organized as bulleted  | False | False |
| Aftershock Festival | **include** | in_article_tables | 2012-2026 continuously except 2020 (skipped/postponed due to COVID-19, | 2012 was a single, unstaged, smaller lineup; by 2024-2026 li | True | partial |
| Welcome to Rockville | **include** | in_article_tables | 2011-2026 continuously except 2020 (cancelled, COVID-19, returned 2021 | Roughly 75-100+ artists per recent year (e.g. ~85 for 2025), | True | False |
| Sonic Temple Art & Music Festival | **include** | in_article_tables | 2019, 2023, 2024, 2025, 2026 (announced). Gap: not held 2020-2022 (COV | ~80-100+ per year. Estimated by having WebFetch enumerate th | True | False |
| Download Festival | **maybe** | mixed | 2003-2026 ['2020 (cancelled, COVID-19)', "2021 ('Download Pilot' - a s | 2003-2009: roughly 50-80 artists per year across multiple st | partial | False |
| Rock am Ring and Rock im Park | **maybe** | in_article_tables | 1985-1988, 1991-2019, 2022-present per the infobox, all within one "Pa | Small — typically only a handful of headliners are named per | partial | False |
| Copenhell | **maybe** | in_article_tables | 2010 through 2026, one subsection per year (e.g., "Copenhell 2010", "C | Not fetched year-by-year to count precisely; based on the in | partial | False |
| Brutal Assault | **maybe** | in_article_tables | Article covers festival history 1996–2024, but only two years have an  | ~50–70 for the two populated years (2014, 2024), estimated f | True | False |
| Maryland Deathfest | **maybe** | in_article_tables | Detailed per-year lineup sections exist only for 2003-2016 (confirmed  | ~60-65 bands for 2016 (counted by having WebFetch tally band | True | False |
| Vans Warped Tour | **maybe** | matrix_list_article | Matrix table spans 1995-2019 plus the 2025 revival and announced 2026  | The full matrix has an estimated 800-1,200+ band rows in tot | False | False |
| Wacken Open Air | **exclude** | in_article_tables | 1990-2026 ['2020 and 2021 (cancelled due to COVID-19)'] | Only ~4-6 named headliners per year despite a 'number of ban | False | False |
| Hellfest | **exclude** | in_article_tables | Festival dates back to 2006 (per article); named-band mentions in pros | Not really estimable from the English article. It gives only | False | False |
| Riot Fest | **exclude** | in_article_tables | History section covers 2012-2026, no festival in 2020 (COVID). Most ye | Highly inconsistent: 0 named artists in many years, ~10-15 n | False | False |
| Psycho Las Vegas | **exclude** | none | None on Wikipedia. Festival has run periodically since ~2016 (Las Vega | Cannot estimate from Wikipedia; no article exists to sample. | False | False |

## What to know

- No festival anywhere in this list publishes set times on Wikipedia. Set times exist only for the demo festivals you enter by hand.
- Two festivals keep lineups in a separate article rather than the main one: Reading and Leeds, and Warped Tour.
- The famous festivals are the thin ones. Wacken lists "200 bands" for 2019 and names five. Hellfest says "350 bands" for 2022 and names none.
- German Wikipedia has a dedicated lineups subpage for Brutal Assault covering 1996-2026 at 40-100+ bands per year, where the English article has two usable years. The same pattern may rescue Wacken and Hellfest.
- Years cancelled for COVID (2020, often 2021) must be recorded as cancellations, not as missing data, or the rising-artist measure will read them as a drop.

## Traps worth coding for

- Maryland Deathfest: the infobox claims 2003-2026 but only 2003-2016 have lineup sections.
- Welcome to Rockville: moved city and renamed every stage in 2021; the two eras cannot be merged.
- Riot Fest: most years have no artist list at all, only prose about reunions.
- Warped Tour: touring festival, different lineup per city, so a year means "toured that year" and nothing about stages.
- Summer Breeze: format changes three times between 2004 and 2019 (tables, then prose, then bullets).
- Sonic Temple: the article is at "Sonic Temple (festival)"; the full name redirects.
- Psycho Las Vegas: no Wikipedia article exists at all.
