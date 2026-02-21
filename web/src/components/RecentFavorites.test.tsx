import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// Mock store
let mockFavorites: import("@/types/favorite").Favorite[] = [];

vi.mock("@/lib/store", () => ({
  useStore: (selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      favorites: mockFavorites,
    }),
}));

import { RecentFavorites } from "./RecentFavorites";
import type { Favorite } from "@/types/favorite";

const sampleFavorites: Favorite[] = [
  { id: 1, user_id: 10, hs_code_id: 100, hs_code: "85094010", description_vn: "Máy xay cà phê điện dùng trong gia đình", notes: null, created_at: "2026-02-20T10:00:00+07:00" },
  { id: 2, user_id: 10, hs_code_id: 200, hs_code: "09011100", description_vn: "Cà phê hạt chưa rang", notes: null, created_at: "2026-02-19T10:00:00+07:00" },
  { id: 3, user_id: 10, hs_code_id: 300, hs_code: "02013000", description_vn: "Thịt trâu tươi", notes: "test", created_at: "2026-02-18T10:00:00+07:00" },
  { id: 4, user_id: 10, hs_code_id: 400, hs_code: "01012100", description_vn: "Ngựa thuần chủng", notes: null, created_at: "2026-02-17T10:00:00+07:00" },
  { id: 5, user_id: 10, hs_code_id: 500, hs_code: "44039100", description_vn: "Gỗ sồi thô", notes: null, created_at: "2026-02-16T10:00:00+07:00" },
  { id: 6, user_id: 10, hs_code_id: 600, hs_code: "73041100", description_vn: "Ống thép không hàn", notes: null, created_at: "2026-02-15T10:00:00+07:00" },
];

describe("RecentFavorites", () => {
  beforeEach(() => {
    mockFavorites = [];
  });

  it("renders nothing when favorites is empty", () => {
    const { container } = render(<RecentFavorites />);
    expect(container.innerHTML).toBe("");
  });

  it("renders up to 5 favorites by default", () => {
    mockFavorites = [...sampleFavorites]; // 6 items
    render(<RecentFavorites />);

    expect(screen.getByText("85094010")).toBeInTheDocument();
    expect(screen.getByText("09011100")).toBeInTheDocument();
    expect(screen.getByText("02013000")).toBeInTheDocument();
    expect(screen.getByText("01012100")).toBeInTheDocument();
    expect(screen.getByText("44039100")).toBeInTheDocument();
    // 6th item should NOT be shown
    expect(screen.queryByText("73041100")).not.toBeInTheDocument();
  });

  it("shows HS code and description for each item", () => {
    mockFavorites = [sampleFavorites[0]];
    render(<RecentFavorites />);

    expect(screen.getByText("85094010")).toBeInTheDocument();
    expect(screen.getByText("Máy xay cà phê điện dùng trong gia đình")).toBeInTheDocument();
  });

  it("shows header with 'Yêu thích gần đây'", () => {
    mockFavorites = [sampleFavorites[0]];
    render(<RecentFavorites />);

    expect(screen.getByText("Yêu thích gần đây")).toBeInTheDocument();
  });

  it("shows 'Xem tất cả' link to /favorites", () => {
    mockFavorites = [sampleFavorites[0]];
    render(<RecentFavorites />);

    const link = screen.getByText("Xem tất cả →");
    expect(link).toBeInTheDocument();
    expect(link.closest("a")).toHaveAttribute("href", "/favorites");
  });

  it("calls onItemClick with hs_code when item is clicked", () => {
    mockFavorites = [sampleFavorites[0]];
    const handleClick = vi.fn();
    render(<RecentFavorites onItemClick={handleClick} />);

    fireEvent.click(screen.getByText("85094010"));
    expect(handleClick).toHaveBeenCalledWith("85094010");
  });

  it("renders collapsed by default when collapsible and defaultCollapsed", () => {
    mockFavorites = [sampleFavorites[0]];
    render(<RecentFavorites collapsible defaultCollapsed />);

    // Header should be visible
    expect(screen.getByText("Yêu thích gần đây")).toBeInTheDocument();
    // Items should NOT be visible
    expect(screen.queryByText("85094010")).not.toBeInTheDocument();
    // View all link should NOT be visible
    expect(screen.queryByText("Xem tất cả →")).not.toBeInTheDocument();
  });

  it("expands on header click when collapsible", () => {
    mockFavorites = [sampleFavorites[0]];
    render(<RecentFavorites collapsible defaultCollapsed />);

    // Click header to expand
    fireEvent.click(screen.getByText("Yêu thích gần đây"));

    // Items should now be visible
    expect(screen.getByText("85094010")).toBeInTheDocument();
    expect(screen.getByText("Xem tất cả →")).toBeInTheDocument();
  });

  it("does not show more than maxItems", () => {
    mockFavorites = [...sampleFavorites]; // 6 items
    render(<RecentFavorites maxItems={3} />);

    expect(screen.getByText("85094010")).toBeInTheDocument();
    expect(screen.getByText("09011100")).toBeInTheDocument();
    expect(screen.getByText("02013000")).toBeInTheDocument();
    // 4th and beyond should NOT be shown
    expect(screen.queryByText("01012100")).not.toBeInTheDocument();
    expect(screen.queryByText("44039100")).not.toBeInTheDocument();
  });

  it("shows most recent favorites first even when store order is not sorted", () => {
    // Simulate addFavoriteLocal appending a new (most recent) favorite to the end
    const newestFavorite: Favorite = {
      id: 99,
      user_id: 10,
      hs_code_id: 999,
      hs_code: "99999999",
      description_vn: "Mới nhất",
      notes: null,
      created_at: "2026-02-25T10:00:00+07:00", // Most recent
    };
    // Store order: oldest-to-newest appended at end (wrong order for display)
    mockFavorites = [...sampleFavorites, newestFavorite]; // 7 items, newest at end

    render(<RecentFavorites maxItems={3} />);

    // The newest item (99999999) should appear in the top 3 despite being at array end
    expect(screen.getByText("99999999")).toBeInTheDocument();
    // Older items beyond maxItems should NOT be shown
    expect(screen.queryByText("44039100")).not.toBeInTheDocument();
    expect(screen.queryByText("73041100")).not.toBeInTheDocument();
  });
});
