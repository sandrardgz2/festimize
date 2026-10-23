-- Must-see artists.
--
-- Every saved artist carried the same weight, so when two of them clashed the
-- scheduler broke the tie on match score — arithmetic deciding which band you
-- lose. Measured 2026-10-23: one demo account had four clashing pairs among
-- its own saved artists on a single bill, and nothing in the data said which
-- of each pair mattered more.
--
-- A festival-goer has two or three bands they came for and a dozen they would
-- like to catch. This is where they say which.
alter table user_artist
    add column if not exists must_see boolean not null default false;

comment on column user_artist.must_see is
    'The person came for this one. Never dropped for a break or a cap, and wins any clash with an ordinary pick.';
