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
        className="flex items-center gap-2 rounded-md border bg-card px-3 py-2 text-sm font-medium hover:bg-muted/50 transition-colors"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        Jump to chapter
        <ChevronDown className="h-4 w-4" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full z-20 mt-1 max-h-80 w-80 overflow-y-auto rounded-md border bg-card shadow-lg">
            {allChapters.length === 0 ? (
              <div className="px-3 py-4 text-sm text-muted-foreground">
                Expand sections to load chapters
              </div>
            ) : (
              <ul role="listbox">
                {allChapters.map((ch) => (
                  <li key={ch.chapterCode}>
                    <button
                      onClick={() => handleSelect(ch.sectionId, ch.chapterCode)}
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-muted/50 transition-colors"
                      role="option"
                      aria-selected={false}
                    >
                      <span className="font-mono font-medium">
                        {ch.chapterCode}
                      </span>
                      <span className="truncate">{ch.name}</span>
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
