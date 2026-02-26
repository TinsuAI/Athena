"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Upload,
  FileSpreadsheet,
  ChevronRight,
  ChevronLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  PackageCheck,
  Copy,
  Ban,
  ArrowLeft,
  Loader2,
  Database,
  ShieldCheck,
  Inbox,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

// --- Types ---

interface SampleRow {
  product_name: string;
  hs_code: string;
  row_number: number;
}

interface PreviewData {
  file_name: string;
  total_rows: number;
  sample_rows: SampleRow[];
  duplicate_count: number;
  unmatched_count: number;
  ready_to_import_count: number;
}

interface ImportResultData {
  file_name: string;
  total_rows: number;
  records_imported: number;
  duplicates_skipped: number;
  unmatched_codes: Array<{ code: string; row: number; product_name: string }>;
  errors: Array<{ row: number; error: string }>;
  elapsed_seconds: number;
}

interface ImportBatch {
  id: number;
  file_name: string;
  company_name: string | null;
  imported_by_email: string | null;
  total_rows: number;
  records_imported: number;
  duplicates_skipped: number;
  unmatched_codes: number;
  errors_count: number;
  started_at: string | null;
  completed_at: string | null;
}

interface SearchMethodBreakdown {
  search_method: string;
  count: number;
}

interface ChapterCoverage {
  chapter_code: string;
  name_vn: string;
  record_count: number;
}

interface KBStats {
  total_verified: number;
  breakdown_by_method: SearchMethodBreakdown[];
  top_chapters: ChapterCoverage[];
  recent_imports: ImportBatch[];
}

type Step = "upload" | "preview" | "result";
type PageTab = "import" | "history";

const HISTORY_PAGE_SIZE = 10;

// --- Step indicator ---

const STEPS: { key: Step; label: string }[] = [
  { key: "upload", label: "Tải tệp lên" },
  { key: "preview", label: "Xem trước" },
  { key: "result", label: "Kết quả" },
];

function StepIndicator({ current }: { current: Step }) {
  const currentIdx = STEPS.findIndex((s) => s.key === current);

  return (
    <div className="flex items-center gap-1 text-xs font-medium select-none mb-8">
      {STEPS.map((step, i) => {
        const isActive = i === currentIdx;
        const isDone = i < currentIdx;
        return (
          <span key={step.key} className="flex items-center gap-1">
            {i > 0 && (
              <ChevronRight
                className={`size-3.5 ${isDone ? "text-emerald-500" : "text-slate-300"}`}
              />
            )}
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 transition-colors ${
                isActive
                  ? "bg-emerald-600 text-white"
                  : isDone
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-slate-100 text-slate-400"
              }`}
            >
              <span
                className={`inline-flex items-center justify-center size-4 rounded-full text-[10px] font-bold leading-none ${
                  isActive
                    ? "bg-white/20 text-white"
                    : isDone
                      ? "bg-emerald-200 text-emerald-700"
                      : "bg-slate-200 text-slate-400"
                }`}
              >
                {isDone ? (
                  <CheckCircle2 className="size-3" />
                ) : (
                  i + 1
                )}
              </span>
              {step.label}
            </span>
          </span>
        );
      })}
    </div>
  );
}

// --- Stat card ---

function StatCard({
  label,
  value,
  icon: Icon,
  accent = "slate",
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  accent?: "emerald" | "amber" | "red" | "slate" | "blue";
}) {
  const colors = {
    emerald: "border-l-emerald-500 bg-emerald-50/60",
    amber: "border-l-amber-500 bg-amber-50/60",
    red: "border-l-red-500 bg-red-50/60",
    slate: "border-l-slate-400 bg-slate-50/60",
    blue: "border-l-blue-500 bg-blue-50/60",
  };
  const iconColors = {
    emerald: "text-emerald-600",
    amber: "text-amber-600",
    red: "text-red-500",
    slate: "text-slate-500",
    blue: "text-blue-600",
  };

  return (
    <div
      className={`rounded-lg border border-slate-200 border-l-4 ${colors[accent]} p-4 flex items-start gap-3`}
    >
      <Icon className={`size-5 mt-0.5 shrink-0 ${iconColors[accent]}`} />
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">
          {label}
        </p>
        <p className="text-xl font-bold text-slate-800 tabular-nums mt-0.5">
          {value}
        </p>
      </div>
    </div>
  );
}

// --- Tab Switcher ---

function TabSwitcher({
  active,
  onChange,
}: {
  active: PageTab;
  onChange: (tab: PageTab) => void;
}) {
  return (
    <div className="flex gap-0 border-b border-slate-200 mb-8">
      <button
        onClick={() => onChange("import")}
        className={`relative px-5 py-2.5 text-sm font-medium transition-colors ${
          active === "import"
            ? "text-emerald-700"
            : "text-slate-400 hover:text-slate-600"
        }`}
      >
        Nhập dữ liệu
        {active === "import" && (
          <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600 rounded-full" />
        )}
      </button>
      <button
        onClick={() => onChange("history")}
        className={`relative px-5 py-2.5 text-sm font-medium transition-colors ${
          active === "history"
            ? "text-emerald-700"
            : "text-slate-400 hover:text-slate-600"
        }`}
      >
        Lịch sử & Thống kê
        {active === "history" && (
          <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600 rounded-full" />
        )}
      </button>
    </div>
  );
}

// --- Helpers ---

const METHOD_LABELS: Record<string, string> = {
  customs_import: "Nhập hải quan",
  notebooklm: "NotebookLM AI",
  expert_correction: "Chuyên gia xác nhận",
};

const METHOD_ICONS: Record<
  string,
  React.ComponentType<{ className?: string }>
> = {
  customs_import: FileSpreadsheet,
  notebooklm: Database,
  expert_correction: ShieldCheck,
};

function formatDate(iso: string | null): string {
  if (!iso) return "\u2014";
  const d = new Date(iso);
  return d.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// --- History & Stats Section ---

function HistoryStatsSection() {
  const [stats, setStats] = useState<KBStats | null>(null);
  const [history, setHistory] = useState<ImportBatch[]>([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyPage, setHistoryPage] = useState(0);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      setIsLoadingStats(true);
      try {
        const res = await fetch(
          `${API_URL}/api/admin/customs-import/stats`,
          { credentials: "include" }
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (json.success) setStats(json.data);
      } catch {
        // silent fail — empty state shown
      } finally {
        setIsLoadingStats(false);
      }
    };
    fetchStats();
  }, []);

  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoadingHistory(true);
      try {
        const res = await fetch(
          `${API_URL}/api/admin/customs-import/history?limit=${HISTORY_PAGE_SIZE}&offset=${historyPage * HISTORY_PAGE_SIZE}`,
          { credentials: "include" }
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (json.success) {
          setHistory(json.data.items);
          setHistoryTotal(json.data.total);
        }
      } catch {
        // silent fail
      } finally {
        setIsLoadingHistory(false);
      }
    };
    fetchHistory();
  }, [historyPage]);

  const totalPages = Math.ceil(historyTotal / HISTORY_PAGE_SIZE);

  const maxChapterCount =
    stats && stats.top_chapters.length > 0
      ? stats.top_chapters[0].record_count
      : 1;

  if (isLoadingStats) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400">
        <Loader2 className="size-5 animate-spin mr-2" />
        Đang tải dữ liệu...
      </div>
    );
  }

  // Empty state: no stats and no history
  if (
    !stats &&
    history.length === 0 &&
    !isLoadingHistory
  ) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-400">
        <div className="rounded-xl bg-slate-100 p-4 mb-4">
          <Inbox className="size-10 text-slate-300" />
        </div>
        <p className="text-base font-medium text-slate-500">
          Chưa có dữ liệu nhập khẩu nào
        </p>
        <p className="text-sm text-slate-400 mt-1">
          Bắt đầu bằng cách tải lên báo cáo hải quan
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* === KB Stats Cards === */}
      {stats && (
        <>
          <div>
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3">
              Thống kê cơ sở kiến thức
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatCard
                label="Tổng bản ghi đã xác minh"
                value={stats.total_verified.toLocaleString("vi-VN")}
                icon={CheckCircle2}
                accent="emerald"
              />
              {stats.breakdown_by_method.map((m) => {
                const Icon = METHOD_ICONS[m.search_method] || FileSpreadsheet;
                return (
                  <StatCard
                    key={m.search_method}
                    label={METHOD_LABELS[m.search_method] || m.search_method}
                    value={m.count.toLocaleString("vi-VN")}
                    icon={Icon}
                    accent="blue"
                  />
                );
              })}
            </div>
          </div>

          {/* === Top Chapters === */}
          {stats.top_chapters.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/80">
                <h3 className="text-sm font-semibold text-slate-700">
                  Chương có nhiều dữ liệu nhất
                </h3>
              </div>
              <div className="divide-y divide-slate-50">
                {stats.top_chapters.map((ch) => (
                  <div
                    key={ch.chapter_code}
                    className="flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50/50 transition-colors"
                  >
                    <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 rounded px-1.5 py-0.5 min-w-[2rem] text-center">
                      {ch.chapter_code}
                    </span>
                    <span className="text-sm text-slate-700 flex-1 truncate">
                      {ch.name_vn}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{
                            width: `${(ch.record_count / maxChapterCount) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs font-mono tabular-nums text-slate-500 min-w-[3rem] text-right">
                        {ch.record_count.toLocaleString("vi-VN")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* === Recent Imports === */}
          {stats.recent_imports.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/80">
                <h3 className="text-sm font-semibold text-slate-700">
                  Nhập gần đây
                </h3>
              </div>
              <div className="divide-y divide-slate-50">
                {stats.recent_imports.map((batch) => (
                  <div
                    key={batch.id}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50/50 transition-colors"
                  >
                    <div className="rounded-lg bg-emerald-50 p-1.5 shrink-0">
                      <FileSpreadsheet className="size-4 text-emerald-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-700 truncate">
                        {batch.file_name}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {formatDate(batch.started_at)}
                        {batch.imported_by_email && (
                          <span className="ml-2">
                            {batch.imported_by_email}
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0 text-xs tabular-nums">
                      <span className="text-emerald-600 font-medium">
                        +{batch.records_imported}
                      </span>
                      {batch.duplicates_skipped > 0 && (
                        <span className="text-amber-500">
                          {batch.duplicates_skipped} trùng
                        </span>
                      )}
                      {batch.errors_count > 0 && (
                        <span className="text-red-500">
                          {batch.errors_count} lỗi
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* === Full History Table === */}
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-700">
            Lịch sử nhập dữ liệu
          </h3>
          {historyTotal > 0 && (
            <span className="text-xs text-slate-400 tabular-nums">
              {historyTotal} bản ghi
            </span>
          )}
        </div>

        {isLoadingHistory ? (
          <div className="flex items-center justify-center py-12 text-slate-400">
            <Loader2 className="size-4 animate-spin mr-2" />
            Đang tải...
          </div>
        ) : history.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-400">
            <Inbox className="size-8 text-slate-300 mb-2" />
            <p className="text-sm">Chưa có dữ liệu nhập khẩu nào</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wider text-slate-400">
                    <th className="px-4 py-2.5 font-medium">Tệp nguồn</th>
                    <th className="px-4 py-2.5 font-medium">Ngày nhập</th>
                    <th className="px-4 py-2.5 font-medium text-right">
                      Đã nhập
                    </th>
                    <th className="px-4 py-2.5 font-medium text-right">
                      Trùng lặp
                    </th>
                    <th className="px-4 py-2.5 font-medium text-right">Lỗi</th>
                    <th className="px-4 py-2.5 font-medium">Người nhập</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((batch) => (
                    <tr
                      key={batch.id}
                      className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition-colors"
                    >
                      <td className="px-4 py-2.5 text-slate-700 max-w-[200px] truncate font-medium">
                        {batch.file_name}
                      </td>
                      <td className="px-4 py-2.5 text-slate-500 text-xs whitespace-nowrap">
                        {formatDate(batch.started_at)}
                      </td>
                      <td className="px-4 py-2.5 text-right tabular-nums font-mono text-xs text-emerald-600 font-medium">
                        {batch.records_imported.toLocaleString("vi-VN")}
                      </td>
                      <td className="px-4 py-2.5 text-right tabular-nums font-mono text-xs text-amber-500">
                        {batch.duplicates_skipped > 0
                          ? batch.duplicates_skipped.toLocaleString("vi-VN")
                          : "\u2014"}
                      </td>
                      <td className="px-4 py-2.5 text-right tabular-nums font-mono text-xs text-red-500">
                        {batch.errors_count > 0
                          ? batch.errors_count.toLocaleString("vi-VN")
                          : "\u2014"}
                      </td>
                      <td className="px-4 py-2.5 text-slate-500 text-xs truncate max-w-[160px]">
                        {batch.imported_by_email || "\u2014"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
                <button
                  onClick={() => setHistoryPage((p) => Math.max(0, p - 1))}
                  disabled={historyPage === 0}
                  className="text-xs font-medium text-slate-500 hover:text-emerald-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                >
                  <ChevronLeft className="size-3.5" />
                  Trang trước
                </button>
                <span className="text-xs text-slate-400 tabular-nums">
                  Trang {historyPage + 1} / {totalPages}
                </span>
                <button
                  onClick={() =>
                    setHistoryPage((p) => Math.min(totalPages - 1, p + 1))
                  }
                  disabled={historyPage >= totalPages - 1}
                  className="text-xs font-medium text-slate-500 hover:text-emerald-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                >
                  Trang sau
                  <ChevronRight className="size-3.5" />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// --- Main page ---

export default function CustomsImportPage() {
  const [pageTab, setPageTab] = useState<PageTab>("import");
  const [step, setStep] = useState<Step>("upload");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [result, setResult] = useState<ImportResultData | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): boolean => {
    const name = file.name.toLowerCase();
    if (!name.endsWith(".xls") && !name.endsWith(".xlsx")) {
      setError("Chỉ chấp nhận tệp XLS hoặc XLSX. Vui lòng chọn lại.");
      return false;
    }
    setError(null);
    return true;
  }, []);

  const handleFileSelect = useCallback(
    (file: File) => {
      if (validateFile(file)) {
        setSelectedFile(file);
        setError(null);
      }
    },
    [validateFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFileSelect(file);
    },
    [handleFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFileSelect(file);
    },
    [handleFileSelect]
  );

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await fetch(
        `${API_URL}/api/admin/customs-import/upload`,
        {
          method: "POST",
          credentials: "include",
          body: formData,
        }
      );

      const json = await res.json();

      if (!json.success) {
        setError(json.error?.detail || "Lỗi khi tải tệp lên. Vui lòng thử lại.");
        return;
      }

      setPreview(json.data);
      setStep("preview");
    } catch {
      setError("Không thể kết nối đến máy chủ. Vui lòng thử lại.");
    } finally {
      setIsUploading(false);
    }
  }, [selectedFile]);

  const handleExecute = useCallback(async () => {
    if (!selectedFile) return;
    setIsImporting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await fetch(
        `${API_URL}/api/admin/customs-import/execute`,
        {
          method: "POST",
          credentials: "include",
          body: formData,
        }
      );

      const json = await res.json();

      if (!json.success) {
        setError(json.error?.detail || "Lỗi khi nhập dữ liệu. Vui lòng thử lại.");
        return;
      }

      setResult(json.data);
      setStep("result");
    } catch {
      setError("Không thể kết nối đến máy chủ. Vui lòng thử lại.");
    } finally {
      setIsImporting(false);
    }
  }, [selectedFile]);

  const handleReset = useCallback(() => {
    setStep("upload");
    setSelectedFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);

  const handleCancel = useCallback(() => {
    handleReset();
  }, [handleReset]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-slate-500 mb-6">
        <Link
          href="/admin"
          className="hover:text-emerald-700 transition-colors flex items-center gap-1"
        >
          <ArrowLeft className="size-3.5" />
          Quản trị
        </Link>
        <ChevronRight className="size-3.5 text-slate-300" />
        <span className="text-slate-800 font-medium">
          Nhập dữ liệu hải quan
        </span>
      </nav>

      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Nhập dữ liệu hải quan
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Tải lên báo cáo hải quan (XLS/XLSX) để nhập dữ liệu vào cơ sở kiến thức
        </p>
      </div>

      {/* Tab switcher */}
      <TabSwitcher active={pageTab} onChange={setPageTab} />

      {/* ===== IMPORT TAB ===== */}
      {pageTab === "import" && (
        <>
          {/* Step indicator */}
          <StepIndicator current={step} />

          {/* Error display */}
          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <XCircle className="size-5 shrink-0 mt-0.5 text-red-500" />
              <div>
                <p className="font-medium">Lỗi</p>
                <p className="mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {/* ===== STEP 1: Upload ===== */}
          {step === "upload" && (
            <div className="space-y-5">
              {/* Drop zone */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
                className={`
                  relative cursor-pointer rounded-xl border-2 border-dashed transition-all
                  flex flex-col items-center justify-center py-16 px-8 text-center
                  ${
                    isDragging
                      ? "border-emerald-400 bg-emerald-50/80 scale-[1.01]"
                      : selectedFile
                        ? "border-emerald-300 bg-emerald-50/40"
                        : "border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50/50"
                  }
                `}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xls,.xlsx"
                  onChange={handleInputChange}
                  className="hidden"
                />

                {selectedFile ? (
                  <>
                    <div className="rounded-xl bg-emerald-100 p-3 mb-4">
                      <FileSpreadsheet className="size-8 text-emerald-600" />
                    </div>
                    <p className="text-base font-semibold text-slate-800">
                      {selectedFile.name}
                    </p>
                    <p className="text-sm text-slate-500 mt-1">
                      {formatFileSize(selectedFile.size)}
                    </p>
                    <p className="text-xs text-slate-400 mt-3">
                      Nhấn để chọn tệp khác
                    </p>
                  </>
                ) : (
                  <>
                    <div className="rounded-xl bg-slate-100 p-3 mb-4">
                      <Upload className="size-8 text-slate-400" />
                    </div>
                    <p className="text-base font-medium text-slate-700">
                      Kéo thả hoặc chọn tệp XLS/XLSX
                    </p>
                    <p className="text-sm text-slate-400 mt-1">
                      Báo cáo hải quan Việt Nam (.xls, .xlsx)
                    </p>
                  </>
                )}
              </div>

              {/* Upload button */}
              <div className="flex justify-end">
                <Button
                  onClick={handleUpload}
                  disabled={!selectedFile || isUploading}
                  size="lg"
                  className="min-w-[200px]"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      Đang xử lý...
                    </>
                  ) : (
                    <>
                      <Upload className="size-4" />
                      Tải lên và xem trước
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* ===== STEP 2: Preview ===== */}
          {step === "preview" && preview && (
            <div className="space-y-6">
              {/* Stats grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard
                  label="Tổng số dòng"
                  value={preview.total_rows}
                  icon={FileSpreadsheet}
                  accent="slate"
                />
                <StatCard
                  label="Sẵn sàng nhập"
                  value={preview.ready_to_import_count}
                  icon={PackageCheck}
                  accent="emerald"
                />
                <StatCard
                  label="Trùng lặp"
                  value={preview.duplicate_count}
                  icon={Copy}
                  accent="amber"
                />
                <StatCard
                  label="Không khớp mã HS"
                  value={preview.unmatched_count}
                  icon={AlertTriangle}
                  accent={preview.unmatched_count > 0 ? "red" : "slate"}
                />
              </div>

              {/* Sample table */}
              <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/80">
                  <h3 className="text-sm font-semibold text-slate-700">
                    Dữ liệu mẫu (10 dòng đầu)
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wider text-slate-400">
                        <th className="px-4 py-2.5 w-16 font-medium">Dòng</th>
                        <th className="px-4 py-2.5 font-medium">Tên hàng</th>
                        <th className="px-4 py-2.5 w-32 font-medium">Mã HS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.sample_rows.map((row, i) => (
                        <tr
                          key={i}
                          className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition-colors"
                        >
                          <td className="px-4 py-2.5 tabular-nums text-slate-400 font-mono text-xs">
                            {row.row_number}
                          </td>
                          <td className="px-4 py-2.5 text-slate-700 max-w-sm truncate">
                            {row.product_name}
                          </td>
                          <td className="px-4 py-2.5 font-mono text-xs text-slate-600 tracking-wide">
                            {row.hs_code}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={handleCancel}
                  disabled={isImporting}
                >
                  <Ban className="size-4" />
                  Hủy bỏ
                </Button>
                <Button
                  onClick={handleExecute}
                  disabled={isImporting || preview.ready_to_import_count === 0}
                  size="lg"
                  className="min-w-[180px]"
                >
                  {isImporting ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      Đang nhập...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="size-4" />
                      Xác nhận nhập
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* ===== STEP 3: Results ===== */}
          {step === "result" && result && (
            <div className="space-y-6">
              {/* Success banner */}
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 flex items-start gap-3">
                <CheckCircle2 className="size-5 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <p className="font-semibold text-emerald-800">
                    Nhập dữ liệu thành công
                  </p>
                  <p className="text-sm text-emerald-700 mt-0.5">
                    Tệp <span className="font-medium">{result.file_name}</span>{" "}
                    đã được xử lý hoàn tất.
                  </p>
                </div>
              </div>

              {/* Result stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard
                  label="Đã nhập"
                  value={result.records_imported}
                  icon={PackageCheck}
                  accent="emerald"
                />
                <StatCard
                  label="Trùng lặp bỏ qua"
                  value={result.duplicates_skipped}
                  icon={Copy}
                  accent="amber"
                />
                <StatCard
                  label="Lỗi"
                  value={result.errors.length}
                  icon={XCircle}
                  accent={result.errors.length > 0 ? "red" : "slate"}
                />
                <StatCard
                  label="Thời gian"
                  value={`${result.elapsed_seconds}s`}
                  icon={Clock}
                  accent="blue"
                />
              </div>

              {/* Unmatched codes detail (if any) */}
              {result.unmatched_codes.length > 0 && (
                <div className="rounded-lg border border-amber-200 bg-amber-50/60 overflow-hidden">
                  <div className="px-4 py-3 border-b border-amber-100 bg-amber-50">
                    <h3 className="text-sm font-semibold text-amber-800 flex items-center gap-2">
                      <AlertTriangle className="size-4" />
                      Mã HS không khớp ({result.unmatched_codes.length})
                    </h3>
                  </div>
                  <div className="overflow-x-auto max-h-48">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-amber-100 text-left text-xs uppercase tracking-wider text-amber-600">
                          <th className="px-4 py-2 w-16 font-medium">Dòng</th>
                          <th className="px-4 py-2 w-32 font-medium">Mã HS</th>
                          <th className="px-4 py-2 font-medium">Tên hàng</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.unmatched_codes.map((item, i) => (
                          <tr
                            key={i}
                            className="border-b border-amber-50 last:border-0"
                          >
                            <td className="px-4 py-2 tabular-nums text-amber-700 font-mono text-xs">
                              {item.row}
                            </td>
                            <td className="px-4 py-2 font-mono text-xs text-amber-800">
                              {item.code}
                            </td>
                            <td className="px-4 py-2 text-amber-700 max-w-sm truncate">
                              {item.product_name}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Reset action */}
              <div className="flex justify-end pt-2">
                <Button onClick={handleReset} variant="outline" size="lg">
                  <Upload className="size-4" />
                  Nhập tệp mới
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* ===== HISTORY & STATS TAB ===== */}
      {pageTab === "history" && <HistoryStatsSection />}
    </div>
  );
}
