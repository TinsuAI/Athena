"use client";

/**
 * Reset password form component.
 * Uses React Hook Form + Zod, validates on blur, reads token from URL.
 */

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { apiClient } from "@/lib/api";

const resetPasswordSchema = z
  .object({
    password: z.string().min(8, "Mật khẩu phải có ít nhất 8 ký tự"),
    passwordConfirm: z.string().min(1, "Vui lòng xác nhận mật khẩu"),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: "Mật khẩu không khớp",
    path: ["passwordConfirm"],
  });

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    mode: "onBlur",
  });

  // If no token in URL, show error immediately
  if (!token) {
    return (
      <div className="space-y-4 rounded-lg border border-border bg-card p-6 shadow-sm">
        <div
          className="rounded-md border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
          role="alert"
        >
          Liên kết đặt lại này đã hết hạn hoặc không hợp lệ.
        </div>
        <p className="text-center text-sm text-muted-foreground">
          <Link
            href="/forgot-password"
            className="font-medium text-primary hover:underline"
          >
            Yêu cầu liên kết đặt lại mới
          </Link>
        </p>
      </div>
    );
  }

  const onSubmit = async (data: ResetPasswordFormData) => {
    setServerError(null);
    setIsSubmitting(true);

    try {
      const response = await apiClient.post<{ message: string }>(
        "/api/auth/reset-password",
        {
          token,
          password: data.password,
          password_confirm: data.passwordConfirm,
        }
      );

      if (!response.success) {
        // Check error type instead of fragile string matching
        if (response.error?.type === "https://athena.example/errors/invalid-token") {
          setServerError(
            "Liên kết đặt lại này đã hết hạn hoặc không hợp lệ. Vui lòng yêu cầu liên kết mới."
          );
        } else {
          setServerError(
            response.error?.detail || "Đã xảy ra lỗi. Vui lòng thử lại."
          );
        }
        return;
      }

      router.push("/login?reset=success");
    } catch (error) {
      console.error("Reset password error:", error);
      setServerError("Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-4 rounded-lg border border-border bg-card p-6 shadow-sm"
      noValidate
    >
      <div>
        <label
          htmlFor="password"
          className="block text-sm font-medium text-foreground"
        >
          Mật khẩu mới
        </label>
        <div className="relative">
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            autoComplete="new-password"
            {...register("password")}
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Tối thiểu 8 ký tự"
            aria-describedby={errors.password ? "password-error" : undefined}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
        </div>
        {errors.password && (
          <p
            id="password-error"
            className="mt-1 text-sm text-destructive"
            role="alert"
          >
            {errors.password.message}
          </p>
        )}
      </div>

      <div>
        <label
          htmlFor="passwordConfirm"
          className="block text-sm font-medium text-foreground"
        >
          Xác nhận mật khẩu
        </label>
        <div className="relative">
          <input
            id="passwordConfirm"
            type={showConfirm ? "text" : "password"}
            autoComplete="new-password"
            {...register("passwordConfirm")}
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Nhập lại mật khẩu mới"
            aria-describedby={
              errors.passwordConfirm ? "passwordConfirm-error" : undefined
            }
          />
          <button
            type="button"
            onClick={() => setShowConfirm(!showConfirm)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label={showConfirm ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
          >
            {showConfirm ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
        </div>
        {errors.passwordConfirm && (
          <p
            id="passwordConfirm-error"
            className="mt-1 text-sm text-destructive"
            role="alert"
          >
            {errors.passwordConfirm.message}
          </p>
        )}
      </div>

      {serverError && (
        <div
          className="rounded-md border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
          role="alert"
        >
          {serverError}
          {serverError.includes("hết hạn hoặc không hợp lệ") && (
            <span>
              {" "}
              <Link
                href="/forgot-password"
                className="font-medium underline"
              >
                Yêu cầu liên kết mới
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
        {isSubmitting ? "Đang đặt lại..." : "Đặt lại mật khẩu"}
      </button>
    </form>
  );
}
