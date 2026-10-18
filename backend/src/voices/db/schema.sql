-- Tables from atlas plate 21 (topics and engagement) and plate 40 (ingested_days).
-- Every statement is safe to run again: setup runs this on every start.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS threads (
    source_id   text PRIMARY KEY,
    title       text NOT NULL,
    created_at  timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS topics (
    id          bigserial PRIMARY KEY,
    label       text NOT NULL,
    description text NOT NULL,
    keywords    text[] NOT NULL DEFAULT '{}',
    centroid    vector(768) NOT NULL,  -- 768: the size nomic-embed-text produces (OPEN-5)
    first_seen  date NOT NULL,
    last_seen   date NOT NULL
);

CREATE TABLE IF NOT EXISTS cluster_decisions (
    id              bigserial PRIMARY KEY,
    day             date NOT NULL,
    decision        text NOT NULL CHECK (decision IN ('attach', 'mint', 'noise')),
    topic_id        bigint REFERENCES topics (id),
    reason          text NOT NULL,
    candidate_tags  jsonb NOT NULL DEFAULT '[]',
    prompt          text NOT NULL,
    model           text NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    source_id         text PRIMARY KEY,
    thread_source_id  text NOT NULL REFERENCES threads (source_id),
    kind              text NOT NULL CHECK (kind IN ('post', 'comment')),
    author            text NOT NULL,
    created_at        timestamptz NOT NULL,
    body              text NOT NULL,
    reddit_score      integer NOT NULL DEFAULT 0,
    upvotes           integer NOT NULL DEFAULT 0,
    parent_source_id  text,
    embedding         vector(768),
    status            text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'tagged')),
    topic_id          bigint REFERENCES topics (id),
    topic_similarity  real,
    cluster_decision_id bigint REFERENCES cluster_decisions (id)
);
CREATE INDEX IF NOT EXISTS posts_created_at ON posts (created_at);
CREATE INDEX IF NOT EXISTS posts_topic ON posts (topic_id);

CREATE TABLE IF NOT EXISTS post_upvotes_daily (
    post_source_id  text NOT NULL REFERENCES posts (source_id) ON DELETE CASCADE,
    day             date NOT NULL,
    count           integer NOT NULL,
    PRIMARY KEY (post_source_id, day)
);

CREATE TABLE IF NOT EXISTS topic_daily_engagement (
    topic_id              bigint NOT NULL REFERENCES topics (id),
    day                   date NOT NULL,
    posts                 integer NOT NULL DEFAULT 0,
    comments              integer NOT NULL DEFAULT 0,
    upvotes               integer NOT NULL DEFAULT 0,
    unique_authors        integer NOT NULL DEFAULT 0,
    new_threads           integer NOT NULL DEFAULT 0,
    unanswered_questions  integer NOT NULL DEFAULT 0,
    PRIMARY KEY (topic_id, day)
);

CREATE TABLE IF NOT EXISTS retrieval_events (
    id              bigserial PRIMARY KEY,
    post_source_id  text NOT NULL REFERENCES posts (source_id) ON DELETE CASCADE,
    run             text NOT NULL,
    agent           text NOT NULL CHECK (agent IN ('report', 'tagging')),
    tool            text NOT NULL CHECK (tool IN ('search', 'lookup')),
    at              timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingested_days (
    day          date PRIMARY KEY,
    status       text NOT NULL CHECK (status IN ('running', 'done', 'failed')),
    counts       jsonb NOT NULL DEFAULT '{}',
    started_at   timestamptz,
    finished_at  timestamptz
);
