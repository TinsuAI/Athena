/**
 * Registration page (server component wrapper).
 * Renders at /register.
 */

import { RegisterForm } from "./RegisterForm";

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground">Tạo tài khoản</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Đăng ký để truy cập các tính năng cá nhân hóa
          </p>
        </div>
        <RegisterForm />
      </div>
    </main>
  );
}
