/**
 * Reset password page (server component wrapper).
 * Renders at /reset-password?token=...
 */

import { ResetPasswordForm } from "./ResetPasswordForm";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Đặt lại mật khẩu - Athena",
  description: "Đặt mật khẩu mới cho tài khoản Athena",
};

export default function ResetPasswordPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground">
            Đặt lại mật khẩu
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Nhập mật khẩu mới của bạn bên dưới
          </p>
        </div>
        <ResetPasswordForm />
      </div>
    </main>
  );
}
