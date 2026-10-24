-- Sets the daily limit left out.
--
-- The cap is a budget for the scheduler's own choices, so when a day runs
-- over it gives up the weakest set it is allowed to give up. That is the
-- right behaviour and it happened in silence: adding Jesus Piece to one demo
-- plan took the day past 450 minutes and Vended, a 58% match, simply was not
-- there afterwards. The add button had said "drops Vended" at the moment of
-- the click and nothing recorded it, so the schedule afterwards could not
-- account for its own contents.
--
-- Rewritten wholesale with the plan, like plan_item: these are a property of
-- the solve, not a decision the person made.
CREATE TABLE IF NOT EXISTS plan_omitted (
    plan_id        bigint NOT NULL REFERENCES plan(plan_id) ON DELETE CASCADE,
    performance_id bigint NOT NULL REFERENCES fact_performance(performance_id) ON DELETE CASCADE,
    day_on         date   NOT NULL,
    minutes        int    NOT NULL,
    PRIMARY KEY (plan_id, performance_id)
);
