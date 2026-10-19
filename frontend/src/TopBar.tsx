import { Link, useSearch } from "@tanstack/react-router";

import { BackendStatus } from "./BackendStatus";
import { CommunityHeadline } from "./CommunityHeadline";
import { IngestionStatus } from "./IngestionStatus";
import { ThemeToggle } from "./ThemeToggle";

const CURRENT_PAGE = { className: "text-teal-700 dark:text-teal-400" };
const OTHER_PAGE = { className: "text-slate-600 dark:text-slate-300" };

export function TopBar() {
  const { start, end } = useSearch({ strict: false }); // the range goes with you to every screen
  return (
    <header className="border-b border-slate-200 dark:border-slate-800">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-1 px-4 py-3">
        <div className="leading-tight">
          <h1 className="font-serif text-lg font-semibold">Community Voices</h1>
          <CommunityHeadline />
        </div>
        <nav className="flex gap-4 text-sm">
          <Link
            to="/"
            search={{ start, end }}
            className="font-medium"
            activeProps={CURRENT_PAGE}
            inactiveProps={OTHER_PAGE}
            activeOptions={{ exact: true, includeSearch: false }}
          >
            Explore
          </Link>
          <Link
            to="/retrievals"
            search={{ start, end }}
            className="font-medium"
            activeProps={CURRENT_PAGE}
            inactiveProps={OTHER_PAGE}
            activeOptions={{ includeSearch: false }}
          >
            Retrieval stats
          </Link>
        </nav>
        <div className="ml-auto flex flex-wrap items-center gap-x-4 text-xs text-slate-500 [&_p]:m-0">
          <IngestionStatus />
          <BackendStatus />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
