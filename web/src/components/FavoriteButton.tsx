"use client";

import { useState, useEffect, useCallback } from "react";
import { Star, Loader2, CheckCircle2 } from "lucide-react";
import { useStore } from "@/lib/store";
import { addFavorite, removeFavorite } from "@/lib/api";

interface FavoriteButtonProps {
  hsCodeId: number;
  size?: "sm" | "md";
}

export function FavoriteButton({ hsCodeId, size = "md" }: FavoriteButtonProps) {
  const favoriteIds = useStore((s) => s.favoriteIds);
  const favorites = useStore((s) => s.favorites);
  const addFavoriteLocal = useStore((s) => s.addFavoriteLocal);
  const removeFavoriteLocal = useStore((s) => s.removeFavoriteLocal);

  const [isToggling, setIsToggling] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const isFavorited = favoriteIds.includes(hsCodeId);

  // Auto-dismiss toast
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2000);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleToggle = useCallback(
    async (e: React.MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();
      if (isToggling) return;

      setIsToggling(true);

      if (isFavorited) {
        // Remove flow — find the favorite object to get its ID
        const favoriteObj = favorites.find((f) => f.hs_code_id === hsCodeId);
        if (!favoriteObj) {
          setIsToggling(false);
          return;
        }

        // Optimistic removal
        removeFavoriteLocal(favoriteObj.id);

        try {
          await removeFavorite(favoriteObj.id);
          setToast("Đã xóa khỏi yêu thích");
        } catch {
          // Revert on error
          addFavoriteLocal(favoriteObj);
          setToast(null);
        } finally {
          setIsToggling(false);
        }
      } else {
        // Add flow — optimistic update with temporary placeholder
        const tempFavorite = {
          id: -Date.now(),
          user_id: 0,
          hs_code_id: hsCodeId,
          hs_code: "",
          description_vn: "",
          notes: null,
          created_at: new Date().toISOString(),
        };
        addFavoriteLocal(tempFavorite);

        try {
          const newFavorite = await addFavorite(hsCodeId);
          // Replace temporary with real server response
          removeFavoriteLocal(tempFavorite.id);
          addFavoriteLocal(newFavorite);
          setToast("Đã thêm vào yêu thích");
        } catch {
          // Revert optimistic add on error
          removeFavoriteLocal(tempFavorite.id);
        } finally {
          setIsToggling(false);
        }
      }
    },
    [
      hsCodeId,
      isFavorited,
      isToggling,
      favorites,
      addFavoriteLocal,
      removeFavoriteLocal,
    ]
  );

  const iconSize = size === "sm" ? 14 : 18;

  return (
    <>
      <button
        type="button"
        onClick={handleToggle}
        disabled={isToggling}
        aria-label={isFavorited ? "Xóa khỏi yêu thích" : "Thêm vào yêu thích"}
        aria-pressed={isFavorited}
        className={`
          group relative inline-flex items-center justify-center
          rounded-full transition-all duration-200 ease-out
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/40 focus-visible:ring-offset-1
          disabled:pointer-events-none
          ${size === "sm" ? "h-7 w-7" : "h-9 w-9"}
          ${isFavorited
            ? "text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
            : "text-slate-300 hover:text-slate-400 hover:bg-slate-50"
          }
        `}
      >
        {isToggling ? (
          <Loader2
            size={iconSize}
            className="animate-spin text-slate-400"
          />
        ) : (
          <Star
            size={iconSize}
            fill={isFavorited ? "currentColor" : "none"}
            strokeWidth={isFavorited ? 0 : 1.5}
            className={`
              transition-all duration-200
              ${isFavorited
                ? "drop-shadow-[0_0_3px_rgba(5,150,105,0.3)] scale-100"
                : "group-hover:scale-110"
              }
            `}
          />
        )}
      </button>

      {/* Toast notification */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 flex items-center gap-2.5 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 shadow-lg animate-in slide-in-from-top-2 duration-300">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span className="text-sm font-semibold text-emerald-800">
            {toast}
          </span>
        </div>
      )}
    </>
  );
}
