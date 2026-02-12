"use client";

import { useCallback, useState } from "react";
import { ChevronRight, ChevronDown, Info, Loader2 } from "lucide-react";
import { getBrowseChapterDetail } from "@/lib/api";
import type {
  BrowseChapterItem,
  BrowseChapterDetailResponse,
} from "@/types/browse";
import { HSCodeRow } from "./HSCodeRow";

interface ChapterViewProps {
  chapter: BrowseChapterItem;
  isExpanded: boolean;
  onToggle: () => void;
  cachedDetail: BrowseChapterDetailResponse | undefined;
  onDetailLoaded: (
    chapterCode: string,
    detail: BrowseChapterDetailResponse
  ) => void;
  highlightedCode?: string | null;
}

export function ChapterView({
  chapter,
  isExpanded,
  onToggle,
  cachedDetail,
  onDetailLoaded,
  highlightedCode,
}: ChapterViewProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showNotes, setShowNotes] = useState(true);
  const [expandedHSCodes, setExpandedHSCodes] = useState<Set<string>>(
    new Set()
  );

  const handleToggle = useCallback(async () => {
    onToggle();

    if (!isExpanded && !cachedDetail) {
      setIsLoading(true);
      setError(null);
      try {
        const detail = await getBrowseChapterDetail(chapter.chapter_code);
        onDetailLoaded(chapter.chapter_code, detail);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Không thể tải chi tiết chương";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    }
  }, [isExpanded, cachedDetail, chapter.chapter_code, onToggle, onDetailLoaded]);

  const toggleHSCode = (code: string) => {
    setExpandedHSCodes((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
  };

  return (
    <div data-testid={`chapter-${chapter.chapter_code}`} className="border-b border-border/50 last:border-b-0">
      <button
        onClick={handleToggle}
        className={`relative flex w-full items-center gap-3 py-2.5 pr-5 pl-[52px] text-left text-sm hover:bg-secondary/50 transition-all before:absolute before:left-0 before:top-0 before:bottom-0 before:w-[3px] before:transition-colors ${
          isExpanded
            ? "before:bg-primary"
            : "before:bg-transparent hover:before:bg-primary/30"
        }`}
        aria-expanded={isExpanded}
      >
        <span
          className={`flex h-[18px] w-[18px] items-center justify-center rounded-[3px] text-[9px] shrink-0 transition-all duration-200 ${
            isExpanded
              ? "bg-primary text-primary-foreground rotate-90"
              : "border-[1.5px] border-border bg-card text-muted-foreground"
          }`}
        >
          &#9656;
        </span>
        <span className="font-mono text-[13px] font-bold text-foreground min-w-[32px]">
          {chapter.chapter_code}
        </span>
        <span className="flex-1 truncate text-[13px] font-medium text-muted-foreground">
          {chapter.name_vn}
        </span>
        <span className="shrink-0 text-[10.5px] font-mono text-muted-foreground font-medium px-2 py-0.5 bg-secondary rounded">
          {chapter.hs_code_count} mã
        </span>
      </button>

      {isExpanded && (
        <div className="border-t border-border/50 bg-secondary/30">
          {isLoading && (
            <div
              className="flex items-center gap-2 py-4 pl-14 text-sm text-muted-foreground"
              data-testid="chapter-loading"
            >
              <Loader2 className="h-4 w-4 animate-spin" />
              Đang tải chi tiết chương...
            </div>
          )}

          {error && (
            <div className="py-2 pl-14 text-sm text-destructive" role="alert">
              {error}
            </div>
          )}

          {cachedDetail && (
            <>
              {cachedDetail.notes_vn && (
                <div className="mx-5 mb-2 mt-2">
                  <button
                    onClick={() => setShowNotes(!showNotes)}
                    className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Info className="h-3.5 w-3.5" />
                    Ghi chú chương
                    {showNotes ? (
                      <ChevronDown className="h-3 w-3" />
                    ) : (
                      <ChevronRight className="h-3 w-3" />
                    )}
                  </button>
                  {showNotes && (
                    <div className="mt-1 rounded bg-muted/50 p-2 text-xs whitespace-pre-wrap">
                      {cachedDetail.notes_vn}
                    </div>
                  )}
                </div>
              )}

              {/* Column headers */}
              <div className="grid grid-cols-[1fr_90px_70px_70px_36px] items-center gap-2 px-5 py-1.5 pl-[134px] bg-secondary/50 border-b-2 border-border border-t border-border/50">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.8px]">Mã HS &amp; Mô tả</span>
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.8px] text-center">NK</span>
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.8px] text-center">VAT</span>
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.8px] text-center">XK</span>
                <span />
              </div>

              {cachedDetail.headings.map((heading) => (
                <div key={heading.id} className="border-b border-border/50 last:border-b-0">
                  <div className="flex items-center gap-3 px-5 py-2.5 pl-[82px] cursor-pointer hover:bg-primary/[0.03] transition-colors">
                    <span className="font-mono text-[12.5px] font-semibold text-accent-foreground min-w-[48px]">
                      {heading.heading_code}
                    </span>
                    <span className="flex-1 text-[12.5px] font-medium text-muted-foreground">
                      {heading.name_vn}
                    </span>
                  </div>
                  {heading.subheadings.map((sub) => (
                    <div key={sub.id} className="border-b border-border/50 last:border-b-0">
                      <div className="flex items-center gap-3 px-5 py-2 pl-[108px]">
                        <span className="font-mono text-xs font-semibold text-muted-foreground min-w-[64px]">
                          {sub.subheading_code}
                        </span>
                        <span className="flex-1 text-xs text-muted-foreground">
                          {sub.name_vn}
                        </span>
                      </div>
                      <div>
                        {sub.hs_codes.map((hsCode) => (
                          <HSCodeRow
                            key={hsCode.id}
                            hsCode={hsCode}
                            isExpanded={expandedHSCodes.has(hsCode.code)}
                            onToggle={() => toggleHSCode(hsCode.code)}
                            highlighted={highlightedCode === hsCode.code}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
