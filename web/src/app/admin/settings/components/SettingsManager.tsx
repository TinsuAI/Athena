"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";

interface Setting {
  key: string;
  value: string;
  description: string | null;
}

const SETTING_LABELS: Record<string, string> = {
  search_requires_auth: "Tìm kiếm yêu cầu đăng nhập",
};

export default function SettingsManager() {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    setLoading(true);
    try {
      const res = await apiClient.get<Setting[]>("/api/admin/settings");
      if (res.success && res.data) {
        setSettings(res.data);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleToggle(key: string, currentValue: string) {
    const newValue = currentValue === "true" ? "false" : "true";
    setUpdating(key);
    setMessage(null);
    try {
      const res = await apiClient.put<Setting>(`/api/admin/settings/${key}`, { value: newValue });
      if (res.success && res.data) {
        setSettings((prev) =>
          prev.map((s) => (s.key === key ? { ...s, value: newValue } : s))
        );
        setMessage({ text: "Cập nhật thành công", type: "success" });
      } else {
        setMessage({ text: "Cập nhật thất bại", type: "error" });
      }
    } catch {
      setMessage({ text: "Đã xảy ra lỗi", type: "error" });
    } finally {
      setUpdating(null);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Cấu hình hệ thống</h1>

      {message && (
        <div
          className={`mb-4 px-4 py-3 rounded-md text-sm ${
            message.type === "success"
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
              : "bg-red-50 text-red-700 border border-red-200"
          }`}
        >
          {message.text}
        </div>
      )}

      {loading ? (
        <p className="text-slate-500">Đang tải...</p>
      ) : settings.length === 0 ? (
        <p className="text-slate-500">Không có cấu hình nào.</p>
      ) : (
        <div className="space-y-4">
          {settings.map((setting) => (
            <div
              key={setting.key}
              className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4"
            >
              <div>
                <p className="font-medium text-slate-900">
                  {SETTING_LABELS[setting.key] ?? setting.key}
                </p>
                {setting.description && (
                  <p className="text-sm text-slate-500 mt-0.5">{setting.description}</p>
                )}
              </div>
              <button
                role="switch"
                aria-checked={setting.value === "true"}
                disabled={updating === setting.key}
                onClick={() => handleToggle(setting.key, setting.value)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50 ${
                  setting.value === "true" ? "bg-emerald-600" : "bg-slate-300"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    setting.value === "true" ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
