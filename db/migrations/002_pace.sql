-- Task 5.3 — the pace settings from the Profile & Settings wireframe.
-- Every column here drives something the scheduler already does, because a
-- settings page whose controls change nothing is worse than no settings page.
--
--   stamina           -> the daily music cap (light 5h, moderate 7.5h, hard 10h)
--   max_run_minutes   -> build_day(max_run_minutes=...), how long before a break
--   meal_by           -> the latest a meal break may land
--   earliest_start    -> sets before this are not offered
--   latest_end        -> sets ending after this are not offered
--
-- Defaults are the constants the scheduler used before anyone could change
-- them, so an account that never visits the page behaves exactly as it did.

BEGIN;

ALTER TABLE app_user ADD COLUMN IF NOT EXISTS stamina text NOT NULL DEFAULT 'moderate';
ALTER TABLE app_user ADD COLUMN IF NOT EXISTS max_run_minutes smallint NOT NULL DEFAULT 180;
ALTER TABLE app_user ADD COLUMN IF NOT EXISTS meal_by time NOT NULL DEFAULT '18:00';
ALTER TABLE app_user ADD COLUMN IF NOT EXISTS earliest_start time;
ALTER TABLE app_user ADD COLUMN IF NOT EXISTS latest_end time;

ALTER TABLE app_user DROP CONSTRAINT IF EXISTS app_user_stamina_check;
ALTER TABLE app_user ADD CONSTRAINT app_user_stamina_check
    CHECK (stamina IN ('light', 'moderate', 'hard'));

COMMIT;
