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
        } catch (err) {
          const message =
            err instanceof Error ? err.message : "Failed to load chapters";
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
    <div className="space-y-1" data-testid="section-list">
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
          >
            <button
              onClick={() => handleToggleSection(section)}
              className="flex w-full items-center gap-2 rounded-lg px-4 py-3 text-left hover:bg-muted/50 transition-colors"
              aria-expanded={isExpanded}
            >
              {isExpanded ? (
                <ChevronDown className="h-5 w-5 shrink-0 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground" />
              )}
              <span className="font-semibold">{section.section_roman}</span>
              <span className="flex-1 truncate">{section.name_vn}</span>
              <span className="shrink-0 text-sm text-muted-foreground">
                {section.chapter_count} chapter
                {section.chapter_count !== 1 ? "s" : ""}
              </span>
            </button>

            {isExpanded && (
              <div className="ml-6 border-l pl-3">
                {isLoadingChapters && (
                  <div className="flex items-center gap-2 py-3 text-sm text-muted-foreground">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted border-t-primary" />
                    Loading chapters...
                  </div>
                )}

                {chapterError && (
                  <div
                    className="py-2 text-sm text-destructive"
                    role="alert"
                  >
                    {chapterError}
                  </div>
                )}

                {cached && (
                  <>
                    {cached.section_notes_vn && (
                      <div className="mb-2">
                        <button
                          onClick={() => toggleSectionNotes(section.id)}
                          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <Info className="h-3.5 w-3.5" />
                          Section Notes
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
