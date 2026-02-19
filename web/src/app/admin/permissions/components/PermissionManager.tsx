"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient } from "@/lib/api";

// --- Types ---

interface PermissionDef {
  code: string;
  name: string;
  description: string | null;
}

interface RolePermissionsItem {
  role: string;
  permissions: string[];
}

interface RolePermissionsData {
  all_permissions: PermissionDef[];
  roles: RolePermissionsItem[];
}

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

interface PermissionOverride {
  code: string;
  granted: boolean;
}

interface UserPermissionsData {
  user_id: number;
  role: string;
  role_permissions: string[];
  overrides: PermissionOverride[];
  effective: string[];
}

// --- Constants ---

const ROLE_LABELS: Record<string, string> = {
  user: "Người dùng",
  expert: "Chuyên gia",
  admin: "Quản trị viên",
};

const ROLE_ORDER = ["user", "expert", "admin"];

type OverrideState = "default" | "granted" | "revoked";

// --- Component ---

export function PermissionManager() {
  const [activeTab, setActiveTab] = useState<"roles" | "users">("roles");

  return (
    <div>
      {/* Tab bar */}
      <div className="flex border-b border-slate-200 mb-6">
        <button
          data-testid="tab-roles"
          onClick={() => setActiveTab("roles")}
          className={`px-5 py-2.5 text-sm font-medium transition-colors relative ${
            activeTab === "roles"
              ? "text-emerald-700"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          Vai trò
          {activeTab === "roles" && (
            <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600 rounded-t" />
          )}
        </button>
        <button
          data-testid="tab-users"
          onClick={() => setActiveTab("users")}
          className={`px-5 py-2.5 text-sm font-medium transition-colors relative ${
            activeTab === "users"
              ? "text-emerald-700"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          Người dùng
          {activeTab === "users" && (
            <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600 rounded-t" />
          )}
        </button>
      </div>

      {activeTab === "roles" ? <RolesTab /> : <UsersTab />}
    </div>
  );
}

// ==================== ROLES TAB ====================

function RolesTab() {
  const [data, setData] = useState<RolePermissionsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Local editable state: role -> Set of permission codes
  const [roleEdits, setRoleEdits] = useState<Record<string, Set<string>>>({});
  const [savingRole, setSavingRole] = useState<string | null>(null);

  const fetchRoles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<RolePermissionsData>(
        "/api/admin/permissions/roles"
      );
      if (response.success && response.data) {
        setData(response.data);
        // Initialize editable state from server data
        const edits: Record<string, Set<string>> = {};
        for (const rp of response.data.roles) {
          edits[rp.role] = new Set(rp.permissions);
        }
        setRoleEdits(edits);
      } else {
        setError(response.error?.detail || "Không thể tải danh sách quyền");
      }
    } catch {
      setError("Không thể tải danh sách quyền");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  const togglePermission = (role: string, code: string) => {
    setRoleEdits((prev) => {
      const next = { ...prev };
      const set = new Set(next[role] || []);
      if (set.has(code)) {
        set.delete(code);
      } else {
        set.add(code);
      }
      next[role] = set;
      return next;
    });
  };

  const handleSaveRole = async (role: string) => {
    setSavingRole(role);
    setError(null);
    setSuccessMessage(null);
    try {
      const permissions = Array.from(roleEdits[role] || []);
      const response = await apiClient.put<{ role: string; permissions: string[] }>(
        `/api/admin/permissions/roles/${role}`,
        { permissions }
      );
      if (response.success) {
        setSuccessMessage(
          `Cập nhật quyền cho "${ROLE_LABELS[role]}" thành công`
        );
        setTimeout(() => setSuccessMessage(null), 3000);
        // Re-fetch to sync server state
        await fetchRoles();
      } else {
        setError(response.error?.detail || "Cập nhật quyền thất bại");
      }
    } catch {
      setError("Cập nhật quyền thất bại");
    } finally {
      setSavingRole(null);
    }
  };

  const hasChanges = (role: string): boolean => {
    if (!data) return false;
    const original = data.roles.find((r) => r.role === role);
    if (!original) return false;
    const current = roleEdits[role] || new Set();
    if (current.size !== original.permissions.length) return true;
    return original.permissions.some((p) => !current.has(p));
  };

  if (loading) {
    return (
      <div className="text-slate-400 text-sm py-8">
        Đang tải cấu hình quyền...
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

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm" aria-label="Role permissions">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="px-4 py-3 text-left font-medium text-slate-600 min-w-[140px]">
                Vai trò
              </th>
              {data.all_permissions.map((perm) => (
                <th
                  key={perm.code}
                  className="px-4 py-3 text-center font-medium text-slate-600 min-w-[120px]"
                  title={perm.description || perm.code}
                >
                  {perm.name}
                </th>
              ))}
              <th className="px-4 py-3 text-right font-medium text-slate-600 min-w-[100px]">
                Thao tác
              </th>
            </tr>
          </thead>
          <tbody>
            {ROLE_ORDER.map((role) => {
              const currentPerms = roleEdits[role] || new Set<string>();
              const changed = hasChanges(role);
              return (
                <tr
                  key={role}
                  className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="font-medium text-slate-900">
                      {ROLE_LABELS[role] || role}
                    </span>
                    <span className="block text-xs text-slate-400 mt-0.5">
                      {role}
                    </span>
                  </td>
                  {data.all_permissions.map((perm) => (
                    <td key={perm.code} className="px-4 py-3 text-center">
                      <label className="inline-flex items-center justify-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={currentPerms.has(perm.code)}
                          onChange={() => togglePermission(role, perm.code)}
                          className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 focus:ring-offset-0 cursor-pointer"
                          aria-label={`${ROLE_LABELS[role]}: ${perm.name}`}
                        />
                      </label>
                    </td>
                  ))}
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleSaveRole(role)}
                      disabled={!changed || savingRole === role}
                      className="inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      {savingRole === role ? "Đang lưu..." : "Lưu thay đổi"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="mt-3 text-xs text-slate-400">
        Thay đổi quyền của vai trò sẽ áp dụng cho tất cả người dùng có vai trò
        đó, trừ khi có ghi đè riêng.
      </p>
    </div>
  );
}

// ==================== USERS TAB ====================

function UsersTab() {
  const [search, setSearch] = useState("");
  const [userResults, setUserResults] = useState<UserItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const [selectedUser, setSelectedUser] = useState<UserItem | null>(null);
  const [userPerms, setUserPerms] = useState<UserPermissionsData | null>(null);
  const [allPermissions, setAllPermissions] = useState<PermissionDef[]>([]);
  const [permsLoading, setPermsLoading] = useState(false);

  // Override edits: code -> OverrideState
  const [overrideEdits, setOverrideEdits] = useState<
    Record<string, OverrideState>
  >({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load all permissions once
  useEffect(() => {
    (async () => {
      try {
        const response = await apiClient.get<RolePermissionsData>(
          "/api/admin/permissions/roles"
        );
        if (response.success && response.data) {
          setAllPermissions(response.data.all_permissions);
        }
      } catch {
        // silently fail - permissions will show when user is selected
      }
    })();
  }, []);

  const searchUsers = useCallback(async (query: string) => {
    if (!query.trim()) {
      setUserResults([]);
      return;
    }
    setSearchLoading(true);
    try {
      const params = new URLSearchParams({
        search: query,
        per_page: "10",
      });
      const response = await apiClient.get<UserListData>(
        `/api/admin/users?${params.toString()}`
      );
      if (response.success && response.data) {
        setUserResults(response.data.items);
      }
    } catch {
      // silent fail for search
    } finally {
      setSearchLoading(false);
    }
  }, []);

  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }
    searchTimerRef.current = setTimeout(() => {
      searchUsers(value);
    }, 300);
  };

  const loadUserPermissions = async (user: UserItem) => {
    setSelectedUser(user);
    setUserResults([]);
    setSearch("");
    setPermsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<UserPermissionsData>(
        `/api/admin/permissions/users/${user.id}`
      );
      if (response.success && response.data) {
        setUserPerms(response.data);
        // Initialize override edits from server data
        const edits: Record<string, OverrideState> = {};
        for (const perm of allPermissions) {
          const override = response.data.overrides.find(
            (o) => o.code === perm.code
          );
          if (override) {
            edits[perm.code] = override.granted ? "granted" : "revoked";
          } else {
            edits[perm.code] = "default";
          }
        }
        setOverrideEdits(edits);
      } else {
        setError(
          response.error?.detail || "Không thể tải quyền của người dùng"
        );
      }
    } catch {
      setError("Không thể tải quyền của người dùng");
    } finally {
      setPermsLoading(false);
    }
  };

  const cycleOverride = (code: string) => {
    setOverrideEdits((prev) => {
      const current = prev[code] || "default";
      const next: OverrideState =
        current === "default"
          ? "granted"
          : current === "granted"
            ? "revoked"
            : "default";
      return { ...prev, [code]: next };
    });
  };

  const handleSaveOverrides = async () => {
    if (!selectedUser) return;
    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    // Build overrides list (only non-default entries)
    const overrides: PermissionOverride[] = [];
    for (const [code, state] of Object.entries(overrideEdits)) {
      if (state === "granted") {
        overrides.push({ code, granted: true });
      } else if (state === "revoked") {
        overrides.push({ code, granted: false });
      }
    }

    try {
      const response = await apiClient.put<UserPermissionsData>(
        `/api/admin/permissions/users/${selectedUser.id}`,
        { overrides }
      );
      if (response.success && response.data) {
        setUserPerms(response.data);
        setSuccessMessage("Cập nhật quyền người dùng thành công");
        setTimeout(() => setSuccessMessage(null), 3000);
      } else {
        setError(response.error?.detail || "Cập nhật quyền thất bại");
      }
    } catch {
      setError("Cập nhật quyền thất bại");
    } finally {
      setSaving(false);
    }
  };

  const hasOverrideChanges = (): boolean => {
    if (!userPerms) return false;
    for (const perm of allPermissions) {
      const currentState = overrideEdits[perm.code] || "default";
      const serverOverride = userPerms.overrides.find(
        (o) => o.code === perm.code
      );
      const serverState: OverrideState = serverOverride
        ? serverOverride.granted
          ? "granted"
          : "revoked"
        : "default";
      if (currentState !== serverState) return true;
    }
    return false;
  };

  const getEffectiveStatus = (
    code: string
  ): { active: boolean; source: string } => {
    if (!userPerms) return { active: false, source: "" };
    const overrideState = overrideEdits[code] || "default";
    const inRoleDefaults = userPerms.role_permissions.includes(code);

    if (overrideState === "granted") {
      return { active: true, source: "Ghi đè: Cấp quyền" };
    }
    if (overrideState === "revoked") {
      return { active: false, source: "Ghi đè: Thu hồi" };
    }
    // default
    return {
      active: inRoleDefaults,
      source: inRoleDefaults ? "Mặc định vai trò" : "Không có quyền",
    };
  };

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

      {/* User search */}
      <div className="relative mb-6">
        <div className="relative">
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
            placeholder="Tìm người dùng theo email..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full rounded-md border border-slate-200 bg-white pl-10 pr-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          {searchLoading && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
              Đang tìm...
            </span>
          )}
        </div>

        {/* Search results dropdown */}
        {userResults.length > 0 && (
          <div className="absolute z-20 mt-1 w-full rounded-md border border-slate-200 bg-white shadow-lg max-h-60 overflow-y-auto">
            {userResults.map((user) => (
              <button
                key={user.id}
                onClick={() => loadUserPermissions(user)}
                className="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors border-b border-slate-50 last:border-0"
              >
                <span className="font-medium text-slate-900">
                  {user.email}
                </span>
                <span className="ml-2 text-xs text-slate-400">
                  {ROLE_LABELS[user.role] || user.role}
                </span>
                {!user.is_active && (
                  <span className="ml-2 text-xs text-red-500">
                    (Vô hiệu hóa)
                  </span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Selected user info */}
      {selectedUser && (
        <div className="mb-4 flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 px-4 py-3">
          <div>
            <span className="text-sm font-medium text-slate-900">
              {selectedUser.email}
            </span>
            <span className="ml-3 inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">
              {ROLE_LABELS[selectedUser.role] || selectedUser.role}
            </span>
          </div>
          <button
            onClick={() => {
              setSelectedUser(null);
              setUserPerms(null);
              setOverrideEdits({});
            }}
            className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
          >
            Bỏ chọn
          </button>
        </div>
      )}

      {/* User permissions table */}
      {permsLoading && (
        <div className="text-slate-400 text-sm py-8">
          Đang tải quyền người dùng...
        </div>
      )}

      {selectedUser && userPerms && !permsLoading && (
        <>
          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-sm" aria-label="User permissions">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="px-4 py-3 text-left font-medium text-slate-600">
                    Quyền
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-slate-600">
                    Mặc định vai trò
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-slate-600">
                    Ghi đè
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-slate-600">
                    Kết quả
                  </th>
                </tr>
              </thead>
              <tbody>
                {allPermissions.map((perm) => {
                  const inRoleDefaults =
                    userPerms.role_permissions.includes(perm.code);
                  const overrideState = overrideEdits[perm.code] || "default";
                  const effective = getEffectiveStatus(perm.code);

                  return (
                    <tr
                      key={perm.code}
                      className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <span className="font-medium text-slate-900">
                          {perm.name}
                        </span>
                        <span className="block text-xs text-slate-400 mt-0.5">
                          {perm.code}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {inRoleDefaults ? (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-700">
                            <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
                            Có
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs text-slate-400">
                            <span className="inline-block h-2 w-2 rounded-full bg-slate-300" />
                            Không
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => cycleOverride(perm.code)}
                          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors cursor-pointer ${
                            overrideState === "default"
                              ? "bg-slate-100 text-slate-600 hover:bg-slate-200"
                              : overrideState === "granted"
                                ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                                : "bg-red-100 text-red-700 hover:bg-red-200"
                          }`}
                          title="Nhấn để chuyển trạng thái: Mặc định -> Cấp quyền -> Thu hồi -> Mặc định"
                        >
                          {overrideState === "default" && "Mặc định"}
                          {overrideState === "granted" && "Cấp quyền"}
                          {overrideState === "revoked" && "Thu hồi"}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-flex items-center gap-1.5 text-xs font-medium ${
                            effective.active
                              ? "text-emerald-700"
                              : "text-slate-400"
                          }`}
                        >
                          <span
                            className={`inline-block h-2 w-2 rounded-full ${
                              effective.active
                                ? "bg-emerald-500"
                                : "bg-slate-300"
                            }`}
                          />
                          {effective.source}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Ghi đè sẽ ưu tiên hơn quyền mặc định của vai trò.
            </p>
            <button
              onClick={handleSaveOverrides}
              disabled={!hasOverrideChanges() || saving}
              className="inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? "Đang lưu..." : "Lưu thay đổi"}
            </button>
          </div>
        </>
      )}

      {!selectedUser && !permsLoading && (
        <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50/50 py-12 text-center">
          <svg
            className="mx-auto h-10 w-10 text-slate-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
          <p className="mt-3 text-sm text-slate-500">
            Tìm và chọn người dùng để xem và chỉnh sửa quyền
          </p>
        </div>
      )}
    </div>
  );
}
