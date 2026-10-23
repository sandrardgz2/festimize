-- Catching part of a set.
--
-- A gap in a day often has something playing across it that you can only
-- see half of, because the first half runs under the band you are already
-- watching. The schedule page offers those, and the offer was wired to the
-- ordinary "add", which pins the whole set — so accepting "40 of its 60
-- minutes fall in this gap" removed the set those other 20 minutes clashed
-- with. On the account this was found on, that was one of the person's own
-- picks.
--
-- A pin may now carry a window. The candidate is clamped to it before the
-- solver runs, so a set you are only catching the end of is, as far as the
-- day is concerned, a set that starts when you get there. It then fits the
-- gap exactly and displaces nothing, which is what the sentence promised.
--
-- Null means the whole set, which is every pin made before today.
ALTER TABLE plan_pinned
    ADD COLUMN IF NOT EXISTS from_at timestamptz,
    ADD COLUMN IF NOT EXISTS to_at   timestamptz;
