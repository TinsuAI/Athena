"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSession } from "next-auth/react";
import { apiClient } from "@/lib/api";

interface UserItem {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface UserListData {
  items: UserItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

const roleLabels: Record<string, string> = {
  user: "Nguoi dung",
  expert: "Chuyen gia",
  admin: "Quan tri vien",
};

export function UserList() {
  const { data: session } = useSession();
  const currentUserId = session?.user
    ? Number((session.user as { id?: string }).id)
    : null;

  const [data, setData] = useState<UserListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Create user modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createEmail, setCreateEmail] = useState("");
  const [createPassword, setCreatePassword] = useState("");
  const [createRole, setCreateRole] = useState("user");
  const [creating, setCreating] = useState(false);

  // Edit user modal state
  const [editUser, setEditUser] = useState<UserItem | null>(null);
  const [editEmail, setEditEmail] = useState("");
  const [editRole, setEditRole] = useState("");
  const [editing, setEditing] = useState(false);

  const perPage = 20;
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchUsers = useCallback(async (pageNum: number = page, searchQuery: string = search) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: String(pageNum),
        per_page: String(perPage),
      });
      if (searchQuery) {
        params.set("search", searchQuery);
      }
      const response = await apiClient.get<UserListData>(
        `/api/admin/users?${params.toString()}`
      );
      if (response.success && response.data) {
        setData(response.data);
      } else {
        if (response.error?.status === 401) {
          window.location.href = "/login";
          return;
        }
        setError(
          response.error?.detail || "Khong the tai danh sach nguoi dung"
        );
      }
    } catch {
      setError("Khong the tai danh sach nguoi dung");
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, search]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }
    searchTimerRef.current = setTimeout(() => {
      setPage(1);
      fetchUsers(1, value);
    }, 300);
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    const confirmed = window.confirm(
      `Ban co chac muon thay doi vai tro cua nguoi dung nay thanh "${roleLabels[newRole] || newRole}"?`
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
        setSuccessMessage("Cap nhat vai tro thanh cong");
        setTimeout(() => setSuccessMessage(null), 3000);
        await fetchUsers();
      } else {
        if (response.error?.status === 401) {
          window.location.href = "/login";
          return;
        }
        setError(response.error?.detail || "Cap nhat vai tro that bai");
      }
    } catch {
      setError("Cap nhat vai tro that bai");
    } finally {
      setUpdatingId(null);
    }
  };

  const handleCreateUser = async () => {
    setCreating(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await apiClient.post<UserItem>("/api/admin/users", {
        email: createEmail,
        password: createPassword,
        role: createRole,
      });

      if (response.success) {
        setSuccessMessage("Tao nguoi dung thanh cong");
        setTimeout(() => setSuccessMessage(null), 3000);
        setShowCreateModal(false);
        setCreateEmail("");
        setCreatePassword("");
        setCreateRole("user");
        await fetchUsers();
      } else {
        if (response.error?.status === 401) {
          window.location.href = "/login";
          return;
        }
        setError(response.error?.detail || "Tao nguoi dung that bai");
      }
    } catch {
      setError("Tao nguoi dung that bai");
    } finally {
      setCreating(false);
    }
  };

  const handleEditUser = async () => {
    if (!editUser) return;
    setEditing(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const body: { email?: string; role?: string } = {};
      if (editEmail !== editUser.email) body.email = editEmail;
      if (editRole !== editUser.role) body.role = editRole;

      const response = await apiClient.patch<UserItem>(
        `/api/admin/users/${editUser.id}`,
        body
      );

      if (response.success) {
        setSuccessMessage("Cap nhat nguoi dung thanh cong");
        setTimeout(() => setSuccessMessage(null), 3000);
        setEditUser(null);
        await fetchUsers();
      } else {
        if (response.error?.status === 401) {
          window.location.href = "/login";
          return;
        }
        setError(response.error?.detail || "Cap nhat nguoi dung that bai");
      }
    } catch {
      setError("Cap nhat nguoi dung that bai");
    } finally {
      setEditing(false);
    }
  };

  const handleToggleStatus = async (user: UserItem) => {
    if (user.is_active) {
      const confirmed = window.confirm(
        `Ban co chac muon vo hieu hoa tai khoan "${user.email}"?`
      );
      if (!confirmed) return;
    }

    setUpdatingId(user.id);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await apiClient.patch<UserItem>(
        `/api/admin/users/${user.id}/status`,
        { is_active: !user.is_active }
      );

      if (response.success) {
        setSuccessMessage(
          user.is_active
            ? "Vo hieu hoa tai khoan thanh cong"
            : "Kich hoat lai tai khoan thanh cong"
        );
        setTimeout(() => setSuccessMessage(null), 3000);
        await fetchUsers();
      } else {
        if (response.error?.status === 401) {
          window.location.href = "/login";
          return;
        }
        setError(response.error?.detail || "Thao tac that bai");
      }
    } catch {
      setError("Thao tac that bai");
    } finally {
      setUpdatingId(null);
    }
  };

  const openEditModal = (user: UserItem) => {
    setEditUser(user);
    setEditEmail(user.email);
    setEditRole(user.role);
  };

  if (loading && !data) {
    return (
      <div className="text-slate-400 text-sm py-8">
        Dang tai danh sach...
      </div>
    );
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

      {/* Toolbar: Search + Create */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="search"
            placeholder="Tim kiem theo email..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full rounded-md border border-slate-200 bg-white pl-10 pr-4 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 transition-colors whitespace-nowrap"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Tao nguoi dung
        </button>
      </div>

      {/* User table */}
      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm" aria-label="Users list">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                Email
              </th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                Vai tro
              </th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                Trang thai
              </th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                Ngay tao
              </th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">
                Thao tac
              </th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((user) => {
              const isSelf = currentUserId === user.id;
              return (
                <tr
                  key={user.id}
                  className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition-colors"
                >
                  <td className="px-4 py-3 text-slate-900 font-medium">
                    {user.email}
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={user.role}
                      onChange={(e) =>
                        handleRoleChange(user.id, e.target.value)
                      }
                      disabled={updatingId === user.id}
                      className="rounded border border-slate-200 bg-white px-2 py-1 text-sm text-slate-700 disabled:opacity-50"
                      aria-label={`Role for ${user.email}`}
                    >
                      <option value="user">Nguoi dung</option>
                      <option value="expert">Chuyen gia</option>
                      <option value="admin">Quan tri vien</option>
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    {user.is_active ? (
                      <span className="inline-flex items-center gap-1.5 text-sm text-emerald-700">
                        <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
                        Hoat dong
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-sm text-red-600">
                        <span className="inline-block h-2 w-2 rounded-full bg-red-500" />
                        Vo hieu hoa
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => openEditModal(user)}
                        className="rounded border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-colors"
                        title="Chinh sua"
                      >
                        Sua
                      </button>
                      {user.is_active ? (
                        <button
                          onClick={() => handleToggleStatus(user)}
                          disabled={
                            isSelf || updatingId === user.id
                          }
                          title={
                            isSelf
                              ? "Khong the vo hieu hoa tai khoan cua chinh minh"
                              : "Vo hieu hoa"
                          }
                          className="rounded border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-100 hover:border-red-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          Vo hieu hoa
                        </button>
                      ) : (
                        <button
                          onClick={() => handleToggleStatus(user)}
                          disabled={updatingId === user.id}
                          title="Kich hoat lai"
                          className="rounded border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100 hover:border-emerald-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          Kich hoat lai
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data.pages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm">
          <span className="text-slate-500">
            Trang {data.page} / {data.pages} ({data.total} nguoi dung)
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded border border-slate-200 px-3 py-1.5 text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Truoc
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
              disabled={page >= data.pages}
              className="rounded border border-slate-200 px-3 py-1.5 text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Sau
            </button>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">
              Tao nguoi dung moi
            </h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={createEmail}
                  onChange={(e) => setCreateEmail(e.target.value)}
                  placeholder="email@example.com"
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Mat khau
                </label>
                <input
                  type="password"
                  value={createPassword}
                  onChange={(e) => setCreatePassword(e.target.value)}
                  placeholder="Toi thieu 8 ky tu"
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  required
                  minLength={8}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Vai tro
                </label>
                <select
                  value={createRole}
                  onChange={(e) => setCreateRole(e.target.value)}
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="user">Nguoi dung</option>
                  <option value="expert">Chuyen gia</option>
                  <option value="admin">Quan tri vien</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setCreateEmail("");
                  setCreatePassword("");
                  setCreateRole("user");
                }}
                className="rounded-md border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Huy
              </button>
              <button
                onClick={handleCreateUser}
                disabled={
                  creating ||
                  !createEmail ||
                  createPassword.length < 8
                }
                className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {creating ? "Dang tao..." : "Tao"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {editUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">
              Chinh sua nguoi dung
            </h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={editEmail}
                  onChange={(e) => setEditEmail(e.target.value)}
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Vai tro
                </label>
                <select
                  value={editRole}
                  onChange={(e) => setEditRole(e.target.value)}
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="user">Nguoi dung</option>
                  <option value="expert">Chuyen gia</option>
                  <option value="admin">Quan tri vien</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setEditUser(null)}
                className="rounded-md border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Huy
              </button>
              <button
                onClick={handleEditUser}
                disabled={editing}
                className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {editing ? "Dang luu..." : "Luu"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
