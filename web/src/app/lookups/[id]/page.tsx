"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { getLookupDetail } from "@/lib/api";
import { CorrectionButton } from "@/app/search/components/CorrectionButton";
import { CorrectionPanel } from "@/app/search/components/CorrectionPanel";
import { HSCodeTree } from "@/components/ui/HSCodeTree";
import { MarkdownContent } from "@/components/ui/MarkdownContent";
import type { LookupDetail } from "@/types/lookup";

function ConfidenceBadge({ score }: { score: number | null }) {
  if (score === null) return null;
  const rounded = Math.round(score);
  let colorClass = "bg-red-50 text-red-700 ring-1 ring-red-200 dark:bg-red-900/20 dark:text-red-300 dark:ring-red-800";
  if (rounded >= 80) {
    colorClass = "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:ring-emerald-800";
  } else if (rounded >= 50) {
    colorClass = "bg-amber-50 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-900/20 dark:text-amber-300 dark:ring-amber-800";
  }
  return (
    <span className={`relative group inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold tracking-wide cursor-help ${colorClass}`}>
      {rounded}%
      <span className="pointer-events-none absolute bottom-full right-0 mb-2 w-56 rounded-lg bg-slate-800 px-3 py-2 text-[11px] font-normal leading-relaxed text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
        Điểm tin cậy dựa trên phân tích ngữ nghĩa và đánh giá AI về mức độ phù hợp giữa mô tả sản phẩm và mã HS.
      </span>
    </span>
  );
}

function LanguageBadge({ lang }: { lang: string | null }) {
  if (!lang) return null;
  return (
    <span className="inline-flex items-center rounded-full bg-blue-50 text-blue-700 ring-1 ring-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:ring-blue-800 px-3 py-1 text-xs font-semibold tracking-wide">
      {lang.toUpperCase()}
    </span>
  );
}

export default function LookupDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  const [lookup, setLookup] = useState<LookupDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefetching, setIsRefetching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCorrectionPanel, setShowCorrectionPanel] = useState(false);
  const [showProcessLogs, setShowProcessLogs] = useState(false);
  const [showNlmResponse, setShowNlmResponse] = useState(false);
  const [expandedLogs, setExpandedLogs] = useState<Set<number>>(new Set());
  const { data: session } = useSession();
  const isAdmin = (session?.user as { role?: string })?.role === "admin";

  const fetchDetail = useCallback(async (isRefetch = false) => {
    if (isRefetch) {
      setIsRefetching(true);
    } else {
      setIsLoading(true);
    }
    setError(null);
    try {
      const data = await getLookupDetail(id);
      setLookup(data);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Không thể tải chi tiết tra cứu";
      setError(message);
    } finally {
      if (isRefetch) {
        setIsRefetching(false);
      } else {
        setIsLoading(false);
      }
    }
  }, [id]);

  useEffect(() => {
    if (!isNaN(id)) {
      fetchDetail();
    } else {
      setError("ID tra cứu không hợp lệ");
      setIsLoading(false);
    }
  }, [id, fetchDetail]);

  const handleCorrectionSuccess = () => {
    setShowCorrectionPanel(false);
    fetchDetail(true); // Pass true to indicate this is a refetch
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-10">
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-emerald-200 border-t-emerald-600 dark:border-emerald-800 dark:border-t-emerald-400" />
        </div>
      </div>
    );
  }

  if (error || !lookup) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-10">
        <div className="rounded-xl border border-border bg-card p-10 text-center shadow-sm">
          <p className="text-lg text-muted-foreground">
            {error || "Không tìm thấy bản ghi tra cứu"}
          </p>
          <Link
            href="/lookups"
            className="mt-4 inline-block text-sm font-medium text-emerald-600 hover:text-emerald-700 hover:underline dark:text-emerald-400 dark:hover:text-emerald-300"
          >
            Quay lại danh sách
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      {/* Refetching indicator */}
      {isRefetching && (
        <div className="fixed top-4 right-4 z-50 rounded-xl border border-border bg-card px-4 py-2.5 shadow-md flex items-center gap-2.5">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600 dark:border-emerald-800 dark:border-t-emerald-400" />
          <span className="text-sm font-medium text-muted-foreground">Đang tải lại...</span>
        </div>
      )}

      {/* Breadcrumb */}
      <nav className="mb-8 flex items-center gap-2 text-sm" aria-label="Breadcrumb">
        <Link href="/lookups" className="font-medium text-emerald-600 hover:text-emerald-700 transition-colors dark:text-emerald-400 dark:hover:text-emerald-300">
          Tra cứu
        </Link>
        <span className="text-slate-300 dark:text-slate-600" aria-hidden="true">/</span>
        <span className="font-medium text-foreground">Chi tiết #{lookup.id}</span>
      </nav>

      {/* Query Section */}
      <div className="mb-6 rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="mb-4 text-[11px] font-bold uppercase tracking-[1.2px] text-muted-foreground">
          Truy vấn tìm kiếm
        </h2>
        <div className="flex items-start gap-4">
          <blockquote className="flex-1 border-l-4 border-emerald-500 pl-5 text-lg italic text-foreground dark:border-emerald-400">
            {lookup.query_text}
          </blockquote>
          <div className="flex flex-col items-end gap-2.5">
            <LanguageBadge lang={lookup.query_language} />
            <span className="text-xs text-muted-foreground">
              {new Date(lookup.created_at).toLocaleDateString("vi-VN", {
                year: "numeric",
                month: "long",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        </div>
      </div>

      {/* Matched Result Section */}
      {lookup.matched_hs_code && (
        <div className="mb-6 rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-[11px] font-bold uppercase tracking-[1.2px] text-muted-foreground">
            Kết quả phù hợp
          </h2>
          <div className="flex items-start justify-between">
            <div>
              <p className="font-mono text-2xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
                {lookup.matched_hs_code.code}
              </p>
              {lookup.matched_hs_code.description_vn && (
                <p className="mt-1.5 text-sm font-medium text-foreground">{lookup.matched_hs_code.description_vn}</p>
              )}
              {lookup.matched_hs_code.description_en && (
                <p className="mt-0.5 text-sm text-muted-foreground">
                  {lookup.matched_hs_code.description_en}
                </p>
              )}
            </div>
            <div className="flex flex-col items-end gap-2.5">
              <ConfidenceBadge score={lookup.confidence_score} />
            </div>
          </div>
          <div className="mt-5 flex gap-4 text-sm">
            {lookup.matched_hs_code.duty_rate && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 font-mono text-xs font-semibold text-blue-700 ring-1 ring-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:ring-blue-800">
                <span className="font-sans font-medium opacity-70">NK</span>
                {lookup.matched_hs_code.duty_rate}
              </span>
            )}
            {lookup.matched_hs_code.vat_rate && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 font-mono text-xs font-semibold text-amber-700 ring-1 ring-amber-200 dark:bg-amber-900/20 dark:text-amber-300 dark:ring-amber-800">
                <span className="font-sans font-medium opacity-70">VAT</span>
                {lookup.matched_hs_code.vat_rate}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Classification Reasoning Section */}
      {lookup.classification_data && (
        <div className="mb-6 rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-5 text-[11px] font-bold uppercase tracking-[1.2px] text-muted-foreground">
            Phân tích phân loại
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-border bg-secondary/50 p-4 dark:bg-muted/30">
              <h3 className="mb-2 text-[10px] font-bold uppercase tracking-[0.8px] text-muted-foreground">
                Chất liệu
              </h3>
              <MarkdownContent
                content={lookup.classification_data.material || (lookup.classification_data as Record<string, string>).reasoning || ""}
                className="prose-p:my-0 text-sm"
              />
            </div>
            <div className="rounded-lg border border-border bg-secondary/50 p-4 dark:bg-muted/30">
              <h3 className="mb-2 text-[10px] font-bold uppercase tracking-[0.8px] text-muted-foreground">
                Công dụng
              </h3>
              <MarkdownContent
                content={lookup.classification_data.function || "Xem mục 'Phân tích chi tiết' để biết thêm"}
                className="prose-p:my-0 text-sm"
              />
            </div>
          </div>
        </div>
      )}

      {/* NotebookLM Raw Response Section */}
      {lookup.nlm_raw_response && (
        <div className="mb-6 rounded-xl border border-border bg-card shadow-sm">
          <button
            type="button"
            onClick={() => setShowNlmResponse(!showNlmResponse)}
            className="w-full flex items-center justify-between px-6 py-4 text-left"
            aria-expanded={showNlmResponse}
            aria-label="Phân tích chi tiết"
          >
            <span className="text-[11px] font-bold uppercase tracking-[1.2px] text-muted-foreground">
              Phân tích chi tiết
            </span>
            <span className="inline-block transition-transform duration-150 text-muted-foreground" style={{ transform: showNlmResponse ? "rotate(180deg)" : "rotate(0deg)" }}>
              &#9662;
            </span>
          </button>
          {showNlmResponse && (
            <div className="border-t border-border px-6 py-4">
              <MarkdownContent content={lookup.nlm_raw_response} />
            </div>
          )}
        </div>
      )}

      {/* Practical Notes Section */}
      {lookup.practical_notes && lookup.practical_notes.length > 0 && (
        <div className="mb-6 rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-[11px] font-bold uppercase tracking-[1.2px] text-muted-foreground">
            Ghi chú thực tế
          </h2>
          <ul className="space-y-2">
            {lookup.practical_notes.map((note, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500 dark:bg-emerald-400" />
                <MarkdownContent content={note} className="prose-p:my-0 prose-ul:my-0 prose-li:my-0" />
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* HS Code Hierarchy Tree */}
      {lookup.matched_hs_code && (
        <div className="mb-6">
          <HSCodeTree hsCode={lookup.matched_hs_code.code} />
        </div>
      )}

      {/* Process Logs Section (admin only) */}
      {isAdmin && lookup.process_logs && lookup.process_logs.length > 0 && (
        <div className="mb-6 rounded-xl border border-border bg-card shadow-sm">
          <button
            type="button"
            onClick={() => setShowProcessLogs(!showProcessLogs)}
            className="w-full flex items-center justify-between px-6 py-4 text-left"
            aria-expanded={showProcessLogs}
            aria-label={`Nhật ký xử lý, ${lookup.process_logs.length} bước`}
          >
            <span className="text-[11px] font-bold uppercase tracking-[1.2px] text-muted-foreground">
              Nhật ký xử lý
            </span>
            <span className="text-[11px] font-semibold text-muted-foreground">
              {lookup.process_logs.length} bước
              <span className="ml-2 inline-block transition-transform duration-150" style={{ transform: showProcessLogs ? "rotate(180deg)" : "rotate(0deg)" }}>
                &#9662;
              </span>
            </span>
          </button>
          {showProcessLogs && (
            <div className="border-t border-border">
              {lookup.process_logs.map((log, i) => (
                <div key={i} className="border-b border-border/50 last:border-b-0">
                  <button
                    type="button"
                    onClick={() => {
                      setExpandedLogs((prev) => {
                        const next = new Set(prev);
                        if (next.has(i)) next.delete(i);
                        else next.add(i);
                        return next;
                      });
                    }}
                    className="w-full flex items-center gap-3 px-6 py-3 text-left hover:bg-secondary/50"
                  >
                    <span className={`h-2 w-2 shrink-0 rounded-full ${
                      log.status === "completed" ? "bg-emerald-500" :
                      log.status === "failed" ? "bg-red-500" :
                      log.status === "skipped" ? "bg-slate-300" :
                      "bg-amber-400"
                    }`} />
                    <span className="text-xs font-semibold text-foreground w-28 shrink-0">{log.step}</span>
                    <span className="text-xs text-muted-foreground flex-1 truncate">{log.message}</span>
                    {typeof log.duration_ms === "number" && (
                      <span className="text-[11px] font-mono text-muted-foreground shrink-0">{log.duration_ms}ms</span>
                    )}
                    {log.details && (
                      <span className="text-[10px] text-muted-foreground shrink-0 transition-transform duration-150" style={{ transform: expandedLogs.has(i) ? "rotate(180deg)" : "rotate(0deg)" }}>
                        &#9662;
                      </span>
                    )}
                  </button>
                  {expandedLogs.has(i) && log.details && (
                    <pre className="mx-6 mb-3 p-3 bg-secondary/50 rounded-lg text-[11px] text-foreground font-mono overflow-x-auto max-h-60 overflow-y-auto whitespace-pre-wrap">
                      {JSON.stringify(log.details, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Correction Section */}
      <div className="mb-6 rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-3">
          <h2 className="text-[11px] font-bold uppercase tracking-[1.2px] text-muted-foreground">
            Hiệu chỉnh
          </h2>
          {lookup.correction_status === "pending" && (
            <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-semibold rounded-full ring-1 ring-amber-200">
              Đang chờ duyệt
            </span>
          )}
          {lookup.correction_status === "approved" && (
            <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs font-semibold rounded-full ring-1 ring-emerald-200">
              Đã phê duyệt
            </span>
          )}
          {lookup.correction_status === "rejected" && (
            <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-semibold rounded-full ring-1 ring-red-200">
              Đã từ chối
            </span>
          )}
        </div>
        {lookup.is_verified && lookup.correct_hs_code ? (
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:ring-emerald-800 px-3 py-1 text-sm font-semibold mb-4">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
              Đã hiệu chỉnh
            </span>
            <div className="mt-2 rounded-lg border border-emerald-200 bg-emerald-50/50 p-5 dark:border-emerald-800 dark:bg-emerald-900/10">
              <p className="font-mono text-lg font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
                {lookup.correct_hs_code.code}
              </p>
              {lookup.correct_hs_code.description_vn && (
                <p className="mt-1.5 text-sm font-medium text-foreground">
                  {lookup.correct_hs_code.description_vn}
                </p>
              )}
              {lookup.correct_hs_code.description_en && (
                <p className="mt-0.5 text-sm text-muted-foreground">
                  {lookup.correct_hs_code.description_en}
                </p>
              )}
              <div className="mt-4 flex gap-3 text-sm">
                {lookup.correct_hs_code.duty_rate && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 font-mono text-xs font-semibold text-blue-700 ring-1 ring-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:ring-blue-800">
                    <span className="font-sans font-medium opacity-70">NK</span>
                    {lookup.correct_hs_code.duty_rate}
                  </span>
                )}
                {lookup.correct_hs_code.vat_rate && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 font-mono text-xs font-semibold text-amber-700 ring-1 ring-amber-200 dark:bg-amber-900/20 dark:text-amber-300 dark:ring-amber-800">
                    <span className="font-sans font-medium opacity-70">VAT</span>
                    {lookup.correct_hs_code.vat_rate}
                  </span>
                )}
              </div>
              {lookup.verified_at && (
                <p className="mt-4 text-xs text-muted-foreground">
                  Ngày xác minh:{" "}
                  {new Date(lookup.verified_at).toLocaleDateString("vi-VN", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              )}
              {lookup.verified_by_user_id && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Người xác minh: ID #{lookup.verified_by_user_id}
                </p>
              )}
              {lookup.notes && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Ghi chú: {lookup.notes}
                </p>
              )}
            </div>
          </div>
        ) : lookup.correction_status === "pending" ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-4 dark:border-amber-800 dark:bg-amber-900/10">
            <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
              Có một đề xuất hiệu chỉnh đang chờ xét duyệt bởi chuyên gia.
            </p>
            {lookup.notes && (
              <p className="mt-2 text-xs text-amber-700 dark:text-amber-400">
                Ghi chú: {lookup.notes}
              </p>
            )}
          </div>
        ) : lookup.correction_status === "rejected" ? (
          <div className="rounded-lg border border-red-200 bg-red-50/50 p-4 dark:border-red-800 dark:bg-red-900/10">
            <p className="text-sm font-medium text-red-800 dark:text-red-300">
              Đề xuất hiệu chỉnh đã bị từ chối.
            </p>
            {lookup.rejection_reason && (
              <p className="mt-2 text-xs text-red-700 dark:text-red-400">
                Lý do: {lookup.rejection_reason}
              </p>
            )}
            {lookup.notes && (
              <p className="mt-1 text-xs text-red-600/70 dark:text-red-400/70">
                Ghi chú ban đầu: {lookup.notes}
              </p>
            )}
          </div>
        ) : (
          <CorrectionButton
            lookupId={lookup.id}
            matchedHsCode={lookup.matched_hs_code?.code ?? ""}
            matchedDescription={lookup.matched_hs_code?.description_vn ?? ""}
            onCorrect={() => setShowCorrectionPanel(true)}
          />
        )}
      </div>

      {/* Correction Panel */}
      <CorrectionPanel
        isOpen={showCorrectionPanel}
        onClose={handleCorrectionSuccess}
        lookupId={lookup.id}
        currentHsCode={lookup.matched_hs_code?.code ?? ""}
        currentDescription={lookup.matched_hs_code?.description_vn ?? ""}
      />
    </div>
  );
}
