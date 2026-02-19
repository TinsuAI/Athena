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
  ArrowRight,
  Clock,
  User,
  FileText,
} from "lucide-react";
import { apiClient } from "@/lib/api";

interface PendingCorrectionItem {
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

interface PaginatedResponse {
  items: PendingCorrectionItem[];
  total: number;
  page: number;
  per_page: number;
}

export default function ExpertCorrectionsPage() {
  const { data: session, status: authStatus } = useSession();
  const userRole = (session?.user as { role?: string } | undefined)?.role;
  const isExpertOrAdmin = userRole === "expert" || userRole === "admin";

  const [corrections, setCorrections] = useState<PendingCorrectionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Track which card is being rejected (shows reason textarea)
  const [rejectingId, setRejectingId] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  // Track in-flight actions to disable buttons
  const [processingId, setProcessingId] = useState<number | null>(null);

  // Success message
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Track cards being dismissed for animation
  const [dismissingId, setDismissingId] = useState<number | null>(null);

  const fetchCorrections = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<PaginatedResponse>(
        `/api/expert/corrections?page=${page}&per_page=${perPage}`
      );
      if (response.success && response.data) {
        setCorrections(response.data.items);
        setTotal(response.data.total);
      } else {
        setError(
          response.error?.detail || "Khong the tai danh sach chinh sua"
        );
      }
    } catch {
      setError("Loi ket noi. Vui long thu lai.");
    } finally {
      setIsLoading(false);
    }
  }, [page, perPage]);

  useEffect(() => {
    if (isExpertOrAdmin) {
      fetchCorrections();
    }
  }, [isExpertOrAdmin, fetchCorrections]);

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
      const response = await apiClient.post(
        `/api/expert/corrections/${id}/approve`,
        {}
      );
      if (response.success) {
        showSuccess("Da phe duyet chinh sua");
        removeCard(id);
      } else {
        setError(response.error?.detail || "Khong the phe duyet");
      }
    } catch {
      setError("Loi ket noi. Vui long thu lai.");
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (id: number) => {
    if (!rejectReason.trim()) return;
    setProcessingId(id);
    try {
      const response = await apiClient.post(
        `/api/expert/corrections/${id}/reject`,
        { reason: rejectReason.trim() }
      );
      if (response.success) {
        showSuccess("Da tu choi chinh sua");
        removeCard(id);
        setRejectingId(null);
        setRejectReason("");
      } else {
        setError(response.error?.detail || "Khong the tu choi");
      }
    } catch {
      setError("Loi ket noi. Vui long thu lai.");
    } finally {
      setProcessingId(null);
    }
  };

  const totalPages = Math.ceil(total / perPage);

  // Auth loading
  if (authStatus === "loading") {
    return (
      <div className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-emerald-200 border-t-emerald-600 dark:border-emerald-800 dark:border-t-emerald-400" />
        </div>
      </div>
    );
  }

  // Access denied
  if (!isExpertOrAdmin) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-100 dark:bg-red-900/20">
            <ShieldAlert className="h-8 w-8 text-red-500 dark:text-red-400" />
          </div>
          <h1 className="text-xl font-bold text-foreground">
            Khong co quyen truy cap
          </h1>
          <p className="mt-2 text-sm text-muted-foreground max-w-md">
            Ban can quyen chuyen gia hoac quan tri vien de truy cap trang nay.
          </p>
          <Link
            href="/"
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-500 transition-colors"
          >
            Ve trang chu
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 py-8 sm:py-10">
      {/* Success toast */}
      {successMessage && (
        <div className="fixed top-4 right-4 z-50 flex items-center gap-2.5 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 shadow-lg dark:border-emerald-800 dark:bg-emerald-900/90 animate-in slide-in-from-top-2 duration-300">
          <CheckCircle2 className="h-4.5 w-4.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">
            {successMessage}
          </span>
        </div>
      )}

      {/* Error toast */}
      {error && (
        <div className="fixed top-4 right-4 z-50 flex items-center gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 shadow-lg dark:border-red-800 dark:bg-red-900/90 animate-in slide-in-from-top-2 duration-300">
          <XCircle className="h-4.5 w-4.5 text-red-600 dark:text-red-400 shrink-0" />
          <span className="text-sm font-semibold text-red-800 dark:text-red-200">
            {error}
          </span>
          <button
            onClick={() => setError(null)}
            className="ml-2 text-red-400 hover:text-red-600 dark:hover:text-red-300"
          >
            &times;
          </button>
        </div>
      )}

      {/* Page header */}
      <div className="mb-8">
        <nav className="mb-4 flex items-center gap-2 text-sm" aria-label="Breadcrumb">
          <Link
            href="/"
            className="font-medium text-emerald-600 hover:text-emerald-700 transition-colors dark:text-emerald-400 dark:hover:text-emerald-300"
          >
            Trang chu
          </Link>
          <span className="text-slate-300 dark:text-slate-600" aria-hidden="true">/</span>
          <span className="font-medium text-foreground">Duyet chinh sua</span>
        </nav>

        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Duyet chinh sua
          </h1>
          {!isLoading && (
            <span className="inline-flex items-center justify-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-bold text-amber-700 ring-1 ring-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:ring-amber-700">
              {total}
            </span>
          )}
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Xem xet va phe duyet hoac tu choi cac de xuat chinh sua ma HS.
        </p>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="rounded-xl border border-border bg-card p-6 shadow-sm animate-pulse"
            >
              <div className="h-5 w-3/4 rounded bg-muted mb-4" />
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="space-y-2">
                  <div className="h-3 w-20 rounded bg-muted" />
                  <div className="h-5 w-32 rounded bg-muted" />
                  <div className="h-3 w-48 rounded bg-muted" />
                </div>
                <div className="space-y-2">
                  <div className="h-3 w-20 rounded bg-muted" />
                  <div className="h-5 w-32 rounded bg-muted" />
                  <div className="h-3 w-48 rounded bg-muted" />
                </div>
              </div>
              <div className="flex gap-3 justify-end">
                <div className="h-9 w-24 rounded-lg bg-muted" />
                <div className="h-9 w-24 rounded-lg bg-muted" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && corrections.length === 0 && (
        <div className="rounded-xl border border-border bg-card p-12 shadow-sm text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-900/20">
            <Inbox className="h-7 w-7 text-emerald-500 dark:text-emerald-400" />
          </div>
          <h2 className="text-lg font-semibold text-foreground">
            Khong co chinh sua cho duyet
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Tat ca de xuat chinh sua da duoc xu ly.
          </p>
        </div>
      )}

      {/* Corrections list */}
      {!isLoading && corrections.length > 0 && (
        <div className="space-y-4">
          {corrections.map((correction) => (
            <div
              key={correction.id}
              className={`rounded-xl border border-border bg-card shadow-sm transition-all duration-300 ${
                dismissingId === correction.id
                  ? "opacity-0 scale-[0.98] translate-x-4"
                  : "opacity-100"
              } hover:shadow-md hover:border-emerald-200 dark:hover:border-emerald-800`}
            >
              <div className="p-5 sm:p-6">
                {/* Query text header */}
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[11px] font-bold uppercase tracking-[1.2px] text-muted-foreground">
                        Truy van
                      </span>
                      <span className="text-[10px] font-mono text-muted-foreground">
                        #{correction.id}
                      </span>
                    </div>
                    <p className="text-base font-semibold text-foreground leading-snug">
                      {correction.query_text}
                    </p>
                  </div>
                  <span className="shrink-0 inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-[10px] font-bold text-amber-700 ring-1 ring-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:ring-amber-700">
                    Cho duyet
                  </span>
                </div>

                {/* HS code comparison */}
                <div className="grid grid-cols-1 sm:grid-cols-[1fr,auto,1fr] gap-3 sm:gap-4 mb-5">
                  {/* Matched (current) */}
                  <div className="rounded-lg border border-border bg-secondary/30 p-4 dark:bg-muted/20">
                    <div className="text-[10px] font-bold uppercase tracking-[0.8px] text-muted-foreground mb-2">
                      Ma HS hien tai
                    </div>
                    {correction.matched_hs_code ? (
                      <>
                        <p className="font-mono text-lg font-bold tracking-tight text-foreground">
                          {correction.matched_hs_code}
                        </p>
                        {correction.matched_description_vn && (
                          <p className="mt-1 text-xs text-muted-foreground leading-relaxed line-clamp-2">
                            {correction.matched_description_vn}
                          </p>
                        )}
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">
                        Khong co
                      </p>
                    )}
                  </div>

                  {/* Arrow */}
                  <div className="hidden sm:flex items-center justify-center">
                    <ArrowRight className="h-5 w-5 text-emerald-500 dark:text-emerald-400" />
                  </div>

                  {/* Suggested correction */}
                  <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4 dark:border-emerald-800 dark:bg-emerald-900/10">
                    <div className="text-[10px] font-bold uppercase tracking-[0.8px] text-emerald-700 dark:text-emerald-400 mb-2">
                      De xuat chinh sua
                    </div>
                    {correction.correct_hs_code ? (
                      <>
                        <p className="font-mono text-lg font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
                          {correction.correct_hs_code}
                        </p>
                        {correction.correct_description_vn && (
                          <p className="mt-1 text-xs text-emerald-800/70 dark:text-emerald-300/70 leading-relaxed line-clamp-2">
                            {correction.correct_description_vn}
                          </p>
                        )}
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">
                        Khong co
                      </p>
                    )}
                  </div>
                </div>

                {/* Meta info row */}
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground mb-4">
                  {correction.submitter_email && (
                    <span className="inline-flex items-center gap-1.5">
                      <User className="h-3 w-3" />
                      {correction.submitter_email}
                    </span>
                  )}
                  <span className="inline-flex items-center gap-1.5">
                    <Clock className="h-3 w-3" />
                    {new Date(correction.submitted_at).toLocaleDateString(
                      "vi-VN",
                      {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      }
                    )}
                  </span>
                  {correction.notes && (
                    <span className="inline-flex items-center gap-1.5">
                      <FileText className="h-3 w-3" />
                      {correction.notes}
                    </span>
                  )}
                </div>

                {/* Reject reason textarea (shown when rejecting) */}
                {rejectingId === correction.id && (
                  <div className="mb-4 rounded-lg border border-red-200 bg-red-50/50 p-4 dark:border-red-800 dark:bg-red-900/10">
                    <label
                      htmlFor={`reject-reason-${correction.id}`}
                      className="block text-[10px] font-bold uppercase tracking-[0.8px] text-red-700 dark:text-red-400 mb-2"
                    >
                      Ly do tu choi
                    </label>
                    <textarea
                      id={`reject-reason-${correction.id}`}
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      placeholder="Nhap ly do tu choi chinh sua nay..."
                      className="w-full rounded-md border border-red-200 bg-white px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-red-400 focus:ring-1 focus:ring-red-400 focus:outline-none dark:border-red-700 dark:bg-slate-900 dark:focus:border-red-500 dark:focus:ring-red-500"
                      rows={2}
                      maxLength={500}
                    />
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-[11px] text-muted-foreground">
                        {rejectReason.length}/500
                      </span>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setRejectingId(null);
                            setRejectReason("");
                          }}
                          className="rounded-md px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                        >
                          Huy
                        </button>
                        <button
                          onClick={() => handleReject(correction.id)}
                          disabled={
                            !rejectReason.trim() ||
                            processingId === correction.id
                          }
                          className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {processingId === correction.id
                            ? "Dang xu ly..."
                            : "Xac nhan tu choi"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Action buttons */}
                {rejectingId !== correction.id && (
                  <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-border/50">
                    <button
                      onClick={() => {
                        setRejectingId(correction.id);
                        setRejectReason("");
                      }}
                      disabled={processingId === correction.id}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 px-4 py-2 text-xs font-semibold text-red-600 hover:bg-red-50 hover:border-red-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors dark:border-red-800 dark:text-red-400 dark:hover:bg-red-900/20 dark:hover:border-red-700"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                      Tu choi
                    </button>
                    <button
                      onClick={() => handleApprove(correction.id)}
                      disabled={processingId === correction.id}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                    >
                      {processingId === correction.id ? (
                        <>
                          <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                          Dang xu ly...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Phe duyet
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
            Trang {page}/{totalPages} ({total} chinh sua)
          </p>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="inline-flex items-center justify-center h-8 w-8 rounded-md border border-border text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              aria-label="Trang truoc"
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
    </div>
  );
}
