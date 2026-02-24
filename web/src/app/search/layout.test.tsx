import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock next/navigation
const mockRedirect = vi.fn();
vi.mock("next/navigation", () => ({ redirect: mockRedirect }));

// Mock auth
const mockAuth = vi.fn();
vi.mock("@/lib/auth", () => ({ auth: mockAuth }));

// Mock fetch
global.fetch = vi.fn();

describe("SearchLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("redirects unauthenticated user when auth required", async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: { search_requires_auth: "true" } }),
    } as Response);
    mockAuth.mockResolvedValueOnce(null); // no session

    const { default: SearchLayout } = await import("./layout");
    await SearchLayout({ children: <div /> });

    expect(mockRedirect).toHaveBeenCalledWith("/login?callbackUrl=/search");
  });

  it("does not redirect authenticated user when auth required", async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: { search_requires_auth: "true" } }),
    } as Response);
    mockAuth.mockResolvedValueOnce({ user: { email: "user@test.com" } }); // has session

    const { default: SearchLayout } = await import("./layout");
    await SearchLayout({ children: <div /> });

    expect(mockRedirect).not.toHaveBeenCalled();
  });

  it("does not redirect when auth not required", async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: { search_requires_auth: "false" } }),
    } as Response);

    const { default: SearchLayout } = await import("./layout");
    await SearchLayout({ children: <div /> });

    expect(mockRedirect).not.toHaveBeenCalled();
    expect(mockAuth).not.toHaveBeenCalled();
  });

  it("fail-safe: redirects if fetch throws (defaults to auth required)", async () => {
    vi.mocked(global.fetch).mockRejectedValueOnce(new Error("Network error"));
    mockAuth.mockResolvedValueOnce(null); // no session

    const { default: SearchLayout } = await import("./layout");
    await SearchLayout({ children: <div /> });

    expect(mockRedirect).toHaveBeenCalledWith("/login?callbackUrl=/search");
  });
});
