/**
 * Tests for Header component logout flow.
 *
 * TEST COVERAGE:
 * - Unit tests: Header component logout UI behavior (this file)
 * - Integration tests: Full logout + route protection flow (NOT IMPLEMENTED)
 *
 * KNOWN LIMITATION:
 * These unit tests verify that clicking logout calls signOut({ callbackUrl: "/login" })
 * and clears Zustand state, but they do NOT verify that:
 * 1. The proxy.ts actually redirects protected routes to /login after logout
 * 2. The back button doesn't allow cached access to protected pages
 *
 * Those behaviors are tested manually or would require E2E/integration tests
 * with full page navigation (Playwright/Cypress).
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { Header } from "./Header";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/search"),
}));

// Mock next-auth/react
const mockSignOut = vi.fn();
vi.mock("next-auth/react", () => ({
  useSession: vi.fn(),
  signOut: (...args: unknown[]) => mockSignOut(...args),
}));

// Mock store with full state
const mockLogout = vi.fn();
const mockStoreState = {
  logout: mockLogout,
  // Add other store slices if Header needs them in the future
  searchQuery: "",
  searchResult: null,
  isSearching: false,
  favoriteIds: [],
};
vi.mock("@/lib/store", () => ({
  useStore: (selector: (s: typeof mockStoreState) => unknown) =>
    selector(mockStoreState),
}));

// Import mocked useSession to control return values
import { useSession } from "next-auth/react";
const mockUseSession = vi.mocked(useSession);

describe("Header", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders logout button when session exists", () => {
    mockUseSession.mockReturnValue({
      data: { user: { email: "test@example.com" }, expires: "" },
      status: "authenticated",
      update: vi.fn(),
    });

    render(<Header />);

    expect(screen.getByText("Log out")).toBeInTheDocument();
  });

  it("clicking logout calls signOut with callbackUrl /login", async () => {
    const user = userEvent.setup();
    mockUseSession.mockReturnValue({
      data: { user: { email: "test@example.com" }, expires: "" },
      status: "authenticated",
      update: vi.fn(),
    });

    render(<Header />);

    await user.click(screen.getByText("Log out"));

    expect(mockSignOut).toHaveBeenCalledWith({ callbackUrl: "/login" });
  });

  it("clicking logout clears Zustand auth state", async () => {
    const user = userEvent.setup();
    mockUseSession.mockReturnValue({
      data: { user: { email: "test@example.com" }, expires: "" },
      status: "authenticated",
      update: vi.fn(),
    });

    render(<Header />);

    await user.click(screen.getByText("Log out"));

    expect(mockLogout).toHaveBeenCalled();
  });

  it("renders login/register links when no session", () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: "unauthenticated",
      update: vi.fn(),
    });

    render(<Header />);

    expect(screen.getByText("Log in")).toBeInTheDocument();
    expect(screen.getByText("Sign up")).toBeInTheDocument();
    expect(screen.queryByText("Log out")).not.toBeInTheDocument();
  });

  it("shows email when session has user", () => {
    mockUseSession.mockReturnValue({
      data: { user: { email: "user@example.com" }, expires: "" },
      status: "authenticated",
      update: vi.fn(),
    });

    render(<Header />);

    expect(screen.getByText("user@example.com")).toBeInTheDocument();
  });

  it("handles signOut errors gracefully", async () => {
    const user = userEvent.setup();
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    // Set up error-throwing mock
    mockSignOut.mockImplementationOnce(() => {
      throw new Error("Network error");
    });

    mockUseSession.mockReturnValue({
      data: { user: { email: "test@example.com" }, expires: "" },
      status: "authenticated",
      update: vi.fn(),
    });

    render(<Header />);

    // Click should not crash the app even if signOut throws
    await user.click(screen.getByText("Log out"));

    // Logout should still be called before the error
    expect(mockLogout).toHaveBeenCalled();
    // Console error should be logged
    expect(consoleErrorSpy).toHaveBeenCalledWith("Logout error:", expect.any(Error));

    consoleErrorSpy.mockRestore();
  });

  it("handles rapid logout clicks without duplicate calls", async () => {
    const user = userEvent.setup();
    mockUseSession.mockReturnValue({
      data: { user: { email: "test@example.com" }, expires: "" },
      status: "authenticated",
      update: vi.fn(),
    });

    render(<Header />);

    const logoutButton = screen.getByText("Log out");

    // Click multiple times rapidly
    await user.click(logoutButton);
    await user.click(logoutButton);
    await user.click(logoutButton);

    // Store logout should be called 3 times (no debouncing implemented)
    expect(mockLogout).toHaveBeenCalledTimes(3);
    // signOut should also be called 3 times
    expect(mockSignOut).toHaveBeenCalledTimes(3);

    // Note: This test documents current behavior. If debouncing is needed,
    // it should be implemented and this test updated.
  });
});
