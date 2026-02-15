"use client";

/**
 * Shows a success message when redirected from password reset.
 * Reads ?reset=success from search params.
 */

import { useSearchParams } from "next/navigation";

export function ResetSuccessMessage() {
  const searchParams = useSearchParams();
  const resetSuccess = searchParams.get("reset") === "success";

  if (!resetSuccess) {
    return null;
  }

  return (
    <div
      className="rounded-md border border-primary/20 bg-primary/10 p-3 text-sm text-foreground"
      role="status"
    >
      Your password has been reset successfully. Please log in with your new
      password.
    </div>
  );
}
