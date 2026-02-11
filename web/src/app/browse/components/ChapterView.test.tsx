import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useState } from "react";

vi.mock("@/lib/api", () => ({
  getBrowseChapterDetail: vi.fn(),
}));

import { getBrowseChapterDetail } from "@/lib/api";
import { ChapterView } from "./ChapterView";
import type {
  BrowseChapterItem,
  BrowseChapterDetailResponse,
} from "@/types/browse";

const mockChapter: BrowseChapterItem = {
  id: 1,
  chapter_code: "01",
  name_vn: "Động vật sống",
  name_en: "Live animals",
  heading_count: 6,
  hs_code_count: 48,
};

const mockChapterDetail: BrowseChapterDetailResponse = {
  id: 1,
  chapter_code: "01",
  name_vn: "Động vật sống",
  name_en: "Live animals",
  notes_vn: "Chương này bao gồm tất cả các loại động vật sống",
  notes_en: "This chapter covers all live animals",
  headings: [
    {
      id: 1,
      heading_code: "0101",
      name_vn: "Ngựa, lừa, la sống",
      name_en: "Live horses, asses, mules",
      subheadings: [
        {
          id: 1,
          subheading_code: "010121",
          name_vn: "Ngựa thuần chủng để nhân giống",
          name_en: "Pure-bred breeding animals",
          indent_level: 1,
          hs_codes: [
            {
              id: 1,
              code: "01012100",
              description_vn: "Ngựa thuần chủng để nhân giống",
              description_en: "Pure-bred breeding horses",
              unit: "con",
              duty_rate: 5.0,
              vat_rate: 5.0,
              export_duty_rate: null,
              special_consumption_tax: null,
              environmental_tax: null,
              vat_reduction: null,
              policy_notes: null,
              fta_rates: [
                {
                  agreement_code: "CPTPP",
                  preferential_rate: 0.0,
                  conditions: "Form CPTPP",
                  rate_year: null,
                  is_export: false,
                  legal_document: "NĐ 57/2019",
                  effective_date: "2019-01-14",
                },
              ],
            },
          ],
        },
      ],
    },
  ],
};

describe("ChapterView", () => {
  const defaultProps = {
    chapter: mockChapter,
    isExpanded: false,
    onToggle: vi.fn(),
    cachedDetail: undefined as BrowseChapterDetailResponse | undefined,
    onDetailLoaded: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("rendering", () => {
    it("renders chapter code and name", () => {
      render(<ChapterView {...defaultProps} />);

      expect(screen.getByText("01")).toBeInTheDocument();
      expect(screen.getByText("Động vật sống")).toBeInTheDocument();
    });

    it("displays HS code count", () => {
      render(<ChapterView {...defaultProps} />);

      expect(screen.getByText("48 codes")).toBeInTheDocument();
    });
  });

  describe("chapter expansion", () => {
    it("fetches chapter detail when expanded without cache", async () => {
      const mockedGetDetail = vi.mocked(getBrowseChapterDetail);
      mockedGetDetail.mockResolvedValueOnce(mockChapterDetail);

      const onDetailLoaded = vi.fn();

      render(
        <ChapterView {...defaultProps} onDetailLoaded={onDetailLoaded} />
      );

      fireEvent.click(screen.getByText("01"));

      await waitFor(() => {
        expect(mockedGetDetail).toHaveBeenCalledWith("01");
      });

      await waitFor(() => {
        expect(onDetailLoaded).toHaveBeenCalledWith("01", mockChapterDetail);
      });
    });

    it("shows loading indicator during fetch", async () => {
      const mockedGetDetail = vi.mocked(getBrowseChapterDetail);
      mockedGetDetail.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockChapterDetail), 100))
      );

      // Stateful wrapper so toggle actually expands
      function Wrapper() {
        const [expanded, setExpanded] = useState(false);
        return (
          <ChapterView
            chapter={mockChapter}
            isExpanded={expanded}
            onToggle={() => setExpanded((prev) => !prev)}
            cachedDetail={undefined}
            onDetailLoaded={vi.fn()}
          />
        );
      }

      render(<Wrapper />);

      fireEvent.click(screen.getByText("01"));

      expect(await screen.findByTestId("chapter-loading")).toBeInTheDocument();
    });

    it("renders hierarchy when detail is cached and expanded", () => {
      render(
        <ChapterView
          {...defaultProps}
          isExpanded={true}
          cachedDetail={mockChapterDetail}
        />
      );

      expect(screen.getByText("0101")).toBeInTheDocument();
      expect(screen.getByText("Ngựa, lừa, la sống")).toBeInTheDocument();
      expect(screen.getByText("010121")).toBeInTheDocument();
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    it("renders HS code inline rates", () => {
      render(
        <ChapterView
          {...defaultProps}
          isExpanded={true}
          cachedDetail={mockChapterDetail}
        />
      );

      expect(screen.getByTestId("duty-rate")).toHaveTextContent("5%");
      expect(screen.getByTestId("vat-rate")).toHaveTextContent("5%");
      expect(screen.getByTestId("export-rate")).toHaveTextContent("—");
    });

    it("shows error when fetch fails", async () => {
      const mockedGetDetail = vi.mocked(getBrowseChapterDetail);
      mockedGetDetail.mockRejectedValueOnce(new Error("Server error"));

      // Stateful wrapper so toggle actually expands
      function Wrapper() {
        const [expanded, setExpanded] = useState(false);
        return (
          <ChapterView
            chapter={mockChapter}
            isExpanded={expanded}
            onToggle={() => setExpanded((prev) => !prev)}
            cachedDetail={undefined}
            onDetailLoaded={vi.fn()}
          />
        );
      }

      render(<Wrapper />);

      fireEvent.click(screen.getByText("01"));

      await waitFor(() => {
        expect(screen.getByText("Server error")).toBeInTheDocument();
      });
    });
  });

  describe("chapter notes", () => {
    it("shows chapter notes toggle when notes exist", () => {
      render(
        <ChapterView
          {...defaultProps}
          isExpanded={true}
          cachedDetail={mockChapterDetail}
        />
      );

      expect(screen.getByText("Chapter Notes")).toBeInTheDocument();
    });

    it("shows notes content when toggled", () => {
      render(
        <ChapterView
          {...defaultProps}
          isExpanded={true}
          cachedDetail={mockChapterDetail}
        />
      );

      fireEvent.click(screen.getByText("Chapter Notes"));
      expect(
        screen.getByText(
          "Chương này bao gồm tất cả các loại động vật sống"
        )
      ).toBeInTheDocument();
    });
  });

  describe("HS code expansion", () => {
    it("expands HS code to show detail panel", () => {
      render(
        <ChapterView
          {...defaultProps}
          isExpanded={true}
          cachedDetail={mockChapterDetail}
        />
      );

      fireEvent.click(screen.getByText("01012100"));

      expect(screen.getByTestId("hs-code-detail")).toBeInTheDocument();
      expect(
        screen.getByText("Pure-bred breeding horses")
      ).toBeInTheDocument();
      expect(screen.getByText("con")).toBeInTheDocument();
    });

    it("shows FTA rates in detail panel", () => {
      render(
        <ChapterView
          {...defaultProps}
          isExpanded={true}
          cachedDetail={mockChapterDetail}
        />
      );

      fireEvent.click(screen.getByText("01012100"));

      expect(screen.getByText("Import FTA Rates")).toBeInTheDocument();
      expect(screen.getByText("CPTPP")).toBeInTheDocument();
      expect(screen.getByText("0%")).toBeInTheDocument();
      expect(screen.getByText("Form CPTPP")).toBeInTheDocument();
    });
  });
});
