"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import {
  Clock,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Search,
  ChevronLeft,
  ChevronRight,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import {
  getSearchHistory,
  deleteSearchHistoryItem,
  clearSearchHistory,
} from "@/lib/api";
import type { SearchHistoryItem } from "@/types/search-history";
import { HistoryCard } from "./components/HistoryCard";

const PAGE_SIZE = 20;

interface Toast {
  message: string;
  type: "success" | "error";
}

export default function HistoryPage() {
  const router = useRouter();
  const { data: session, status: authStatus } = useSession();
  const [items, setItems] = useState<SearchHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);
  const itemsRef = useRef<SearchHistoryItem[]>([]);
  const totalRef = useRef(0);

  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
  };

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getSearchHistory(PAGE_SIZE, offset);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Không thể tải lịch sử tìm kiếm. Vui lòng thử lại.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    if (authStatus === "loading") return;
    if (!session?.user) {
      setIsLoading(false);
      return;
    }
    fetchHistory();
  }, [authStatus, session?.user, fetchHistory]);

  const handleReExecute = (query: string) => {
    router.push(`/search?q=${encodeURIComponent(query)}`);
  };

  const handleDeleteItem = (id: number) => {
    // Save for rollback
    itemsRef.current = items;
    totalRef.current = total;
    // Optimistic removal
    setItems((prev) => prev.filter((item) => item.id !== id));
    setTotal((prev) => prev - 1);
    showToast("Đã xóa khỏi lịch sử", "success");

    deleteSearchHistoryItem(id).catch(() => {
      // Rollback on failure
      setItems(itemsRef.current);
      setTotal(totalRef.current);
      showToast("Không thể xóa. Vui lòng thử lại.", "error");
    });
  };

  const handleClearAll = async () => {
    setIsClearing(true);
    try {
      await clearSearchHistory();
      setItems([]);
      setTotal(0);
      setOffset(0);
      setShowClearConfirm(false);
      showToast("Lịch sử đã được xóa", "success");
    } catch {
      showToast("Không thể xóa. Vui lòng thử lại.", "error");
      setShowClearConfirm(false);
    } finally {
      setIsClearing(false);
    }
  };

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="max-w-[1600px] mx-auto px-7 py-6">
      {/* Toast notification */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 flex items-center gap-2.5 rounded-xl border px-4 py-3 shadow-lg animate-in slide-in-from-top-2 duration-300 ${
            toast.type === "success"
              ? "border-emerald-200 bg-emerald-50"
              : "border-red-200 bg-red-50"
          }`}
        >
          {toast.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
          )}
          <span
            className={`text-sm font-semibold ${
              toast.type === "success" ? "text-emerald-800" : "text-red-800"
            }`}
          >
            {toast.message}
          </span>
        </div>
      )}

      {/* Clear all confirmation dialog */}
      {showClearConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl mx-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-amber-50">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
              </div>
              <h2 className="text-[15px] font-semibold text-slate-900">
                Xóa tất cả lịch sử?
              </h2>
            </div>
            <p className="text-[13px] text-slate-500 mb-6">
              Bạn có chắc chắn? Điều này không thể hoàn tác.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="rounded-lg border border-slate-200 px-4 py-2 text-[13px] font-medium text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Hủy
              </button>
              <button
                onClick={handleClearAll}
                disabled={isClearing}
                className="rounded-lg bg-red-600 px-4 py-2 text-[13px] font-medium text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isClearing ? "Đang xóa..." : "Xóa tất cả"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Page header */}
      <div className="mb-5 flex items-center gap-3">
        <Clock className="h-5 w-5 text-emerald-600" />
        <div className="flex-1">
          <h1 className="text-[22px] font-bold text-slate-900 tracking-tight">
            Lịch sử tìm kiếm
          </h1>
          {!isLoading && !error && total > 0 && (
            <p className="mt-0.5 text-[13px] text-slate-500 font-medium">
              {total} tìm kiếm
            </p>
          )}
        </div>
        {!isLoading && !error && items.length > 0 && (
          <button
            onClick={() => setShowClearConfirm(true)}
            className="flex items-center gap-1.5 rounded-lg border border-red-200 px-3 py-2 text-[13px] font-medium text-red-600 hover:bg-red-50 transition-colors"
          >
            <Trash2 size={14} />
            Xóa tất cả
          </button>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div
          className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 flex items-start gap-3 text-[13px] font-medium text-red-700"
          role="alert"
        >
          <AlertCircle size={16} className="shrink-0 mt-0.5 text-red-500" />
          <div className="flex-1">
            <span>{error}</span>
            <button
              onClick={fetchHistory}
              className="ml-3 text-[13px] font-semibold text-red-600 hover:text-red-800 underline"
            >
              Thử lại
            </button>
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-slate-200 border-t-emerald-600" />
        </div>
      )}

      {/* History list */}
      {!isLoading && !error && items.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden">
          {/* Count badge header */}
          <div className="flex items-center gap-2.5 px-5 py-3 border-b border-slate-100 bg-slate-50/40">
            <Clock size={14} className="text-emerald-600" />
            <span className="text-[12px] font-semibold text-slate-600">
              {total} tìm kiếm
            </span>
          </div>

          {/* Card list */}
          {items.map((item, index) => (
            <HistoryCard
              key={item.id}
              item={item}
              onReExecute={handleReExecute}
              onDelete={handleDeleteItem}
              isEven={index % 2 === 1}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!isLoading && !error && totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-4">
          <button
            onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_SIZE))}
            disabled={offset === 0}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[13px] font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft size={14} />
            Trang trước
          </button>
          <span className="text-[13px] font-medium text-slate-500">
            Trang {currentPage} / {totalPages}
          </span>
          <button
            onClick={() => setOffset((prev) => prev + PAGE_SIZE)}
            disabled={offset + PAGE_SIZE >= total}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[13px] font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Trang sau
            <ChevronRight size={14} />
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && items.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-14 text-center shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)]">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100">
            <Clock size={24} className="text-slate-400" strokeWidth={1.5} />
          </div>
          <p className="text-[14px] font-semibold text-slate-700">
            Chưa có lịch sử tìm kiếm
          </p>
          <p className="mt-1 text-[13px] text-slate-400">
            Các tìm kiếm của bạn sẽ hiển thị tại đây.
          </p>
          <Link
            href="/search"
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-[13px] font-semibold text-white hover:bg-emerald-500 transition-colors duration-150"
          >
            <Search size={14} />
            Bắt đầu tìm kiếm
          </Link>
        </div>
      )}
    </div>
  );
}
