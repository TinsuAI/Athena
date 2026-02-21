"use client";

import { RotateCcw, Trash2 } from "lucide-react";
import type { SearchHistoryItem } from "@/types/search-history";

interface HistoryCardProps {
  item: SearchHistoryItem;
  onReExecute: (query: string) => void;
  onDelete: (id: number) => void;
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

export function HistoryCard({ item, onReExecute, onDelete, isEven }: HistoryCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    onDelete(item.id);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onReExecute(item.query)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onReExecute(item.query);
        }
      }}
      className={`group flex items-center gap-4 px-5 py-3.5 border-b border-slate-100 cursor-pointer transition-all duration-150 hover:bg-emerald-50/50 hover:border-l-[3px] hover:border-l-emerald-500 ${
        isEven ? "bg-slate-50/60" : "bg-white"
      }`}
    >
      {/* Left: query + matched code */}
      <div className="min-w-0 flex-1">
        <div className="text-[13px] font-medium text-slate-900 truncate">
          {item.query}
        </div>
        {item.selected_hs_code ? (
          <div className="mt-1 flex items-baseline gap-2">
            <span className="shrink-0 font-mono text-[12px] font-bold text-emerald-700 tracking-tight">
              {item.selected_hs_code}
            </span>
            {item.selected_description_vn && (
              <span className="truncate text-[11px] text-slate-500">
                {item.selected_description_vn}
              </span>
            )}
          </div>
        ) : (
          <div className="mt-1 text-[12px] text-slate-400">
            Không có kết quả phù hợp
          </div>
        )}
      </div>

      {/* Right: date + re-execute */}
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-[11px] text-slate-400 font-medium whitespace-nowrap tabular-nums">
          {formatDate(item.created_at)}
        </span>
        <div
          className="flex items-center justify-center h-7 w-7 rounded-md text-slate-300 transition-all duration-150 hover:text-emerald-600 hover:bg-emerald-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40"
          aria-hidden="true"
        >
          <RotateCcw size={14} strokeWidth={1.8} />
        </div>
        <button
          type="button"
          onClick={handleDelete}
          aria-label="Xóa khỏi lịch sử"
          className="flex items-center justify-center h-7 w-7 rounded-md text-slate-300 transition-all duration-150 hover:text-red-500 hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400/40"
        >
          <Trash2 size={14} strokeWidth={1.8} />
        </button>
      </div>
    </div>
  );
}
