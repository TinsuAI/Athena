"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import { getBrowseSections, getBrowseChapters } from "@/lib/api";
import type {
  BrowseSectionItem,
  BrowseChaptersResponse,
  BrowseChapterDetailResponse,
} from "@/types/browse";
import { SectionList } from "./components/SectionList";
import { ChapterJumper } from "./components/ChapterJumper";
import { BrowseSearch } from "./components/BrowseSearch";

export default function BrowsePage() {
  const [sections, setSections] = useState<BrowseSectionItem[]>([]);
  const [isLoadingSections, setIsLoadingSections] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [expandedSections, setExpandedSections] = useState<Set<number>>(
    new Set()
  );
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(
    new Set()
  );

  const [chaptersCache, setChaptersCache] = useState<
    Map<number, BrowseChaptersResponse>
  >(new Map());
  const [chapterDetailsCache, setChapterDetailsCache] = useState<
    Map<string, BrowseChapterDetailResponse>
  >(new Map());

  const [chapterFilter, setChapterFilter] = useState("");

  const fetchSections = useCallback(async () => {
    setIsLoadingSections(true);
    setError(null);
    try {
      const data = await getBrowseSections();
      setSections(data);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load sections";
      setError(message);
    } finally {
      setIsLoadingSections(false);
    }
  }, []);

  useEffect(() => {
    fetchSections();
  }, [fetchSections]);

  const toggleSection = (id: number) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleChapter = (chapterCode: string) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(chapterCode)) next.delete(chapterCode);
      else next.add(chapterCode);
      return next;
    });
  };

  const handleChaptersLoaded = (
    sectionId: number,
    data: BrowseChaptersResponse
  ) => {
    setChaptersCache((prev) => new Map(prev).set(sectionId, data));
  };

  const handleChapterDetailLoaded = (
    chapterCode: string,
    detail: BrowseChapterDetailResponse
  ) => {
    setChapterDetailsCache((prev) => new Map(prev).set(chapterCode, detail));
  };

  const handleJump = useCallback(
    async (sectionId: number, chapterCode: string) => {
      // Expand the section if not already expanded
      setExpandedSections((prev) => new Set(prev).add(sectionId));

      // Load chapters if not cached
      if (!chaptersCache.has(sectionId)) {
        try {
          const data = await getBrowseChapters(sectionId);
          setChaptersCache((prev) => new Map(prev).set(sectionId, data));
        } catch {
          // Ignore errors during jump
        }
      }

      // Expand the chapter
      setExpandedChapters((prev) => new Set(prev).add(chapterCode));

      // Scroll to the section
      setTimeout(() => {
        const el = document.getElementById(`section-${sectionId}`);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    },
    [chaptersCache]
  );

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Tariff Schedule Browser</h1>
          <p className="mt-1 text-muted-foreground">
            Browse the full HS code hierarchy with duty rates and FTA
            preferences
          </p>
        </div>
        <ChapterJumper
          sections={sections}
          chaptersCache={
            new Map(
              Array.from(chaptersCache.entries()).map(([k, v]) => [
                k,
                { chapters: v.chapters },
              ])
            )
          }
          onJump={handleJump}
        />
      </div>

      <div className="mb-6">
        <BrowseSearch
          chapterFilter={chapterFilter}
          onChapterFilterChange={setChapterFilter}
        />
      </div>

      {error && (
        <div
          className="mb-4 rounded-lg bg-destructive/10 p-4 text-destructive"
          role="alert"
        >
          <p>{error}</p>
          <button
            onClick={fetchSections}
            className="mt-2 rounded-md bg-destructive/20 px-3 py-1.5 text-sm font-medium hover:bg-destructive/30 transition-colors"
            data-testid="retry-button"
          >
            Retry
          </button>
        </div>
      )}

      {isLoadingSections && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {!isLoadingSections && !error && sections.length > 0 && (
        <SectionList
          sections={sections}
          expandedSections={expandedSections}
          onToggleSection={toggleSection}
          chaptersCache={chaptersCache}
          onChaptersLoaded={handleChaptersLoaded}
          chapterDetailsCache={chapterDetailsCache}
          onChapterDetailLoaded={handleChapterDetailLoaded}
          expandedChapters={expandedChapters}
          onToggleChapter={toggleChapter}
        />
      )}
    </div>
  );
}
