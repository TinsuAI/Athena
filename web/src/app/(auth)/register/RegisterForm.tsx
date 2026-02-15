"use client";

/**
 * Registration form component.
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
    .email("Please enter a valid email address")
    .transform((val) => val.toLowerCase().trim()),
  password: z.string().min(8, "Password must be at least 8 characters"),
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
          setServerError("Email already registered");
          return;
        }
        setServerError(response.error?.detail || "Registration failed");
        return;
      }

      // Step 2: Sign in via NextAuth to create session
      const signInResult = await signIn("credentials", {
        email: data.email,
        password: data.password,
        redirect: false,
      });

      if (signInResult?.error) {
        setServerError("Account created but sign-in failed. Please log in.");
        return;
      }

      // Step 3: Redirect to search page
      router.push("/search");
    } catch (error) {
      console.error("Registration error:", error);
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
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="new-password"
          {...register("password")}
          className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          placeholder="Min. 8 characters"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-destructive" role="alert">
            {errors.password.message}
          </p>
        )}
      </div>

      {serverError && (
        <div className="rounded-md border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive" role="alert">
          {serverError}
          {serverError === "Email already registered" && (
            <span>
              {" "}
              <Link href="/login" className="font-medium underline">
                Log in instead
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
        {isSubmitting ? "Creating account..." : "Create Account"}
      </button>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-primary hover:underline">
          Log in
        </Link>
      </p>
    </form>
  );
}
