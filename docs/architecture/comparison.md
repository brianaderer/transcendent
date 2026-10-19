# comparison

**Source:** `backend/src/voices/comparison/` (`commitment.py`, `answer_key.py`, `matching.py`, `scoring.py`)   ·   **Tests:** `backend/tests/comparison/`

## Purpose
Scores a report against what the data says about its date range ([atlas plate
70](../atlas/70-comparison.md), OPEN-21, OPEN-22, OPEN-25), the same way for the version
written with retrieval and the one written without. A report commits to a fixed list beside
its prose; this module builds the answer key from the topic and engagement data, matches the
report's topic names to our topics by meaning, and counts what it got right. All code, no
model call.

## Public interface
- `commitment.Commitment` — `topics: list[NamedTopic]` (`name`, `rank` with 1 the biggest,
  `direction`) and `predicted: list[PredictedTopic]` (`name`, `direction`), with
  `topic_names()` and `predicted_names()`.
- `answer_key.active_topics(data, days) -> list[KeyTopic]` — every topic with engagement in
  the range, ranked biggest first. `answer_key.answer_key(data, days)` — the main topics:
  those ranked `MAIN_TOPICS` or better. `answer_key.main_topics(active)` cuts an already
  read list. `KeyTopic` has `topic_id`, `label`, `description`, `rank` (equal engagement
  shares a rank, the next skips: 1, 2, 2, 4, so a tie at the cut keeps every tied topic),
  `engagement` and `direction`, plus a read-only `id` (the same as `topic_id`) so it can be
  matched. `data` is anything with explore's `TopicData` reads (`ExploreStore`).
- `matching.match_names(names, topics, embedder) -> dict[str, int | None]` — each distinct
  name to the id of the topic it means, or `None`. `topics` are anything with `id`, `label`
  and `description` (`TopicInfo`, `KeyTopic`); `embedder` anything with
  `embed_for_comparison(texts)` (`ComparisonEmbedder`; the ingestion `NomicEmbedder` has it).
- `scoring.score(report, prediction, marking) -> Scores` — `report.topics` scored against
  the main topics and `prediction.predicted` against what happened in the range;
  `report.predicted` (about a period still to come) is not scored. `marking` is a
  `scoring.Marking`: `active` (from `active_topics`), `report_matches` (from
  `match_names(report.topic_names(), active, embedder)`) and `prediction_matches` (from
  `match_names(prediction.predicted_names(), active, embedder)`), matched separately so the
  report and the prediction may each claim the same topic.
- `scoring.Scores` — `main_topics`, `topics_found` (distinct main topics named),
  `topics_invented` (names matching no topic active in the range), `order_agreement`
  (Spearman's rank correlation over the found topics, `None` with fewer than two or when
  one side gives them all one rank), `directions_named` and `directions_right` (over the
  found topics), `predicted_named`, `predicted_prominent` (matched a main topic),
  `predicted_never_came_up` (matched no active topic), `predicted_direction_right` and
  `prediction_score` (`predicted_direction_right / predicted_named`, 0 when none named).
- `scoring.rank_agreement(ours, theirs)` — the Spearman correlation on its own.

All shapes are Pydantic models, so the API can return them.

## How it works
- **The answer key is the Explore page's own measurement.** `active_topics` calls
  `voices.explore.range_topics.topics_in_range`, the function behind the Explore page's topic
  list, so a topic's engagement and direction (`new` if first seen in the range, otherwise
  against the period of the same length before it) are exactly the badge a reviewer sees.
- **Matching by meaning.** Every name and every topic (as `"label: description"`) is
  embedded in one call; a name matches its most similar topic when the cosine similarity is
  at least `MATCH_SIMILARITY`. A topic is claimed once: when several names' best match is
  the same topic, the most similar keeps it and the others match nothing. A name with an
  empty embedding matches nothing; no names means no embedding call.
- **Scoring.** A report name found a topic when its match is a main topic (the first entry
  naming it counts); a name whose match is `None` or a topic quiet in the range was
  invented; a match to an active topic below the cut is neither. Order agreement compares
  the report's ranks with the key's ranks over the found topics, ties sharing their average
  rank. The prediction's names are counted the same way against the key.

## Uses
[explore](explore.md) (`range_topics.topics_in_range` and `TopicData`, `Direction`,
`DayRange`), numpy, Pydantic; an embedder such as
[ingestion](ingestion.md)'s `NomicEmbedder`, passed in.

## Used by
[report](report.md) (`comparison_run` builds the marking and scores both versions).

## Configuration and data
Fixed in code: `MAIN_TOPICS = 10`, `MATCH_SIMILARITY = 0.7` (a starting default, to be
tuned against names real reports produce). Reads `topic_daily_engagement` and `topics`
through its data interface; writes nothing (reports are ephemeral, OPEN-24).
