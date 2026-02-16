/**
 * Forgot password page (server component wrapper).
 * Renders at /forgot-password.
 */

import { ForgotPasswordForm } from "./ForgotPasswordForm";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Quên mật khẩu - Athena",
  description: "Đặt lại mật khẩu tài khoản Athena",
};

export default function ForgotPasswordPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground">
            Quên mật khẩu
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Nhập email của bạn và chúng tôi sẽ gửi liên kết đặt lại
          </p>
        </div>
        <ForgotPasswordForm />
      </div>
    </main>
  );
}
