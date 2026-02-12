"use client";

import { useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import type { BrowseSectionItem, BrowseChapterItem } from "@/types/browse";

interface ChapterJumperProps {
  sections: BrowseSectionItem[];
  chaptersCache: Map<number, { chapters: BrowseChapterItem[] }>;
  onJump: (sectionId: number, chapterCode: string) => void;
}

export function ChapterJumper({
  sections,
  chaptersCache,
  onJump,
}: ChapterJumperProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const allChapters: {
    sectionId: number;
    sectionRoman: string;
    chapterCode: string;
    name: string;
  }[] = [];

  for (const section of sections) {
    const cached = chaptersCache.get(section.id);
    if (cached) {
      for (const ch of cached.chapters) {
        allChapters.push({
          sectionId: section.id,
          sectionRoman: section.section_roman,
          chapterCode: ch.chapter_code,
          name: ch.name_vn,
        });
      }
    }
  }

  const handleSelect = (sectionId: number, chapterCode: string) => {
    onJump(sectionId, chapterCode);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef} data-testid="chapter-jumper">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-[11px] font-semibold text-muted-foreground hover:bg-accent hover:text-accent-foreground hover:border-primary/30 transition-all"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="opacity-60"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        Đến chương
        <ChevronDown className="h-3.5 w-3.5 ml-1" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full z-20 mt-1 max-h-80 w-80 overflow-y-auto rounded-lg border border-border bg-card shadow-lg">
            {allChapters.length === 0 ? (
              <div className="px-4 py-4 text-sm text-muted-foreground">
                Mở phần để tải danh sách chương
              </div>
            ) : (
              <ul role="listbox">
                {allChapters.map((ch) => (
                  <li key={ch.chapterCode} className="border-b border-border/50 last:border-b-0">
                    <button
                      onClick={() => handleSelect(ch.sectionId, ch.chapterCode)}
                      className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-[13px] hover:bg-accent transition-colors"
                      role="option"
                      aria-selected={false}
                    >
                      <span className="font-mono text-[13px] font-bold text-foreground min-w-[28px]">
                        {ch.chapterCode}
                      </span>
                      <span className="truncate text-muted-foreground font-medium">{ch.name}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
