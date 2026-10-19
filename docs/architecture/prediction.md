# prediction

**Source:** `backend/src/voices/prediction/` (`trends.py`)   ·   **Tests:** `backend/tests/prediction/`

## Purpose
Each topic's trend as it stood the day before a date range began, projected onto the range
([atlas plate 50](../atlas/50-prediction.md)). The report run (build step 5) hands these
numbers to version B of the report so it can predict the range, and checks the projection
against what happened, outside the A/B scores (atlas OPEN-22). Only what was known the day
before the range is used, never anything from inside it (OPEN-11).

## Public interface
- `trends.topic_trends(data, days) -> list[TopicTrend]` — every topic known before
  `days.start` (its `first_seen` is earlier) with engagement in the `PERIODS_SHOWN` periods
  before the range, highest projection first (ties by topic id). Topics quiet in every
  period are left out.
- `trends.TopicTrend` (Pydantic) — `topic_id`, `label`, `description`, `periods`
  (engagement in each period before the range, oldest first), `expected` (projected
  engagement for the range), `low` and `high` (the projection's range, never below zero),
  `direction` (`new`, `rising`, `steady` or `fading`).
- `trends.TrendData` — the reads it needs: `topic_days(first_day, last_day)` and
  `topics(ids)`, the same as explore's `TopicData`; `ExploreStore` satisfies it.
- `trends.periods_before(days)` — the `PERIODS_SHOWN` periods of the range's length just
  before it, oldest first, the last ending the day before the range.
- `trends.damped_projection(series) -> (next, spread)` — the projection itself, on any
  series (the caller takes `log1p` first).

## How it works
- **One read**, from the first day of the oldest period to the day before the range; each
  topic's daily engagement (posts, comments and upvotes) is summed per period.
- **Damped trend on a log scale.** Each topic's per-period engagement goes through `log1p`,
  so 2 → 4 and 50 → 100 read as the same growth, then through Holt's linear method with a
  damped trend: the level moves `LEVEL_SMOOTHING` of the way to each new value, the trend
  `TREND_SMOOTHING` of the way to the latest change, and each step ahead keeps only
  `DAMPING` of the trend, so growth levels off instead of running away. The fit starts at
  the topic's first period with any engagement (silence before a topic existed is not
  growth) with a flat trend, so a single jump can't launch it: a history of 10, 10, 10,
  1000 projects about 900, not past the spike, while 10, 20, 40, 80 projects about 104.
  The result goes back through `expm1`.
- **The range** is the projection plus and minus the typical one-step fitting error (root
  mean square, on the log scale), never narrower than `SMALLEST_SPREAD`.
- **Direction.** `new` when the topic was first seen in the last period before the range;
  otherwise `voices.explore.direction.trend` comparing the rounded projection with the last
  period: more than a quarter up is `rising`, more than a quarter down `fading`.

## Uses
[explore](explore.md) (`DayRange`, `direction.trend`, `range_topics.TopicData` and
`rows_by_topic`, the `TopicDay` and `TopicInfo` rows), Pydantic.

## Used by
[report](report.md) (version B's `topic_trends` tool when predicting a range).

## Configuration and data
Fixed in code: `PERIODS_SHOWN = 4`, `LEVEL_SMOOTHING = 0.7`, `TREND_SMOOTHING = 0.5`,
`DAMPING = 0.8`, `SMALLEST_SPREAD = 0.4` (on the log scale, about ±50%). Reads
`topic_daily_engagement` and `topics` through its data interface; writes nothing.
Labels and descriptions are read as they are now, not as they stood before the range.
