export default function Loading() {
  return (
    <div
      className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-4 py-10"
      role="status"
      aria-live="polite"
      aria-label="Loading page"
    >
      <span className="sr-only">Loading…</span>

      <div className="animate-pulse">
        <div className="mb-8 h-8 w-48 rounded-lg bg-muted" />

        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="rounded-xl border border-border bg-card p-6"
            >
              <div className="mb-4 h-5 w-2/3 rounded bg-muted" />
              <div className="mb-2 h-4 w-full rounded bg-muted" />
              <div className="h-4 w-4/5 rounded bg-muted" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}