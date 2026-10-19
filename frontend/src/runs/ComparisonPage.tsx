import { Link, useParams } from "@tanstack/react-router";
import Markdown from "react-markdown";

import type { KeyTopic, RunResult, VersionResult } from "../api/generated";
import { describeDays } from "../explore/range";
import { scoreboard } from "./scoreboard";
import { useFinishedRun } from "./useFinishedRun";
import { VERSION_ORDER, VERSIONS } from "./versions";

/** Version A against version B (atlas plate 31, screen 3, and plate 70). */
export function ComparisonPage() {
  const { runId } = useParams({ from: "/runs/$runId/comparison" });
  const run = useFinishedRun(runId);
  if ("notice" in run) return <p>{run.notice}</p>;
  const [a, b] = VERSION_ORDER.map((v) => run.result.versions.find((r) => r.version === v)!);
  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-serif text-2xl font-semibold">With and without retrieval</h1>
        <p className="text-sm text-slate-500">
          {describeDays(run.result)} · {run.result.model} · identical instructions; version A reads
          a few posts, only version B searches
        </p>
      </header>
      <Scoreboard a={a} b={b} />
      <TopicGrid result={run.result} a={a} b={b} />
      <div className="grid gap-6 lg:grid-cols-2">
        <Column version={a} title={VERSIONS.A.long} runId={runId} accent="text-amber-700" />
        <Column version={b} title={VERSIONS.B.long} runId={runId} accent="text-teal-700" />
      </div>
    </div>
  );
}

function Scoreboard({ a, b }: { a: VersionResult; b: VersionResult }) {
  return (
    <table className="w-full max-w-2xl text-sm" aria-label="Scores">
      <thead>
        <tr className="text-left text-slate-500">
          <th className="py-1 font-medium">Measurement</th>
          <th className="py-1 font-medium text-amber-700">A</th>
          <th className="py-1 font-medium text-teal-700">B</th>
        </tr>
      </thead>
      <tbody>
        {scoreboard(a, b).map((row) => (
          <tr key={row.measurement} className="border-t border-slate-200 dark:border-slate-700">
            <td className="py-1">{row.measurement}</td>
            <td className="py-1 tabular-nums">{row.a}</td>
            <td className="py-1 tabular-nums">{row.b}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** The answer key against both reports: what each named, at what rank, and which way. */
function TopicGrid({ result, a, b }: { result: RunResult; a: VersionResult; b: VersionResult }) {
  return (
    <table className="w-full text-sm" aria-label="The range's real topics against both reports">
      <thead>
        <tr className="text-left text-slate-500">
          <th className="py-1 font-medium">The range's main topics</th>
          <th className="py-1 font-medium">Measured</th>
          <th className="py-1 font-medium text-amber-700">A said</th>
          <th className="py-1 font-medium text-teal-700">B said</th>
        </tr>
      </thead>
      <tbody>
        {result.main_topics.map((topic) => (
          <tr key={topic.topic_id} className="border-t border-slate-200 dark:border-slate-700">
            <td className="py-1">
              {topic.rank}. {topic.label}
            </td>
            <td className="py-1 capitalize">{topic.direction}</td>
            <td className="py-1">{whatItSaid(a, topic)}</td>
            <td className="py-1">{whatItSaid(b, topic)}</td>
          </tr>
        ))}
        {[a, b].flatMap((version) =>
          invented(version).map((name) => (
            <tr
              key={`${version.version}-${name}`}
              className="border-t border-slate-200 text-rose-700 dark:border-slate-700"
            >
              <td className="py-1">{name}</td>
              <td className="py-1">not discussed in the range</td>
              <td className="py-1">{version.version === "A" ? "named" : ""}</td>
              <td className="py-1">{version.version === "B" ? "named" : ""}</td>
            </tr>
          )),
        )}
      </tbody>
    </table>
  );
}

function whatItSaid(version: VersionResult, topic: KeyTopic): string {
  const named = version.topics.find((t) => version.report_matches[t.name] === topic.topic_id);
  return named ? `#${named.rank}, ${named.direction}` : "—";
}

function invented(version: VersionResult): string[] {
  return version.topics.filter((t) => version.report_matches[t.name] == null).map((t) => t.name);
}

type ColumnProps = { version: VersionResult; title: string; runId: string; accent: string };

function Column({ version, title, runId, accent }: ColumnProps) {
  return (
    <section>
      <h2 className={`mb-2 text-sm font-semibold ${accent}`}>
        {version.version} · {title}
      </h2>
      <div className="font-serif text-sm [&_h2]:mt-4 [&_h2]:font-semibold [&_h3]:mt-3 [&_h3]:font-semibold [&_p]:my-2">
        <Markdown>{version.document}</Markdown>
      </div>
      <Link
        to="/runs/$runId/report"
        params={{ runId }}
        search={{ version: version.version }}
        className="mt-2 inline-block text-sm text-teal-700 dark:text-teal-400"
      >
        Read version {version.version} on its own
      </Link>
    </section>
  );
}
