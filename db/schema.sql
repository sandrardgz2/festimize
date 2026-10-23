-- Festimize — PostgreSQL schema (Neon)
-- Task 2.3.  Two halves in one database:
--   app_*      the operational side the web app reads and writes
--   dim_/fact_ the star schema the analytics service reads
-- Run top to bottom on a fresh database.

BEGIN;

-- ---------------------------------------------------------------- reference
CREATE TABLE dim_artist (
    artist_id        bigserial PRIMARY KEY,
    mbid             uuid UNIQUE,                    -- MusicBrainz id: the canonical key
    name             text        NOT NULL,
    name_normalized  text        NOT NULL,           -- lowercased, punctuation stripped, for matching
    disambiguation   text,                           -- MusicBrainz uses this to split same-name artists
    country          char(2),
    formed_year      smallint,
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_artist_normalized ON dim_artist (name_normalized);
-- Identity for artists without a MusicBrainz id yet: name plus disambiguation.
-- Without this there is no key to use for ON CONFLICT, because mbid is nullable
-- and NULL never conflicts with NULL.
CREATE UNIQUE INDEX idx_artist_identity ON dim_artist (name_normalized, COALESCE(disambiguation, ''));

-- Tags are the whole basis of taste matching, so weight and source both matter.
CREATE TABLE artist_tag (
    artist_id  bigint      NOT NULL REFERENCES dim_artist ON DELETE CASCADE,
    tag        text        NOT NULL,
    weight     numeric(6,3) NOT NULL DEFAULT 1,      -- Last.fm count, or 1 for MusicBrainz genres
    source     text        NOT NULL,                 -- 'musicbrainz' | 'lastfm'
    PRIMARY KEY (artist_id, tag, source)
);
CREATE INDEX idx_artist_tag_tag ON artist_tag (tag);

CREATE TABLE dim_festival (
    festival_id  bigserial PRIMARY KEY,
    name         text NOT NULL,
    country      char(2),
    city         text,
    website      text,
    UNIQUE (name, country)
);

-- One row per year the festival runs. Lineups belong to an edition, not a festival.
CREATE TABLE dim_festival_edition (
    edition_id   bigserial PRIMARY KEY,
    festival_id  bigint NOT NULL REFERENCES dim_festival ON DELETE CASCADE,
    year         smallint NOT NULL,
    start_date   date,
    end_date     date,
    -- An edition that was announced and then called off. The lineup is kept
    -- rather than deleted: it is a real fact about who was booked, and it is
    -- not an appearance. Counting one would show an artist's career carrying
    -- on through a year nobody played, so the rising measure filters on this.
    happened     boolean NOT NULL DEFAULT true,
    UNIQUE (festival_id, year)
);

CREATE TABLE dim_stage (
    stage_id     bigserial PRIMARY KEY,
    festival_id  bigint NOT NULL REFERENCES dim_festival ON DELETE CASCADE,
    name         text NOT NULL,
    size_rank    smallint,                           -- 1 = main stage. Drives the rising-artist measure.
    UNIQUE (festival_id, name)
);

CREATE TABLE dim_date (
    date_id      integer PRIMARY KEY,                -- yyyymmdd
    date         date NOT NULL UNIQUE,
    year         smallint NOT NULL,
    month        smallint NOT NULL,
    day          smallint NOT NULL,
    day_of_week  smallint NOT NULL
);

-- ---------------------------------------------------------------- the fact
-- One row = one artist playing one festival edition.
-- Historical rows have no set times; demo festivals are entered by hand and do.
CREATE TABLE fact_performance (
    performance_id bigserial PRIMARY KEY,
    artist_id      bigint  NOT NULL REFERENCES dim_artist,
    edition_id     bigint  NOT NULL REFERENCES dim_festival_edition ON DELETE CASCADE,
    stage_id       bigint  REFERENCES dim_stage,
    date_id        integer REFERENCES dim_date,
    starts_at      timestamptz,
    ends_at        timestamptz,
    billing_rank   smallint,                         -- position on the poster, 1 = top
    is_headliner   boolean NOT NULL DEFAULT false,
    source         text    NOT NULL,                 -- 'wikipedia' | 'wikidata' | 'manual'
    confidence     numeric(3,2) NOT NULL DEFAULT 1.0,-- below 1 = flagged for review
    UNIQUE (artist_id, edition_id, stage_id, starts_at)
);
CREATE INDEX idx_perf_artist  ON fact_performance (artist_id);
CREATE INDEX idx_perf_edition ON fact_performance (edition_id);
CREATE INDEX idx_perf_review  ON fact_performance (confidence) WHERE confidence < 1.0;
-- Historical rows have no set time, and in Postgres one NULL is never equal to
-- another, so the index above can never fire for them. This is the key the
-- corpus actually has: one artist, one edition, one stage.
CREATE UNIQUE INDEX idx_perf_historical
    ON fact_performance (artist_id, edition_id, COALESCE(stage_id, 0))
    WHERE starts_at IS NULL;
-- Which source a row came from decides whether it may be used commercially:
-- Wikipedia facts and MusicBrainz are fine, setlist.fm's API is non-commercial.
CREATE INDEX idx_perf_source ON fact_performance (source);

-- ---------------------------------------------------------------- the app
CREATE TABLE app_user (
    user_id       bigserial PRIMARY KEY,
    email         text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    display_name  text,
    -- How this person wants their days paced. Every one of these drives
    -- something the scheduler does; a settings page whose controls change
    -- nothing is worse than no settings page. Defaults are the constants used
    -- before anyone could change them, so an untouched account is unaffected.
    stamina         text NOT NULL DEFAULT 'moderate'
                    CHECK (stamina IN ('light', 'moderate', 'hard')),
    max_run_minutes smallint NOT NULL DEFAULT 180,   -- before a break is due
    meal_by         time NOT NULL DEFAULT '18:00',   -- latest a meal may land
    earliest_start  time,                            -- null = whenever it opens
    latest_end      time,                            -- null = until it closes
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- Taste lives on the account, never on a plan: that is what makes switching festivals cheap.
CREATE TABLE user_artist (
    user_id    bigint NOT NULL REFERENCES app_user ON DELETE CASCADE,
    artist_id  bigint NOT NULL REFERENCES dim_artist,
    added_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, artist_id)
);

CREATE TABLE plan (
    plan_id     bigserial PRIMARY KEY,
    user_id     bigint NOT NULL REFERENCES app_user ON DELETE CASCADE,
    edition_id  bigint NOT NULL REFERENCES dim_festival_edition ON DELETE CASCADE,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, edition_id)                     -- one plan per person per festival edition
);

CREATE TABLE plan_item (
    plan_item_id   bigserial PRIMARY KEY,
    plan_id        bigint NOT NULL REFERENCES plan ON DELETE CASCADE,
    item_type      text   NOT NULL CHECK (item_type IN ('SET','REST','MEAL')),
    performance_id bigint REFERENCES fact_performance, -- null for REST and MEAL
    starts_at      timestamptz NOT NULL,
    ends_at        timestamptz NOT NULL,
    reason         text,                               -- why the scheduler chose this
    CHECK (ends_at > starts_at),
    CHECK ((item_type = 'SET') = (performance_id IS NOT NULL))
);
CREATE INDEX idx_plan_item_plan ON plan_item (plan_id, starts_at);

-- Sets turned down on this plan. A plan-level fact, deliberately not a
-- taste-level one: "not this one, this weekend" is a different statement from
-- "this artist is not to my taste", and only the second belongs in the
-- profile that scores everything else. Declines survive a rebuild, because
-- the plan is regenerated from scratch and the rejected set would otherwise
-- come straight back.
CREATE TABLE plan_declined (
    plan_id        bigint NOT NULL REFERENCES plan ON DELETE CASCADE,
    performance_id bigint NOT NULL REFERENCES fact_performance ON DELETE CASCADE,
    declined_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (plan_id, performance_id)
);

-- Cached taste scores, so a lineup page is a read and not 120 model calls.
CREATE TABLE artist_score (
    user_id      bigint NOT NULL REFERENCES app_user ON DELETE CASCADE,
    artist_id    bigint NOT NULL REFERENCES dim_artist ON DELETE CASCADE,
    match_score  numeric(5,4) NOT NULL,              -- 0..1
    computed_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, artist_id)
);

-- Rising measure: one row per artist, recomputed in batch.
CREATE TABLE artist_momentum (
    artist_id       bigint PRIMARY KEY REFERENCES dim_artist ON DELETE CASCADE,
    momentum_score  numeric(5,4) NOT NULL,
    appearances     smallint NOT NULL,
    -- How many different festivals, which is not the same as how many
    -- appearances: two neighbouring festivals every year is a residency, not
    -- a rise, and three is the least a rising badge accepts.
    festivals       smallint,
    first_year      smallint,
    last_year       smallint,
    -- Which case produced the score. 'trajectory' is a measured climb over
    -- three or more years; 'returning' is the same climb by an artist who
    -- formed decades ago; 'new' is too little history to say anything, and the
    -- page shows the bookings instead; 'arrived' is an artist already at the
    -- top of the circuit, excluded on purpose because a rising badge on them
    -- tells a user nothing. See docs/evaluation/momentum-backtest.md.
    basis           text NOT NULL DEFAULT 'trajectory',
    computed_at     timestamptz NOT NULL DEFAULT now()
);

COMMIT;
