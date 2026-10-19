import { Link, useParams, useSearch } from "@tanstack/react-router";
import Markdown from "react-markdown";

import type { RunResult, VersionResult } from "../api/generated";
import { SUBREDDIT } from "../community";
import { describeDays } from "../explore/range";
import { useFinishedRun } from "./useFinishedRun";
import { VERSIONS } from "./versions";

/** The Community Voices Document (atlas plate 31, screen 2). */
export function ReportPage() {
  const { runId } = useParams({ from: "/runs/$runId/report" });
  const { version = "B" } = useSearch({ from: "/runs/$runId/report" });
  const run = useFinishedRun(runId);
  if ("notice" in run) return <p>{run.notice}</p>;
  const shown = run.result.versions.find((v) => v.version === version) ?? run.result.versions[0];
  return <Document result={run.result} version={shown} />;
}

function Document({ result, version }: { result: RunResult; version: VersionResult }) {
  return (
    <article className="mx-auto max-w-3xl">
      <header className="mb-6 border-b border-slate-200 pb-4 dark:border-slate-700">
        <h1 className="font-serif text-3xl font-semibold">Community Voices — r/{SUBREDDIT}</h1>
        <p className="mt-1 text-slate-500">{describeDays(result)}</p>
        <p className="mt-1 text-sm text-slate-500">
          Written {VERSIONS[version.version].short} · {result.model} ·{" "}
          <Link
            to="/runs/$runId/comparison"
            params={{ runId: result.run_id }}
            className="text-teal-700 dark:text-teal-400"
          >
            See the comparison
          </Link>
        </p>
      </header>
      <div className="grid gap-8 lg:grid-cols-[1fr_16rem]">
        <div className="prose prose-slate max-w-none font-serif dark:prose-invert [&_h2]:mt-6 [&_h2]:text-xl [&_h2]:font-semibold [&_h3]:mt-4 [&_h3]:font-semibold [&_p]:my-3">
          <Markdown>{version.document}</Markdown>
        </div>
        <aside className="space-y-6 text-sm">
          <TopicList
            title="Its topics"
            rows={version.topics.map((t) => [`${t.rank}. ${t.name}`, t.direction])}
          />
          <TopicList
            title="What it expected"
            rows={version.predicted.map((p) => [p.name, p.direction])}
          />
          <p className="text-xs text-slate-500">{version.prediction_reasoning}</p>
        </aside>
      </div>
    </article>
  );
}

function TopicList({ title, rows }: { title: string; rows: [string, string][] }) {
  return (
    <section>
      <h2 className="mb-1 font-semibold">{title}</h2>
      <table className="w-full">
        <tbody>
          {rows.map(([name, direction]) => (
            <tr key={name} className="border-t border-slate-200 dark:border-slate-700">
              <td className="py-1">{name}</td>
              <td className="py-1 text-right capitalize text-slate-500">{direction}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
