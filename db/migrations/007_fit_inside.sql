-- Making room for what you asked for.
--
-- The daily limit budgets the sets the scheduler chooses; sets the person
-- adds sit on top of it, so the day runs long and says so. That was the
-- right answer to the software silently booting a band, and it left a worse
-- hole: nothing the person drops brings them back inside, because the
-- scheduler refills the space, so the only way back was to give up the set
-- they had deliberately asked for.
--
-- This is the third option. When it is set, the limit covers the whole day,
-- and the scheduler fits its own choices around what the person asked for
-- instead of alongside it. Korn stays; something the scheduler picked goes.
-- Off by default: nothing is trimmed unless the person asks for it.
ALTER TABLE plan
    ADD COLUMN IF NOT EXISTS fit_inside_limit boolean NOT NULL DEFAULT false;
