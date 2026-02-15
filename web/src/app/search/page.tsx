"use client";

import { useRef, useCallback, useState } from "react";
import { SearchBar } from "./components/SearchBar";
import { CorrectionButton } from "./components/CorrectionButton";
import { CorrectionPanel } from "./components/CorrectionPanel";
import { HSCodeTree } from "@/components/ui/HSCodeTree";
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
  const [correctionPanelOpen, setCorrectionPanelOpen] = useState(false);

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
    <div className="min-h-screen bg-[var(--background)]">
      <div className="mx-auto px-7 py-10 max-w-4xl">
        {/* Header area */}
        <div className="mb-10 text-center">
          <h1 className="text-[32px] font-extrabold text-slate-900 tracking-tight mb-1.5">
            Athena
          </h1>
          <p className="text-[14px] text-slate-400 font-medium">
            HS Code Lookup Tool &mdash; Search by product description
          </p>
        </div>

        {/* Search bar */}
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
          <p className="text-[12px] text-slate-400 mt-2.5 text-center font-medium">
            Press Enter or click Search to find HS codes
          </p>
        </div>

        {/* Error message */}
        {searchError && (
          <div
            className="mb-6 p-4 bg-red-50 text-red-700 border border-red-100 rounded-xl text-[13px] font-medium"
            role="alert"
          >
            {searchError}
          </div>
        )}

        {/* Search result card */}
        {searchResult && (
          <div className="space-y-4">
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)]">
              <div className="flex items-start justify-between mb-5">
                <div>
                  <h2 className="text-[22px] font-mono font-bold text-emerald-700 tracking-tight leading-tight">
                    {searchResult.hs_code}
                  </h2>
                  <p className="text-[13.5px] text-slate-500 mt-1.5 font-medium leading-snug">
                    {searchResult.description}
                  </p>
                </div>
                <span className="inline-flex items-center px-3.5 py-1 rounded-full text-[12px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100 shrink-0 ml-4">
                  {searchResult.confidence}% match
                </span>
              </div>

              {/* Rate pills */}
              <div className="flex gap-2.5 mb-5">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-semibold bg-blue-50 text-blue-800 border border-blue-100">
                  <span className="font-sans font-medium text-[10px] opacity-70">Import</span>
                  {searchResult.duty_rate}
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-semibold bg-amber-50 text-amber-800 border border-amber-100">
                  <span className="font-sans font-medium text-[10px] opacity-70">VAT</span>
                  {searchResult.vat_rate}
                </span>
              </div>

              {/* Classification reasoning */}
              {searchResult.classification && (
                <div className="border-t border-slate-100 pt-4 mt-4">
                  <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">
                    Classification Reasoning
                  </h3>
                  <div className="space-y-2.5">
                    <div className="flex gap-3">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider w-20 pt-0.5 shrink-0">Material</span>
                      <span className="text-[13px] text-slate-700 font-medium">{searchResult.classification.material}</span>
                    </div>
                    <div className="flex gap-3">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider w-20 pt-0.5 shrink-0">Function</span>
                      <span className="text-[13px] text-slate-700 font-medium">{searchResult.classification.function}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Practical notes */}
              {searchResult.practical_notes && searchResult.practical_notes.length > 0 && (
                <div className="border-t border-slate-100 pt-4 mt-4">
                  <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">
                    Practical Notes
                  </h3>
                  <ul className="space-y-1.5">
                    {searchResult.practical_notes.map((note, index) => (
                      <li key={index} className="text-[12.5px] text-slate-500 font-medium flex gap-2">
                        <span className="text-emerald-500 shrink-0">•</span>
                        {note}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Correction button */}
              <div className="border-t border-slate-100 pt-4 mt-4 flex justify-end">
                <CorrectionButton
                  lookupId={searchResult.lookup_id ?? null}
                  matchedHsCode={searchResult.hs_code}
                  matchedDescription={searchResult.description}
                  onCorrect={() => setCorrectionPanelOpen(true)}
                />
              </div>
            </div>

            {/* HS Code Hierarchy Tree */}
            <HSCodeTree hsCode={searchResult.hs_code} />
          </div>
        )}

        {/* Correction Panel */}
        {searchResult && (
          <CorrectionPanel
            isOpen={correctionPanelOpen}
            onClose={() => setCorrectionPanelOpen(false)}
            lookupId={searchResult.lookup_id ?? 0}
            currentHsCode={searchResult.hs_code}
            currentDescription={searchResult.description}
          />
        )}

        {/* Empty state */}
        {!searchQuery && !isSearching && !searchResult && !searchError && (
          <div className="text-center py-16">
            <p className="text-[14px] text-slate-400 font-medium mb-1.5">Enter a product description to search</p>
            <p className="text-[12.5px] text-slate-300">
              Try: &quot;coffee beans&quot;, &quot;máy xay&quot;, or an HS code like &quot;0901&quot;
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
