/**
 * Tests for RegisterForm component.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { RegisterForm } from "./RegisterForm";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock next-auth/react
const mockSignIn = vi.fn();
vi.mock("next-auth/react", () => ({
  signIn: (...args: unknown[]) => mockSignIn(...args),
}));

// Mock API client
const mockPost = vi.fn();
vi.mock("@/lib/api", () => ({
  apiClient: {
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

describe("RegisterForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders email and password fields", () => {
    render(<RegisterForm />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create account/i })
    ).toBeInTheDocument();
  });

  it("shows validation error on blur for invalid email", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, "not-an-email");
    await user.tab();

    await waitFor(() => {
      expect(
        screen.getByText(/please enter a valid email address/i)
      ).toBeInTheDocument();
    });
  });

  it("shows validation error on blur for short password", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    const passwordInput = screen.getByLabelText(/password/i);
    await user.type(passwordInput, "short");
    await user.tab();

    await waitFor(() => {
      expect(
        screen.getByText(/password must be at least 8 characters/i)
      ).toBeInTheDocument();
    });
  });

  it("submits successfully and redirects to /search", async () => {
    const user = userEvent.setup();

    mockPost.mockResolvedValue({
      success: true,
      data: { id: 1, email: "new@example.com", role: "user" },
      error: null,
    });
    mockSignIn.mockResolvedValue({ error: null });

    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/email/i), "new@example.com");
    await user.type(screen.getByLabelText(/password/i), "securepass123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/auth/register", {
        email: "new@example.com",
        password: "securepass123",
      });
    });

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith("credentials", {
        email: "new@example.com",
        password: "securepass123",
        redirect: false,
      });
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/search");
    });
  });

  it("displays error for duplicate email with login link", async () => {
    const user = userEvent.setup();

    mockPost.mockResolvedValue({
      success: false,
      data: null,
      error: {
        type: "https://athena.example/errors/validation",
        title: "Email Already Registered",
        status: 409,
        detail: "An account with this email already exists.",
        instance: "/api/auth/register",
      },
    });

    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/email/i), "existing@example.com");
    await user.type(screen.getByLabelText(/password/i), "securepass123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/email already registered/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/log in instead/i)).toBeInTheDocument();
  });
});
