-- When this person last changed something the scheduler reads about them.
--
-- "Rebuild my schedule" re-ran the solver and overwrote the timeline, which
-- almost never changed anything: the edits a person makes on that page —
-- pins, declines, the meal, the day's hours, the fit-inside flag — live in
-- their own tables and are inputs to the solve, not part of its output. Same
-- inputs, deterministic solver, same schedule. Meanwhile every action on the
-- page already rebuilds for itself, so by the time anybody pressed the
-- button the plan was already current.
--
-- The one thing it is actually for is picking up a change made somewhere
-- else: artists saved or removed on setup, a must-see starred, a pace
-- setting edited. This records that, so the button can be shown only when it
-- would do something.
--
-- Backfilled to created_at rather than now(), so existing plans — all built
-- after their account was made — do not all come back wanting a rebuild.
alter table app_user
    add column if not exists taste_changed_at timestamptz;

update app_user set taste_changed_at = created_at where taste_changed_at is null;

alter table app_user
    alter column taste_changed_at set not null,
    alter column taste_changed_at set default now();

comment on column app_user.taste_changed_at is
    'Last change to the artists, stars or pace this person''s schedule is built from. Compared against plan.updated_at to decide whether a rebuild would do anything.';
