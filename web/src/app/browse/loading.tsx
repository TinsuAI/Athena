export default function BrowseLoading() {
  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 space-y-2">
        <div className="h-9 w-72 animate-pulse rounded bg-muted" />
        <div className="h-5 w-96 animate-pulse rounded bg-muted" />
      </div>
      <div className="mb-6 flex gap-4">
        <div className="h-10 w-48 animate-pulse rounded bg-muted" />
        <div className="h-10 flex-1 animate-pulse rounded bg-muted" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-14 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    </div>
  );
}
