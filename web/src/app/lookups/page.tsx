"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getLookups } from "@/lib/api";
import { LookupList } from "./components/LookupList";
import type { LookupListItem } from "@/types/lookup";

type VerifiedFilter = "all" | "verified" | "unverified";

const PAGE_SIZE = 20;

export default function LookupsPage() {
  const router = useRouter();
  const [items, setItems] = useState<LookupListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [verifiedFilter, setVerifiedFilter] = useState<VerifiedFilter>("all");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLookups = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const verified =
        verifiedFilter === "all"
          ? undefined
          : verifiedFilter === "verified";

      const data = await getLookups(PAGE_SIZE, offset, verified);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Không thể tải lịch sử tra cứu";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [offset, verifiedFilter]);

  useEffect(() => {
    fetchLookups();
  }, [fetchLookups]);

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const handlePrevious = () => {
    if (offset >= PAGE_SIZE) {
      setOffset(offset - PAGE_SIZE);
    }
  };

  const handleNext = () => {
    if (offset + PAGE_SIZE < total) {
      setOffset(offset + PAGE_SIZE);
    }
  };

  const handleFilterChange = (filter: VerifiedFilter) => {
    setVerifiedFilter(filter);
    setOffset(0);
  };

  const handleRowClick = (id: number) => {
    router.push(`/lookups/${id}`);
  };

  const filterButtons: { label: string; value: VerifiedFilter }[] = [
    { label: "Tất cả", value: "all" },
    { label: "Đã xác minh", value: "verified" },
    { label: "Chưa xác minh", value: "unverified" },
  ];

  return (
    <div className="max-w-[1600px] mx-auto px-7 py-6">
      {/* Page header */}
      <div className="mb-5">
        <h1 className="text-[22px] font-bold text-slate-900 tracking-tight">
          Lịch sử tra cứu
        </h1>
        <p className="mt-0.5 text-[13px] text-slate-500 font-medium">
          Xem lại các tra cứu mã HS và trạng thái xác minh
        </p>
      </div>

      {/* Filter pills */}
      <div className="mb-4 flex gap-2">
        {filterButtons.map((btn) => (
          <button
            key={btn.value}
            onClick={() => handleFilterChange(btn.value)}
            className={`rounded-full px-4 py-1.5 text-[12px] font-semibold transition-all duration-150 ${
              verifiedFilter === btn.value
                ? "bg-emerald-600 text-white shadow-sm shadow-emerald-200"
                : "bg-white text-slate-600 border border-slate-200 hover:border-emerald-300 hover:text-emerald-700 hover:bg-emerald-50/50"
            }`}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div
          className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-[13px] font-medium text-red-700"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-slate-200 border-t-emerald-600" />
        </div>
      )}

      {/* Results */}
      {!isLoading && !error && items.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden">
          <LookupList items={items} onRowClick={handleRowClick} />

          {/* Pagination */}
          <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3">
            <button
              onClick={handlePrevious}
              disabled={offset === 0}
              className="rounded-md border border-slate-200 bg-white px-3.5 py-1.5 text-[12px] font-semibold text-slate-600 transition-all duration-150 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-300 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-white disabled:hover:text-slate-600 disabled:hover:border-slate-200"
            >
              &larr; Trước
            </button>
            <span className="text-[11px] text-slate-400 font-medium">
              Trang {currentPage} / {totalPages}
            </span>
            <button
              onClick={handleNext}
              disabled={offset + PAGE_SIZE >= total}
              className="rounded-md border border-slate-200 bg-white px-3.5 py-1.5 text-[12px] font-semibold text-slate-600 transition-all duration-150 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-300 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-white disabled:hover:text-slate-600 disabled:hover:border-slate-200"
            >
              Sau &rarr;
            </button>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && items.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-14 text-center shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)]">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100">
            <svg className="h-6 w-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
          </div>
          <p className="text-[14px] font-semibold text-slate-700">
            Không tìm thấy tra cứu nào
          </p>
          <p className="mt-1 text-[13px] text-slate-400">
            Bắt đầu tra cứu mã HS để xây dựng lịch sử.
          </p>
        </div>
      )}
    </div>
  );
}
