/**
 * Tests for ResetPasswordForm component.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ResetPasswordForm } from "./ResetPasswordForm";

// Mock next/navigation
const mockPush = vi.fn();
const mockGet = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: mockGet }),
}));

// Mock the API client
const mockPost = vi.fn();
vi.mock("@/lib/api", () => ({
  apiClient: {
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

describe("ResetPasswordForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockReturnValue("valid-token-123");
  });

  it("renders password and confirm password inputs", () => {
    render(<ResetPasswordForm />);

    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /reset password/i })
    ).toBeInTheDocument();
  });

  it("shows validation error for short password on blur", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordForm />);

    const passwordInput = screen.getByLabelText(/new password/i);
    await user.type(passwordInput, "short");
    await user.tab();

    await waitFor(() => {
      expect(
        screen.getByText(/password must be at least 8 characters/i)
      ).toBeInTheDocument();
    });
  });

  it("shows 'Passwords do not match' for mismatched passwords", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordForm />);

    await user.type(screen.getByLabelText(/new password/i), "password123");
    await user.type(
      screen.getByLabelText(/confirm password/i),
      "differentpassword"
    );
    await user.click(
      screen.getByRole("button", { name: /reset password/i })
    );

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
  });

  it("submits with valid token and redirects to /login", async () => {
    const user = userEvent.setup();
    mockPost.mockResolvedValue({
      success: true,
      data: { message: "Password has been reset successfully" },
      error: null,
    });

    render(<ResetPasswordForm />);

    await user.type(screen.getByLabelText(/new password/i), "newpassword123");
    await user.type(
      screen.getByLabelText(/confirm password/i),
      "newpassword123"
    );
    await user.click(
      screen.getByRole("button", { name: /reset password/i })
    );

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/auth/reset-password", {
        token: "valid-token-123",
        password: "newpassword123",
        password_confirm: "newpassword123",
      });
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/login?reset=success");
    });
  });

  it("shows error for expired/invalid token", async () => {
    const user = userEvent.setup();
    mockPost.mockResolvedValue({
      success: false,
      data: null,
      error: {
        status: 400,
        detail:
          "This reset link has expired or is invalid. Please request a new one.",
      },
    });

    render(<ResetPasswordForm />);

    await user.type(screen.getByLabelText(/new password/i), "newpassword123");
    await user.type(
      screen.getByLabelText(/confirm password/i),
      "newpassword123"
    );
    await user.click(
      screen.getByRole("button", { name: /reset password/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/this reset link has expired or is invalid/i)
      ).toBeInTheDocument();
    });
  });

  it("shows link to request new reset when token is invalid", async () => {
    const user = userEvent.setup();
    mockPost.mockResolvedValue({
      success: false,
      data: null,
      error: {
        status: 400,
        detail:
          "This reset link has expired or is invalid. Please request a new one.",
      },
    });

    render(<ResetPasswordForm />);

    await user.type(screen.getByLabelText(/new password/i), "newpassword123");
    await user.type(
      screen.getByLabelText(/confirm password/i),
      "newpassword123"
    );
    await user.click(
      screen.getByRole("button", { name: /reset password/i })
    );

    await waitFor(() => {
      const requestLink = screen.getByText(/request a new link/i);
      expect(requestLink).toBeInTheDocument();
      expect(requestLink.closest("a")).toHaveAttribute(
        "href",
        "/forgot-password"
      );
    });
  });

  it("shows error when no token in URL", () => {
    mockGet.mockReturnValue(null);

    render(<ResetPasswordForm />);

    expect(
      screen.getByText(/this reset link has expired or is invalid/i)
    ).toBeInTheDocument();
    const requestLink = screen.getByText(/request a new reset link/i);
    expect(requestLink.closest("a")).toHaveAttribute(
      "href",
      "/forgot-password"
    );
  });

  it("handles unexpected error gracefully", async () => {
    const user = userEvent.setup();
    mockPost.mockRejectedValue(new Error("Network failure"));

    render(<ResetPasswordForm />);

    await user.type(screen.getByLabelText(/new password/i), "newpassword123");
    await user.type(
      screen.getByLabelText(/confirm password/i),
      "newpassword123"
    );
    await user.click(
      screen.getByRole("button", { name: /reset password/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/an unexpected error occurred/i)
      ).toBeInTheDocument();
    });
  });
});
