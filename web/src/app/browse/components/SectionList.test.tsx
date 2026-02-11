import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useState } from "react";

// Mock the API module
vi.mock("@/lib/api", () => ({
  getBrowseChapters: vi.fn(),
  getBrowseChapterDetail: vi.fn(),
}));

import { getBrowseChapters } from "@/lib/api";
import { SectionList } from "./SectionList";
import type { BrowseSectionItem, BrowseChaptersResponse } from "@/types/browse";

const mockSections: BrowseSectionItem[] = [
  {
    id: 1,
    section_number: 1,
    section_roman: "I",
    name_vn: "Động vật sống; sản phẩm từ động vật",
    name_en: "Live animals; animal products",
    chapter_count: 5,
  },
  {
    id: 2,
    section_number: 2,
    section_roman: "II",
    name_vn: "Sản phẩm thực vật",
    name_en: "Vegetable products",
    chapter_count: 14,
  },
  {
    id: 3,
    section_number: 3,
    section_roman: "III",
    name_vn: "Mỡ và dầu động vật hoặc thực vật",
    name_en: "Animal or vegetable fats and oils",
    chapter_count: 1,
  },
];

const mockChaptersResponse = {
  section_notes_vn: "Ghi chú phần I",
  section_notes_en: "Section I notes",
  chapters: [
    {
      id: 1,
      chapter_code: "01",
      name_vn: "Động vật sống",
      name_en: "Live animals",
      heading_count: 6,
      hs_code_count: 48,
    },
    {
      id: 2,
      chapter_code: "02",
      name_vn: "Thịt và phụ phẩm dạng thịt ăn được",
      name_en: "Meat and edible meat offal",
      heading_count: 10,
      hs_code_count: 142,
    },
  ],
};

describe("SectionList", () => {
  const defaultProps = {
    sections: mockSections,
    expandedSections: new Set<number>(),
    onToggleSection: vi.fn(),
    chaptersCache: new Map(),
    onChaptersLoaded: vi.fn(),
    chapterDetailsCache: new Map(),
    onChapterDetailLoaded: vi.fn(),
    expandedChapters: new Set<string>(),
    onToggleChapter: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("rendering", () => {
    it("renders all sections with correct data", () => {
      render(<SectionList {...defaultProps} />);

      expect(screen.getByTestId("section-I")).toBeInTheDocument();
      expect(screen.getByTestId("section-II")).toBeInTheDocument();
      expect(screen.getByTestId("section-III")).toBeInTheDocument();
    });

    it("displays section roman numeral and name", () => {
      render(<SectionList {...defaultProps} />);

      expect(screen.getByText("I")).toBeInTheDocument();
      expect(
        screen.getByText("Động vật sống; sản phẩm từ động vật")
      ).toBeInTheDocument();
    });

    it("displays chapter count for each section", () => {
      render(<SectionList {...defaultProps} />);

      expect(screen.getByText("5 chapters")).toBeInTheDocument();
      expect(screen.getByText("14 chapters")).toBeInTheDocument();
      expect(screen.getByText("1 chapter")).toBeInTheDocument();
    });
  });

  describe("section expansion", () => {
    it("calls onToggleSection when a section is clicked", () => {
      const onToggleSection = vi.fn();
      render(
        <SectionList {...defaultProps} onToggleSection={onToggleSection} />
      );

      fireEvent.click(screen.getByText("I"));
      expect(onToggleSection).toHaveBeenCalledWith(1);
    });

    it("fetches chapters when expanding a section for the first time", async () => {
      const mockedGetChapters = vi.mocked(getBrowseChapters);
      mockedGetChapters.mockResolvedValueOnce(mockChaptersResponse);

      const onChaptersLoaded = vi.fn();

      render(
        <SectionList
          {...defaultProps}
          onChaptersLoaded={onChaptersLoaded}
        />
      );

      fireEvent.click(screen.getByText("I"));

      await waitFor(() => {
        expect(mockedGetChapters).toHaveBeenCalledWith(1);
      });

      await waitFor(() => {
        expect(onChaptersLoaded).toHaveBeenCalledWith(1, mockChaptersResponse);
      });
    });

    it("displays chapters when section is expanded with cached data", () => {
      const cache = new Map();
      cache.set(1, mockChaptersResponse);

      render(
        <SectionList
          {...defaultProps}
          expandedSections={new Set([1])}
          chaptersCache={cache}
        />
      );

      expect(screen.getByText("01")).toBeInTheDocument();
      expect(screen.getByText("Động vật sống")).toBeInTheDocument();
      expect(screen.getByText("48 codes")).toBeInTheDocument();
      expect(screen.getByText("02")).toBeInTheDocument();
    });

    it("does not re-fetch chapters when already cached", () => {
      const mockedGetChapters = vi.mocked(getBrowseChapters);
      const cache = new Map();
      cache.set(1, mockChaptersResponse);

      render(
        <SectionList
          {...defaultProps}
          expandedSections={new Set([1])}
          chaptersCache={cache}
        />
      );

      fireEvent.click(screen.getByText("I"));
      expect(mockedGetChapters).not.toHaveBeenCalled();
    });

    it("shows error when chapter fetch fails", async () => {
      const mockedGetChapters = vi.mocked(getBrowseChapters);
      mockedGetChapters.mockRejectedValueOnce(new Error("Network error"));

      // Stateful wrapper so toggle actually expands the section
      function Wrapper() {
        const [expanded, setExpanded] = useState<Set<number>>(new Set());
        const [cache, setCache] = useState<Map<number, BrowseChaptersResponse>>(new Map());
        return (
          <SectionList
            sections={mockSections}
            expandedSections={expanded}
            onToggleSection={(id) => {
              setExpanded((prev) => {
                const next = new Set(prev);
                if (next.has(id)) next.delete(id);
                else next.add(id);
                return next;
              });
            }}
            chaptersCache={cache}
            onChaptersLoaded={(id, data) => setCache((prev) => new Map(prev).set(id, data))}
            chapterDetailsCache={new Map()}
            onChapterDetailLoaded={vi.fn()}
            expandedChapters={new Set<string>()}
            onToggleChapter={vi.fn()}
          />
        );
      }

      render(<Wrapper />);

      fireEvent.click(screen.getByText("I"));

      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
    });
  });

  describe("section notes", () => {
    it("shows section notes toggle when notes exist", () => {
      const cache = new Map();
      cache.set(1, mockChaptersResponse);

      render(
        <SectionList
          {...defaultProps}
          expandedSections={new Set([1])}
          chaptersCache={cache}
        />
      );

      expect(screen.getByText("Section Notes")).toBeInTheDocument();
    });

    it("toggles section notes visibility on click", () => {
      const cache = new Map();
      cache.set(1, mockChaptersResponse);

      render(
        <SectionList
          {...defaultProps}
          expandedSections={new Set([1])}
          chaptersCache={cache}
        />
      );

      fireEvent.click(screen.getByText("Section Notes"));
      expect(screen.getByText("Ghi chú phần I")).toBeInTheDocument();

      fireEvent.click(screen.getByText("Section Notes"));
      expect(screen.queryByText("Ghi chú phần I")).not.toBeInTheDocument();
    });
  });
});
