import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock store
const mockStore = {
  favoriteIds: [] as number[],
  favorites: [] as Array<{ id: number; hs_code_id: number }>,
  addFavoriteLocal: vi.fn(),
  removeFavoriteLocal: vi.fn(),
};

vi.mock("@/lib/store", () => ({
  useStore: (selector: (state: typeof mockStore) => unknown) =>
    selector(mockStore),
}));

// Mock API
const mockAddFavorite = vi.fn();
const mockRemoveFavorite = vi.fn();

vi.mock("@/lib/api", () => ({
  addFavorite: (...args: unknown[]) => mockAddFavorite(...args),
  removeFavorite: (...args: unknown[]) => mockRemoveFavorite(...args),
}));

import { FavoriteButton } from "./FavoriteButton";

describe("FavoriteButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockStore.favoriteIds = [];
    mockStore.favorites = [];
  });

  it("renders star icon button", () => {
    render(<FavoriteButton hsCodeId={100} />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-label", "Thêm vào yêu thích");
  });

  it("shows unfavorited state when not in favoriteIds", () => {
    render(<FavoriteButton hsCodeId={100} />);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-pressed", "false");
  });

  it("shows favorited state when in favoriteIds", () => {
    mockStore.favoriteIds = [100];
    mockStore.favorites = [{ id: 1, hs_code_id: 100 }];

    render(<FavoriteButton hsCodeId={100} />);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-pressed", "true");
    expect(button).toHaveAttribute("aria-label", "Xóa khỏi yêu thích");
  });

  it("optimistically adds then calls API on click when not favorited", async () => {
    mockAddFavorite.mockResolvedValue({
      id: 1,
      user_id: 10,
      hs_code_id: 100,
      hs_code: "01012100",
      description_vn: "Test",
      notes: null,
      created_at: "2026-02-21",
    });

    render(<FavoriteButton hsCodeId={100} />);
    fireEvent.click(screen.getByRole("button"));

    // Optimistic add called immediately with temp favorite
    expect(mockStore.addFavoriteLocal).toHaveBeenCalled();

    await waitFor(() => {
      expect(mockAddFavorite).toHaveBeenCalledWith(100);
    });
  });

  it("calls removeFavorite API on click when favorited", async () => {
    mockStore.favoriteIds = [100];
    mockStore.favorites = [{ id: 1, hs_code_id: 100 }];
    mockRemoveFavorite.mockResolvedValue(undefined);

    render(<FavoriteButton hsCodeId={100} />);
    fireEvent.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(mockRemoveFavorite).toHaveBeenCalledWith(1);
    });
  });

  it("shows toast after successful add", async () => {
    mockAddFavorite.mockResolvedValue({
      id: 1,
      user_id: 10,
      hs_code_id: 100,
      hs_code: "01012100",
      description_vn: "Test",
      notes: null,
      created_at: "2026-02-21",
    });

    render(<FavoriteButton hsCodeId={100} />);
    fireEvent.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(screen.getByText("Đã thêm vào yêu thích")).toBeInTheDocument();
    });
  });

  it("respects size prop", () => {
    const { container } = render(<FavoriteButton hsCodeId={100} size="sm" />);
    const button = container.querySelector("button");
    expect(button?.className).toContain("h-7");
  });
});
