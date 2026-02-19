import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock next-auth/react
vi.mock("next-auth/react", () => ({
  useSession: vi.fn(),
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/expert/corrections",
}));

// Mock api client
vi.mock("@/lib/api", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { useSession } from "next-auth/react";
import { apiClient } from "@/lib/api";
const mockUseSession = vi.mocked(useSession);
const mockApiGet = vi.mocked(apiClient.get);
const mockApiPost = vi.mocked(apiClient.post);

import ExpertCorrectionsPage from "./page";

describe("ExpertCorrectionsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows access denied for user role", () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { email: "user@example.com", role: "user" },
        expires: "",
      },
      status: "authenticated",
      update: vi.fn(),
    });

    render(<ExpertCorrectionsPage />);

    expect(
      screen.getByText("Khong co quyen truy cap")
    ).toBeInTheDocument();
  });

  it("displays pending corrections list for expert user", async () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { email: "expert@example.com", role: "expert" },
        expires: "",
      },
      status: "authenticated",
      update: vi.fn(),
    });

    mockApiGet.mockResolvedValue({
      success: true,
      data: {
        items: [
          {
            id: 1,
            query_text: "copper towel rack",
            matched_hs_code: "7418.20.00",
            matched_description_vn: "Do dung ve sinh bang dong",
            matched_description_en: null,
            correct_hs_code: "7418.20.10",
            correct_description_vn: "Gia treo khan dong",
            correct_description_en: null,
            submitter_email: "user@example.com",
            submitted_at: "2026-02-18T10:00:00+00:00",
            notes: "Ma HS chinh xac hon",
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
      },
      error: null,
    });

    render(<ExpertCorrectionsPage />);

    await waitFor(() => {
      expect(screen.getByText("copper towel rack")).toBeInTheDocument();
    });

    expect(screen.getByText("7418.20.00")).toBeInTheDocument();
    expect(screen.getByText("7418.20.10")).toBeInTheDocument();
    expect(screen.getByText("user@example.com")).toBeInTheDocument();
  });

  it("approve button triggers API call", async () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { email: "expert@example.com", role: "expert" },
        expires: "",
      },
      status: "authenticated",
      update: vi.fn(),
    });

    mockApiGet.mockResolvedValue({
      success: true,
      data: {
        items: [
          {
            id: 1,
            query_text: "copper towel rack",
            matched_hs_code: "7418.20.00",
            matched_description_vn: null,
            matched_description_en: null,
            correct_hs_code: "7418.20.10",
            correct_description_vn: null,
            correct_description_en: null,
            submitter_email: "user@example.com",
            submitted_at: "2026-02-18T10:00:00+00:00",
            notes: null,
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
      },
      error: null,
    });

    mockApiPost.mockResolvedValue({
      success: true,
      data: { id: 1, correction_status: "approved", is_verified: true },
      error: null,
    });

    render(<ExpertCorrectionsPage />);

    await waitFor(() => {
      expect(screen.getByText("copper towel rack")).toBeInTheDocument();
    });

    const approveButton = screen.getByText("Phe duyet");
    fireEvent.click(approveButton);

    await waitFor(() => {
      expect(mockApiPost).toHaveBeenCalledWith(
        "/api/expert/corrections/1/approve",
        {}
      );
    });
  });

  it("reject with reason triggers API call", async () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { email: "expert@example.com", role: "expert" },
        expires: "",
      },
      status: "authenticated",
      update: vi.fn(),
    });

    mockApiGet.mockResolvedValue({
      success: true,
      data: {
        items: [
          {
            id: 1,
            query_text: "copper towel rack",
            matched_hs_code: "7418.20.00",
            matched_description_vn: null,
            matched_description_en: null,
            correct_hs_code: "7418.20.10",
            correct_description_vn: null,
            correct_description_en: null,
            submitter_email: "user@example.com",
            submitted_at: "2026-02-18T10:00:00+00:00",
            notes: null,
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
      },
      error: null,
    });

    mockApiPost.mockResolvedValue({
      success: true,
      data: {
        id: 1,
        correction_status: "rejected",
        rejection_reason: "Ma HS sai",
      },
      error: null,
    });

    render(<ExpertCorrectionsPage />);

    await waitFor(() => {
      expect(screen.getByText("copper towel rack")).toBeInTheDocument();
    });

    // Click reject to open the reason textarea
    const rejectButton = screen.getByText("Tu choi");
    fireEvent.click(rejectButton);

    // Type reason
    const textarea = screen.getByPlaceholderText(
      "Nhap ly do tu choi chinh sua nay..."
    );
    fireEvent.change(textarea, { target: { value: "Ma HS sai" } });

    // Submit rejection
    const confirmButton = screen.getByText("Xac nhan tu choi");
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockApiPost).toHaveBeenCalledWith(
        "/api/expert/corrections/1/reject",
        { reason: "Ma HS sai" }
      );
    });
  });
});
