import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock next-auth/react — stable reference to prevent useEffect re-triggers
const mockSessionData = {
  data: { user: { email: "test@example.com", role: "user" } },
  status: "authenticated" as const,
};
vi.mock("next-auth/react", () => ({
  useSession: () => mockSessionData,
}));

// Mock API
const mockGetSearchHistory = vi.fn();
const mockDeleteSearchHistoryItem = vi.fn();
const mockClearSearchHistory = vi.fn();
vi.mock("@/lib/api", () => ({
  getSearchHistory: (...args: unknown[]) => mockGetSearchHistory(...args),
  deleteSearchHistoryItem: (...args: unknown[]) =>
    mockDeleteSearchHistoryItem(...args),
  clearSearchHistory: (...args: unknown[]) => mockClearSearchHistory(...args),
}));

import HistoryPage from "./page";
import type { SearchHistoryItem } from "@/types/search-history";

const sampleItems: SearchHistoryItem[] = [
  {
    id: 1,
    user_id: 10,
    query: "laptop xách tay",
    selected_hs_code_id: 100,
    selected_hs_code: "84713000",
    selected_description_vn: "Máy tính xách tay",
    created_at: "2026-02-21T10:00:00+07:00",
  },
  {
    id: 2,
    user_id: 10,
    query: "gạo trắng",
    selected_hs_code_id: null,
    selected_hs_code: null,
    selected_description_vn: null,
    created_at: "2026-02-20T09:00:00+07:00",
  },
];

describe("HistoryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSearchHistory.mockReset();
    mockDeleteSearchHistoryItem.mockReset();
    mockClearSearchHistory.mockReset();
    mockGetSearchHistory.mockResolvedValue({ items: [], total: 0 });
    mockDeleteSearchHistoryItem.mockResolvedValue(undefined);
    mockClearSearchHistory.mockResolvedValue(undefined);
  });

  it("shows loading spinner while fetching", () => {
    mockGetSearchHistory.mockReturnValue(new Promise(() => {})); // never resolves
    render(<HistoryPage />);
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("renders history items after successful fetch", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 2,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("laptop xách tay")).toBeInTheDocument();
    });
    expect(screen.getByText("gạo trắng")).toBeInTheDocument();
  });

  it("shows error state with retry button on fetch failure", async () => {
    mockGetSearchHistory.mockRejectedValue(new Error("Network error"));
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText("Thử lại")).toBeInTheDocument();
  });

  it("retries on clicking retry button", async () => {
    mockGetSearchHistory.mockRejectedValueOnce(new Error("Network error"));
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Thử lại")).toBeInTheDocument();
    });

    mockGetSearchHistory.mockResolvedValue({ items: sampleItems, total: 2 });
    fireEvent.click(screen.getByText("Thử lại"));

    await waitFor(() => {
      expect(screen.getByText("laptop xách tay")).toBeInTheDocument();
    });
  });

  it("shows empty state when no items", async () => {
    mockGetSearchHistory.mockResolvedValue({ items: [], total: 0 });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(
        screen.getByText("Chưa có lịch sử tìm kiếm")
      ).toBeInTheDocument();
    });
  });

  it("empty state has link to search page", async () => {
    mockGetSearchHistory.mockResolvedValue({ items: [], total: 0 });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Bắt đầu tìm kiếm")).toBeInTheDocument();
    });
    const link = screen.getByText("Bắt đầu tìm kiếm").closest("a");
    expect(link).toHaveAttribute("href", "/search");
  });

  it("shows pagination when items span multiple pages", async () => {
    // 25 items with PAGE_SIZE=20 = 2 pages
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 25,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Trang 1 / 2")).toBeInTheDocument();
    });
  });

  it("Previous button is disabled on first page", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 25,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      const prevBtn = screen.getByText("Trang trước").closest("button");
      expect(prevBtn).toBeDisabled();
    });
  });

  it("Next button navigates to second page", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 25,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Trang sau")).toBeInTheDocument();
    });

    const nextBtn = screen.getByText("Trang sau").closest("button")!;
    expect(nextBtn).not.toBeDisabled();
    fireEvent.click(nextBtn);

    // Should fetch with offset=20
    await waitFor(() => {
      expect(mockGetSearchHistory).toHaveBeenCalledWith(20, 20);
    });
  });

  it("clicking a history item navigates to search page", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 2,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("laptop xách tay")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("laptop xách tay"));
    expect(mockPush).toHaveBeenCalledWith(
      "/search?q=laptop%20x%C3%A1ch%20tay"
    );
  });

  it("shows page header with history text", async () => {
    mockGetSearchHistory.mockResolvedValue({ items: [], total: 0 });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(
        screen.getByText("Lịch sử tìm kiếm")
      ).toBeInTheDocument();
    });
  });

  // Delete and Clear tests

  it("shows 'Xóa tất cả' button when history items exist", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 2,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Xóa tất cả")).toBeInTheDocument();
    });
  });

  it("does not show 'Xóa tất cả' button when no items", async () => {
    mockGetSearchHistory.mockResolvedValue({ items: [], total: 0 });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(
        screen.getByText("Chưa có lịch sử tìm kiếm")
      ).toBeInTheDocument();
    });
    expect(screen.queryByText("Xóa tất cả")).not.toBeInTheDocument();
  });

  it("clicking 'Xóa tất cả' opens confirmation dialog", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 2,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Xóa tất cả")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Xóa tất cả"));

    expect(
      screen.getByText("Xóa tất cả lịch sử?")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Bạn có chắc chắn? Điều này không thể hoàn tác.")
    ).toBeInTheDocument();
  });

  it("clicking 'Hủy' closes dialog without deleting", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 2,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Xóa tất cả")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Xóa tất cả"));
    expect(
      screen.getByText("Xóa tất cả lịch sử?")
    ).toBeInTheDocument();

    fireEvent.click(screen.getByText("Hủy"));

    expect(
      screen.queryByText("Xóa tất cả lịch sử?")
    ).not.toBeInTheDocument();
    expect(mockClearSearchHistory).not.toHaveBeenCalled();
    // Items still displayed
    expect(screen.getByText("laptop xách tay")).toBeInTheDocument();
  });

  it("confirming clear all deletes history and shows empty state", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 2,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Xóa tất cả")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Xóa tất cả"));

    // Find the red confirm button in the dialog
    const allButtons = screen.getAllByRole("button");
    const confirmBtn = allButtons.find((btn) =>
      btn.className.includes("bg-red-600")
    )!;

    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    expect(mockClearSearchHistory).toHaveBeenCalled();
    await waitFor(() => {
      expect(
        screen.getByText("Chưa có lịch sử tìm kiếm")
      ).toBeInTheDocument();
    });
  });

  it("shows success toast after clear all", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 2,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Xóa tất cả")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Xóa tất cả"));

    const allButtons = screen.getAllByRole("button");
    const confirmBtn = allButtons.find((btn) =>
      btn.className.includes("bg-red-600")
    )!;

    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    expect(
      screen.getByText("Lịch sử đã được xóa")
    ).toBeInTheDocument();
  });

  it("clicking delete on single item removes it from list", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 2,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("laptop xách tay")).toBeInTheDocument();
    });

    // Find all delete buttons and click the first one
    const deleteButtons = screen.getAllByLabelText("Xóa khỏi lịch sử");
    fireEvent.click(deleteButtons[0]);

    // Item should be removed optimistically
    await waitFor(() => {
      expect(
        screen.queryByText("laptop xách tay")
      ).not.toBeInTheDocument();
    });
    expect(mockDeleteSearchHistoryItem).toHaveBeenCalledWith(1);
  });

  it("shows success toast after single delete", async () => {
    mockGetSearchHistory.mockResolvedValue({
      items: sampleItems,
      total: 2,
    });
    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("laptop xách tay")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByLabelText("Xóa khỏi lịch sử");
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(
        screen.getByText("Đã xóa khỏi lịch sử")
      ).toBeInTheDocument();
    });
  });
});
