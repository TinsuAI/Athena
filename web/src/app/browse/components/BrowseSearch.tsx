"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { searchBrowse } from "@/lib/api";
import type { BrowseSearchResultItem } from "@/types/browse";

interface BrowseSearchProps {
  onResultClick?: (result: BrowseSearchResultItem) => void;
}

const PAGE_SIZE = 50;

function formatRate(rate: number | string | null): string {
  if (rate === null || rate === undefined) return "\u2014";
  if (typeof rate === "number") return `${rate}%`;
  return rate;
}

export function BrowseSearch({ onResultClick }: BrowseSearchProps) {
  const [query, setQuery] = useState("");
  const [chapterFilter, setChapterFilter] = useState("");
  const [results, setResults] = useState<BrowseSearchResultItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
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
          chapterFilter || undefined,
          PAGE_SIZE,
          searchOffset
        );
        setResults(data.items);
        setTotal(data.total);
        setHasSearched(true);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Tìm kiếm thất bại";
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
    setSelectedCode(null);
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
    <div data-testid="browse-search" className="flex flex-col h-full">
      {/* Sidebar header */}
      <div className="px-[18px] pt-[18px]">
        <div className="flex items-center gap-1.5 text-[11px] font-bold text-muted-foreground uppercase tracking-[1.2px] mb-3 before:w-[3px] before:h-3 before:bg-primary before:rounded-sm before:block">
          Tìm nhanh
        </div>
        <div className="relative mb-2.5">
          <div className="absolute left-[11px] top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
            <Search className="h-3.5 w-3.5" aria-hidden="true" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => handleInputChange(e.target.value)}
            placeholder="Tìm mã HS, mô tả hàng hóa..."
            className="h-10 w-full rounded-md border-[1.5px] border-border bg-card pl-9 pr-9 text-[13px] font-medium text-foreground placeholder:text-muted-foreground placeholder:font-normal focus:outline-none focus:border-primary focus:ring-[3px] focus:ring-primary/10 transition-all"
            aria-label="Tìm kiếm mã thuế"
            data-testid="browse-search-input"
          />
          {query && (
            <button
              onClick={handleClear}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Xóa tìm kiếm"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={chapterFilter}
            onChange={(e) => setChapterFilter(e.target.value)}
            placeholder="Lọc theo chương (01-97)"
            className="flex-1 h-9 rounded-md border-[1.5px] border-border bg-card px-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary focus:ring-[3px] focus:ring-primary/10 transition-all"
            aria-label="Lọc theo chương"
            data-testid="browse-chapter-filter"
          />
          {chapterFilter && (
            <button
              onClick={() => setChapterFilter("")}
              className="px-3 h-9 border-[1.5px] border-border rounded-md bg-card text-xs font-semibold text-muted-foreground hover:bg-accent hover:text-accent-foreground hover:border-primary/30 transition-all"
            >
              Xóa
            </button>
          )}
        </div>
      </div>

      {/* Results header */}
      {hasSearched && (
        <div className="flex items-center justify-between px-[18px] py-3 border-t border-border/50 mt-3">
          <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
            {total} kết quả
          </span>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center gap-2 px-[18px] py-4 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Đang tìm kiếm...
        </div>
      )}

      {error && (
        <div
          className="mx-3 mt-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive"
          role="alert"
        >
          {error}
        </div>
      )}

      {!isLoading && hasSearched && results.length === 0 && !error && (
        <div
          className="py-6 text-center text-sm text-muted-foreground"
          data-testid="browse-search-empty"
        >
          Không tìm thấy mã HS phù hợp
        </div>
      )}

      {/* Results list */}
      {results.length > 0 && (
        <div className="flex-1 overflow-y-auto px-3 pb-3 scrollbar-thin">
          <div className="space-y-2">
            {results.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  setSelectedCode(item.code);
                  onResultClick?.(item);
                }}
                className={`relative w-full rounded-lg border bg-card px-3.5 py-3 text-left transition-all cursor-pointer before:absolute before:left-0 before:top-2 before:bottom-2 before:w-[3px] before:rounded-r before:transition-colors ${
                  selectedCode === item.code
                    ? "border-primary bg-accent shadow-[0_0_0_3px_rgba(16,185,129,0.08)] before:bg-primary"
                    : "border-border hover:border-primary/30 hover:bg-emerald-50/50 hover:shadow-sm before:bg-transparent hover:before:bg-primary"
                }`}
                data-testid={`search-result-${item.code}`}
              >
                <div className="flex items-start justify-between mb-1.5">
                  <span className="font-mono text-[13px] font-bold text-accent-foreground tracking-tight">
                    {item.code}
                  </span>
                  <span className="text-[10px] text-muted-foreground font-medium flex items-center gap-1">
                    {item.section_roman}
                    <span className="text-[8px] opacity-50">&#9656;</span>
                    Ch.{item.chapter_code}
                    <span className="text-[8px] opacity-50">&#9656;</span>
                    {item.heading_code}
                  </span>
                </div>
                <div className="text-[12.5px] font-medium text-foreground leading-snug mb-2.5 truncate">
                  {item.description_vn}
                </div>
                <div className="flex gap-1.5">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-semibold font-mono bg-blue-100 text-blue-800">
                    <span className="font-sans font-medium opacity-70 text-[10px]">NK</span>
                    {formatRate(item.duty_rate)}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-semibold font-mono bg-amber-100 text-amber-800">
                    <span className="font-sans font-medium opacity-70 text-[10px]">VAT</span>
                    {formatRate(item.vat_rate)}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-semibold font-mono bg-secondary text-muted-foreground">
                    <span className="font-sans font-medium opacity-70 text-[10px]">XK</span>
                    {formatRate(item.export_duty_rate)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Pagination */}
      {hasSearched && (
        <div className="flex items-center justify-between px-[18px] py-3 border-t border-border/50">
          <button
            onClick={handlePrevious}
            disabled={offset === 0}
            className="px-3.5 py-1.5 border border-border rounded-md bg-card text-xs font-semibold text-muted-foreground hover:bg-accent hover:text-accent-foreground hover:border-primary/30 transition-all disabled:cursor-not-allowed disabled:opacity-40"
          >
            &larr; Trước
          </button>
          <span className="text-[11px] text-muted-foreground font-medium">
            Trang {currentPage} / {totalPages}
          </span>
          <button
            onClick={handleNext}
            disabled={offset + PAGE_SIZE >= total}
            className="px-3.5 py-1.5 border border-border rounded-md bg-card text-xs font-semibold text-muted-foreground hover:bg-accent hover:text-accent-foreground hover:border-primary/30 transition-all disabled:cursor-not-allowed disabled:opacity-40"
          >
            Sau &rarr;
          </button>
        </div>
      )}
    </div>
  );
}
