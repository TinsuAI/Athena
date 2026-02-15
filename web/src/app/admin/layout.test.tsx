import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock next-auth/react
vi.mock("next-auth/react", () => ({
  useSession: vi.fn(),
}));

import { useSession } from "next-auth/react";
const mockUseSession = vi.mocked(useSession);

import AdminLayout from "./layout";

describe("AdminLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders children for admin user", () => {
    mockUseSession.mockReturnValue({
      data: { user: { email: "admin@example.com", role: "admin" }, expires: "" },
      status: "authenticated",
      update: vi.fn(),
    });

    render(
      <AdminLayout>
        <div>Admin Content</div>
      </AdminLayout>
    );

    expect(screen.getByText("Admin Content")).toBeInTheDocument();
  });

  it("shows Access Denied for non-admin user", () => {
    mockUseSession.mockReturnValue({
      data: { user: { email: "user@example.com", role: "user" }, expires: "" },
      status: "authenticated",
      update: vi.fn(),
    });

    render(
      <AdminLayout>
        <div>Admin Content</div>
      </AdminLayout>
    );

    expect(screen.getByText("Access Denied")).toBeInTheDocument();
    expect(screen.queryByText("Admin Content")).not.toBeInTheDocument();
  });

  it("redirects non-admin user to /search after 2 seconds", () => {
    mockUseSession.mockReturnValue({
      data: { user: { email: "user@example.com", role: "user" }, expires: "" },
      status: "authenticated",
      update: vi.fn(),
    });

    render(
      <AdminLayout>
        <div>Admin Content</div>
      </AdminLayout>
    );

    expect(mockPush).not.toHaveBeenCalled();

    vi.advanceTimersByTime(2000);

    expect(mockPush).toHaveBeenCalledWith("/search");
  });

  it("shows loading spinner when session is loading", () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: "loading",
      update: vi.fn(),
    });

    render(
      <AdminLayout>
        <div>Admin Content</div>
      </AdminLayout>
    );

    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("Admin Content")).not.toBeInTheDocument();
  });
});
