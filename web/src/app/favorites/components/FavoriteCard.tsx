"use client";

import { FileText, Trash2 } from "lucide-react";
import type { Favorite } from "@/types/favorite";

interface FavoriteCardProps {
  favorite: Favorite;
  onRemove: (id: number) => void;
  onClick: () => void;
  isEven: boolean;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function FavoriteCard({
  favorite,
  onRemove,
  onClick,
  isEven,
}: FavoriteCardProps) {
  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    onRemove(favorite.id);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
      className={`group flex items-center gap-4 px-5 py-3.5 border-b border-slate-100 cursor-pointer transition-all duration-150 hover:bg-emerald-50/50 hover:border-l-[3px] hover:border-l-emerald-500 ${
        isEven ? "bg-slate-50/60" : "bg-white"
      }`}
    >
      {/* Left: HS code + description */}
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2.5">
          <span className="shrink-0 font-mono text-[13px] font-bold text-emerald-700 tracking-tight group-hover:bg-emerald-100/60 group-hover:px-1.5 group-hover:py-0.5 group-hover:-mx-1.5 group-hover:rounded transition-all duration-150">
            {favorite.hs_code}
          </span>
          <span className="truncate text-[13px] text-slate-700 font-medium">
            {favorite.description_vn}
          </span>
        </div>

        {/* Notes preview — only when notes exist */}
        {favorite.notes && (
          <div className="mt-1 flex items-center gap-1.5 min-w-0">
            <FileText
              size={12}
              className="shrink-0 text-slate-400"
              strokeWidth={1.8}
            />
            <span className="truncate text-[12px] italic text-slate-400">
              {favorite.notes}
            </span>
          </div>
        )}
      </div>

      {/* Right: date + remove */}
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-[11px] text-slate-400 font-medium whitespace-nowrap tabular-nums">
          {formatDate(favorite.created_at)}
        </span>
        <button
          type="button"
          onClick={handleRemove}
          aria-label="Xóa khỏi yêu thích"
          className="flex items-center justify-center h-7 w-7 rounded-md text-slate-300 transition-all duration-150 hover:text-red-500 hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400/40"
        >
          <Trash2 size={14} strokeWidth={1.8} />
        </button>
      </div>
    </div>
  );
}
