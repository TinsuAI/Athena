"use client";

import Link from "next/link";

export default function AdminDashboard() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">
        Bảng điều khiển quản trị
      </h1>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          href="/admin/users"
          className="block rounded-lg border border-slate-200 bg-white p-6 hover:border-emerald-300 hover:shadow-sm transition-all"
        >
          <h2 className="text-lg font-semibold text-slate-900">
            Quản lý người dùng
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Xem người dùng, phân quyền và quản lý truy cập
          </p>
        </Link>
        <Link
          href="/admin/permissions"
          className="block rounded-lg border border-slate-200 bg-white p-6 hover:border-emerald-300 hover:shadow-sm transition-all"
        >
          <h2 className="text-lg font-semibold text-slate-900">
            Quản lý quyền hạn
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Cấu hình quyền truy cập theo vai trò và người dùng
          </p>
        </Link>
      </div>
    </div>
  );
}
