"use client";

import { useCallback, useState } from "react";
import { ChevronRight, ChevronDown, Info } from "lucide-react";
import { getBrowseChapters } from "@/lib/api";
import type {
  BrowseSectionItem,
  BrowseChapterItem,
  BrowseChaptersResponse,
  BrowseChapterDetailResponse,
} from "@/types/browse";
import { ChapterView } from "./ChapterView";

interface SectionListProps {
  sections: BrowseSectionItem[];
  expandedSections: Set<number>;
  onToggleSection: (id: number) => void;
  chaptersCache: Map<number, BrowseChaptersResponse>;
  onChaptersLoaded: (sectionId: number, data: BrowseChaptersResponse) => void;
  chapterDetailsCache: Map<string, BrowseChapterDetailResponse>;
  onChapterDetailLoaded: (
    chapterCode: string,
    detail: BrowseChapterDetailResponse
  ) => void;
  expandedChapters: Set<string>;
  onToggleChapter: (chapterCode: string) => void;
  highlightedCode?: string | null;
}

export function SectionList({
  sections,
  expandedSections,
  onToggleSection,
  chaptersCache,
  onChaptersLoaded,
  chapterDetailsCache,
  onChapterDetailLoaded,
  expandedChapters,
  onToggleChapter,
  highlightedCode,
}: SectionListProps) {
  const [loadingChapters, setLoadingChapters] = useState<Set<number>>(
    new Set()
  );
  const [chapterErrors, setChapterErrors] = useState<Map<number, string>>(
    new Map()
  );
  const [showNotes, setShowNotes] = useState<Set<number>>(new Set());

  const handleToggleSection = useCallback(
    async (section: BrowseSectionItem) => {
      onToggleSection(section.id);

      if (!expandedSections.has(section.id) && !chaptersCache.has(section.id)) {
        setLoadingChapters((prev) => new Set(prev).add(section.id));
        setChapterErrors((prev) => {
          const next = new Map(prev);
          next.delete(section.id);
          return next;
        });

        try {
          const data = await getBrowseChapters(section.id);
          onChaptersLoaded(section.id, data);
          if (data.section_notes_vn) {
            setShowNotes((prev) => new Set(prev).add(section.id));
          }
        } catch (err) {
          const message =
            err instanceof Error ? err.message : "Không thể tải danh sách chương";
          setChapterErrors((prev) => new Map(prev).set(section.id, message));
        } finally {
          setLoadingChapters((prev) => {
            const next = new Set(prev);
            next.delete(section.id);
            return next;
          });
        }
      }
    },
    [expandedSections, chaptersCache, onToggleSection, onChaptersLoaded]
  );

  const toggleSectionNotes = (sectionId: number) => {
    setShowNotes((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) next.delete(sectionId);
      else next.add(sectionId);
      return next;
    });
  };

  return (
    <div data-testid="section-list">
      {sections.map((section) => {
        const isExpanded = expandedSections.has(section.id);
        const isLoadingChapters = loadingChapters.has(section.id);
        const chapterError = chapterErrors.get(section.id);
        const cached = chaptersCache.get(section.id);

        return (
          <div
            key={section.id}
            id={`section-${section.id}`}
            data-testid={`section-${section.section_roman}`}
            className="border-b border-border"
          >
            <button
              onClick={() => handleToggleSection(section)}
              className="group flex w-full items-center gap-2 sm:gap-3.5 px-3 sm:px-5 py-3 sm:py-3.5 text-left hover:bg-secondary/50 transition-colors"
              aria-expanded={isExpanded}
            >
              <span
                className={`flex h-[22px] w-[22px] items-center justify-center rounded text-[11px] shrink-0 transition-all duration-200 ${
                  isExpanded
                    ? "bg-primary text-primary-foreground rotate-90"
                    : "border-[1.5px] border-border bg-card text-muted-foreground group-hover:border-primary group-hover:text-primary"
                }`}
              >
                &#9656;
              </span>
              <span className="font-mono text-xs font-bold text-accent-foreground bg-accent px-2.5 py-1 rounded min-w-[52px] text-center tracking-wide">
                {section.section_roman}
              </span>
              <span className="flex-1 text-xs sm:text-[13.5px] font-semibold text-foreground">
                {section.name_vn}
              </span>
              <span className="shrink-0 text-[10px] sm:text-[11px] text-muted-foreground font-medium px-1.5 sm:px-2.5 py-0.5 sm:py-1 bg-secondary rounded">
                {section.chapter_count} chương
              </span>
            </button>

            {isExpanded && (
              <div className="border-t border-border/50">
                {isLoadingChapters && (
                  <div className="flex items-center gap-2 py-3 pl-6 sm:pl-14 text-sm text-muted-foreground">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted border-t-primary" />
                    Đang tải danh sách chương...
                  </div>
                )}

                {chapterError && (
                  <div
                    className="py-2 pl-14 text-sm text-destructive"
                    role="alert"
                  >
                    {chapterError}
                  </div>
                )}

                {cached && (
                  <>
                    {cached.section_notes_vn && (
                      <div className="mx-3 sm:mx-5 mb-2 mt-2">
                        <button
                          onClick={() => toggleSectionNotes(section.id)}
                          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <Info className="h-3.5 w-3.5" />
                          Ghi chú phần
                          {showNotes.has(section.id) ? (
                            <ChevronDown className="h-3 w-3" />
                          ) : (
                            <ChevronRight className="h-3 w-3" />
                          )}
                        </button>
                        {showNotes.has(section.id) && (
                          <div className="mt-1 rounded bg-muted/50 p-2 text-xs whitespace-pre-wrap">
                            {cached.section_notes_vn}
                          </div>
                        )}
                      </div>
                    )}

                    {cached.chapters.map((chapter) => (
                      <ChapterView
                        key={chapter.id}
                        chapter={chapter}
                        isExpanded={expandedChapters.has(chapter.chapter_code)}
                        onToggle={() => onToggleChapter(chapter.chapter_code)}
                        cachedDetail={chapterDetailsCache.get(
                          chapter.chapter_code
                        )}
                        onDetailLoaded={onChapterDetailLoaded}
                        highlightedCode={highlightedCode}
                      />
                    ))}
                  </>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
