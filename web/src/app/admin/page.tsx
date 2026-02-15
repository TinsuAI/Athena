"use client";

import Link from "next/link";

export default function AdminDashboard() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">
        Admin Dashboard
      </h1>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          href="/admin/users"
          className="block rounded-lg border border-slate-200 bg-white p-6 hover:border-emerald-300 hover:shadow-sm transition-all"
        >
          <h2 className="text-lg font-semibold text-slate-900">
            User Management
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            View users, assign roles, and manage access
          </p>
        </Link>
      </div>
    </div>
  );
}
