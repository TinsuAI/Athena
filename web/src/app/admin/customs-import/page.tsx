"use client";

import { useCallback, useRef, useState } from "react";
import Link from "next/link";
import {
  Upload,
  FileSpreadsheet,
  ChevronRight,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  PackageCheck,
  Copy,
  Ban,
  ArrowLeft,
  Loader2,
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

type Step = "upload" | "preview" | "result";

// --- Step indicator ---

const STEPS: { key: Step; label: string }[] = [
  { key: "upload", label: "Tai tep len" },
  { key: "preview", label: "Xem truoc" },
  { key: "result", label: "Ket qua" },
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

// --- Main page ---

export default function CustomsImportPage() {
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
      setError("Chi chap nhan tep XLS hoac XLSX. Vui long chon lai.");
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
        setError(json.error?.detail || "Loi khi tai tep len. Vui long thu lai.");
        return;
      }

      setPreview(json.data);
      setStep("preview");
    } catch {
      setError("Khong the ket noi den may chu. Vui long thu lai.");
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
        setError(json.error?.detail || "Loi khi nhap du lieu. Vui long thu lai.");
        return;
      }

      setResult(json.data);
      setStep("result");
    } catch {
      setError("Khong the ket noi den may chu. Vui long thu lai.");
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
          Quan tri
        </Link>
        <ChevronRight className="size-3.5 text-slate-300" />
        <span className="text-slate-800 font-medium">
          Nhap du lieu hai quan
        </span>
      </nav>

      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Nhap du lieu hai quan
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Tai len bao cao hai quan (XLS/XLSX) de nhap du lieu vao co so kien thuc
        </p>
      </div>

      {/* Step indicator */}
      <StepIndicator current={step} />

      {/* Error display */}
      {error && (
        <div className="mb-6 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <XCircle className="size-5 shrink-0 mt-0.5 text-red-500" />
          <div>
            <p className="font-medium">Loi</p>
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
                  Nhan de chon tep khac
                </p>
              </>
            ) : (
              <>
                <div className="rounded-xl bg-slate-100 p-3 mb-4">
                  <Upload className="size-8 text-slate-400" />
                </div>
                <p className="text-base font-medium text-slate-700">
                  Keo tha hoac chon tep XLS/XLSX
                </p>
                <p className="text-sm text-slate-400 mt-1">
                  Bao cao hai quan Viet Nam (.xls, .xlsx)
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
                  Dang xu ly...
                </>
              ) : (
                <>
                  <Upload className="size-4" />
                  Tai len va xem truoc
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
              label="Tong so dong"
              value={preview.total_rows}
              icon={FileSpreadsheet}
              accent="slate"
            />
            <StatCard
              label="San sang nhap"
              value={preview.ready_to_import_count}
              icon={PackageCheck}
              accent="emerald"
            />
            <StatCard
              label="Trung lap"
              value={preview.duplicate_count}
              icon={Copy}
              accent="amber"
            />
            <StatCard
              label="Khong khop ma HS"
              value={preview.unmatched_count}
              icon={AlertTriangle}
              accent={preview.unmatched_count > 0 ? "red" : "slate"}
            />
          </div>

          {/* Sample table */}
          <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/80">
              <h3 className="text-sm font-semibold text-slate-700">
                Du lieu mau (10 dong dau)
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wider text-slate-400">
                    <th className="px-4 py-2.5 w-16 font-medium">Dong</th>
                    <th className="px-4 py-2.5 font-medium">Ten hang</th>
                    <th className="px-4 py-2.5 w-32 font-medium">Ma HS</th>
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
              Huy bo
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
                  Dang nhap...
                </>
              ) : (
                <>
                  <CheckCircle2 className="size-4" />
                  Xac nhan nhap
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
                Nhap du lieu thanh cong
              </p>
              <p className="text-sm text-emerald-700 mt-0.5">
                Tep <span className="font-medium">{result.file_name}</span>{" "}
                da duoc xu ly hoan tat.
              </p>
            </div>
          </div>

          {/* Result stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard
              label="Da nhap"
              value={result.records_imported}
              icon={PackageCheck}
              accent="emerald"
            />
            <StatCard
              label="Trung lap bo qua"
              value={result.duplicates_skipped}
              icon={Copy}
              accent="amber"
            />
            <StatCard
              label="Loi"
              value={result.errors.length}
              icon={XCircle}
              accent={result.errors.length > 0 ? "red" : "slate"}
            />
            <StatCard
              label="Thoi gian"
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
                  Ma HS khong khop ({result.unmatched_codes.length})
                </h3>
              </div>
              <div className="overflow-x-auto max-h-48">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-amber-100 text-left text-xs uppercase tracking-wider text-amber-600">
                      <th className="px-4 py-2 w-16 font-medium">Dong</th>
                      <th className="px-4 py-2 w-32 font-medium">Ma HS</th>
                      <th className="px-4 py-2 font-medium">Ten hang</th>
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
              Nhap tep moi
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
