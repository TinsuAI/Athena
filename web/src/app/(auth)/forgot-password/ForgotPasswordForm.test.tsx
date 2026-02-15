/**
 * Tests for ForgotPasswordForm component.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ForgotPasswordForm } from "./ForgotPasswordForm";

// Mock the API client
const mockPost = vi.fn();
vi.mock("@/lib/api", () => ({
  apiClient: {
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

describe("ForgotPasswordForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders email input and submit button", () => {
    render(<ForgotPasswordForm />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /send reset link/i })
    ).toBeInTheDocument();
  });

  it("shows validation error for invalid email on blur", async () => {
    const user = userEvent.setup();
    render(<ForgotPasswordForm />);

    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, "not-an-email");
    await user.tab();

    await waitFor(() => {
      expect(
        screen.getByText(/please enter a valid email address/i)
      ).toBeInTheDocument();
    });
  });

  it("submits request and shows success message", async () => {
    const user = userEvent.setup();
    mockPost.mockResolvedValue({
      success: true,
      data: { message: "If this email exists, a reset link has been sent" },
      error: null,
    });

    render(<ForgotPasswordForm />);

    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/if this email exists, a reset link has been sent/i)
      ).toBeInTheDocument();
    });

    expect(mockPost).toHaveBeenCalledWith("/api/auth/forgot-password", {
      email: "user@example.com",
    });
  });

  it("handles API error gracefully", async () => {
    const user = userEvent.setup();
    mockPost.mockResolvedValue({
      success: false,
      data: null,
      error: {
        status: 429,
        detail: "Too many password reset requests. Please try again later.",
      },
    });

    render(<ForgotPasswordForm />);

    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/too many password reset requests/i)
      ).toBeInTheDocument();
    });
  });

  it("handles unexpected error gracefully", async () => {
    const user = userEvent.setup();
    mockPost.mockRejectedValue(new Error("Network failure"));

    render(<ForgotPasswordForm />);

    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/an unexpected error occurred/i)
      ).toBeInTheDocument();
    });
  });

  it("shows link to login page", () => {
    render(<ForgotPasswordForm />);

    const loginLink = screen.getByText(/log in/i);
    expect(loginLink).toBeInTheDocument();
    expect(loginLink.closest("a")).toHaveAttribute("href", "/login");
  });

  it("shows back to login link in success state", async () => {
    const user = userEvent.setup();
    mockPost.mockResolvedValue({
      success: true,
      data: { message: "If this email exists, a reset link has been sent" },
      error: null,
    });

    render(<ForgotPasswordForm />);

    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      const backLink = screen.getByText(/back to login/i);
      expect(backLink).toBeInTheDocument();
      expect(backLink.closest("a")).toHaveAttribute("href", "/login");
    });
  });
});
