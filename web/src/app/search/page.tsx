"use client";

import { useRef, useCallback } from "react";
import { SearchBar } from "./components/SearchBar";
import { useKeyboardShortcuts } from "@/lib/hooks/useKeyboardShortcuts";
import { useStore } from "@/lib/store";
import { searchHsCodes } from "@/lib/api";

/**
 * Search page with SearchBar component.
 * Search is triggered by button click or Enter key to avoid unnecessary API calls.
 */
export default function SearchPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Zustand store selectors
  const searchQuery = useStore((state) => state.searchQuery);
  const searchResult = useStore((state) => state.searchResult);
  const isSearching = useStore((state) => state.isSearching);
  const searchError = useStore((state) => state.searchError);
  const setSearchQuery = useStore((state) => state.setSearchQuery);
  const setSearchResult = useStore((state) => state.setSearchResult);
  const setIsSearching = useStore((state) => state.setIsSearching);
  const setSearchError = useStore((state) => state.setSearchError);
  const clearSearch = useStore((state) => state.clearSearch);

  // Set up keyboard shortcuts (/ and Cmd+K)
  useKeyboardShortcuts({ inputRef });

  // Execute search when button clicked or Enter pressed
  const executeSearch = useCallback(async () => {
    const query = searchQuery.trim();

    // Skip empty queries
    if (!query) {
      return;
    }

    // Cancel any in-flight requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();

    setIsSearching(true);
    setSearchError(null);

    try {
      const result = await searchHsCodes(
        query,
        abortControllerRef.current.signal
      );
      setSearchResult(result);
    } catch (err) {
      // Ignore abort errors
      if (err instanceof Error && err.name === "AbortError") {
        return;
      }
      const message =
        err instanceof Error ? err.message : "Search failed. Please try again.";
      setSearchError(message);
      setSearchResult(null);
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery, setSearchResult, setIsSearching, setSearchError]);

  const handleQueryChange = (value: string) => {
    setSearchQuery(value);
  };

  const handleClear = () => {
    clearSearch();
  };

  return (
    <div className="flex min-h-screen flex-col">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2">Athena</h1>
          <p className="text-muted-foreground text-lg">
            HS Code Lookup Tool - Search by product description
          </p>
        </div>

        {/* Search bar with button */}
        <div className="mb-8">
          <SearchBar
            ref={inputRef}
            value={searchQuery}
            onChange={handleQueryChange}
            onSearch={executeSearch}
            onClear={handleClear}
            isLoading={isSearching}
            autoFocus
          />
          <p className="text-sm text-muted-foreground mt-2 text-center">
            Press Enter or click Search to find HS codes
          </p>
        </div>

        {/* Error message */}
        {searchError && (
          <div
            className="mb-4 p-4 bg-destructive/10 text-destructive rounded-lg"
            role="alert"
          >
            {searchError}
          </div>
        )}

        {/* Search result - single best match */}
        {searchResult && (
          <div className="space-y-4">
            <div className="border rounded-lg p-6 bg-card">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-mono font-bold text-primary">
                    {searchResult.hs_code}
                  </h2>
                  <p className="text-muted-foreground mt-1">
                    {searchResult.description}
                  </p>
                </div>
                <div className="text-right">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary/10 text-primary">
                    {searchResult.confidence}% match
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <span className="text-sm text-muted-foreground">Duty Rate</span>
                  <p className="font-semibold">{searchResult.duty_rate}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">VAT Rate</span>
                  <p className="font-semibold">{searchResult.vat_rate}</p>
                </div>
              </div>

              {searchResult.classification && (
                <div className="border-t pt-4 mt-4">
                  <h3 className="text-sm font-semibold mb-2">Classification Reasoning</h3>
                  <div className="space-y-2 text-sm">
                    <p><span className="text-muted-foreground">Material:</span> {searchResult.classification.material}</p>
                    <p><span className="text-muted-foreground">Function:</span> {searchResult.classification.function}</p>
                  </div>
                </div>
              )}

              {searchResult.practical_notes && searchResult.practical_notes.length > 0 && (
                <div className="border-t pt-4 mt-4">
                  <h3 className="text-sm font-semibold mb-2">Practical Notes</h3>
                  <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                    {searchResult.practical_notes.map((note, index) => (
                      <li key={index}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty state - only show when no query and no result */}
        {!searchQuery && !isSearching && !searchResult && !searchError && (
          <div className="text-center py-12 text-muted-foreground">
            <p className="mb-2">Enter a product description to search</p>
            <p className="text-sm">
              Try: &quot;coffee beans&quot;, &quot;máy xay&quot;, or an HS code like &quot;0901&quot;
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
