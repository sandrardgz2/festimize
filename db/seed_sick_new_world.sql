-- Sick New World 2027 — demonstration edition.
--
-- IMPORTANT: Sick New World is a real festival, but this 2027 lineup and these set
-- times are fabricated for demonstration. They are not an announced lineup and must
-- never be presented as one, nor mixed into the historical dataset.
--
-- Set times are stored without a timezone offset, matching the other seeds: the
-- database runs in GMT and every festival's times are treated as local wall-clock.
--
-- Chosen as a demo because its nu-metal and alternative-metal bill exercises the
-- recommender against a modern-metal taste profile, where the classic-metal
-- Bloodstock lineup does not.

BEGIN;

INSERT INTO dim_festival (name, country, city, website)
SELECT 'Sick New World', 'US', 'Las Vegas', NULL
WHERE NOT EXISTS (SELECT 1 FROM dim_festival WHERE name = 'Sick New World');

INSERT INTO dim_festival_edition (festival_id, year, start_date, end_date)
SELECT festival_id, 2027, DATE '2027-04-24', DATE '2027-04-24' FROM dim_festival WHERE name = 'Sick New World'
ON CONFLICT (festival_id, year) DO NOTHING;

INSERT INTO dim_stage (festival_id, name, size_rank)
SELECT festival_id, 'Main Stage', 1 FROM dim_festival WHERE name = 'Sick New World'
ON CONFLICT (festival_id, name) DO NOTHING;
INSERT INTO dim_stage (festival_id, name, size_rank)
SELECT festival_id, 'Desert Stage', 2 FROM dim_festival WHERE name = 'Sick New World'
ON CONFLICT (festival_id, name) DO NOTHING;
INSERT INTO dim_stage (festival_id, name, size_rank)
SELECT festival_id, 'Neon Stage', 3 FROM dim_festival WHERE name = 'Sick New World'
ON CONFLICT (festival_id, name) DO NOTHING;

INSERT INTO dim_date (date_id, date, year, month, day, day_of_week)
VALUES (20270424, DATE '2027-04-24', 2027, 4, 24, 6) ON CONFLICT DO NOTHING;

INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 13:00:00+00:00', TIMESTAMPTZ '2027-04-24 13:45:00+00:00', 7, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'static-x' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Main Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 14:15:00+00:00', TIMESTAMPTZ '2027-04-24 15:00:00+00:00', 6, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'sevendust' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Main Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 15:30:00+00:00', TIMESTAMPTZ '2027-04-24 16:30:00+00:00', 5, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'mudvayne' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Main Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 17:00:00+00:00', TIMESTAMPTZ '2027-04-24 18:00:00+00:00', 4, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'evanescence' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Main Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 18:30:00+00:00', TIMESTAMPTZ '2027-04-24 19:30:00+00:00', 3, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'bring me the horizon' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Main Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 20:00:00+00:00', TIMESTAMPTZ '2027-04-24 21:15:00+00:00', 2, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'slipknot' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Main Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 21:45:00+00:00', TIMESTAMPTZ '2027-04-24 23:15:00+00:00', 1, true, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'system of a down' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Main Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 12:30:00+00:00', TIMESTAMPTZ '2027-04-24 13:10:00+00:00', 8, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'drain' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Desert Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 13:30:00+00:00', TIMESTAMPTZ '2027-04-24 14:10:00+00:00', 7, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'scowl' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Desert Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 14:30:00+00:00', TIMESTAMPTZ '2027-04-24 15:10:00+00:00', 6, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'dying wish' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Desert Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 15:30:00+00:00', TIMESTAMPTZ '2027-04-24 16:20:00+00:00', 5, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'knocked loose' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Desert Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 16:45:00+00:00', TIMESTAMPTZ '2027-04-24 17:40:00+00:00', 4, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'turnstile' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Desert Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 18:00:00+00:00', TIMESTAMPTZ '2027-04-24 18:55:00+00:00', 3, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'underoath' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Desert Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 19:30:00+00:00', TIMESTAMPTZ '2027-04-24 20:40:00+00:00', 2, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'deftones' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Desert Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 21:15:00+00:00', TIMESTAMPTZ '2027-04-24 22:40:00+00:00', 1, true, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'korn' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Desert Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 12:15:00+00:00', TIMESTAMPTZ '2027-04-24 12:50:00+00:00', 8, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'zulu' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Neon Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 13:15:00+00:00', TIMESTAMPTZ '2027-04-24 13:55:00+00:00', 7, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'vended' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Neon Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 14:15:00+00:00', TIMESTAMPTZ '2027-04-24 14:55:00+00:00', 6, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'static dress' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Neon Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 15:15:00+00:00', TIMESTAMPTZ '2027-04-24 16:05:00+00:00', 5, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'spiritbox' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Neon Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 16:30:00+00:00', TIMESTAMPTZ '2027-04-24 17:20:00+00:00', 4, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'code orange' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Neon Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 17:45:00+00:00', TIMESTAMPTZ '2027-04-24 18:40:00+00:00', 3, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'bad omens' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Neon Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 19:15:00+00:00', TIMESTAMPTZ '2027-04-24 20:15:00+00:00', 2, false, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'ministry' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Neon Stage'
ON CONFLICT DO NOTHING;
INSERT INTO fact_performance (artist_id, edition_id, stage_id, date_id, starts_at, ends_at, billing_rank, is_headliner, source, confidence)
SELECT a.artist_id, e.edition_id, s.stage_id, 20270424,
       TIMESTAMPTZ '2027-04-24 21:00:00+00:00', TIMESTAMPTZ '2027-04-24 22:15:00+00:00', 1, true, 'manual', 1.0
FROM dim_artist a, dim_festival_edition e, dim_festival f, dim_stage s
WHERE a.name_normalized = 'the prodigy' AND f.name = 'Sick New World' AND e.festival_id = f.festival_id
  AND e.year = 2027 AND s.festival_id = f.festival_id AND s.name = 'Neon Stage'
ON CONFLICT DO NOTHING;

COMMIT;
