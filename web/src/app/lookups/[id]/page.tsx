"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getLookupDetail } from "@/lib/api";
import { CorrectionButton } from "@/app/search/components/CorrectionButton";
import { CorrectionPanel } from "@/app/search/components/CorrectionPanel";
import type { LookupDetail } from "@/types/lookup";

function ConfidenceBadge({ score }: { score: number | null }) {
  if (score === null) return null;
  const rounded = Math.round(score);
  let colorClass = "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300";
  if (rounded >= 80) {
    colorClass = "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
  } else if (rounded >= 50) {
    colorClass = "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300";
  }
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClass}`}>
      {rounded}%
    </span>
  );
}

function LanguageBadge({ lang }: { lang: string | null }) {
  if (!lang) return null;
  return (
    <span className="inline-flex items-center rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 px-2.5 py-0.5 text-xs font-medium">
      {lang.toUpperCase()}
    </span>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === "completed") return <span className="text-green-600">&#10003;</span>;
  if (status === "failed") return <span className="text-red-600">&#10007;</span>;
  if (status === "skipped") return <span className="text-gray-400">&#8212;</span>;
  return <span className="text-blue-500">&#9679;</span>;
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
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
        </div>
      </div>
    );
  }

  if (error || !lookup) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <div className="rounded-lg border bg-card p-8 text-center">
          <p className="text-lg text-muted-foreground">
            {error || "Không tìm thấy bản ghi tra cứu"}
          </p>
          <Link
            href="/lookups"
            className="mt-4 inline-block text-sm text-primary hover:underline"
          >
            Quay lại danh sách
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      {/* Refetching indicator */}
      {isRefetching && (
        <div className="fixed top-4 right-4 rounded-lg border bg-card px-4 py-2 shadow-lg flex items-center gap-2">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted border-t-primary" />
          <span className="text-sm text-muted-foreground">Đang tải lại...</span>
        </div>
      )}

      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-muted-foreground" aria-label="Breadcrumb">
        <Link href="/lookups" className="hover:text-foreground transition-colors">
          Tra cứu
        </Link>
        <span className="mx-2" aria-hidden="true">&gt;</span>
        <span className="text-foreground">Chi tiết #{lookup.id}</span>
      </nav>

      {/* Query Section */}
      <div className="mb-6 rounded-lg border bg-card p-6">
        <h2 className="text-sm font-medium text-muted-foreground mb-3">
          Truy vấn tìm kiếm
        </h2>
        <div className="flex items-start gap-3">
          <blockquote className="flex-1 border-l-4 border-primary/30 pl-4 text-lg italic">
            {lookup.query_text}
          </blockquote>
          <div className="flex flex-col items-end gap-2">
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
        <div className="mb-6 rounded-lg border bg-card p-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-3">
            Kết quả phù hợp
          </h2>
          <div className="flex items-start justify-between">
            <div>
              <p className="font-mono text-2xl font-bold text-primary">
                {lookup.matched_hs_code.code}
              </p>
              {lookup.matched_hs_code.description_vn && (
                <p className="mt-1 text-sm">{lookup.matched_hs_code.description_vn}</p>
              )}
              {lookup.matched_hs_code.description_en && (
                <p className="mt-0.5 text-sm text-muted-foreground">
                  {lookup.matched_hs_code.description_en}
                </p>
              )}
            </div>
            <div className="flex flex-col items-end gap-2">
              <ConfidenceBadge score={lookup.confidence_score} />
              <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
                {lookup.search_method}
              </span>
            </div>
          </div>
          <div className="mt-4 flex gap-6 text-sm">
            {lookup.matched_hs_code.duty_rate && (
              <div>
                <span className="text-muted-foreground">Thuế NK:</span>{" "}
                <span className="font-medium">{lookup.matched_hs_code.duty_rate}</span>
              </div>
            )}
            {lookup.matched_hs_code.vat_rate && (
              <div>
                <span className="text-muted-foreground">VAT:</span>{" "}
                <span className="font-medium">{lookup.matched_hs_code.vat_rate}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Classification Reasoning Section */}
      {lookup.classification_data && (
        <div className="mb-6 rounded-lg border bg-card p-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-3">
            Phân tích phân loại
          </h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-semibold uppercase text-muted-foreground mb-1">
                Chất liệu
              </h3>
              <p className="text-sm">{lookup.classification_data.material}</p>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase text-muted-foreground mb-1">
                Công dụng
              </h3>
              <p className="text-sm">{lookup.classification_data.function}</p>
            </div>
          </div>
        </div>
      )}

      {/* Practical Notes Section */}
      {lookup.practical_notes && lookup.practical_notes.length > 0 && (
        <div className="mb-6 rounded-lg border bg-card p-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-3">
            Ghi chú thực tế
          </h2>
          <ul className="list-disc list-inside space-y-1 text-sm">
            {lookup.practical_notes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Process Log Section */}
      {lookup.process_logs && lookup.process_logs.length > 0 && (
        <div className="mb-6 rounded-lg border bg-card p-6">
          <button
            type="button"
            onClick={() => setShowProcessLogs(!showProcessLogs)}
            className="flex w-full items-center justify-between text-sm font-medium text-muted-foreground"
            aria-expanded={showProcessLogs}
            aria-label={`Nhật ký xử lý, ${lookup.process_logs.length} bước, ${showProcessLogs ? "thu gọn" : "mở rộng"}`}
          >
            <span>Nhật ký xử lý ({lookup.process_logs.length} bước)</span>
            <span className="text-xs" aria-hidden="true">{showProcessLogs ? "Thu gọn" : "Mở rộng"}</span>
          </button>
          {showProcessLogs && (
            <div className="mt-4 space-y-2">
              {lookup.process_logs.map((log, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 rounded-md bg-muted/50 px-3 py-2 text-sm"
                >
                  <StatusIcon status={log.status} />
                  <span className="font-medium min-w-[120px]">{log.step}</span>
                  <span className="flex-1 text-muted-foreground truncate">
                    {log.message}
                  </span>
                  {typeof log.duration_ms === "number" && (
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {log.duration_ms}ms
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Correction Section */}
      <div className="mb-6 rounded-lg border bg-card p-6">
        <h2 className="text-sm font-medium text-muted-foreground mb-3">
          Hiệu chỉnh
        </h2>
        {lookup.is_verified && lookup.correct_hs_code ? (
          <div>
            <span className="inline-flex items-center rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 px-3 py-1 text-sm font-medium mb-3">
              Đã hiệu chỉnh
            </span>
            <div className="mt-2 rounded-md bg-muted/50 p-4">
              <p className="font-mono text-lg font-bold text-primary">
                {lookup.correct_hs_code.code}
              </p>
              {lookup.correct_hs_code.description_vn && (
                <p className="mt-1 text-sm">
                  {lookup.correct_hs_code.description_vn}
                </p>
              )}
              {lookup.correct_hs_code.description_en && (
                <p className="mt-0.5 text-sm text-muted-foreground">
                  {lookup.correct_hs_code.description_en}
                </p>
              )}
              <div className="mt-3 flex gap-6 text-sm">
                {lookup.correct_hs_code.duty_rate && (
                  <div>
                    <span className="text-muted-foreground">Thuế NK:</span>{" "}
                    <span className="font-medium">{lookup.correct_hs_code.duty_rate}</span>
                  </div>
                )}
                {lookup.correct_hs_code.vat_rate && (
                  <div>
                    <span className="text-muted-foreground">VAT:</span>{" "}
                    <span className="font-medium">{lookup.correct_hs_code.vat_rate}</span>
                  </div>
                )}
              </div>
              {lookup.verified_at && (
                <p className="mt-3 text-xs text-muted-foreground">
                  Ngày xác minh:{" "}
                  {new Date(lookup.verified_at).toLocaleDateString("vi-VN", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              )}
              {lookup.notes && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Ghi chú: {lookup.notes}
                </p>
              )}
            </div>
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
