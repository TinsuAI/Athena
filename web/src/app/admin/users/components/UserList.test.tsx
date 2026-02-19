import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { UserList } from "./UserList";

// Mock the API client
const mockGet = vi.fn();
const mockPatch = vi.fn();
const mockPost = vi.fn();
vi.mock("@/lib/api", () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

// Mock next-auth/react useSession
const mockUseSession = vi.fn();
vi.mock("next-auth/react", () => ({
  useSession: () => mockUseSession(),
}));

const mockUsers = {
  items: [
    { id: 1, email: "admin@example.com", role: "admin", is_active: true, created_at: "2026-02-15T00:00:00Z" },
    { id: 2, email: "user@example.com", role: "user", is_active: true, created_at: "2026-02-15T00:00:00Z" },
    { id: 3, email: "inactive@example.com", role: "user", is_active: false, created_at: "2026-02-15T00:00:00Z" },
  ],
  total: 3,
  page: 1,
  per_page: 20,
  pages: 1,
};

describe("UserList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue({ success: true, data: mockUsers, error: null });
    mockUseSession.mockReturnValue({
      data: { user: { id: "1", email: "admin@example.com", role: "admin" } },
      status: "authenticated",
    });
  });

  it("renders user table with emails and roles", async () => {
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("admin@example.com")).toBeInTheDocument();
      expect(screen.getByText("user@example.com")).toBeInTheDocument();
    });
  });

  it("role dropdown triggers PATCH request on change", async () => {
    const user = userEvent.setup();
    window.confirm = vi.fn(() => true);
    mockPatch.mockResolvedValue({
      success: true,
      data: { id: 2, email: "user@example.com", role: "admin", is_active: true, created_at: "2026-02-15T00:00:00Z" },
      error: null,
    });

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("user@example.com")).toBeInTheDocument();
    });

    const selects = screen.getAllByRole("combobox");
    // Second user's select
    await user.selectOptions(selects[1], "admin");

    expect(mockPatch).toHaveBeenCalledWith("/api/admin/users/2/role", { role: "admin" });
  });

  it("shows confirmation before role change", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.fn(() => false);
    window.confirm = confirmSpy;

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("user@example.com")).toBeInTheDocument();
    });

    const selects = screen.getAllByRole("combobox");
    await user.selectOptions(selects[1], "admin");

    expect(confirmSpy).toHaveBeenCalled();
    // PATCH should NOT be called if confirm returns false
    expect(mockPatch).not.toHaveBeenCalled();
  });

  it("shows success message after role change", async () => {
    const user = userEvent.setup();
    window.confirm = vi.fn(() => true);
    mockPatch.mockResolvedValue({
      success: true,
      data: { id: 2, email: "user@example.com", role: "admin", is_active: true, created_at: "2026-02-15T00:00:00Z" },
      error: null,
    });

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("user@example.com")).toBeInTheDocument();
    });

    const selects = screen.getAllByRole("combobox");
    await user.selectOptions(selects[1], "admin");

    await waitFor(() => {
      expect(screen.getByText("Cap nhat vai tro thanh cong")).toBeInTheDocument();
    });
  });

  it("handles API error gracefully", async () => {
    const user = userEvent.setup();
    window.confirm = vi.fn(() => true);
    mockPatch.mockResolvedValue({
      success: false,
      data: null,
      error: { detail: "Cannot change your own role", type: "", title: "", status: 400, instance: "" },
    });

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("user@example.com")).toBeInTheDocument();
    });

    const selects = screen.getAllByRole("combobox");
    await user.selectOptions(selects[1], "admin");

    await waitFor(() => {
      expect(screen.getByText("Cannot change your own role")).toBeInTheDocument();
    });
  });

  it("role dropdown has three options: user, expert, admin", async () => {
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("user@example.com")).toBeInTheDocument();
    });

    const selects = screen.getAllByRole("combobox");
    const firstSelect = selects[0];
    const options = firstSelect.querySelectorAll("option");

    expect(options).toHaveLength(3);
    expect(options[0]).toHaveValue("user");
    expect(options[0]).toHaveTextContent("Nguoi dung");
    expect(options[1]).toHaveValue("expert");
    expect(options[1]).toHaveTextContent("Chuyen gia");
    expect(options[2]).toHaveValue("admin");
    expect(options[2]).toHaveTextContent("Quan tri vien");
  });

  it("can change role to expert", async () => {
    const user = userEvent.setup();
    window.confirm = vi.fn(() => true);
    mockPatch.mockResolvedValue({
      success: true,
      data: { id: 2, email: "user@example.com", role: "expert", is_active: true, created_at: "2026-02-15T00:00:00Z" },
      error: null,
    });

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("user@example.com")).toBeInTheDocument();
    });

    const selects = screen.getAllByRole("combobox");
    await user.selectOptions(selects[1], "expert");

    expect(mockPatch).toHaveBeenCalledWith("/api/admin/users/2/role", { role: "expert" });
  });

  it("pagination controls work", async () => {
    mockGet.mockResolvedValue({
      success: true,
      data: {
        ...mockUsers,
        total: 40,
        pages: 2,
      },
      error: null,
    });

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("Trang 1 / 2 (40 nguoi dung)")).toBeInTheDocument();
    });

    expect(screen.getByText("Truoc")).toBeDisabled();
    expect(screen.getByText("Sau")).not.toBeDisabled();
  });

  // === New tests for Story 5-4 features ===

  it("search input passes query to API", async () => {
    const user = userEvent.setup();
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("admin@example.com")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Tim kiem theo email...");
    expect(searchInput).toBeInTheDocument();

    await user.type(searchInput, "user@");

    // Wait for debounce (300ms) and re-fetch
    await waitFor(() => {
      const lastCall = mockGet.mock.calls[mockGet.mock.calls.length - 1][0];
      expect(lastCall).toContain("search=user%40");
    }, { timeout: 1000 });
  });

  it("create user button opens form", async () => {
    const user = userEvent.setup();
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("admin@example.com")).toBeInTheDocument();
    });

    const createButton = screen.getByText("Tao nguoi dung");
    await user.click(createButton);

    await waitFor(() => {
      expect(screen.getByText("Tao nguoi dung moi")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("email@example.com")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("Toi thieu 8 ky tu")).toBeInTheDocument();
    });
  });

  it("deactivate button shows confirmation", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.fn(() => false);
    window.confirm = confirmSpy;

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("user@example.com")).toBeInTheDocument();
    });

    // Find deactivate buttons (not including the one for admin's own row which is disabled)
    const deactivateButtons = screen.getAllByText("Vo hieu hoa");
    // Click the first non-disabled one (for user@example.com)
    const enabledButton = deactivateButtons.find(btn => !(btn as HTMLButtonElement).disabled);
    if (enabledButton) {
      await user.click(enabledButton);
      expect(confirmSpy).toHaveBeenCalled();
    }
  });

  it("status column shows active and inactive indicators", async () => {
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("admin@example.com")).toBeInTheDocument();
    });

    // Check for active indicators
    const activeIndicators = screen.getAllByText("Hoat dong");
    expect(activeIndicators.length).toBeGreaterThanOrEqual(2);

    // Check for inactive indicator
    const inactiveIndicator = screen.getByText((content, element) => {
      return element?.tagName === "SPAN" && content === "Vo hieu hoa" && element?.classList.contains("text-red-600");
    });
    expect(inactiveIndicator).toBeInTheDocument();
  });
});
