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
    password: z.string().min(8, "Password must be at least 8 characters"),
    passwordConfirm: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: "Passwords do not match",
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
          This reset link has expired or is invalid.
        </div>
        <p className="text-center text-sm text-muted-foreground">
          <Link
            href="/forgot-password"
            className="font-medium text-primary hover:underline"
          >
            Request a new reset link
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
            "This reset link has expired or is invalid. Please request a new one."
          );
        } else {
          setServerError(
            response.error?.detail || "An error occurred. Please try again."
          );
        }
        return;
      }

      router.push("/login?reset=success");
    } catch (error) {
      console.error("Reset password error:", error);
      setServerError("An unexpected error occurred. Please try again.");
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
          New Password
        </label>
        <div className="relative">
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            autoComplete="new-password"
            {...register("password")}
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Min. 8 characters"
            aria-describedby={errors.password ? "password-error" : undefined}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label={showPassword ? "Hide password" : "Show password"}
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
          Confirm Password
        </label>
        <div className="relative">
          <input
            id="passwordConfirm"
            type={showConfirm ? "text" : "password"}
            autoComplete="new-password"
            {...register("passwordConfirm")}
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Repeat your new password"
            aria-describedby={
              errors.passwordConfirm ? "passwordConfirm-error" : undefined
            }
          />
          <button
            type="button"
            onClick={() => setShowConfirm(!showConfirm)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label={showConfirm ? "Hide password" : "Show password"}
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
          {serverError.includes("expired or is invalid") && (
            <span>
              {" "}
              <Link
                href="/forgot-password"
                className="font-medium underline"
              >
                Request a new link
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
        {isSubmitting ? "Resetting..." : "Reset Password"}
      </button>
    </form>
  );
}
