# Deliberately not in this version

Ideas raised while building, parked on purpose so the current scope stays deliverable.

## Setup
- **Type-ahead artist entry.** Instead of a list of checkboxes, let people type any artist
  name and have the system complete it as they type, matching against MusicBrainz rather
  than only the artists already in the database. The checkbox list is a stand-in: it works,
  but it limits taste to artists someone else chose to load.

## Scheduling
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
