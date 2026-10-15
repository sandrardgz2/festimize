-- Task 4.3 — what loading the historical corpus needs that the base schema
-- did not. Run before db/load_corpus.py; safe to run twice.

BEGIN;

-- An edition that was announced and then called off is kept in the corpus on
-- purpose: a gap and a cancelled year mean different things to a measure that
-- counts how often an artist appears. The announced lineup is real information
-- about who was booked, and it is not an appearance, so the fact rows stay and
-- the edition carries the flag. Every momentum query filters on it.
ALTER TABLE dim_festival_edition
    ADD COLUMN IF NOT EXISTS happened boolean NOT NULL DEFAULT true;

-- A performance read from an article has no set time, so the unique index on
-- (artist, edition, stage, starts_at) never fires for historical rows: in
-- Postgres one NULL is not equal to another. This is the key the corpus
-- actually has — one artist, one edition, one stage.
CREATE UNIQUE INDEX IF NOT EXISTS idx_perf_historical
    ON fact_performance (artist_id, edition_id, COALESCE(stage_id, 0))
    WHERE starts_at IS NULL;

-- Which source a row came from decides whether it may be used commercially:
-- Wikipedia facts and MusicBrainz are fine, setlist.fm's API is licensed for
-- non-commercial use only. Kept queryable rather than written into a comment.
CREATE INDEX IF NOT EXISTS idx_perf_source ON fact_performance (source);

COMMIT;

-- Task 4.4 — the rising measure needs to say which case produced it.
-- Three are possible and they mean different things on a page: a trajectory
-- measured over three or more years, a new name with too little history to
-- have one, and an artist already at the top, who is excluded on purpose
-- because a rising badge on Metallica tells a user nothing.
BEGIN;
ALTER TABLE artist_momentum
    ADD COLUMN IF NOT EXISTS basis text NOT NULL DEFAULT 'trajectory';
ALTER TABLE artist_momentum
    ADD COLUMN IF NOT EXISTS festivals smallint;
COMMIT;
