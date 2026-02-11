"use client";

import { useRef, useCallback, useState } from "react";
import { SearchBar } from "./components/SearchBar";
import { CorrectionButton } from "./components/CorrectionButton";
import { CorrectionPanel } from "./components/CorrectionPanel";
import { ModelSelect } from "@/components/ui/ModelSelect";
import { useKeyboardShortcuts } from "@/lib/hooks/useKeyboardShortcuts";
import { useStore } from "@/lib/store";
import { searchHsCodes } from "@/lib/api";
import type { ProcessLogEntry } from "@/types/hs-code";

/**
 * Search page with SearchBar component.
 * Search is triggered by button click or Enter key to avoid unnecessary API calls.
 */
export default function SearchPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [showLogs, setShowLogs] = useState(true);
  const [expandedLogs, setExpandedLogs] = useState<Set<number>>(new Set());
  const [correctionPanelOpen, setCorrectionPanelOpen] = useState(false);

  // Zustand store selectors
  const searchQuery = useStore((state) => state.searchQuery);
  const searchResult = useStore((state) => state.searchResult);
  const isSearching = useStore((state) => state.isSearching);
  const searchError = useStore((state) => state.searchError);
  const llmModel = useStore((state) => state.llmModel);
  const setSearchQuery = useStore((state) => state.setSearchQuery);
  const setSearchResult = useStore((state) => state.setSearchResult);
  const setIsSearching = useStore((state) => state.setIsSearching);
  const setSearchError = useStore((state) => state.setSearchError);
  const setLlmModel = useStore((state) => state.setLlmModel);
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
        abortControllerRef.current.signal,
        llmModel || undefined
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
  }, [searchQuery, llmModel, setSearchResult, setIsSearching, setSearchError]);

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

        {/* Model selector for testing */}
        <div className="mb-8 p-4 border rounded-lg bg-muted/30">
          <label className="block text-sm font-medium mb-2">
            LLM Model (for classification reasoning)
          </label>
          <ModelSelect
            value={llmModel}
            onChange={setLlmModel}
            placeholder="Search or enter model..."
          />
          <p className="text-xs text-muted-foreground mt-1">
            Type to search models or enter any OpenRouter model ID
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

              {/* Correction button */}
              <div className="border-t pt-4 mt-4 flex justify-end">
                <CorrectionButton
                  lookupId={searchResult.lookup_id ?? null}
                  matchedHsCode={searchResult.hs_code}
                  matchedDescription={searchResult.description}
                  onCorrect={() => setCorrectionPanelOpen(true)}
                />
              </div>
            </div>
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

        {/* Empty state - only show when no query and no result */}
        {!searchQuery && !isSearching && !searchResult && !searchError && (
          <div className="text-center py-12 text-muted-foreground">
            <p className="mb-2">Enter a product description to search</p>
            <p className="text-sm">
              Try: &quot;coffee beans&quot;, &quot;máy xay&quot;, or an HS code like &quot;0901&quot;
            </p>
          </div>
        )}

        {/* Process Logs Panel */}
        {searchResult?.process_logs && searchResult.process_logs.length > 0 && (
          <div className="mt-8 border rounded-lg bg-card">
            <button
              onClick={() => setShowLogs(!showLogs)}
              className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold">Process Logs</span>
                <span className="text-xs text-muted-foreground">
                  ({searchResult.process_logs.length} steps)
                </span>
              </div>
              <span className="text-muted-foreground">
                {showLogs ? "▼" : "▶"}
              </span>
            </button>

            {showLogs && (
              <div className="border-t">
                <div className="p-4 space-y-2 max-h-[500px] overflow-y-auto font-mono text-xs">
                  {searchResult.process_logs.map((log, idx) => (
                    <LogEntry
                      key={idx}
                      log={log}
                      isExpanded={expandedLogs.has(idx)}
                      onToggle={() => {
                        const newExpanded = new Set(expandedLogs);
                        if (newExpanded.has(idx)) {
                          newExpanded.delete(idx);
                        } else {
                          newExpanded.add(idx);
                        }
                        setExpandedLogs(newExpanded);
                      }}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function LogEntry({
  log,
  isExpanded,
  onToggle,
}: {
  log: ProcessLogEntry;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const statusColors: Record<string, string> = {
    started: "text-blue-500",
    completed: "text-green-500",
    failed: "text-red-500",
    skipped: "text-yellow-500",
  };

  const statusIcons: Record<string, string> = {
    started: "○",
    completed: "✓",
    failed: "✗",
    skipped: "⊘",
  };

  const hasDetails = log.details && Object.keys(log.details).length > 0;

  return (
    <div className="border-l-2 border-muted pl-3 py-1">
      <div
        className={`flex items-start gap-2 ${hasDetails ? "cursor-pointer hover:bg-muted/30 -ml-3 pl-3 -mr-1 pr-1 rounded" : ""}`}
        onClick={hasDetails ? onToggle : undefined}
      >
        <span className={statusColors[log.status] || "text-muted-foreground"}>
          {statusIcons[log.status] || "•"}
        </span>
        <span className="text-muted-foreground uppercase w-24 shrink-0">
          [{log.step}]
        </span>
        <span className="flex-1">{log.message}</span>
        {log.duration_ms !== undefined && (
          <span className="text-muted-foreground shrink-0">
            {log.duration_ms}ms
          </span>
        )}
        {hasDetails && (
          <span className="text-muted-foreground shrink-0">
            {isExpanded ? "▼" : "▶"}
          </span>
        )}
      </div>

      {/* Expanded details */}
      {hasDetails && isExpanded && (
        <div className="mt-2 ml-8 p-2 bg-muted/30 rounded text-[10px] overflow-x-auto">
          <pre className="whitespace-pre-wrap break-words">
            {JSON.stringify(log.details, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
