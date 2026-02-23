/**
 * Tests for LoginForm component.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { LoginForm } from "./LoginForm";

// Mock next/navigation
const mockPush = vi.fn();
const mockGet = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: mockGet }),
}));

// Mock next-auth/react
const mockSignIn = vi.fn();
vi.mock("next-auth/react", () => ({
  signIn: (...args: unknown[]) => mockSignIn(...args),
}));

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockReturnValue(null);
  });

  it("renders email and password fields", () => {
    render(<LoginForm />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Nhập mật khẩu của bạn")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Đăng nhập$/i })
    ).toBeInTheDocument();
  });

  it("shows validation error on blur for invalid email", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, "not-an-email");
    await user.tab();

    await waitFor(() => {
      expect(
        screen.getByText(/Vui lòng nhập địa chỉ email hợp lệ/i)
      ).toBeInTheDocument();
    });
  });

  it("shows validation error on blur for empty password", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    const passwordInput = screen.getByPlaceholderText("Nhập mật khẩu của bạn");
    await user.click(passwordInput);
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/Vui lòng nhập mật khẩu/i)).toBeInTheDocument();
    });
  });

  it("displays error on failed login", async () => {
    const user = userEvent.setup();

    mockSignIn.mockResolvedValue({ error: "CredentialsSignin" });

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByPlaceholderText("Nhập mật khẩu của bạn"), "wrongpassword");
    await user.click(screen.getByRole("button", { name: /Đăng nhập$/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/Email hoặc mật khẩu không đúng/i)
      ).toBeInTheDocument();
    });
  });

  it("successful login calls signIn and redirects to /search", async () => {
    const user = userEvent.setup();

    mockSignIn.mockResolvedValue({ error: null });

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByPlaceholderText("Nhập mật khẩu của bạn"), "mypassword123");
    await user.click(screen.getByRole("button", { name: /Đăng nhập$/i }));

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith("credentials", {
        email: "test@example.com",
        password: "mypassword123",
        redirect: false,
      });
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/search");
    });
  });

  it("uses callbackUrl from search params for redirect", async () => {
    const user = userEvent.setup();

    mockGet.mockImplementation((key: string) =>
      key === "callbackUrl" ? "/favorites" : null
    );
    mockSignIn.mockResolvedValue({ error: null });

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByPlaceholderText("Nhập mật khẩu của bạn"), "mypassword123");
    await user.click(screen.getByRole("button", { name: /Đăng nhập$/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/favorites");
    });
  });

  it("shows link to registration page", () => {
    render(<LoginForm />);

    const signUpLink = screen.getByText(/Đăng ký/i);
    expect(signUpLink).toBeInTheDocument();
    expect(signUpLink.closest("a")).toHaveAttribute("href", "/register");
  });

  it("displays error on unexpected exception", async () => {
    const user = userEvent.setup();

    mockSignIn.mockRejectedValue(new Error("Network failure"));

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByPlaceholderText("Nhập mật khẩu của bạn"), "mypassword123");
    await user.click(screen.getByRole("button", { name: /Đăng nhập$/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/Đã xảy ra lỗi không mong muốn/i)
      ).toBeInTheDocument();
    });
  });

  // Social login button tests (AC #1, #2, #4)
  it("renders Google login button with Vietnamese text", () => {
    render(<LoginForm />);

    expect(
      screen.getByRole("button", { name: /Đăng nhập với Google/i })
    ).toBeInTheDocument();
  });

  it("renders Facebook login button with Vietnamese text", () => {
    render(<LoginForm />);

    expect(
      screen.getByRole("button", { name: /Đăng nhập với Facebook/i })
    ).toBeInTheDocument();
  });

  it("renders divider between social buttons and email form", () => {
    render(<LoginForm />);

    expect(screen.getByText("— hoặc —")).toBeInTheDocument();
  });

  it("displays conflict error when URL has OAuthAccountNotLinked error", () => {
    mockGet.mockImplementation((key: string) =>
      key === "error" ? "OAuthAccountNotLinked" : null
    );

    render(<LoginForm />);

    expect(
      screen.getByText(/Tài khoản này đã đăng ký bằng email\/mật khẩu/i)
    ).toBeInTheDocument();
  });

  it("Google button calls signIn with google provider", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.click(
      screen.getByRole("button", { name: /Đăng nhập với Google/i })
    );

    expect(mockSignIn).toHaveBeenCalledWith("google", {
      callbackUrl: "/search",
    });
  });

  it("Facebook button calls signIn with facebook provider", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.click(
      screen.getByRole("button", { name: /Đăng nhập với Facebook/i })
    );

    expect(mockSignIn).toHaveBeenCalledWith("facebook", {
      callbackUrl: "/search",
    });
  });
});
