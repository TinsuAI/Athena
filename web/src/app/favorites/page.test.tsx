import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock next-auth/react
vi.mock("next-auth/react", () => ({
  useSession: () => ({
    data: { user: { email: "test@example.com", role: "user" } },
    status: "authenticated",
  }),
}));

// Mock store
let mockFavorites: import("@/types/favorite").Favorite[] = [];
const mockSetFavorites = vi.fn();
const mockRemoveFavoriteLocal = vi.fn();
const mockAddFavoriteLocal = vi.fn();

vi.mock("@/lib/store", () => ({
  useStore: (selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      favorites: mockFavorites,
      setFavorites: mockSetFavorites,
      removeFavoriteLocal: mockRemoveFavoriteLocal,
      addFavoriteLocal: mockAddFavoriteLocal,
    }),
}));

// Mock API
const mockGetFavorites = vi.fn();
const mockRemoveFavorite = vi.fn();
const mockAddFavorite = vi.fn();

vi.mock("@/lib/api", () => ({
  getFavorites: (...args: unknown[]) => mockGetFavorites(...args),
  removeFavorite: (...args: unknown[]) => mockRemoveFavorite(...args),
  addFavorite: (...args: unknown[]) => mockAddFavorite(...args),
}));

import FavoritesPage from "./page";
import type { Favorite } from "@/types/favorite";

const sampleFavorites: Favorite[] = [
  {
    id: 1,
    user_id: 10,
    hs_code_id: 100,
    hs_code: "01012100",
    description_vn: "Ngựa thuần chủng",
    notes: "Ghi chú test",
    created_at: "2026-02-20T10:00:00+07:00",
  },
  {
    id: 2,
    user_id: 10,
    hs_code_id: 200,
    hs_code: "02013000",
    description_vn: "Thịt trâu tươi",
    notes: null,
    created_at: "2026-02-19T10:00:00+07:00",
  },
];

describe("FavoritesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
    mockFavorites = [];
    mockGetFavorites.mockResolvedValue([]);
  });

  it("shows loading spinner on initial render", () => {
    mockGetFavorites.mockReturnValue(new Promise(() => {})); // never resolves
    render(<FavoritesPage />);
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("renders FavoriteCard for each favorite after fetch", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
      expect(screen.getByText("02013000")).toBeInTheDocument();
    });
  });

  it("shows empty state icon and message when no favorites", async () => {
    mockGetFavorites.mockResolvedValue([]);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(
        screen.getByText("Chưa có mã yêu thích")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Lưu mã HS để truy cập nhanh.")
      ).toBeInTheDocument();
    });
  });

  it("shows 'Bat dau tim kiem' link to /search in empty state", async () => {
    mockGetFavorites.mockResolvedValue([]);

    render(<FavoritesPage />);

    await waitFor(() => {
      const link = screen.getByText("Bắt đầu tìm kiếm");
      expect(link).toBeInTheDocument();
      expect(link.closest("a")).toHaveAttribute("href", "/search");
    });
  });

  it("shows error alert on fetch failure", async () => {
    mockGetFavorites.mockRejectedValue(new Error("Network error"));

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("removes favorite from list on unfavorite click", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const removeButtons = screen.getAllByRole("button", {
      name: "Xóa khỏi yêu thích",
    });
    fireEvent.click(removeButtons[0]);

    expect(mockRemoveFavoriteLocal).toHaveBeenCalledWith(1);
  });

  it("shows undo toast after removal", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const removeButtons = screen.getAllByRole("button", {
      name: "Xóa khỏi yêu thích",
    });
    fireEvent.click(removeButtons[0]);

    expect(
      screen.getByText("Đã xóa khỏi yêu thích")
    ).toBeInTheDocument();
    expect(screen.getByText("Hoàn tác")).toBeInTheDocument();
  });

  it("restores favorite when undo is clicked within timeout", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const removeButtons = screen.getAllByRole("button", {
      name: "Xóa khỏi yêu thích",
    });
    fireEvent.click(removeButtons[0]);

    // Click undo
    fireEvent.click(screen.getByText("Hoàn tác"));

    expect(mockAddFavoriteLocal).toHaveBeenCalledWith(sampleFavorites[0]);
  });

  it("calls removeFavorite API after undo timeout expires", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);
    mockRemoveFavorite.mockResolvedValue(undefined);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const removeButtons = screen.getAllByRole("button", {
      name: "Xóa khỏi yêu thích",
    });
    fireEvent.click(removeButtons[0]);

    // Advance past the 5-second undo window
    act(() => {
      vi.advanceTimersByTime(5100);
    });

    expect(mockRemoveFavorite).toHaveBeenCalledWith(1);

    vi.useRealTimers();
  });

  it("flushes pending undo when second remove is clicked", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);
    mockRemoveFavorite.mockResolvedValue(undefined);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const removeButtons = screen.getAllByRole("button", {
      name: "Xóa khỏi yêu thích",
    });

    // Remove first card — starts 5s undo window
    fireEvent.click(removeButtons[0]);
    expect(mockRemoveFavoriteLocal).toHaveBeenCalledWith(1);
    expect(mockRemoveFavorite).not.toHaveBeenCalled();

    // Remove second card — should flush pending delete of first card
    fireEvent.click(removeButtons[1]);
    expect(mockRemoveFavoriteLocal).toHaveBeenCalledWith(2);

    // First card's delete API should have been called immediately (flushed)
    expect(mockRemoveFavorite).toHaveBeenCalledWith(1);
  });

  // --- Search/filter tests (Story 6-4) ---

  it("renders search input with placeholder when favorites exist", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    expect(
      screen.getByPlaceholderText("Tìm trong yêu thích...")
    ).toBeInTheDocument();
  });

  it("filters by partial HS code match", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Tìm trong yêu thích...");
    fireEvent.change(searchInput, { target: { value: "0101" } });

    expect(screen.getByText("01012100")).toBeInTheDocument();
    expect(screen.queryByText("02013000")).not.toBeInTheDocument();
  });

  it("filters by partial description match (case-insensitive)", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Tìm trong yêu thích...");
    fireEvent.change(searchInput, { target: { value: "trâu" } });

    expect(screen.queryByText("01012100")).not.toBeInTheDocument();
    expect(screen.getByText("02013000")).toBeInTheDocument();
  });

  it("filters by notes content match", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Tìm trong yêu thích...");
    fireEvent.change(searchInput, { target: { value: "ghi chú" } });

    expect(screen.getByText("01012100")).toBeInTheDocument();
    expect(screen.queryByText("02013000")).not.toBeInTheDocument();
  });

  it("shows no-matches state when filter produces zero results", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Tìm trong yêu thích...");
    fireEvent.change(searchInput, { target: { value: "xyznotfound" } });

    expect(
      screen.getByText("Không có mã yêu thích phù hợp với tìm kiếm")
    ).toBeInTheDocument();
  });

  it("shows clear button when search has text", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    // No clear button initially
    expect(screen.queryByRole("button", { name: "Xóa bộ lọc" })).not.toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText("Tìm trong yêu thích...");
    fireEvent.change(searchInput, { target: { value: "test" } });

    expect(screen.getByRole("button", { name: "Xóa bộ lọc" })).toBeInTheDocument();
  });

  it("clears filter and shows all favorites when clear button clicked", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Tìm trong yêu thích...");
    fireEvent.change(searchInput, { target: { value: "0101" } });

    // Only one card visible
    expect(screen.queryByText("02013000")).not.toBeInTheDocument();

    // Click clear
    fireEvent.click(screen.getByRole("button", { name: "Xóa bộ lọc" }));

    // Both cards visible again
    expect(screen.getByText("01012100")).toBeInTheDocument();
    expect(screen.getByText("02013000")).toBeInTheDocument();
  });

  it("shows result count when filtering", async () => {
    mockFavorites = [...sampleFavorites];
    mockGetFavorites.mockResolvedValue(sampleFavorites);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("01012100")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Tìm trong yêu thích...");
    fireEvent.change(searchInput, { target: { value: "0101" } });

    expect(screen.getByText("1 / 2 mã yêu thích")).toBeInTheDocument();
  });

  it("search input not rendered when favorites list is empty", async () => {
    mockGetFavorites.mockResolvedValue([]);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText("Chưa có mã yêu thích")).toBeInTheDocument();
    });

    expect(
      screen.queryByPlaceholderText("Tìm trong yêu thích...")
    ).not.toBeInTheDocument();
  });
});
