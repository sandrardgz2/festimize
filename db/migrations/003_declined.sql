-- Task 5.4 — sets the person has turned down on a particular plan.
--
-- A plan-level fact, deliberately not a taste-level one. Turning down a set
-- says "not this one, this weekend"; it does not say the artist is not to
-- their taste, and it must not reach the profile that scores every other
-- artist. Saving an artist you have never heard, by contrast, would do both —
-- it would pull every future recommendation toward them and hand them the
-- scheduler's +10 pick bonus. These are different intentions and this table
-- is the smaller of the two.
--
-- Declines survive a rebuild, which is the point: the plan is regenerated
-- from scratch each time, so without somewhere to record them the set the
-- person just rejected comes straight back.

BEGIN;

CREATE TABLE IF NOT EXISTS plan_declined (
    plan_id        bigint NOT NULL REFERENCES plan ON DELETE CASCADE,
    performance_id bigint NOT NULL REFERENCES fact_performance ON DELETE CASCADE,
    declined_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (plan_id, performance_id)
);

COMMIT;
