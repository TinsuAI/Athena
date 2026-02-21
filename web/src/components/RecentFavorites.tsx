"use client";

import { useMemo, useState } from "react";
import { Star, ChevronDown, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useStore } from "@/lib/store";

interface RecentFavoritesProps {
  maxItems?: number;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  onItemClick?: (hsCode: string) => void;
}

export function RecentFavorites({
  maxItems = 5,
  collapsible = false,
  defaultCollapsed = false,
  onItemClick,
}: RecentFavoritesProps) {
  const favorites = useStore((s) => s.favorites);
  const [isExpanded, setIsExpanded] = useState(!defaultCollapsed);

  // Sort by created_at desc (most recent first) before slicing — addFavoriteLocal
  // appends to end, so store order may not reflect recency.
  const recentFavorites = useMemo(
    () =>
      [...favorites]
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, maxItems),
    [favorites, maxItems]
  );

  if (recentFavorites.length === 0) return null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      {/* Header */}
      {collapsible ? (
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center gap-2 px-4 py-3 text-left bg-slate-50/80"
          aria-expanded={isExpanded}
        >
          <Star className="h-3.5 w-3.5 text-emerald-600" fill="currentColor" />
          <span className="text-[12px] font-bold text-slate-700 uppercase tracking-wider flex-1">
            Yêu thích gần đây
          </span>
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-slate-400" />
          )}
        </button>
      ) : (
        <div className="flex items-center gap-2 px-4 py-3 bg-slate-50/80">
          <Star className="h-3.5 w-3.5 text-emerald-600" fill="currentColor" />
          <span className="text-[12px] font-bold text-slate-700 uppercase tracking-wider">
            Yêu thích gần đây
          </span>
        </div>
      )}

      {/* Items */}
      {(!collapsible || isExpanded) && (
        <>
          <div className="divide-y divide-slate-100">
            {recentFavorites.map((fav) => (
              <button
                key={fav.id}
                type="button"
                onClick={() => onItemClick?.(fav.hs_code)}
                className="w-full text-left px-4 py-2.5 hover:bg-emerald-50/50 transition-colors"
              >
                <div className="font-mono text-[12px] font-bold text-emerald-700">
                  {fav.hs_code}
                </div>
                <div className="text-[11px] text-slate-500 truncate">
                  {fav.description_vn}
                </div>
              </button>
            ))}
          </div>
          {/* View all link */}
          <div className="px-4 py-2.5 border-t border-slate-100">
            <Link
              href="/favorites"
              className="text-[11px] font-semibold text-emerald-600 hover:text-emerald-700 hover:underline"
            >
              Xem tất cả →
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
