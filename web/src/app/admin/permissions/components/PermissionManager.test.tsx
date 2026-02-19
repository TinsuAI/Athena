import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { PermissionManager } from "./PermissionManager";

// Mock the API client
const mockGet = vi.fn();
const mockPut = vi.fn();
vi.mock("@/lib/api", () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    put: (...args: unknown[]) => mockPut(...args),
  },
}));

const mockRolePermissions = {
  all_permissions: [
    { code: "correction.submit", name: "Gui chinh sua", description: "Can submit corrections" },
    { code: "correction.approve", name: "Phe duyet chinh sua", description: "Can approve corrections" },
    { code: "user.manage", name: "Quan ly nguoi dung", description: "Can manage users" },
    { code: "data.manage", name: "Quan ly du lieu", description: "Can manage data" },
    { code: "lookup.view_all", name: "Xem tat ca tra cuu", description: "Can view all lookups" },
  ],
  roles: [
    { role: "user", permissions: ["correction.submit"] },
    { role: "expert", permissions: ["correction.submit", "correction.approve", "lookup.view_all"] },
    { role: "admin", permissions: ["correction.submit", "correction.approve", "user.manage", "data.manage", "lookup.view_all"] },
  ],
};

const mockUsers = {
  items: [
    { id: 2, email: "user@example.com", role: "user", is_active: true, created_at: "2026-02-18T00:00:00Z" },
    { id: 3, email: "expert@example.com", role: "expert", is_active: true, created_at: "2026-02-18T00:00:00Z" },
  ],
  total: 2,
  page: 1,
  per_page: 10,
  pages: 1,
};

const mockUserPerms = {
  user_id: 2,
  role: "user",
  role_permissions: ["correction.submit"],
  overrides: [],
  effective: ["correction.submit"],
};

describe("PermissionManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: roles tab loads permissions
    mockGet.mockImplementation((url: string) => {
      if (url.includes("/api/admin/permissions/roles")) {
        return Promise.resolve({ success: true, data: mockRolePermissions, error: null });
      }
      if (url.includes("/api/admin/users")) {
        return Promise.resolve({ success: true, data: mockUsers, error: null });
      }
      if (url.includes("/api/admin/permissions/users/")) {
        return Promise.resolve({ success: true, data: mockUserPerms, error: null });
      }
      return Promise.resolve({ success: false, data: null, error: { detail: "Not found" } });
    });
  });

  it("renders roles tab with role permissions checkboxes", async () => {
    render(<PermissionManager />);

    // Wait for permission column headers to appear (these are unique)
    await waitFor(() => {
      expect(screen.getByText("Gui chinh sua")).toBeInTheDocument();
      expect(screen.getByText("Phe duyet chinh sua")).toBeInTheDocument();
      expect(screen.getByText("Quan ly nguoi dung")).toBeInTheDocument();
    });

    // Role labels should appear in the table
    expect(screen.getByText("Chuyên gia")).toBeInTheDocument();
    expect(screen.getByText("Quản trị viên")).toBeInTheDocument();
  });

  it("switches to users tab and shows search input", async () => {
    const user = userEvent.setup();
    render(<PermissionManager />);

    // Wait for roles tab to load
    await waitFor(() => {
      expect(screen.getByText("Gui chinh sua")).toBeInTheDocument();
    });

    // Click the "Nguoi dung" tab button using data-testid
    const usersTabButton = screen.getByTestId("tab-users");
    await user.click(usersTabButton);

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Tìm người dùng theo email...")
      ).toBeInTheDocument();
    });
  });

  it("permission checkbox toggles on click in roles tab", async () => {
    const user = userEvent.setup();
    render(<PermissionManager />);

    // Wait for permission table to render
    await waitFor(() => {
      expect(screen.getByText("Gui chinh sua")).toBeInTheDocument();
    });

    // Find all checkboxes
    const checkboxes = screen.getAllByRole("checkbox");
    // Roles tab: 3 roles * 5 permissions = 15 checkboxes
    expect(checkboxes.length).toBe(15);

    // The first checkbox is user role's correction.submit - should be checked
    expect(checkboxes[0]).toBeChecked();

    // Click to uncheck it
    await user.click(checkboxes[0]);
    expect(checkboxes[0]).not.toBeChecked();

    // Click again to re-check
    await user.click(checkboxes[0]);
    expect(checkboxes[0]).toBeChecked();
  });
});
