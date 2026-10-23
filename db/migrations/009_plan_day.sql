-- Arrival and departure, a day at a time.
--
-- app_user.earliest_start and latest_end are one window applied to every day
-- of every festival. Nobody attends a weekend that way: people drive up after
-- work on the Friday and are on site from ten on the Saturday. With only the
-- account-wide setting, somebody arriving late on day one had to either lose
-- the mornings of every other day or lie to the app about the first.
--
-- One row per plan per day, and both columns are nullable: "I arrive at four
-- on Friday" says nothing about when I leave. No row means the day keeps the
-- account-wide window, which is still the right answer for most days.
--
-- These are wall-clock times at the festival, with no zone, and must not be
-- converted — see AppUserRepository.paceTimes for the five-hour bug that
-- taught us so. Java moves them as text and lets Postgres do the only cast.
CREATE TABLE IF NOT EXISTS plan_day (
    plan_id    bigint NOT NULL REFERENCES plan(plan_id) ON DELETE CASCADE,
    day_on     date   NOT NULL,
    arrive_at  time,
    leave_by   time,
    chosen_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (plan_id, day_on),
    -- A row that says nothing is just a row the scheduler has to look at.
    CONSTRAINT plan_day_says_something CHECK (arrive_at IS NOT NULL OR leave_by IS NOT NULL)
);
