/**
 * Login page (server component wrapper).
 * Renders at /login.
 * Shows success message when redirected from password reset (?reset=success).
 */

import { LoginForm } from "./LoginForm";
import { ResetSuccessMessage } from "./ResetSuccessMessage";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Đăng nhập - Athena",
  description: "Đăng nhập để truy cập mục yêu thích và lịch sử tìm kiếm",
};

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground">Chào mừng trở lại</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Đăng nhập để truy cập mục yêu thích và lịch sử tìm kiếm
          </p>
        </div>
        <ResetSuccessMessage />
        <LoginForm />
      </div>
    </main>
  );
}
