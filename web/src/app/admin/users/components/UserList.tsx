"use client";

import { useCallback, useEffect, useState } from "react";
import { apiClient } from "@/lib/api";

interface UserItem {
  id: number;
  email: string;
  role: string;
  created_at: string;
}

interface UserListData {
  items: UserItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export function UserList() {
  const [data, setData] = useState<UserListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const perPage = 20;

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<UserListData>(
        `/api/admin/users?page=${page}&per_page=${perPage}`
      );
      if (response.success && response.data) {
        setData(response.data);
      } else {
        // Redirect to login on session expiry
        if (response.error?.status === 401) {
          window.location.href = "/login";
          return;
        }
        setError(response.error?.detail || "Failed to fetch users");
      }
    } catch {
      setError("Failed to fetch users");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleRoleChange = async (userId: number, newRole: string) => {
    const confirmed = window.confirm(
      `Are you sure you want to change this user's role to "${newRole}"?`
    );
    if (!confirmed) return;

    setUpdatingId(userId);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await apiClient.patch<UserItem>(
        `/api/admin/users/${userId}/role`,
        { role: newRole }
      );

      if (response.success) {
        setSuccessMessage("Role updated successfully");
        setTimeout(() => setSuccessMessage(null), 3000);
        await fetchUsers();
      } else {
        // Redirect to login on session expiry
        if (response.error?.status === 401) {
          window.location.href = "/login";
          return;
        }
        setError(response.error?.detail || "Failed to update role");
      }
    } catch {
      setError("Failed to update role");
    } finally {
      setUpdatingId(null);
    }
  };

  if (loading && !data) {
    return <div className="text-slate-400 text-sm py-8">Loading users...</div>;
  }

  if (error && !data) {
    return <div className="text-red-600 text-sm py-8">{error}</div>;
  }

  if (!data) return null;

  return (
    <div>
      {successMessage && (
        <div className="mb-4 rounded-md bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-800">
          {successMessage}
        </div>
      )}
      {error && (
        <div className="mb-4 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm" aria-label="Users list">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                Email
              </th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                Role
              </th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                Created
              </th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((user) => (
              <tr key={user.id} className="border-b border-slate-50 last:border-0">
                <td className="px-4 py-3 text-slate-900">{user.email}</td>
                <td className="px-4 py-3">
                  <select
                    value={user.role}
                    onChange={(e) => handleRoleChange(user.id, e.target.value)}
                    disabled={updatingId === user.id}
                    className="rounded border border-slate-200 bg-white px-2 py-1 text-sm text-slate-700 disabled:opacity-50"
                    aria-label={`Role for ${user.email}`}
                  >
                    <option value="user">user</option>
                    <option value="admin">admin</option>
                  </select>
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.pages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm">
          <span className="text-slate-500">
            Page {data.page} of {data.pages} ({data.total} users)
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded border border-slate-200 px-3 py-1.5 text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
              disabled={page >= data.pages}
              className="rounded border border-slate-200 px-3 py-1.5 text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
