# Deliberately not in this version

Ideas raised while building, parked on purpose so the current scope stays deliverable.

## Setup
- **Type-ahead artist entry.** Instead of a list of checkboxes, let people type any artist
  name and have the system complete it as they type, matching against MusicBrainz rather
  than only the artists already in the database. The checkbox list is a stand-in: it works,
  but it limits taste to artists someone else chose to load.

## Recommender
- **Split taste breaks the single profile.** The profile is the average of every saved
  artist, so someone who loves both metal and electronic music gets a profile sitting
  between the two, matching neither well. The artists that should score highest score
  middling instead. Known fixes, in order of effort: score against the *best matching*
  saved artist rather than the average; or cluster the saved artists into two or three
  profiles and take the strongest match across them. This matters for real users, not
  just in theory — it is the normal case for anyone with range.

## Scheduling
- **Splitting a clash.** The scheduler treats a set as all or nothing, so when two artists
  someone loves play at once, one is simply lost. People do not behave that way: they watch
  half of one and walk to the other. Modelling it means deciding how much of a set's value
  half of it is worth (not half — the headline moment is usually at the end), accounting for
  the walk between stages, and showing split blocks on the timeline. Worth doing, and bigger
  than it looks.

- **A discovery dial.** The scheduler reserves one set in three for artists the user did not
  name. That ratio is a configuration value today; exposing it as a slider ("how adventurous")
  would let people choose between a favourites weekend and a discovery weekend, and makes the
  novelty metric something the user controls rather than something done to them.
- Constraint solver (CP-SAT) benchmarked against the greedy scheduler.
- Walking distance between stages; break timing informed by the weather forecast.

## Social
- Group mode: one schedule that works for several people at once.
- Plain-language refinement: "keep Sunday easy", and the day rebuilds.

## Data
- Publish the historical lineup dataset.
