"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  getBrowseSections,
  getBrowseChapters,
  getBrowseChapterDetail,
} from "@/lib/api";
import type {
  BrowseSectionItem,
  BrowseChaptersResponse,
  BrowseChapterDetailResponse,
  BrowseSearchResultItem,
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

  const [highlightedCode, setHighlightedCode] = useState<string | null>(null);
  const highlightTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchSections = useCallback(async () => {
    setIsLoadingSections(true);
    setError(null);
    try {
      const data = await getBrowseSections();
      setSections(data);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Không thể tải danh sách phần";
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
      setExpandedSections((prev) => new Set(prev).add(sectionId));

      if (!chaptersCache.has(sectionId)) {
        try {
          const data = await getBrowseChapters(sectionId);
          setChaptersCache((prev) => new Map(prev).set(sectionId, data));
        } catch {
          return;
        }
      }

      setExpandedChapters((prev) => new Set(prev).add(chapterCode));

      setTimeout(() => {
        const el = document.getElementById(`section-${sectionId}`);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    },
    [chaptersCache]
  );

  const handleExpandAll = () => {
    setExpandedSections(new Set(sections.map((s) => s.id)));
  };

  const handleCollapseAll = () => {
    setExpandedSections(new Set());
    setExpandedChapters(new Set());
  };

  const handleSearchResultClick = useCallback(
    async (result: BrowseSearchResultItem) => {
      const section = sections.find(
        (s) => s.section_roman === result.section_roman
      );
      if (!section) return;

      // Clear any existing highlight timer
      if (highlightTimerRef.current) {
        clearTimeout(highlightTimerRef.current);
      }
      setHighlightedCode(result.code);

      // Expand the section
      setExpandedSections((prev) => new Set(prev).add(section.id));

      // Load chapters if not cached
      let chapters = chaptersCache.get(section.id);
      if (!chapters) {
        try {
          chapters = await getBrowseChapters(section.id);
          setChaptersCache((prev) =>
            new Map(prev).set(section.id, chapters!)
          );
        } catch {
          return;
        }
      }

      // Expand the chapter
      setExpandedChapters((prev) => new Set(prev).add(result.chapter_code));

      // Load chapter detail if not cached
      let detail = chapterDetailsCache.get(result.chapter_code);
      if (!detail) {
        try {
          detail = await getBrowseChapterDetail(result.chapter_code);
          setChapterDetailsCache((prev) =>
            new Map(prev).set(result.chapter_code, detail!)
          );
        } catch {
          return;
        }
      }

      // Wait for render then scroll to the HS code
      setTimeout(() => {
        const el = document.getElementById(`hs-code-${result.code}`);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 200);

      // Clear highlight after 3 seconds
      highlightTimerRef.current = setTimeout(
        () => setHighlightedCode(null),
        3000
      );
    },
    [sections, chaptersCache, chapterDetailsCache]
  );

  return (
    <div className="mx-auto max-w-[1600px] px-7 py-5">
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[340px_1fr]">
        {/* Sidebar: search */}
        <aside className="xl:sticky xl:top-[84px] xl:h-[calc(100vh-104px)] flex flex-col bg-card rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)] border border-border overflow-hidden max-h-[400px] xl:max-h-none">
          <BrowseSearch onResultClick={handleSearchResultClick} />
        </aside>

        {/* Main content */}
        <main className="min-w-0">
          {/* Stats bar */}
          <div className="grid grid-cols-2 gap-3 mb-4 sm:grid-cols-4">
            <div className="flex items-center gap-3 bg-card rounded-lg border border-border shadow-sm px-4 py-3.5">
              <div className="flex items-center justify-center w-[38px] h-[38px] rounded-md bg-[#ede9fe] text-[#7c3aed] shrink-0">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
              </div>
              <div className="flex flex-col">
                <span className="font-mono text-lg font-extrabold leading-tight">{sections.length}</span>
                <span className="text-[11px] text-muted-foreground">Phần</span>
              </div>
            </div>
            <div className="flex items-center gap-3 bg-card rounded-lg border border-border shadow-sm px-4 py-3.5">
              <div className="flex items-center justify-center w-[38px] h-[38px] rounded-md bg-[#dbeafe] text-[#2563eb] shrink-0">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
              </div>
              <div className="flex flex-col">
                <span className="font-mono text-lg font-extrabold leading-tight">97</span>
                <span className="text-[11px] text-muted-foreground">Chương</span>
              </div>
            </div>
            <div className="flex items-center gap-3 bg-card rounded-lg border border-border shadow-sm px-4 py-3.5">
              <div className="flex items-center justify-center w-[38px] h-[38px] rounded-md bg-accent/20 text-accent-foreground shrink-0">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
              </div>
              <div className="flex flex-col">
                <span className="font-mono text-lg font-extrabold leading-tight">11,234</span>
                <span className="text-[11px] text-muted-foreground">Mã HS</span>
              </div>
            </div>
            <div className="flex items-center gap-3 bg-card rounded-lg border border-border shadow-sm px-4 py-3.5">
              <div className="flex items-center justify-center w-[38px] h-[38px] rounded-md bg-[#fef3c7] text-[#d97706] shrink-0">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>
              </div>
              <div className="flex flex-col">
                <span className="font-mono text-lg font-extrabold leading-tight">16</span>
                <span className="text-[11px] text-muted-foreground">Hiệp định FTA</span>
              </div>
            </div>
          </div>

          {/* Toolbar */}
          <div className="mb-4 rounded-xl border border-border bg-card shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden">
            <div className="flex items-center gap-3 px-5 py-3 bg-secondary/50 border-b border-border w-full justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Biểu thuế</span>
                <span className="px-2 py-0.5 bg-accent text-accent-foreground text-xs font-semibold rounded-full font-mono">2024</span>
              </div>
              <div className="flex items-center gap-2">
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
                <button
                  onClick={handleExpandAll}
                  className="px-2.5 py-1 border border-border rounded bg-card text-[11px] font-semibold text-muted-foreground hover:bg-accent hover:text-accent-foreground hover:border-primary/30 transition-all"
                >
                  Mở tất cả
                </button>
                <button
                  onClick={handleCollapseAll}
                  className="px-2.5 py-1 border border-border rounded bg-card text-[11px] font-semibold text-muted-foreground hover:bg-accent hover:text-accent-foreground hover:border-primary/30 transition-all"
                >
                  Thu gọn
                </button>
                <button
                  className="px-2.5 py-1 border border-border rounded bg-card text-[11px] font-semibold text-muted-foreground hover:bg-accent hover:text-accent-foreground hover:border-primary/30 transition-all"
                >
                  Xuất CSV
                </button>
              </div>
            </div>
          </div>

          {/* Tree container */}
          <div className="rounded-xl border border-border bg-card shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden">
            {error && (
              <div
                className="m-4 rounded-lg bg-destructive/10 p-4 text-destructive"
                role="alert"
              >
                <p>{error}</p>
                <button
                  onClick={fetchSections}
                  className="mt-2 rounded-md bg-destructive/20 px-3 py-1.5 text-sm font-medium hover:bg-destructive/30 transition-colors"
                  data-testid="retry-button"
                >
                  Thử lại
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
                highlightedCode={highlightedCode}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
