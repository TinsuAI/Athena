"use client";

import { useCallback, useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Inbox,
  Clock,
  User,
  FileText,
  ArrowRightLeft,
  MessageSquare,
  History,
  ClipboardList,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { HSCodeTree } from "@/components/ui/HSCodeTree";

interface CorrectionItem {
  id: number;
  query_text: string;
  matched_hs_code: string | null;
  matched_description_vn: string | null;
  matched_description_en: string | null;
  correct_hs_code: string | null;
  correct_description_vn: string | null;
  correct_description_en: string | null;
  submitter_email: string | null;
  submitted_at: string;
  notes: string | null;
}

interface PendingCorrectionItem extends CorrectionItem {}

interface HistoryCorrectionItem extends CorrectionItem {
  correction_status: "approved" | "rejected";
  rejection_reason: string | null;
  verified_at: string | null;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

type ActiveTab = "pending" | "history";

export default function ExpertCorrectionsPage() {
  const { data: session, status: authStatus } = useSession();
  const userRole = (session?.user as { role?: string } | undefined)?.role;
  const isExpertOrAdmin = userRole === "expert" || userRole === "admin";

  const [activeTab, setActiveTab] = useState<ActiveTab>("pending");

  // Pending state
  const [corrections, setCorrections] = useState<PendingCorrectionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [rejectingId, setRejectingId] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [processingId, setProcessingId] = useState<number | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [dismissingId, setDismissingId] = useState<number | null>(null);

  // History state
  const [historyItems, setHistoryItems] = useState<HistoryCorrectionItem[]>([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyPage, setHistoryPage] = useState(1);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);

  const fetchCorrections = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<PaginatedResponse<PendingCorrectionItem>>(
        `/api/expert/corrections?page=${page}&per_page=${perPage}`
      );
      if (response.success && response.data) {
        setCorrections(response.data.items);
        setTotal(response.data.total);
      } else {
        setError(response.error?.detail || "Không thể tải danh sách chỉnh sửa");
      }
    } catch {
      setError("Lỗi kết nối. Vui lòng thử lại.");
    } finally {
      setIsLoading(false);
    }
  }, [page, perPage]);

  const fetchHistory = useCallback(async () => {
    setIsHistoryLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<PaginatedResponse<HistoryCorrectionItem>>(
        `/api/expert/corrections/history?page=${historyPage}&per_page=${perPage}`
      );
      if (response.success && response.data) {
        setHistoryItems(response.data.items);
        setHistoryTotal(response.data.total);
      } else {
        setError(response.error?.detail || "Không thể tải lịch sử chỉnh sửa");
      }
    } catch {
      setError("Lỗi kết nối. Vui lòng thử lại.");
    } finally {
      setIsHistoryLoading(false);
    }
  }, [historyPage, perPage]);

  useEffect(() => {
    if (isExpertOrAdmin && activeTab === "pending") {
      fetchCorrections();
    }
  }, [isExpertOrAdmin, activeTab, fetchCorrections]);

  useEffect(() => {
    if (isExpertOrAdmin && activeTab === "history") {
      fetchHistory();
    }
  }, [isExpertOrAdmin, activeTab, fetchHistory]);

  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const removeCard = (id: number) => {
    setDismissingId(id);
    setTimeout(() => {
      setCorrections((prev) => prev.filter((c) => c.id !== id));
      setTotal((prev) => prev - 1);
      setDismissingId(null);
    }, 300);
  };

  const handleApprove = async (id: number) => {
    setProcessingId(id);
    try {
      const response = await apiClient.post(`/api/expert/corrections/${id}/approve`, {});
      if (response.success) {
        showSuccess("Đã phê duyệt chỉnh sửa");
        removeCard(id);
      } else {
        setError(response.error?.detail || "Không thể phê duyệt");
      }
    } catch {
      setError("Lỗi kết nối. Vui lòng thử lại.");
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (id: number) => {
    if (!rejectReason.trim()) return;
    setProcessingId(id);
    try {
      const response = await apiClient.post(`/api/expert/corrections/${id}/reject`, {
        reason: rejectReason.trim(),
      });
      if (response.success) {
        showSuccess("Đã từ chối chỉnh sửa");
        removeCard(id);
        setRejectingId(null);
        setRejectReason("");
      } else {
        setError(response.error?.detail || "Không thể từ chối");
      }
    } catch {
      setError("Lỗi kết nối. Vui lòng thử lại.");
    } finally {
      setProcessingId(null);
    }
  };

  const totalPages = Math.ceil(total / perPage);
  const historyTotalPages = Math.ceil(historyTotal / perPage);

  if (authStatus === "loading") {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-emerald-200 border-t-emerald-600" />
      </div>
    );
  }

  if (!isExpertOrAdmin) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center px-6">
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-100 dark:bg-red-900/20">
          <ShieldAlert className="h-8 w-8 text-red-500" />
        </div>
        <h1 className="text-xl font-bold text-foreground">Không có quyền truy cập</h1>
        <p className="mt-2 text-sm text-muted-foreground max-w-md">
          Bạn cần quyền chuyên gia hoặc quản trị viên để truy cập trang này.
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-500 transition-colors"
        >
          Về trang chủ
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
      {/* Success toast */}
      {successMessage && (
        <div className="fixed top-4 right-4 z-50 flex items-center gap-2.5 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 shadow-lg animate-in slide-in-from-top-2 duration-300">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span className="text-sm font-semibold text-emerald-800">{successMessage}</span>
        </div>
      )}

      {/* Error toast */}
      {error && (
        <div className="fixed top-4 right-4 z-50 flex items-center gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 shadow-lg animate-in slide-in-from-top-2 duration-300">
          <XCircle className="h-4 w-4 text-red-600 shrink-0" />
          <span className="text-sm font-semibold text-red-800">{error}</span>
          <button onClick={() => setError(null)} className="ml-2 text-red-400 hover:text-red-600">
            &times;
          </button>
        </div>
      )}

      {/* Page header */}
      <div className="mb-8">
        <nav className="mb-4 flex items-center gap-2 text-sm" aria-label="Breadcrumb">
          <Link
            href="/"
            className="font-medium text-emerald-600 hover:text-emerald-700 transition-colors"
          >
            Trang chủ
          </Link>
          <span className="text-slate-300" aria-hidden="true">/</span>
          <span className="font-medium text-foreground">Chỉnh sửa mã HS</span>
        </nav>

        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Chỉnh sửa mã HS</h1>
          {activeTab === "pending" && !isLoading && (
            <span className="inline-flex items-center justify-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-bold text-amber-700 ring-1 ring-amber-200">
              {total}
            </span>
          )}
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Xem xét và phê duyệt hoặc từ chối các đề xuất chỉnh sửa mã HS.
        </p>
      </div>

      {/* Tab switcher */}
      <div className="mb-6 flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1 w-fit">
        <button
          onClick={() => setActiveTab("pending")}
          className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-all ${
            activeTab === "pending"
              ? "bg-white text-slate-900 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          <ClipboardList className="h-4 w-4" />
          Chờ duyệt
          {!isLoading && total > 0 && (
            <span className="inline-flex items-center justify-center rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">
              {total}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-all ${
            activeTab === "history"
              ? "bg-white text-slate-900 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          <History className="h-4 w-4" />
          Lịch sử
        </button>
      </div>

      {/* ── PENDING TAB ── */}
      {activeTab === "pending" && (
        <>
          {/* Loading skeletons */}
          {isLoading && (
            <div className="space-y-6">
              {[1, 2].map((i) => (
                <div key={i} className="rounded-2xl border border-slate-200 bg-white shadow-sm animate-pulse overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
                    <div className="h-4 w-1/2 rounded bg-slate-200 mb-2" />
                    <div className="h-3 w-1/4 rounded bg-slate-200" />
                  </div>
                  <div className="grid grid-cols-2 divide-x divide-slate-100">
                    <div className="p-6 space-y-3">
                      <div className="h-3 w-24 rounded bg-slate-200" />
                      <div className="h-7 w-36 rounded bg-slate-200" />
                      <div className="h-3 w-full rounded bg-slate-200" />
                      <div className="h-3 w-3/4 rounded bg-slate-200" />
                      <div className="mt-4 h-32 w-full rounded-xl bg-slate-100" />
                    </div>
                    <div className="p-6 space-y-3">
                      <div className="h-3 w-24 rounded bg-emerald-100" />
                      <div className="h-7 w-36 rounded bg-emerald-100" />
                      <div className="h-3 w-full rounded bg-emerald-100" />
                      <div className="h-3 w-3/4 rounded bg-emerald-100" />
                      <div className="mt-4 h-32 w-full rounded-xl bg-emerald-50" />
                    </div>
                  </div>
                  <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50 flex justify-between">
                    <div className="h-8 w-28 rounded-lg bg-slate-200" />
                    <div className="flex gap-2">
                      <div className="h-8 w-24 rounded-lg bg-slate-200" />
                      <div className="h-8 w-24 rounded-lg bg-emerald-200" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty state */}
          {!isLoading && corrections.length === 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-16 shadow-sm text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50">
                <Inbox className="h-7 w-7 text-emerald-500" />
              </div>
              <h2 className="text-lg font-semibold text-foreground">Không có chỉnh sửa chờ duyệt</h2>
              <p className="mt-1 text-sm text-muted-foreground">Tất cả đề xuất chỉnh sửa đã được xử lý.</p>
            </div>
          )}

          {/* Corrections list */}
          {!isLoading && corrections.length > 0 && (
            <div className="space-y-6">
              {corrections.map((correction) => (
                <div
                  key={correction.id}
                  className={`rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-300 overflow-hidden ${
                    dismissingId === correction.id
                      ? "opacity-0 scale-[0.98] translate-x-4"
                      : "opacity-100"
                  } hover:shadow-md hover:border-slate-300`}
                >
                  {/* ── Card header ── */}
                  <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/70">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2.5 mb-1.5">
                          <span className="text-[10px] font-bold uppercase tracking-[1.2px] text-slate-400">
                            Truy vấn
                          </span>
                          <Link
                            href={`/lookups/${correction.id}`}
                            className="text-[10px] font-mono font-semibold text-emerald-600 hover:text-emerald-700 hover:underline transition-colors"
                          >
                            #{correction.id}
                          </Link>
                        </div>
                        <p className="text-base font-semibold text-slate-900 leading-snug">
                          {correction.query_text}
                        </p>
                        {/* Meta row */}
                        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                          {correction.submitter_email && (
                            <span className="inline-flex items-center gap-1.5">
                              <User className="h-3 w-3" />
                              {correction.submitter_email}
                            </span>
                          )}
                          <span className="inline-flex items-center gap-1.5">
                            <Clock className="h-3 w-3" />
                            {new Date(correction.submitted_at).toLocaleDateString("vi-VN", {
                              year: "numeric",
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>
                        {/* Notes callout */}
                        {correction.notes && (
                          <div className="mt-3 flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5">
                            <MessageSquare className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                            <p className="text-sm font-medium text-amber-900 leading-snug">
                              {correction.notes}
                            </p>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <ArrowRightLeft className="h-4 w-4 text-slate-300" />
                        <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-[10px] font-bold text-amber-700 ring-1 ring-amber-200">
                          Chờ duyệt
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* ── Two-column comparison ── */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-100">
                    {/* Left column — current HS code */}
                    <div className="p-6">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[1px] text-slate-500">
                          <span className="inline-block h-2 w-2 rounded-full bg-slate-300" />
                          Mã HS hiện tại
                        </span>
                      </div>

                      {correction.matched_hs_code ? (
                        <>
                          <p className="font-mono text-2xl font-bold tracking-tight text-slate-800">
                            {correction.matched_hs_code}
                          </p>
                          {correction.matched_description_vn && (
                            <p className="mt-1.5 text-sm font-medium text-slate-600 leading-relaxed">
                              {correction.matched_description_vn}
                            </p>
                          )}
                          {correction.matched_description_en && (
                            <p className="mt-0.5 text-xs text-slate-400 leading-relaxed">
                              {correction.matched_description_en}
                            </p>
                          )}
                          <HSCodeTree hsCode={correction.matched_hs_code} />
                        </>
                      ) : (
                        <p className="text-sm text-slate-400 italic">Không có</p>
                      )}
                    </div>

                    {/* Right column — proposed correction */}
                    <div className="p-6 bg-emerald-50/40">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[1px] text-emerald-700">
                          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
                          Đề xuất chỉnh sửa
                        </span>
                      </div>

                      {correction.correct_hs_code ? (
                        <>
                          <p className="font-mono text-2xl font-bold tracking-tight text-emerald-700">
                            {correction.correct_hs_code}
                          </p>
                          {correction.correct_description_vn && (
                            <p className="mt-1.5 text-sm font-medium text-slate-700 leading-relaxed">
                              {correction.correct_description_vn}
                            </p>
                          )}
                          {correction.correct_description_en && (
                            <p className="mt-0.5 text-xs text-slate-400 leading-relaxed">
                              {correction.correct_description_en}
                            </p>
                          )}
                          <HSCodeTree hsCode={correction.correct_hs_code} />
                        </>
                      ) : (
                        <p className="text-sm text-slate-400 italic">Không có</p>
                      )}
                    </div>
                  </div>

                  {/* ── Reject reason form ── */}
                  {rejectingId === correction.id && (
                    <div className="px-6 py-4 border-t border-red-100 bg-red-50/40">
                      <label
                        htmlFor={`reject-reason-${correction.id}`}
                        className="block text-[10px] font-bold uppercase tracking-[0.8px] text-red-700 mb-2"
                      >
                        Lý do từ chối
                      </label>
                      <textarea
                        id={`reject-reason-${correction.id}`}
                        value={rejectReason}
                        onChange={(e) => setRejectReason(e.target.value)}
                        placeholder="Nhập lý do từ chối chỉnh sửa này..."
                        className="w-full rounded-lg border border-red-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-red-400 focus:ring-1 focus:ring-red-400 focus:outline-none"
                        rows={2}
                        maxLength={500}
                      />
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-[11px] text-slate-400">{rejectReason.length}/500</span>
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setRejectingId(null);
                              setRejectReason("");
                            }}
                            className="rounded-md px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 hover:bg-white transition-colors"
                          >
                            Hủy
                          </button>
                          <button
                            onClick={() => handleReject(correction.id)}
                            disabled={!rejectReason.trim() || processingId === correction.id}
                            className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {processingId === correction.id ? "Đang xử lý..." : "Xác nhận từ chối"}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* ── Action bar ── */}
                  <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50/70 flex items-center justify-between gap-3">
                    <Link
                      href={`/lookups/${correction.id}`}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-colors shadow-sm"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      Xem tra cứu
                    </Link>

                    {rejectingId !== correction.id && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setRejectingId(correction.id);
                            setRejectReason("");
                          }}
                          disabled={processingId === correction.id}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-white px-4 py-2 text-xs font-semibold text-red-600 hover:bg-red-50 hover:border-red-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          <XCircle className="h-3.5 w-3.5" />
                          Từ chối
                        </button>
                        <button
                          onClick={() => handleApprove(correction.id)}
                          disabled={processingId === correction.id}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                        >
                          {processingId === correction.id ? (
                            <>
                              <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                              Đang xử lý...
                            </>
                          ) : (
                            <>
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              Phê duyệt
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {!isLoading && totalPages > 1 && (
            <div className="mt-8 flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                Trang {page}/{totalPages} ({total} chỉnh sửa)
              </p>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="inline-flex items-center justify-center h-8 w-8 rounded-md border border-border text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  aria-label="Trang trước"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  let pageNum: number;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (page <= 3) {
                    pageNum = i + 1;
                  } else if (page >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = page - 2 + i;
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`inline-flex items-center justify-center h-8 w-8 rounded-md text-xs font-semibold transition-colors ${
                        page === pageNum
                          ? "bg-emerald-600 text-white shadow-sm"
                          : "border border-border text-muted-foreground hover:bg-secondary hover:text-foreground"
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="inline-flex items-center justify-center h-8 w-8 rounded-md border border-border text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  aria-label="Trang sau"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── HISTORY TAB ── */}
      {activeTab === "history" && (
        <>
          {/* Loading skeletons */}
          {isHistoryLoading && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="rounded-2xl border border-slate-200 bg-white shadow-sm animate-pulse overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
                    <div className="h-4 w-1/2 rounded bg-slate-200 mb-2" />
                    <div className="h-3 w-1/3 rounded bg-slate-200" />
                  </div>
                  <div className="grid grid-cols-2 divide-x divide-slate-100">
                    <div className="p-5 space-y-2">
                      <div className="h-3 w-20 rounded bg-slate-200" />
                      <div className="h-6 w-32 rounded bg-slate-200" />
                      <div className="h-3 w-full rounded bg-slate-200" />
                    </div>
                    <div className="p-5 space-y-2">
                      <div className="h-3 w-20 rounded bg-slate-200" />
                      <div className="h-6 w-32 rounded bg-slate-200" />
                      <div className="h-3 w-full rounded bg-slate-200" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty state */}
          {!isHistoryLoading && historyItems.length === 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-16 shadow-sm text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-50">
                <History className="h-7 w-7 text-slate-400" />
              </div>
              <h2 className="text-lg font-semibold text-foreground">Chưa có lịch sử</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Các chỉnh sửa đã được phê duyệt hoặc từ chối sẽ hiển thị ở đây.
              </p>
            </div>
          )}

          {/* History list */}
          {!isHistoryLoading && historyItems.length > 0 && (
            <div className="space-y-4">
              {historyItems.map((item) => {
                const isApproved = item.correction_status === "approved";
                return (
                  <div
                    key={item.id}
                    className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden hover:shadow-md hover:border-slate-300 transition-all"
                  >
                    {/* Card header */}
                    <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/70">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2.5 mb-1.5">
                            <span className="text-[10px] font-bold uppercase tracking-[1.2px] text-slate-400">
                              Truy vấn
                            </span>
                            <Link
                              href={`/lookups/${item.id}`}
                              className="text-[10px] font-mono font-semibold text-emerald-600 hover:text-emerald-700 hover:underline transition-colors"
                            >
                              #{item.id}
                            </Link>
                          </div>
                          <p className="text-base font-semibold text-slate-900 leading-snug">
                            {item.query_text}
                          </p>
                          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                            {item.submitter_email && (
                              <span className="inline-flex items-center gap-1.5">
                                <User className="h-3 w-3" />
                                {item.submitter_email}
                              </span>
                            )}
                            <span className="inline-flex items-center gap-1.5">
                              <Clock className="h-3 w-3" />
                              {new Date(item.submitted_at).toLocaleDateString("vi-VN", {
                                year: "numeric",
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                            {item.verified_at && (
                              <span className="inline-flex items-center gap-1.5">
                                <CheckCircle2 className="h-3 w-3" />
                                {isApproved ? "Phê duyệt" : "Từ chối"}{" "}
                                {new Date(item.verified_at).toLocaleDateString("vi-VN", {
                                  year: "numeric",
                                  month: "short",
                                  day: "numeric",
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })}
                              </span>
                            )}
                          </div>
                          {/* Rejection reason */}
                          {!isApproved && item.rejection_reason && (
                            <div className="mt-3 flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5">
                              <XCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                              <div>
                                <p className="text-[10px] font-bold uppercase tracking-[0.8px] text-red-500 mb-0.5">
                                  Lý do từ chối
                                </p>
                                <p className="text-sm font-medium text-red-900 leading-snug">
                                  {item.rejection_reason}
                                </p>
                              </div>
                            </div>
                          )}
                          {/* Notes */}
                          {item.notes && (
                            <div className="mt-2 flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5">
                              <MessageSquare className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                              <p className="text-sm font-medium text-amber-900 leading-snug">
                                {item.notes}
                              </p>
                            </div>
                          )}
                        </div>
                        <div className="shrink-0">
                          {isApproved ? (
                            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-2.5 py-0.5 text-[10px] font-bold text-emerald-700 ring-1 ring-emerald-200">
                              <CheckCircle2 className="h-3 w-3" />
                              Đã duyệt
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-2.5 py-0.5 text-[10px] font-bold text-red-700 ring-1 ring-red-200">
                              <XCircle className="h-3 w-3" />
                              Đã từ chối
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Two-column comparison */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-100">
                      {/* Left — original HS code */}
                      <div className="p-5">
                        <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[1px] text-slate-500 mb-3">
                          <span className="inline-block h-2 w-2 rounded-full bg-slate-300" />
                          Mã HS ban đầu
                        </span>
                        {item.matched_hs_code ? (
                          <>
                            <p className="font-mono text-xl font-bold tracking-tight text-slate-800">
                              {item.matched_hs_code}
                            </p>
                            {item.matched_description_vn && (
                              <p className="mt-1 text-sm text-slate-600 leading-relaxed">
                                {item.matched_description_vn}
                              </p>
                            )}
                            {item.matched_description_en && (
                              <p className="mt-0.5 text-xs text-slate-400 leading-relaxed">
                                {item.matched_description_en}
                              </p>
                            )}
                            <HSCodeTree hsCode={item.matched_hs_code} />
                          </>
                        ) : (
                          <p className="text-sm text-slate-400 italic">Không có</p>
                        )}
                      </div>

                      {/* Right — proposed correction */}
                      <div className={`p-5 ${isApproved ? "bg-emerald-50/40" : "bg-red-50/20"}`}>
                        <span
                          className={`inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[1px] mb-3 ${
                            isApproved ? "text-emerald-700" : "text-red-600"
                          }`}
                        >
                          <span
                            className={`inline-block h-2 w-2 rounded-full ${
                              isApproved ? "bg-emerald-500" : "bg-red-400"
                            }`}
                          />
                          Mã HS đề xuất
                        </span>
                        {item.correct_hs_code ? (
                          <>
                            <p
                              className={`font-mono text-xl font-bold tracking-tight ${
                                isApproved ? "text-emerald-700" : "text-red-600"
                              }`}
                            >
                              {item.correct_hs_code}
                            </p>
                            {item.correct_description_vn && (
                              <p className="mt-1 text-sm text-slate-600 leading-relaxed">
                                {item.correct_description_vn}
                              </p>
                            )}
                            {item.correct_description_en && (
                              <p className="mt-0.5 text-xs text-slate-400 leading-relaxed">
                                {item.correct_description_en}
                              </p>
                            )}
                            <HSCodeTree hsCode={item.correct_hs_code} />
                          </>
                        ) : (
                          <p className="text-sm text-slate-400 italic">Không có</p>
                        )}
                      </div>
                    </div>

                    {/* Footer */}
                    <div className="px-6 py-3 border-t border-slate-100 bg-slate-50/70">
                      <Link
                        href={`/lookups/${item.id}`}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-colors shadow-sm"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        Xem tra cứu
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* History pagination */}
          {!isHistoryLoading && historyTotalPages > 1 && (
            <div className="mt-8 flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                Trang {historyPage}/{historyTotalPages} ({historyTotal} chỉnh sửa)
              </p>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setHistoryPage((p) => Math.max(1, p - 1))}
                  disabled={historyPage <= 1}
                  className="inline-flex items-center justify-center h-8 w-8 rounded-md border border-border text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  aria-label="Trang trước"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                {Array.from({ length: Math.min(historyTotalPages, 5) }, (_, i) => {
                  let pageNum: number;
                  if (historyTotalPages <= 5) {
                    pageNum = i + 1;
                  } else if (historyPage <= 3) {
                    pageNum = i + 1;
                  } else if (historyPage >= historyTotalPages - 2) {
                    pageNum = historyTotalPages - 4 + i;
                  } else {
                    pageNum = historyPage - 2 + i;
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setHistoryPage(pageNum)}
                      className={`inline-flex items-center justify-center h-8 w-8 rounded-md text-xs font-semibold transition-colors ${
                        historyPage === pageNum
                          ? "bg-emerald-600 text-white shadow-sm"
                          : "border border-border text-muted-foreground hover:bg-secondary hover:text-foreground"
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                <button
                  onClick={() => setHistoryPage((p) => Math.min(historyTotalPages, p + 1))}
                  disabled={historyPage >= historyTotalPages}
                  className="inline-flex items-center justify-center h-8 w-8 rounded-md border border-border text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  aria-label="Trang sau"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
