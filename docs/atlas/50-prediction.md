# 50 — Prediction (DRAFT)

[← Index](00-index.md) · [01 System Map](01-system-map.md) · [21 Topics](20-data-model/21-topics.md) · [Open questions](90-open-questions.md)

How the "next week" half of the Community Voices Document is produced.

**Specified by Brian:** posts are tagged day by day on intake (plate
[21](20-data-model/21-topics.md)), so any period is a range of days. Lining those
periods up gives each tag a **trend
vector**, and next week is predicted by **extrapolating** each tag's trend.
**Everything else is *proposed*,** except where a section says what build step 5 has
already built (`backend/src/voices/prediction/`, see `docs/architecture/prediction.md`).

```mermaid
flowchart LR
    ENG[("topic_daily_engagement<br/>see 21")]
    VEC["Trend vector per tag<br/>engagement in each of the four periods before the range"]
    FIT["Extrapolate one period ahead<br/>damped trend on a log scale: growth slows rather than running away"]
    RANK["Rank tags<br/>rising · steady · fading · new"]
    CTX["Signals the numbers can't see<br/>(dates mentioned in posts, threads still open)"]
    LLM["LLM writes the prediction<br/>each claim cites its numbers and posts"]
    BT["Prediction score<br/>predict the range from the day before it,<br/>score against what happened"]

    ENG --> VEC --> FIT --> RANK --> LLM
    CTX --> LLM
    FIT --> BT
    classDef open stroke-dasharray: 5 5
    class CTX,BT open
```

## The trend vector *(built in step 5)*

For each tag, one number per period: its engagement (posts, comments and upvotes, that
is agreeing replies, added together), summed from plate 21's daily table. The vector
covers the **four periods** before the range, each as long as the range (so four weeks
for a weekly report), and is read only up to the day before the range begins. The
daily table also counts distinct people, new threads and unanswered questions; the
projection does not use them yet. A tag minted recently has zeros in its early periods,
and the fit starts at its first period with any engagement. Tags quiet in all four
periods are left out.

## Extrapolating *(built in step 5)*

- **A damped trend, not a straight line.** With only a few periods of history a
  straight-line projection overreacts: one viral thread looks like a rocket. A damped
  trend (Holt's method with damping) follows the direction but expects it to level off,
  which is how online conversations usually behave. The fit starts with a flat trend, so
  a single spike can't launch it: 10, 10, 10, 1000 projects about 900, not past the
  spike, while 10, 20, 40, 80 projects about 104. The settings (how quickly the level
  and the trend follow new values, and how much of the trend each step ahead keeps)
  are fixed in code and listed in `docs/architecture/prediction.md`.
- **On a log scale** (one plus the engagement, so a silent period is zero), so a topic
  going from 2 to 4 posts and one going from 50 to 100 read as the same growth.
- **The output per tag:** expected engagement for the period, a range (one typical
  fitting error either side, never narrower than about two thirds to one and a half times
  the expected value), and a label: **new** if the tag was first seen in the last period
  before the range, otherwise **rising**, **steady** or **fading** by the Explore page's
  rule (more than a quarter above or below the last period).

## What extrapolation can't see, and how it's covered *(proposed)*

- **A topic with no history** can't be extrapolated. A tag first seen on or after the
  range's first day is left out of the projection; one first seen in the last period
  before it is labelled new.
- **Scheduled things:** a contest deadline or a software release mentioned in posts.
  These are pulled from the period's posts and handed to the LLM alongside the
  numbers.
- **Brand-new conversations next week** can't be predicted by any method. The
  document says so rather than inventing them.

## The written prediction *(proposed)*

The LLM receives the ranked tags with their trend numbers, the scheduled-event
signals, and the most typical posts for each tag. It writes the prediction, and
every claim names its evidence ("up from 3 to 11 threads over three weeks").
Version A of the comparison (`CLAUDE.md` §7) receives none of this, only the
community and the dates.

## Scoring the prediction

**Decided by Brian (OPEN-22), to try first:**

- **The A/B test scores a committed list, not prose or numbers.** Alongside its prose,
  each version (with and without our data) commits to a short fixed list: the topics
  it expects to be prominent in the next period, and whether each is rising, steady or
  fading. That list is checked against what actually happened: how many named topics
  became prominent, how many never came up, how many directions were right. Version A
  has no data to make numbers from, so comparing numbers would not be a fair contest.
- **Scored straight away, on a period that has already happened.** When a report is
  generated for a date range, both versions are also asked to predict that range using
  only what was known the day before it began — posts, tags and centroids as they stood
  then, nothing from inside the range (OPEN-11). The range has already happened, so both
  predictions are scored at once, and every report shows a prediction score, including
  the first one in a demo.
- **The code's numerical projections are checked separately.** How close the projected
  engagement for each topic came to the real figure is shown on its own, as a check on
  the trend method, and is not part of the A/B scores.

The stored history covers **eight weeks** (specified, OPEN-7), so the earliest ranges
have little history before them; the score says how much history the prediction had.

## Open in this draft

- Nothing open on this plate.
