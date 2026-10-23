-- Task 5.4 — choosing the other artist when two clash.
--
-- Dropping a set frees its slot and lets the solver decide what fills it.
-- That is not the same as asking for a particular artist: dropping Dying
-- Wish gave the slot to Sevendust, not to the act the page said it beat.
-- Swapping is the other half — "I want this one" — and the solver has to
-- honour it rather than work it out again.
--
-- plan_item.alternative_id records which performance a chosen set displaced,
-- so the page can offer it. It is written by the planner, which is the only
-- thing that knows: the explanation sentence had the artist's name in it and
-- nothing a form could post back.

BEGIN;

ALTER TABLE plan_item
    ADD COLUMN IF NOT EXISTS alternative_id bigint REFERENCES fact_performance;

CREATE TABLE IF NOT EXISTS plan_pinned (
    plan_id        bigint NOT NULL REFERENCES plan ON DELETE CASCADE,
    performance_id bigint NOT NULL REFERENCES fact_performance ON DELETE CASCADE,
    pinned_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (plan_id, performance_id)
);

COMMIT;
