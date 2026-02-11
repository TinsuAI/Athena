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
}

export function ChapterView({
  chapter,
  isExpanded,
  onToggle,
  cachedDetail,
  onDetailLoaded,
}: ChapterViewProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showNotes, setShowNotes] = useState(false);
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
          err instanceof Error ? err.message : "Failed to load chapter detail";
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
    <div data-testid={`chapter-${chapter.chapter_code}`}>
      <button
        onClick={handleToggle}
        className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm hover:bg-muted/50 transition-colors"
        aria-expanded={isExpanded}
      >
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        )}
        <span className="font-mono font-medium">{chapter.chapter_code}</span>
        <span className="flex-1 truncate">{chapter.name_vn}</span>
        <span className="shrink-0 text-xs text-muted-foreground">
          {chapter.hs_code_count} codes
        </span>
      </button>

      {isExpanded && (
        <div className="ml-6 border-l pl-3">
          {isLoading && (
            <div
              className="flex items-center gap-2 py-4 text-sm text-muted-foreground"
              data-testid="chapter-loading"
            >
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading chapter details...
            </div>
          )}

          {error && (
            <div className="py-2 text-sm text-destructive" role="alert">
              {error}
            </div>
          )}

          {cachedDetail && (
            <>
              {cachedDetail.notes_vn && (
                <div className="mb-2">
                  <button
                    onClick={() => setShowNotes(!showNotes)}
                    className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Info className="h-3.5 w-3.5" />
                    Chapter Notes
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

              {/* Rate column headers */}
              <div className="flex items-center gap-2 px-2 py-1 text-xs font-medium text-muted-foreground border-b">
                <span className="w-3.5" />
                <span className="font-mono w-20">Code</span>
                <span className="flex-1">Description</span>
                <span className="shrink-0 w-14 text-right">Import</span>
                <span className="shrink-0 w-14 text-right">VAT</span>
                <span className="shrink-0 w-14 text-right">Export</span>
              </div>

              {cachedDetail.headings.map((heading) => (
                <div key={heading.id} className="mt-1">
                  <div className="px-2 py-1 text-sm font-medium text-foreground/80">
                    <span className="font-mono mr-2">{heading.heading_code}</span>
                    {heading.name_vn}
                  </div>
                  {heading.subheadings.map((sub) => (
                    <div key={sub.id} className="ml-4">
                      <div className="px-2 py-0.5 text-sm text-muted-foreground">
                        <span className="font-mono mr-2">
                          {sub.subheading_code}
                        </span>
                        {sub.name_vn}
                      </div>
                      <div className="ml-4">
                        {sub.hs_codes.map((hsCode) => (
                          <HSCodeRow
                            key={hsCode.id}
                            hsCode={hsCode}
                            isExpanded={expandedHSCodes.has(hsCode.code)}
                            onToggle={() => toggleHSCode(hsCode.code)}
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
