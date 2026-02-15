/**
 * Reset password page (server component wrapper).
 * Renders at /reset-password?token=...
 */

import { ResetPasswordForm } from "./ResetPasswordForm";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Reset Password - Athena",
  description: "Set a new password for your Athena account",
};

export default function ResetPasswordPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground">
            Reset Password
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Enter your new password below
          </p>
        </div>
        <ResetPasswordForm />
      </div>
    </main>
  );
}
