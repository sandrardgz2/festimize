-- Choosing where to eat.
--
-- The scheduler places one meal a day, in the first real opportunity after
-- the middle of the day, honouring the "eat by" deadline. That is a
-- reasonable default and it is still only a guess about somebody else's
-- afternoon. Where there are gaps to choose between, the person should be
-- able to say which one.
--
-- One row per plan per day. No row means the scheduler decides, which is
-- also what happens when the chosen gap stops existing because the day was
-- rebuilt around different artists.
CREATE TABLE IF NOT EXISTS plan_meal (
    plan_id    bigint      NOT NULL REFERENCES plan(plan_id) ON DELETE CASCADE,
    meal_on    date        NOT NULL,
    starts_at  timestamptz NOT NULL,
    chosen_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (plan_id, meal_on)
);
