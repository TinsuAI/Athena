import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CorrectionPanel } from "./CorrectionPanel";

// Mock next-auth/react useSession
const mockUseSession = vi.fn();
vi.mock("next-auth/react", () => ({
  useSession: () => mockUseSession(),
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) => (
    <a href={href} className={className}>{children}</a>
  ),
}));

// Mock apiClient
vi.mock("@/lib/api", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const defaultProps = {
  isOpen: true,
  onClose: vi.fn(),
  lookupId: 1,
  currentHsCode: "74182000",
  currentDescription: "Thanh treo khăn bằng đồng",
};

describe("CorrectionPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders nothing when isOpen is false", () => {
    mockUseSession.mockReturnValue({
      data: { user: { id: 1, email: "user@example.com" } },
      status: "authenticated",
    });

    const { container } = render(<CorrectionPanel {...defaultProps} isOpen={false} />);
    expect(container.firstChild).toBeNull();
  });

  it("shows login prompt when not authenticated (AC #1)", () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: "unauthenticated",
    });

    render(<CorrectionPanel {...defaultProps} />);

    // AC #1: shows "Dang nhap de gui chinh sua"
    expect(screen.getByText("Dang nhap de gui chinh sua")).toBeInTheDocument();

    // AC #1: shows login link
    const loginLink = screen.getByRole("link", { name: "Dang nhap" });
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute("href", "/login");
  });

  it("does NOT show correction form when unauthenticated (AC #1)", () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: "unauthenticated",
    });

    render(<CorrectionPanel {...defaultProps} />);

    // Form elements should not be visible
    expect(screen.queryByText("Ma HS dung")).not.toBeInTheDocument();
    expect(screen.queryByText("Gui de xuat sua doi")).not.toBeInTheDocument();
  });

  it("shows loading spinner while auth status is loading", () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: "loading",
    });

    render(<CorrectionPanel {...defaultProps} />);

    // Should not show the login prompt or form during loading
    expect(screen.queryByText("Dang nhap de gui chinh sua")).not.toBeInTheDocument();
    expect(screen.queryByText("Gui de xuat sua doi")).not.toBeInTheDocument();
  });

  it("shows correction form when authenticated", () => {
    mockUseSession.mockReturnValue({
      data: { user: { id: 7, email: "user@example.com", role: "user" } },
      status: "authenticated",
    });

    render(<CorrectionPanel {...defaultProps} />);

    // Should show the form, not the login prompt
    expect(screen.queryByText("Dang nhap de gui chinh sua")).not.toBeInTheDocument();
    expect(screen.getByText("Ma HS dung")).toBeInTheDocument();
    expect(screen.getByText("Gui de xuat sua doi")).toBeInTheDocument();
  });

  it("shows the current HS code as read-only reference when authenticated", () => {
    mockUseSession.mockReturnValue({
      data: { user: { id: 7, email: "user@example.com", role: "user" } },
      status: "authenticated",
    });

    render(<CorrectionPanel {...defaultProps} />);

    expect(screen.getByText("74182000")).toBeInTheDocument();
    expect(screen.getByText("Thanh treo khăn bằng đồng")).toBeInTheDocument();
  });

  it("shows pending success message on successful submit (AC #2)", async () => {
    const { apiClient } = await import("@/lib/api");

    mockUseSession.mockReturnValue({
      data: { user: { id: 7, email: "user@example.com", role: "user" } },
      status: "authenticated",
    });

    // Mock a successful API response
    vi.mocked(apiClient.post).mockResolvedValue({
      success: true,
      data: {
        id: 1,
        correction_status: "pending",
        is_verified: false,
        submitted_by_user_id: 7,
      },
      error: null,
    });

    // Mock autocomplete to return a result
    vi.mocked(apiClient.get).mockResolvedValue({
      success: true,
      data: [
        { id: 55, code: "74199900", description_vn: "Đồ đồng khác", description_en: "Other copper articles" },
      ],
      error: null,
    });

    render(<CorrectionPanel {...defaultProps} />);

    // Type in search box to trigger autocomplete
    const searchInput = screen.getByPlaceholderText("Tim theo ma hoac mo ta...");
    fireEvent.change(searchInput, { target: { value: "74199900" } });

    // Wait for and click the autocomplete suggestion
    await waitFor(() => {
      expect(screen.getByText("74199900")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("74199900"));

    // Click submit button
    fireEvent.click(screen.getByText("Gui de xuat sua doi"));

    // Confirm dialog should appear
    await waitFor(() => {
      expect(screen.getByText("Xac nhan sua doi")).toBeInTheDocument();
    });

    // Click confirm
    fireEvent.click(screen.getByText("Xac nhan"));

    // AC #2: Should show "Chinh sua da duoc gui, dang cho duyet"
    await waitFor(() => {
      expect(
        screen.getByText("Chinh sua da duoc gui, dang cho duyet")
      ).toBeInTheDocument();
    });
  });

  it("shows error when already-pending 409 response received (AC #6)", async () => {
    const { apiClient } = await import("@/lib/api");

    mockUseSession.mockReturnValue({
      data: { user: { id: 7, email: "user@example.com", role: "user" } },
      status: "authenticated",
    });

    vi.mocked(apiClient.post).mockResolvedValue({
      success: false,
      data: null,
      error: {
        status: 409,
        detail: "Chinh sua dang cho duyet",
        title: "Correction Already Pending",
      },
    });

    vi.mocked(apiClient.get).mockResolvedValue({
      success: true,
      data: [
        { id: 55, code: "74199900", description_vn: "Đồ đồng khác", description_en: "Other copper articles" },
      ],
      error: null,
    });

    render(<CorrectionPanel {...defaultProps} />);

    const searchInput = screen.getByPlaceholderText("Tim theo ma hoac mo ta...");
    fireEvent.change(searchInput, { target: { value: "74199900" } });

    await waitFor(() => {
      expect(screen.getByText("74199900")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("74199900"));

    fireEvent.click(screen.getByText("Gui de xuat sua doi"));

    await waitFor(() => {
      expect(screen.getByText("Xac nhan sua doi")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Xac nhan"));

    await waitFor(() => {
      expect(screen.getByText("Chinh sua dang cho duyet")).toBeInTheDocument();
    });
  });

  it("shows error when already-corrected 409 response received (AC #4)", async () => {
    const { apiClient } = await import("@/lib/api");

    mockUseSession.mockReturnValue({
      data: { user: { id: 7, email: "user@example.com", role: "user" } },
      status: "authenticated",
    });

    vi.mocked(apiClient.post).mockResolvedValue({
      success: false,
      data: null,
      error: {
        status: 409,
        detail: "Tra cuu nay da duoc chinh sua",
        title: "Already Corrected",
      },
    });

    vi.mocked(apiClient.get).mockResolvedValue({
      success: true,
      data: [
        { id: 55, code: "74199900", description_vn: "Đồ đồng khác", description_en: "Other copper articles" },
      ],
      error: null,
    });

    render(<CorrectionPanel {...defaultProps} />);

    const searchInput = screen.getByPlaceholderText("Tim theo ma hoac mo ta...");
    fireEvent.change(searchInput, { target: { value: "74199900" } });

    await waitFor(() => {
      expect(screen.getByText("74199900")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("74199900"));

    fireEvent.click(screen.getByText("Gui de xuat sua doi"));

    await waitFor(() => {
      expect(screen.getByText("Xac nhan sua doi")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Xac nhan"));

    await waitFor(() => {
      expect(screen.getByText("Tra cuu nay da duoc chinh sua")).toBeInTheDocument();
    });
  });

  it("validates that a HS code must be selected before submit", () => {
    mockUseSession.mockReturnValue({
      data: { user: { id: 7, email: "user@example.com", role: "user" } },
      status: "authenticated",
    });

    render(<CorrectionPanel {...defaultProps} />);

    // Click submit without selecting a HS code
    fireEvent.click(screen.getByText("Gui de xuat sua doi"));

    expect(screen.getByText("Vui long chon ma HS dung")).toBeInTheDocument();
  });

  it("closes panel when backdrop is clicked", () => {
    mockUseSession.mockReturnValue({
      data: { user: { id: 7, email: "user@example.com", role: "user" } },
      status: "authenticated",
    });

    const onClose = vi.fn();
    render(<CorrectionPanel {...defaultProps} onClose={onClose} />);

    // Click the backdrop (first div with bg-black/20)
    const backdrop = document.querySelector(".fixed.inset-0.bg-black\\/20");
    if (backdrop) {
      fireEvent.click(backdrop);
      expect(onClose).toHaveBeenCalledOnce();
    }
  });
});
