import { useEffect, useState } from "react";

/** Light or dark: starts from the system's choice, then follows the button. */
export function ThemeToggle() {
  const [dark, setDark] = useState(
    () => window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false,
  );
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);
  return (
    <button
      type="button"
      className="rounded border border-slate-300 px-2 py-0.5 dark:border-slate-600"
      onClick={() => setDark(!dark)}
    >
      {dark ? "Light" : "Dark"}
    </button>
  );
}
