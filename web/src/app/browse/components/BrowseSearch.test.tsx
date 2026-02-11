import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("@/lib/api", () => ({
  searchBrowse: vi.fn(),
}));

import { searchBrowse } from "@/lib/api";
import { BrowseSearch } from "./BrowseSearch";

const mockSearchResults = {
  items: [
    {
      id: 123,
      code: "74181000",
      description_vn: "Bộ đồ ăn, đồ nhà bếp bằng đồng",
      description_en: "Table, kitchen articles of copper",
      unit: "kg",
      duty_rate: 30.0,
      vat_rate: 10.0,
      export_duty_rate: null,
      section_roman: "XV",
      chapter_code: "74",
      heading_code: "7418",
    },
    {
      id: 124,
      code: "74182000",
      description_vn: "Đồ vệ sinh bằng đồng",
      description_en: "Sanitary ware of copper",
      unit: "kg",
      duty_rate: 30.0,
      vat_rate: 10.0,
      export_duty_rate: null,
      section_roman: "XV",
      chapter_code: "74",
      heading_code: "7418",
    },
  ],
  total: 2,
  limit: 50,
  offset: 0,
};

describe("BrowseSearch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders search input", () => {
    render(<BrowseSearch />);
    expect(screen.getByTestId("browse-search-input")).toBeInTheDocument();
  });

  it("renders chapter filter when callback provided", () => {
    render(
      <BrowseSearch
        chapterFilter=""
        onChapterFilterChange={vi.fn()}
      />
    );
    expect(screen.getByTestId("browse-chapter-filter")).toBeInTheDocument();
  });

  it("does not search with less than 2 characters", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const mockedSearch = vi.mocked(searchBrowse);

    render(<BrowseSearch />);

    await user.type(screen.getByTestId("browse-search-input"), "a");
    await vi.advanceTimersByTimeAsync(400);

    expect(mockedSearch).not.toHaveBeenCalled();
  });

  it("triggers search with debounce after 2+ characters", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const mockedSearch = vi.mocked(searchBrowse);
    mockedSearch.mockResolvedValueOnce(mockSearchResults);

    render(<BrowseSearch />);

    await user.type(screen.getByTestId("browse-search-input"), "copper");
    await vi.advanceTimersByTimeAsync(400);

    await waitFor(() => {
      expect(mockedSearch).toHaveBeenCalledWith("copper", undefined, 50, 0);
    });
  });

  it("displays search results", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const mockedSearch = vi.mocked(searchBrowse);
    mockedSearch.mockResolvedValueOnce(mockSearchResults);

    render(<BrowseSearch />);

    await user.type(screen.getByTestId("browse-search-input"), "copper");
    await vi.advanceTimersByTimeAsync(400);

    await waitFor(() => {
      expect(screen.getByText("74181000")).toBeInTheDocument();
      expect(screen.getByText("74182000")).toBeInTheDocument();
    });

    expect(screen.getByText("2 results found")).toBeInTheDocument();
  });

  it("displays hierarchy path in results", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const mockedSearch = vi.mocked(searchBrowse);
    mockedSearch.mockResolvedValueOnce(mockSearchResults);

    render(<BrowseSearch />);

    await user.type(screen.getByTestId("browse-search-input"), "copper");
    await vi.advanceTimersByTimeAsync(400);

    await waitFor(() => {
      expect(screen.getAllByText(/XV > Ch\.74 > 7418/).length).toBeGreaterThan(0);
    });
  });

  it("shows empty state when no results", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const mockedSearch = vi.mocked(searchBrowse);
    mockedSearch.mockResolvedValueOnce({
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
    });

    render(<BrowseSearch />);

    await user.type(screen.getByTestId("browse-search-input"), "xyz123");
    await vi.advanceTimersByTimeAsync(400);

    await waitFor(() => {
      expect(screen.getByTestId("browse-search-empty")).toBeInTheDocument();
      expect(
        screen.getByText("No HS codes match your search")
      ).toBeInTheDocument();
    });
  });

  it("shows error state when search fails", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const mockedSearch = vi.mocked(searchBrowse);
    mockedSearch.mockRejectedValueOnce(new Error("Network error"));

    render(<BrowseSearch />);

    await user.type(screen.getByTestId("browse-search-input"), "copper");
    await vi.advanceTimersByTimeAsync(400);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("clears results when input is cleared", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const mockedSearch = vi.mocked(searchBrowse);
    mockedSearch.mockResolvedValueOnce(mockSearchResults);

    render(<BrowseSearch />);

    await user.type(screen.getByTestId("browse-search-input"), "copper");
    await vi.advanceTimersByTimeAsync(400);

    await waitFor(() => {
      expect(screen.getByText("74181000")).toBeInTheDocument();
    });

    await user.click(screen.getByLabelText("Clear search"));

    expect(screen.queryByText("74181000")).not.toBeInTheDocument();
  });

  it("displays inline rates in results", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const mockedSearch = vi.mocked(searchBrowse);
    mockedSearch.mockResolvedValueOnce(mockSearchResults);

    render(<BrowseSearch />);

    await user.type(screen.getByTestId("browse-search-input"), "copper");
    await vi.advanceTimersByTimeAsync(400);

    await waitFor(() => {
      const result = screen.getByTestId("search-result-74181000");
      expect(result).toHaveTextContent("Import: 30%");
      expect(result).toHaveTextContent("VAT: 10%");
      expect(result).toHaveTextContent("Export: —");
    });
  });
});
