"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { searchBrowse } from "@/lib/api";
import type { BrowseSearchResultItem } from "@/types/browse";

interface BrowseSearchProps {
  chapterFilter?: string;
  onChapterFilterChange?: (chapter: string) => void;
}

const PAGE_SIZE = 50;

function formatRate(rate: number | string | null): string {
  if (rate === null || rate === undefined) return "—";
  if (typeof rate === "number") return `${rate}%`;
  return rate;
}

export function BrowseSearch({
  chapterFilter,
  onChapterFilterChange,
}: BrowseSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<BrowseSearchResultItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const doSearch = useCallback(
    async (searchQuery: string, searchOffset: number) => {
      if (searchQuery.length < 2) {
        setResults([]);
        setTotal(0);
        setHasSearched(false);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const data = await searchBrowse(
          searchQuery,
          chapterFilter,
          PAGE_SIZE,
          searchOffset
        );
        setResults(data.items);
        setTotal(data.total);
        setHasSearched(true);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Search failed";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [chapterFilter]
  );

  const handleInputChange = (value: string) => {
    setQuery(value);
    setOffset(0);

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      doSearch(value, 0);
    }, 300);
  };

  const handleClear = () => {
    setQuery("");
    setResults([]);
    setTotal(0);
    setOffset(0);
    setHasSearched(false);
    setError(null);
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
  };

  const handlePrevious = () => {
    const newOffset = Math.max(0, offset - PAGE_SIZE);
    setOffset(newOffset);
    doSearch(query, newOffset);
  };

  const handleNext = () => {
    const newOffset = offset + PAGE_SIZE;
    setOffset(newOffset);
    doSearch(query, newOffset);
  };

  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div data-testid="browse-search">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            <Search className="h-4 w-4" aria-hidden="true" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => handleInputChange(e.target.value)}
            placeholder="Search within tariff schedule..."
            className="h-10 w-full rounded-md border bg-background pl-9 pr-9 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label="Search tariff codes"
            data-testid="browse-search-input"
          />
          {query && (
            <button
              onClick={handleClear}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        {onChapterFilterChange && (
          <input
            type="text"
            value={chapterFilter || ""}
            onChange={(e) => onChapterFilterChange(e.target.value)}
            placeholder="Ch."
            className="h-10 w-16 rounded-md border bg-background px-2 text-sm text-center focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label="Filter by chapter"
            data-testid="browse-chapter-filter"
          />
        )}
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Searching...
        </div>
      )}

      {error && (
        <div className="mt-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">
          {error}
        </div>
      )}

      {!isLoading && hasSearched && results.length === 0 && !error && (
        <div className="py-6 text-center text-sm text-muted-foreground" data-testid="browse-search-empty">
          No HS codes match your search
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-3">
          <div className="mb-2 text-xs text-muted-foreground">
            {total} result{total !== 1 ? "s" : ""} found
          </div>
          <div className="space-y-1">
            {results.map((item) => (
              <div
                key={item.id}
                className="rounded-md border px-3 py-2 text-sm"
                data-testid={`search-result-${item.code}`}
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono font-medium">{item.code}</span>
                  <span className="text-xs text-muted-foreground">
                    {item.section_roman} &gt; Ch.{item.chapter_code} &gt;{" "}
                    {item.heading_code}
                  </span>
                </div>
                <div className="mt-0.5 truncate text-muted-foreground">
                  {item.description_vn}
                </div>
                <div className="mt-1 flex gap-3 text-xs">
                  <span>Import: {formatRate(item.duty_rate)}</span>
                  <span>VAT: {formatRate(item.vat_rate)}</span>
                  <span>Export: {formatRate(item.export_duty_rate)}</span>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-3 flex items-center justify-between">
              <button
                onClick={handlePrevious}
                disabled={offset === 0}
                className="rounded-md px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-xs text-muted-foreground">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={handleNext}
                disabled={offset + PAGE_SIZE >= total}
                className="rounded-md px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
