import { Link } from "@tanstack/react-router";

import { BackendStatus } from "./BackendStatus";
import { IngestionStatus } from "./IngestionStatus";
import { ThemeToggle } from "./ThemeToggle";

export function TopBar() {
  return (
    <header className="border-b border-slate-200 dark:border-slate-800">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-1 px-4 py-3">
        <h1 className="font-serif text-lg font-semibold">Community Voices</h1>
        <nav className="text-sm">
          <Link to="/" className="font-medium text-teal-700 dark:text-teal-400">
            Explore
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
