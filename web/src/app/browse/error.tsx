"use client";

export default function BrowseError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      <div className="rounded-lg border bg-card p-12 text-center">
        <h2 className="mb-2 text-xl font-semibold text-destructive">
          Failed to load Tariff Schedule
        </h2>
        <p className="mb-4 text-muted-foreground">{error.message}</p>
        <button
          onClick={reset}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
