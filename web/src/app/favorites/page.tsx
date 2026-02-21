"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Star, Search, X, CheckCircle2, AlertCircle, Undo2, Trash2 } from "lucide-react";
import Link from "next/link";
import { useStore } from "@/lib/store";
import { getFavorites, removeFavorite, addFavorite } from "@/lib/api";
import { FavoriteCard } from "./components/FavoriteCard";
import type { Favorite } from "@/types/favorite";

interface UndoState {
  favorite: Favorite;
  timerId: ReturnType<typeof setTimeout>;
}

export default function FavoritesPage() {
  const router = useRouter();
  const { data: session, status: authStatus } = useSession();
  const favorites = useStore((s) => s.favorites);
  const setFavorites = useStore((s) => s.setFavorites);
  const removeFavoriteLocal = useStore((s) => s.removeFavoriteLocal);
  const addFavoriteLocal = useStore((s) => s.addFavoriteLocal);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [undoState, setUndoState] = useState<UndoState | null>(null);
  const [restoreToast, setRestoreToast] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");
  const undoRef = useRef<UndoState | null>(null);

  // Keep ref in sync for cleanup
  useEffect(() => {
    undoRef.current = undoState;
  }, [undoState]);

  // Fetch favorites on mount
  useEffect(() => {
    // Stop loading once auth status is resolved (not "loading")
    if (authStatus === "loading") return;
    if (!session?.user) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;

    async function fetchData() {
      try {
        const data = await getFavorites();
        if (!cancelled) {
          setFavorites(data);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error
              ? err.message
              : "Không thể tải danh sách yêu thích";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [authStatus, session?.user, setFavorites]);

  // Cleanup pending undo timer on unmount
  useEffect(() => {
    return () => {
      if (undoRef.current) {
        clearTimeout(undoRef.current.timerId);
      }
    };
  }, []);

  // Auto-dismiss restore toast
  useEffect(() => {
    if (!restoreToast) return;
    const timer = setTimeout(() => setRestoreToast(false), 2000);
    return () => clearTimeout(timer);
  }, [restoreToast]);

  const handleRemove = useCallback(
    (favoriteId: number) => {
      // If there's a pending undo, flush it immediately
      if (undoState) {
        clearTimeout(undoState.timerId);
        const pendingFav = undoState.favorite;
        setUndoState(null);
        // Fire-and-forget the pending delete
        removeFavorite(pendingFav.id).catch(() => {
          addFavoriteLocal(pendingFav);
        });
      }

      // Find the favorite object before removing
      const favoriteObj = favorites.find((f) => f.id === favoriteId);
      if (!favoriteObj) return;

      // Optimistic removal
      removeFavoriteLocal(favoriteId);

      // Start 5-second undo window
      const timerId = setTimeout(() => {
        setUndoState(null);
        // Actually delete from backend
        removeFavorite(favoriteId).catch(() => {
          // Revert on API failure
          addFavoriteLocal(favoriteObj);
        });
      }, 5000);

      setUndoState({ favorite: favoriteObj, timerId });
    },
    [favorites, undoState, removeFavoriteLocal, addFavoriteLocal]
  );

  const handleUndo = useCallback(() => {
    if (!undoState) return;

    // Cancel the pending delete
    clearTimeout(undoState.timerId);
    const restoredFavorite = undoState.favorite;

    // Re-add to store locally
    addFavoriteLocal(restoredFavorite);
    setUndoState(null);
    setRestoreToast(true);
  }, [undoState, addFavoriteLocal]);

  const handleCardClick = useCallback(
    (hsCode: string) => {
      router.push(`/search?q=${encodeURIComponent(hsCode)}`);
    },
    [router]
  );

  // Sort favorites by created_at descending (most recent first)
  const sortedFavorites = [...favorites].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  // Client-side filtering
  const filteredFavorites = useMemo(() => {
    if (!filterQuery.trim()) return sortedFavorites;
    const q = filterQuery.toLowerCase().trim();
    return sortedFavorites.filter(
      (f) =>
        f.hs_code.includes(q) ||
        f.description_vn.toLowerCase().includes(q) ||
        (f.notes && f.notes.toLowerCase().includes(q))
    );
  }, [sortedFavorites, filterQuery]);

  return (
    <div className="max-w-[1600px] mx-auto px-7 py-6">
      {/* Page header */}
      <div className="mb-5">
        <h1 className="text-[22px] font-bold text-slate-900 tracking-tight">
          Yêu thích
        </h1>
        <p className="mt-0.5 text-[13px] text-slate-500 font-medium">
          Mã HS đã lưu của bạn
        </p>
      </div>

      {/* Error state */}
      {error && (
        <div
          className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 flex items-start gap-3 text-[13px] font-medium text-red-700"
          role="alert"
        >
          <AlertCircle size={16} className="shrink-0 mt-0.5 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-slate-200 border-t-emerald-600" />
        </div>
      )}

      {/* Search input — only shown when there are favorites */}
      {!isLoading && !error && favorites.length > 0 && (
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Tìm trong yêu thích..."
            aria-label="Tìm trong yêu thích"
            className="w-full rounded-lg border border-slate-200 bg-white pl-10 pr-10 py-2.5 text-[13px] text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-300 transition-all"
          />
          {filterQuery && (
            <button
              onClick={() => setFilterQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 rounded-full bg-slate-200 hover:bg-slate-300 flex items-center justify-center transition-colors"
              aria-label="Xóa bộ lọc"
            >
              <X className="h-3 w-3 text-slate-600" />
            </button>
          )}
        </div>
      )}

      {/* Result count when filtering */}
      {!isLoading && !error && filterQuery.trim() && favorites.length > 0 && (
        <p className="mb-3 text-[12px] text-slate-500 font-medium">
          {filteredFavorites.length} / {favorites.length} mã yêu thích
        </p>
      )}

      {/* Favorites list */}
      {!isLoading && !error && filteredFavorites.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden">
          {/* Count badge */}
          <div className="flex items-center gap-2.5 px-5 py-3 border-b border-slate-100 bg-slate-50/40">
            <Star size={14} className="text-emerald-600" fill="currentColor" />
            <span className="text-[12px] font-semibold text-slate-600">
              {filteredFavorites.length} mã đã lưu
            </span>
          </div>

          {/* Card list */}
          {filteredFavorites.map((fav, index) => (
            <FavoriteCard
              key={fav.id}
              favorite={fav}
              onRemove={handleRemove}
              onClick={() => handleCardClick(fav.hs_code)}
              isEven={index % 2 === 1}
            />
          ))}
        </div>
      )}

      {/* Filtered empty state — no matches */}
      {!isLoading && !error && filteredFavorites.length === 0 && favorites.length > 0 && filterQuery.trim() && (
        <div className="rounded-xl border border-slate-200 bg-white p-10 text-center shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)]">
          <Search className="mx-auto h-8 w-8 text-slate-300 mb-3" />
          <p className="text-[14px] font-semibold text-slate-700">
            Không có mã yêu thích phù hợp với tìm kiếm
          </p>
          <button
            onClick={() => setFilterQuery("")}
            className="mt-3 text-[13px] font-medium text-emerald-600 hover:text-emerald-700 hover:underline"
          >
            Xóa bộ lọc
          </button>
        </div>
      )}

      {/* Empty state — no favorites at all */}
      {!isLoading && !error && favorites.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-14 text-center shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)]">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100">
            <Star size={24} className="text-slate-400" strokeWidth={1.5} />
          </div>
          <p className="text-[14px] font-semibold text-slate-700">
            Chưa có mã yêu thích
          </p>
          <p className="mt-1 text-[13px] text-slate-400">
            Lưu mã HS để truy cập nhanh.
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

      {/* Undo remove toast */}
      {undoState && (
        <div className="fixed top-4 right-4 z-50 flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 shadow-lg animate-in slide-in-from-top-2 duration-300">
          <Trash2 className="h-4 w-4 text-slate-500 shrink-0" />
          <span className="text-sm font-semibold text-slate-700">
            Đã xóa khỏi yêu thích
          </span>
          <button
            type="button"
            onClick={handleUndo}
            className="flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-white px-3 py-1.5 text-[12px] font-bold text-emerald-700 hover:bg-emerald-50 transition-colors duration-150"
          >
            <Undo2 size={12} />
            Hoàn tác
          </button>
        </div>
      )}

      {/* Restore success toast */}
      {restoreToast && (
        <div className="fixed top-4 right-4 z-50 flex items-center gap-2.5 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 shadow-lg animate-in slide-in-from-top-2 duration-300">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span className="text-sm font-semibold text-emerald-800">
            Đã khôi phục
          </span>
        </div>
      )}
    </div>
  );
}
