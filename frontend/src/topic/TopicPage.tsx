import { Link, useParams, useSearch } from "@tanstack/react-router";
import { useMemo } from "react";

import {
  type DayCount,
  type PostCard,
  type TopicDecision,
  type TopicDetail,
  useReportTopic,
  useReportTopics,
} from "../api/generated";
import { ApiError } from "../api/fetchOrThrow";
import { redditLink } from "../explore/links";
import { type DayRange, dayAndMonth, rangeFrom } from "../explore/range";
import { BADGES } from "../explore/badges";
import { HistoryGate } from "../HistoryGate";
import { engagementSeries } from "./engagement";
import { EngagementChart } from "./EngagementChart";

const NOT_FOUND = 404;

/** One topic in depth (atlas plate 31, screen 4), with the range chosen on Explore. */
export function TopicPage() {
  const { topicId } = useParams({ from: "/topics/$topicId" });
  return (
    <HistoryGate>
      {(history) => <TopicPageForRange topicId={Number(topicId)} history={history} />}
    </HistoryGate>
  );
}

function TopicPageForRange({ topicId, history }: { topicId: number; history: DayCount[] }) {
  const asked = useSearch({ from: "/topics/$topicId" });
  const days = useMemo(() => history.map((day) => day.day), [history]);
  const range = rangeFrom(asked, days);
  const topic = useReportTopic(topicId);
  if (topic.isPending) return <p>Loading the topic…</p>;
  if (topic.isError) return <p>{whyNotShown(topic.error)}</p>;
  return <TopicView topic={topic.data} days={days} range={range} />;
}

function whyNotShown(error: unknown): string {
  if (error instanceof ApiError && error.status === NOT_FOUND) return "There is no such topic.";
  return "The topic couldn't be loaded.";
}

type ViewProps = { topic: TopicDetail; days: string[]; range: DayRange };

function TopicView({ topic, days, range }: ViewProps) {
  const series = useMemo(() => engagementSeries(days, topic.daily), [days, topic.daily]);
  return (
    <article className="space-y-8">
      <TopicHeader topic={topic} range={range} />
      <EngagementChart series={series} range={range} />
      <TypicalPosts posts={topic.typical_posts} />
      <Timeline decisions={topic.decisions} />
    </article>
  );
}

function TopicHeader({ topic, range }: { topic: TopicDetail; range: DayRange }) {
  return (
    <header className="space-y-2">
      <Link to="/" search={range} className="text-sm text-teal-700 dark:text-teal-400">
        ← Back to Explore
      </Link>
      <div className="flex flex-wrap items-baseline gap-3">
        <h2 className="font-serif text-2xl font-semibold">{topic.label}</h2>
        <Badge topicId={topic.id} range={range} />
      </div>
      <p className="max-w-3xl">{topic.description}</p>
      <ul aria-label="Keywords" className="flex flex-wrap gap-2">
        {topic.keywords.map((keyword) => (
          <li
            key={keyword}
            className="rounded-full bg-slate-200 px-2 py-0.5 text-xs dark:bg-slate-800"
          >
            {keyword}
          </li>
        ))}
      </ul>
      <p className="text-sm text-slate-500">
        First seen {dayAndMonth(topic.first_seen)} · last seen {dayAndMonth(topic.last_seen)}
      </p>
    </header>
  );
}

/** The badge the topic has on Explore for the same range, read from the same answer. */
function Badge({ topicId, range }: { topicId: number; range: DayRange }) {
  const topics = useReportTopics(range);
  const inRange = topics.data?.find((topic) => topic.id === topicId);
  if (!topics.data) return null;
  const label = inRange ? BADGES[inRange.direction] : "Quiet in these days";
  return (
    <span className="rounded border border-slate-300 px-2 py-0.5 text-xs font-medium dark:border-slate-600">
      {label}
    </span>
  );
}

function TypicalPosts({ posts }: { posts: PostCard[] }) {
  return (
    <section aria-label="Typical posts" className="space-y-3">
      <SectionHeading>Typical posts</SectionHeading>
      <ul className="grid gap-4 md:grid-cols-3">
        {posts.map((post) => (
          <li
            key={post.post_id}
            className="space-y-2 rounded-lg border border-slate-200 p-4 dark:border-slate-700"
          >
            <p className="text-xs text-slate-500">
              u/{post.author} · {dayAndMonth(post.day)}
            </p>
            <p className="font-medium">{post.title}</p>
            <p className="text-sm">{post.excerpt}</p>
            <a
              href={redditLink({ id: post.post_id, thread_id: post.thread_id, kind: post.kind })}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-teal-700 dark:text-teal-400"
            >
              Open on Reddit
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Timeline({ decisions }: { decisions: TopicDecision[] }) {
  return (
    <section aria-label="How this topic was built" className="space-y-3">
      <SectionHeading>How this topic was built</SectionHeading>
      <ol className="space-y-2 border-l border-slate-300 pl-4 dark:border-slate-700">
        {decisions.map((decision, n) => (
          <li key={n} className="text-sm">
            <span className="font-medium">
              {dayAndMonth(decision.day)} · {describeDecision(decision)}
            </span>{" "}
            <span className="text-slate-600 dark:text-slate-400">— {decision.reason}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

/** "minted · 3 threads", or just "attached" when its threads were all decided again later. */
export function describeDecision(decision: Pick<TopicDecision, "decision" | "threads">): string {
  const action = decision.decision === "mint" ? "minted" : "attached";
  if (decision.threads === 0) return action;
  return `${action} · ${decision.threads} ${decision.threads === 1 ? "thread" : "threads"}`;
}

function SectionHeading({ children }: { children: string }) {
  return (
    <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">{children}</h3>
  );
}
