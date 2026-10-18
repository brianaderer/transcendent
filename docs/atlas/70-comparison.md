# 70 — Comparison: with and without retrieval (DRAFT)

[← Index](00-index.md) · [01 System Map](01-system-map.md) · [50 Prediction](50-prediction.md) · [60 Agents](60-agents.md) · [Open questions](90-open-questions.md)

The brief's step 5: how the model writes the Community Voices Document **without** our
store (version A) and **with** it (version B), compared inside the app. Brian asked for
this plate (OPEN-15); everything on it is *proposed*.

```mermaid
flowchart LR
    REQ["Request: a date range<br/>from Explore's Generate report"]
    A["Report agent, version A<br/>no tools"]
    B["Report agent, version B<br/>search · lookup · trends · events"]
    MEAS["Score both against the same answer key<br/>topics, order, direction, prediction"]
    KEY[("Answer key<br/>tags + daily engagement for the range")]
    KEY --> MEAS
    BT["Prediction score<br/>see 50"]
    SCR["Comparison screen<br/>see 31"]

    REQ --> A
    REQ --> B
    A --> MEAS
    B --> MEAS
    MEAS --> SCR
    BT --> SCR
```

## What makes it a fair test

- **One code path, one switch** ([60](60-agents.md), `CLAUDE.md` §7). Same model, same
  settings, same prompt wording, same date range, same output structure. The only difference
  is that version B has tools that read our store.
- **Both run from the same request,** in parallel.

## The measurements

**Specified by Brian:** the document's conclusions are **aggregate** — which topics
the community talked about, how much, and which way each was moving — drawn from the
topic and engagement data, not from individual posts. So the two versions are scored
on whether their aggregate conclusions match what the data shows, **not** on whether
each sentence traces to a post. Per-sentence checking is dropped (OPEN-21).

The answer key is computed by code from the topic tags and the daily engagement table
([21](20-data-model/21-topics.md)) for the date range: which topics were biggest, in
what order, which rose, which fell, which were new. Both versions are scored against
that same answer key *(proposed details below)*.

| Measurement | What it shows | How it's computed *(proposed)* |
|---|---|---|
| **Topics found** | Did the report name the range's real main topics? | Each topic the report names is matched to the nearest tag; count how many of the range's top topics (by engagement) it found |
| **Topics invented** | Topics the report names that the community didn't discuss in the range | Named topics that match no tag with real activity in the range |
| **Order of importance** | Did it rank the topics the way the data does? | How closely the report's ranking agrees with the ranking by engagement |
| **Direction** | For each topic it names, did it say rising, steady or fading correctly? | Compared with the measured trend for that tag |
| **Prediction** | Did the topics it said would be prominent next actually become prominent, moving the way it said? | Both versions commit to a list of expected topics and directions for the requested range, made using only what was known the day before the range began; scored against what happened in the range (OPEN-22, plate [50](50-prediction.md)) |
| **Cost and time** | What retrieval costs | Tokens, tool calls, seconds |

- **The report states its conclusions in a fixed form** alongside its prose: a list of
  topics, each with its rank and direction, plus the predicted ones (OPEN-25). That
  form is what gets scored, so scoring is code, not judgment.
- **Matching a named topic to a tag** is the one step that needs judgment ("winter
  prep" versus the tag "Winterizing and haul-out"). It's done by meaning, with one
  fixed judging prompt for borderline matches, saved with the run and the same for
  both versions.

## No run history

Reports are ephemeral (Brian, OPEN-24): the two reports and their scores are shown when
the run finishes, and nothing keeps them. They may be made downloadable — that's the
only way a report outlives the page *(maybe, Brian)*.

## Open in this draft

- `?` How many of the range's top topics count as "main topics" for scoring — proposed
  the top ten by engagement.
