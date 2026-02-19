import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { UserList } from "./UserList";

// Mock the API client
const mockGet = vi.fn();
const mockPatch = vi.fn();
vi.mock("@/lib/api", () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
  },
}));

const mockUsers = {
  items: [
    { id: 1, email: "admin@example.com", role: "admin", created_at: "2026-02-15T00:00:00Z" },
    { id: 2, email: "user@example.com", role: "user", created_at: "2026-02-15T00:00:00Z" },
  ],
  total: 2,
  page: 1,
  per_page: 20,
  pages: 1,
};

describe("UserList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue({ success: true, data: mockUsers, error: null });
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
      data: { id: 2, email: "user@example.com", role: "admin", created_at: "2026-02-15T00:00:00Z" },
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
      data: { id: 2, email: "user@example.com", role: "admin", created_at: "2026-02-15T00:00:00Z" },
      error: null,
    });

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText("user@example.com")).toBeInTheDocument();
    });

    const selects = screen.getAllByRole("combobox");
    await user.selectOptions(selects[1], "admin");

    await waitFor(() => {
      expect(screen.getByText("Cập nhật vai trò thành công")).toBeInTheDocument();
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
    expect(options[0]).toHaveTextContent("Người dùng");
    expect(options[1]).toHaveValue("expert");
    expect(options[1]).toHaveTextContent("Chuyên gia");
    expect(options[2]).toHaveValue("admin");
    expect(options[2]).toHaveTextContent("Quản trị viên");
  });

  it("can change role to expert", async () => {
    const user = userEvent.setup();
    window.confirm = vi.fn(() => true);
    mockPatch.mockResolvedValue({
      success: true,
      data: { id: 2, email: "user@example.com", role: "expert", created_at: "2026-02-15T00:00:00Z" },
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
      expect(screen.getByText("Trang 1 / 2 (40 người dùng)")).toBeInTheDocument();
    });

    expect(screen.getByText("Trước")).toBeDisabled();
    expect(screen.getByText("Sau")).not.toBeDisabled();
  });
});
