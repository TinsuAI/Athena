/**
 * Loading skeleton for the search page.
 * Shows a skeleton UI while the page is loading.
 */
export default function SearchLoading() {
  return (
    <div className="flex min-h-screen flex-col">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header skeleton */}
        <div className="mb-8 text-center">
          <div className="h-10 w-48 bg-muted animate-pulse rounded mx-auto mb-2" />
          <div className="h-5 w-64 bg-muted animate-pulse rounded mx-auto" />
        </div>

        {/* Search bar skeleton */}
        <div className="mb-8">
          <div className="h-12 w-full bg-muted animate-pulse rounded-md" />
        </div>

        {/* Results skeleton - 3 cards */}
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-24 w-full bg-muted animate-pulse rounded-lg"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
