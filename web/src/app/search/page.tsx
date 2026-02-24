"use client";

import { useRef, useCallback, useState, useEffect, Suspense } from "react";
import { useSession } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { SearchBar } from "./components/SearchBar";
import { CorrectionButton } from "./components/CorrectionButton";
import { CorrectionPanel } from "./components/CorrectionPanel";
import { HSCodeTree } from "@/components/ui/HSCodeTree";
import { useKeyboardShortcuts } from "@/lib/hooks/useKeyboardShortcuts";
import { MarkdownContent } from "@/components/ui/MarkdownContent";
import { useStore } from "@/lib/store";
import { searchHsCodes, getFavorites, recordSearchHistory } from "@/lib/api";
import { FavoriteButton } from "@/components/FavoriteButton";
import { FavoriteNotes } from "@/components/FavoriteNotes";
import { RecentFavorites } from "@/components/RecentFavorites";

/**
 * Search page with SearchBar component.
 * Search is triggered by button click or Enter key to avoid unnecessary API calls.
 */
function SearchPageInner() {
  const searchParams = useSearchParams();
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [correctionPanelOpen, setCorrectionPanelOpen] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [showNlmResponse, setShowNlmResponse] = useState(true);
  const [expandedLogs, setExpandedLogs] = useState<Set<number>>(new Set());
  const { data: session } = useSession();
  const isAdmin = (session?.user as { role?: string })?.role === "admin";

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

  const setFavorites = useStore((state) => state.setFavorites);
  const favorites = useStore((state) => state.favorites);

  // Sync favorites from backend on mount when authenticated
  useEffect(() => {
    if (session?.user && favorites.length === 0) {
      getFavorites()
        .then((data) => setFavorites(data))
        .catch(() => {}); // silent fail — favorites are non-critical
    }
  }, [session?.user, favorites.length, setFavorites]);

  // Set up keyboard shortcuts (/ and Cmd+K)
  useKeyboardShortcuts({ inputRef });

  // Execute search when button clicked or Enter pressed
  const executeSearch = useCallback(async (queryOverride?: string, skipHistory = false) => {
    const query = (queryOverride ?? searchQuery).trim();

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
      // Fire-and-forget: record search history for authenticated users
      // Skip when re-executing from history to avoid duplicating entries
      if (session?.user && !skipHistory) {
        recordSearchHistory(query, result.hs_code_id ?? null).catch(() => {});
      }
    } catch (err) {
      // Ignore abort errors
      if (err instanceof Error && err.name === "AbortError") {
        return;
      }
      const message =
        err instanceof Error ? err.message : "Tìm kiếm thất bại. Vui lòng thử lại.";
      setSearchError(message);
      setSearchResult(null);
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery, setSearchResult, setIsSearching, setSearchError, session]);

  // Auto-execute search from URL query param (e.g., /search?q=laptop)
  const initialQueryHandled = useRef(false);
  useEffect(() => {
    const q = searchParams.get("q");
    if (q && q.trim() && !initialQueryHandled.current) {
      initialQueryHandled.current = true;
      setSearchQuery(q);
      executeSearch(q, true);
    }
  }, [searchParams, setSearchQuery, executeSearch]);

  const handleQueryChange = (value: string) => {
    setSearchQuery(value);
  };

  const handleClear = () => {
    clearSearch();
  };

  const handleFavoriteClick = useCallback(
    (hsCode: string) => {
      setSearchQuery(hsCode);
      executeSearch(hsCode);
    },
    [setSearchQuery, executeSearch]
  );

  const hasFavorites = !!session?.user && favorites.length > 0;

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <div className="mx-auto px-7 py-10 max-w-6xl">
        {/* Header area */}
        <div className="mb-10 text-center">
          <h1 className="text-[32px] font-extrabold text-slate-900 tracking-tight mb-1.5">
            Athena
          </h1>
          <p className="text-[14px] text-slate-400 font-medium">
            Công cụ tra cứu mã HS &mdash; Tìm kiếm theo mô tả sản phẩm
          </p>
        </div>

        {/* Mobile: collapsible favorites above search */}
        {hasFavorites && (
          <div className="lg:hidden mb-4">
            <RecentFavorites maxItems={5} collapsible defaultCollapsed onItemClick={handleFavoriteClick} />
          </div>
        )}

        {/* Main content grid */}
        <div className={hasFavorites ? "grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6" : ""}>
          {/* Left: search content */}
          <div className={hasFavorites ? "min-w-0" : "max-w-4xl mx-auto"}>
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
              <p className="text-[12px] text-slate-400 mt-2.5 text-center font-medium transition-opacity duration-300">
                {searchQuery.trim()
                  ? "Nhấn Enter hoặc bấm Tìm kiếm để tra cứu mã HS"
                  : "Mô tả chi tiết sản phẩm để có kết quả chính xác hơn (ví dụ: vật liệu, công dụng, thông số kỹ thuật)"}
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
                    <div className="flex items-center gap-2 shrink-0 ml-4">
                      {searchResult.hs_code_id && session?.user && (
                        <FavoriteButton hsCodeId={searchResult.hs_code_id} size="sm" />
                      )}
                      <span className="relative group inline-flex items-center px-3.5 py-1 rounded-full text-[12px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100 cursor-help">
                        {searchResult.confidence}%
                        <span className="pointer-events-none absolute bottom-full right-0 mb-2 w-56 rounded-lg bg-slate-800 px-3 py-2 text-[11px] font-normal leading-relaxed text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
                          Điểm tin cậy dựa trên phân tích ngữ nghĩa và đánh giá AI về mức độ phù hợp giữa mô tả sản phẩm và mã HS.
                        </span>
                      </span>
                    </div>
                  </div>

                  {/* Rate pills */}
                  <div className="flex gap-2.5 mb-5">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-semibold bg-blue-50 text-blue-800 border border-blue-100">
                      <span className="font-sans font-medium text-[10px] opacity-70">NK</span>
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
                        Phân tích phân loại
                      </h3>
                      <div className="space-y-2.5">
                        <div className="flex gap-3">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider w-20 pt-0.5 shrink-0">Chất liệu</span>
                          <MarkdownContent content={searchResult.classification.material} className="prose-p:my-0 text-[13px] text-slate-700" />
                        </div>
                        <div className="flex gap-3">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider w-20 pt-0.5 shrink-0">Công dụng</span>
                          <MarkdownContent content={searchResult.classification.function} className="prose-p:my-0 text-[13px] text-slate-700" />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Practical notes */}
                  {searchResult.practical_notes && searchResult.practical_notes.length > 0 && (
                    <div className="border-t border-slate-100 pt-4 mt-4">
                      <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">
                        Ghi chú thực tế
                      </h3>
                      <ul className="space-y-1.5">
                        {searchResult.practical_notes.map((note, index) => (
                          <li key={index} className="text-[12.5px] text-slate-500 font-medium flex gap-2">
                            <span className="text-emerald-500 shrink-0">•</span>
                            <MarkdownContent content={note} className="prose-p:my-0 prose-ul:my-0 prose-li:my-0 [&>div]:inline" />
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Favorite notes (only if favorited) */}
                  {searchResult.hs_code_id && session?.user && (() => {
                    const fav = favorites.find((f) => f.hs_code_id === searchResult.hs_code_id);
                    if (!fav) return null;
                    return (
                      <div className="border-t border-slate-100 pt-3 mt-4">
                        <FavoriteNotes
                          favoriteId={fav.id}
                          hsCodeId={searchResult.hs_code_id}
                          initialNotes={fav.notes}
                        />
                      </div>
                    );
                  })()}

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

                {/* NLM Detailed Analysis (collapsible) */}
                {searchResult.nlm_raw_response && (
                  <div className="bg-white border border-slate-200 rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)]">
                    <button
                      type="button"
                      onClick={() => setShowNlmResponse(!showNlmResponse)}
                      className="w-full flex items-center justify-between px-6 py-4 text-left"
                      aria-expanded={showNlmResponse}
                      aria-label="Phân tích chi tiết"
                    >
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        Phân tích chi tiết
                      </span>
                      <span className="inline-block transition-transform duration-150 text-slate-400" style={{ transform: showNlmResponse ? "rotate(180deg)" : "rotate(0deg)" }}>
                        &#9662;
                      </span>
                    </button>
                    {showNlmResponse && (
                      <div className="border-t border-slate-100 px-6 py-4">
                        <MarkdownContent content={searchResult.nlm_raw_response} />
                      </div>
                    )}
                  </div>
                )}

                {/* HS Code Hierarchy Tree */}
                <HSCodeTree hsCode={searchResult.hs_code} />

                {/* Process Logs Panel (admin only) */}
                {isAdmin && searchResult.process_logs && searchResult.process_logs.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)]">
                    <button
                      type="button"
                      onClick={() => setShowLogs(!showLogs)}
                      className="w-full flex items-center justify-between px-6 py-4 text-left"
                      aria-expanded={showLogs}
                    >
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        Nhật ký xử lý
                      </span>
                      <span className="text-[11px] font-semibold text-slate-400">
                        {searchResult.process_logs.length} bước
                        <span className="ml-2 inline-block transition-transform duration-150" style={{ transform: showLogs ? "rotate(180deg)" : "rotate(0deg)" }}>
                          &#9662;
                        </span>
                      </span>
                    </button>
                    {showLogs && (
                      <div className="border-t border-slate-100">
                        {searchResult.process_logs.map((log, i) => (
                          <div key={i} className="border-b border-slate-50 last:border-b-0">
                            <button
                              type="button"
                              onClick={() => {
                                setExpandedLogs((prev) => {
                                  const next = new Set(prev);
                                  if (next.has(i)) next.delete(i);
                                  else next.add(i);
                                  return next;
                                });
                              }}
                              className="w-full flex items-center gap-3 px-6 py-3 text-left hover:bg-slate-50/50"
                            >
                              <span className={`h-2 w-2 shrink-0 rounded-full ${
                                log.status === "completed" ? "bg-emerald-500" :
                                log.status === "failed" ? "bg-red-500" :
                                log.status === "skipped" ? "bg-slate-300" :
                                "bg-amber-400"
                              }`} />
                              <span className="text-[12px] font-semibold text-slate-600 w-28 shrink-0">{log.step}</span>
                              <span className="text-[12px] text-slate-500 flex-1 truncate">{log.message}</span>
                              {typeof log.duration_ms === "number" && (
                                <span className="text-[11px] font-mono text-slate-400 shrink-0">{log.duration_ms}ms</span>
                              )}
                              {log.details && (
                                <span className="text-[10px] text-slate-300 shrink-0" style={{ transform: expandedLogs.has(i) ? "rotate(180deg)" : "rotate(0deg)" }}>
                                  &#9662;
                                </span>
                              )}
                            </button>
                            {expandedLogs.has(i) && log.details && (
                              <pre className="mx-6 mb-3 p-3 bg-slate-50 rounded-lg text-[11px] text-slate-600 font-mono overflow-x-auto max-h-60 overflow-y-auto">
                                {JSON.stringify(log.details, null, 2)}
                              </pre>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
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
                <p className="text-[14px] text-slate-400 font-medium mb-1.5">Nhập mô tả sản phẩm để tìm kiếm</p>
                <p className="text-[12.5px] text-slate-300">
                  Thử: &quot;coffee beans&quot;, &quot;máy xay&quot;, hoặc mã HS như &quot;0901&quot;
                </p>
              </div>
            )}
          </div>

          {/* Right: sidebar (desktop only) */}
          {hasFavorites && (
            <div className="hidden lg:block">
              <div className="sticky top-24">
                <RecentFavorites maxItems={5} onItemClick={handleFavoriteClick} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense>
      <SearchPageInner />
    </Suspense>
  );
}
