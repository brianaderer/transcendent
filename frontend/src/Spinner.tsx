/** Turns while work is under way, so it is visible (the loading line, a report's scoring). */
export function Spinner() {
  return (
    <span
      role="status"
      aria-label="Working"
      className="inline-block h-3 w-3 shrink-0 animate-spin rounded-full border-2 border-teal-600 border-t-transparent"
    />
  );
}
