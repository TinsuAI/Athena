"use client";

/**
 * Registration form component with social OAuth buttons.
 * Uses React Hook Form + Zod, validates on blur, calls FastAPI directly.
 */

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api";

const registerSchema = z.object({
  email: z
    .string()
    .email("Vui lòng nhập địa chỉ email hợp lệ")
    .transform((val) => val.toLowerCase().trim()),
  password: z.string().min(8, "Mật khẩu phải có ít nhất 8 ký tự"),
});

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: RegisterFormData) => {
    setServerError(null);
    setIsSubmitting(true);

    try {
      // Step 1: Register via FastAPI
      const response = await apiClient.post<{
        id: number;
        email: string;
        role: string;
      }>("/api/auth/register", data);

      if (!response.success) {
        if (response.error?.status === 409) {
          setServerError("Email đã được đăng ký");
          return;
        }
        setServerError(response.error?.detail || "Đăng ký thất bại");
        return;
      }

      // Step 2: Sign in via NextAuth to create session
      const signInResult = await signIn("credentials", {
        email: data.email,
        password: data.password,
        redirect: false,
      });

      if (signInResult?.error) {
        setServerError("Tài khoản đã được tạo nhưng đăng nhập thất bại. Vui lòng đăng nhập.");
        return;
      }

      // Step 3: Redirect to search page
      router.push("/search");
    } catch (error) {
      console.error("Registration error:", error);
      setServerError("Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4 rounded-lg border border-border bg-card p-6 shadow-sm">
      {/* Social login buttons */}
      <div className="space-y-2.5">
        <button
          type="button"
          onClick={() => signIn("google", { callbackUrl: "/search" })}
          className="flex w-full items-center justify-center gap-3 rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
        >
          <svg
            className="h-[18px] w-[18px]"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
              fill="#4285F4"
            />
            <path
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              fill="#34A853"
            />
            <path
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              fill="#FBBC05"
            />
            <path
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              fill="#EA4335"
            />
          </svg>
          Đăng nhập với Google
        </button>

        <button
          type="button"
          onClick={() => signIn("facebook", { callbackUrl: "/search" })}
          className="flex w-full items-center justify-center gap-3 rounded-md bg-[#1877F2] px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-[#166FE5] focus:outline-none focus:ring-2 focus:ring-[#1877F2] focus:ring-offset-2"
        >
          <svg
            className="h-[18px] w-[18px]"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
          </svg>
          Đăng nhập với Facebook
        </button>
      </div>

      {/* Divider */}
      <div className="relative flex items-center py-1">
        <div className="flex-1 border-t border-slate-200" />
        <span className="px-4 text-xs font-medium text-slate-400">— hoặc —</span>
        <div className="flex-1 border-t border-slate-200" />
      </div>

      {/* Email/password form */}
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-4"
        noValidate
      >
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-foreground"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            {...register("email")}
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="you@example.com"
          />
          {errors.email && (
            <p className="mt-1 text-sm text-destructive" role="alert">
              {errors.email.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-foreground"
          >
            Mật khẩu
          </label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            {...register("password")}
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Tối thiểu 8 ký tự"
          />
          {errors.password && (
            <p className="mt-1 text-sm text-destructive" role="alert">
              {errors.password.message}
            </p>
          )}
        </div>

        {serverError && (
          <div
            className="rounded-md border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
            role="alert"
          >
            {serverError}
            {serverError === "Email đã được đăng ký" && (
              <span>
                {" "}
                <Link href="/login" className="font-medium underline">
                  Đăng nhập
                </Link>
              </span>
            )}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50"
        >
          {isSubmitting ? "Đang tạo tài khoản..." : "Tạo tài khoản"}
        </button>

        <p className="text-center text-sm text-muted-foreground">
          Đã có tài khoản?{" "}
          <Link
            href="/login"
            className="font-medium text-primary hover:underline"
          >
            Đăng nhập
          </Link>
        </p>
      </form>
    </div>
  );
}
