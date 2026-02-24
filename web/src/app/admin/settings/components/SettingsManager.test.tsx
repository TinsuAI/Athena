import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// vi.mock is hoisted — use vi.hoisted() so mockGet/mockPut are available inside the factory
const { mockGet, mockPut } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPut: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  apiClient: {
    get: mockGet,
    put: mockPut,
  },
}));

import SettingsManager from "./SettingsManager";

describe("SettingsManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders settings with toggle in correct state", async () => {
    mockGet.mockResolvedValueOnce({
      success: true,
      data: [
        {
          key: "search_requires_auth",
          value: "true",
          description: "Yêu cầu đăng nhập để sử dụng tính năng tìm kiếm",
        },
      ],
    });

    render(<SettingsManager />);

    await waitFor(() => {
      expect(screen.getByRole("switch")).toBeInTheDocument();
    });

    const toggle = screen.getByRole("switch");
    expect(toggle).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("Tìm kiếm yêu cầu đăng nhập")).toBeInTheDocument();
  });

  it("calls PUT and updates toggle state on click", async () => {
    mockGet.mockResolvedValueOnce({
      success: true,
      data: [{ key: "search_requires_auth", value: "true", description: null }],
    });
    mockPut.mockResolvedValueOnce({
      success: true,
      data: { key: "search_requires_auth", value: "false", description: null },
    });

    render(<SettingsManager />);

    await waitFor(() => screen.getByRole("switch"));

    fireEvent.click(screen.getByRole("switch"));

    await waitFor(() => {
      expect(mockPut).toHaveBeenCalledWith(
        "/api/admin/settings/search_requires_auth",
        { value: "false" }
      );
    });

    await waitFor(() => {
      expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "false");
    });
  });

  it("shows success message after update", async () => {
    mockGet.mockResolvedValueOnce({
      success: true,
      data: [{ key: "search_requires_auth", value: "false", description: null }],
    });
    mockPut.mockResolvedValueOnce({
      success: true,
      data: { key: "search_requires_auth", value: "true", description: null },
    });

    render(<SettingsManager />);
    await waitFor(() => screen.getByRole("switch"));
    fireEvent.click(screen.getByRole("switch"));

    await waitFor(() => {
      expect(screen.getByText("Cập nhật thành công")).toBeInTheDocument();
    });
  });

  it("shows error message when PUT fails", async () => {
    mockGet.mockResolvedValueOnce({
      success: true,
      data: [{ key: "search_requires_auth", value: "true", description: null }],
    });
    mockPut.mockResolvedValueOnce({ success: false, data: null, error: { detail: "error" } });

    render(<SettingsManager />);
    await waitFor(() => screen.getByRole("switch"));
    fireEvent.click(screen.getByRole("switch"));

    await waitFor(() => {
      expect(screen.getByText("Cập nhật thất bại")).toBeInTheDocument();
    });
  });
});
