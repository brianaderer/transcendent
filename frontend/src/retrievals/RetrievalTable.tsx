import { Link } from "@tanstack/react-router";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { useState } from "react";

import type { RankedPost } from "../api/generated";
import { redditLink } from "../explore/links";
import type { DayRange } from "../explore/range";
import { type Agent, AGENT_NAMES } from "./search";
import { NO_TOPIC_YET } from "./TopicBars";

type Props = { posts: RankedPost[]; agent: Agent; range: DayRange };

const BY_RANK: SortingState = [{ id: "rank", desc: false }];

/** The most retrieved posts as a table sortable by any column (TanStack Table). */
export function RetrievalTable({ posts, agent, range }: Props) {
  const [sorting, setSorting] = useState<SortingState>(BY_RANK);
  const table = useReactTable({
    data: posts,
    columns: columnsFor(agent, range),
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm" aria-label="Most retrieved posts">
        <thead className="border-b border-slate-300 dark:border-slate-700">
          {table.getHeaderGroups().map((group) => (
            <tr key={group.id}>
              {group.headers.map((header) => (
                <th
                  key={header.id}
                  className="py-2 pr-4 font-semibold"
                  aria-sort={ariaSort(header.column.getIsSorted())}
                >
                  <button type="button" onClick={header.column.getToggleSortingHandler()}>
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {sortArrow(header.column.getIsSorted())}
                  </button>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="py-2 pr-4 align-top">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function columnsFor(agent: Agent, range: DayRange): ColumnDef<RankedPost>[] {
  return [
    { accessorKey: "rank", header: "Rank" },
    {
      accessorKey: "excerpt",
      header: "Post",
      cell: ({ row }) => <PostExcerpt post={row.original} />,
    },
    { accessorKey: "author", header: "Author", cell: ({ getValue }) => `u/${getValue()}` },
    {
      id: "topic",
      accessorFn: (post) => post.topic_label ?? NO_TOPIC_YET,
      header: "Topic",
      cell: ({ row }) => <TopicName post={row.original} range={range} />,
    },
    { accessorKey: "times_retrieved", header: "Times retrieved" },
    {
      accessorKey: "last_retrieved",
      header: "Last retrieved",
      cell: ({ getValue }) => whenRetrieved(getValue<string>()),
    },
    { id: "agent", accessorFn: () => AGENT_NAMES[agent], header: "Retrieved by" },
  ];
}

function PostExcerpt({ post }: { post: RankedPost }) {
  const link = redditLink({ id: post.post_id, thread_id: post.thread_id, kind: post.kind });
  return (
    <a href={link} target="_blank" rel="noreferrer" className="line-clamp-2 hover:underline">
      {post.excerpt}
    </a>
  );
}

function TopicName({ post, range }: { post: RankedPost; range: DayRange }) {
  if (post.topic_id === null) return <span className="text-slate-500">{NO_TOPIC_YET}</span>;
  return (
    <Link
      to="/topics/$topicId"
      params={{ topicId: String(post.topic_id) }}
      search={range}
      className="text-teal-700 hover:underline dark:text-teal-400"
    >
      {post.topic_label}
    </Link>
  );
}

/** "19 Oct, 07:48" in UTC, the time the store keeps. */
export function whenRetrieved(at: string): string {
  return new Date(at).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  });
}

type Sorted = false | "asc" | "desc";

function ariaSort(sorted: Sorted): "ascending" | "descending" | "none" {
  if (sorted === "asc") return "ascending";
  return sorted === "desc" ? "descending" : "none";
}

function sortArrow(sorted: Sorted): string {
  if (sorted === "asc") return " ↑";
  return sorted === "desc" ? " ↓" : "";
}
