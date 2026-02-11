"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getLookups } from "@/lib/api";
import { LookupList } from "./components/LookupList";
import type { LookupListItem } from "@/types/lookup";

type VerifiedFilter = "all" | "verified" | "unverified";

const PAGE_SIZE = 20;

export default function LookupsPage() {
  const router = useRouter();
  const [items, setItems] = useState<LookupListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [verifiedFilter, setVerifiedFilter] = useState<VerifiedFilter>("all");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLookups = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const verified =
        verifiedFilter === "all"
          ? undefined
          : verifiedFilter === "verified";

      const data = await getLookups(PAGE_SIZE, offset, verified);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load lookups";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [offset, verifiedFilter]);

  useEffect(() => {
    fetchLookups();
  }, [fetchLookups]);

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const handlePrevious = () => {
    if (offset >= PAGE_SIZE) {
      setOffset(offset - PAGE_SIZE);
    }
  };

  const handleNext = () => {
    if (offset + PAGE_SIZE < total) {
      setOffset(offset + PAGE_SIZE);
    }
  };

  const handleFilterChange = (filter: VerifiedFilter) => {
    setVerifiedFilter(filter);
    setOffset(0);
  };

  const handleRowClick = (id: number) => {
    router.push(`/lookups/${id}`);
  };

  const filterButtons: { label: string; value: VerifiedFilter }[] = [
    { label: "All", value: "all" },
    { label: "Verified", value: "verified" },
    { label: "Unverified", value: "unverified" },
  ];

  return (
    <div className="container mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Lookup History</h1>
        <p className="mt-1 text-muted-foreground">
          Browse past HS code lookups and their verification status
        </p>
      </div>

      {/* Filter toggle */}
      <div className="mb-4 flex gap-2">
        {filterButtons.map((btn) => (
          <button
            key={btn.value}
            onClick={() => handleFilterChange(btn.value)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              verifiedFilter === btn.value
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div
          className="mb-4 rounded-lg bg-destructive/10 p-4 text-destructive"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
        </div>
      )}

      {/* Results */}
      {!isLoading && !error && items.length > 0 && (
        <div className="rounded-lg border bg-card">
          <LookupList items={items} onRowClick={handleRowClick} />

          {/* Pagination */}
          <div className="flex items-center justify-between border-t px-4 py-3">
            <button
              onClick={handlePrevious}
              disabled={offset === 0}
              className="rounded-md px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={handleNext}
              disabled={offset + PAGE_SIZE >= total}
              className="rounded-md px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && items.length === 0 && (
        <div className="rounded-lg border bg-card p-12 text-center">
          <p className="text-lg text-muted-foreground">
            No lookups yet. Search for HS codes to start building history.
          </p>
        </div>
      )}
    </div>
  );
}
