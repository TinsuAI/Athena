"use client";

import type { LookupListItem } from "@/types/lookup";

interface LookupListProps {
  items: LookupListItem[];
  onRowClick: (id: number) => void;
}

function ConfidenceBadge({ score }: { score: number | null }) {
  if (score === null) {
    return <span className="text-sm text-slate-400">—</span>;
  }

  let classes: string;
  if (score >= 80) {
    classes = "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200";
  } else if (score >= 50) {
    classes = "bg-amber-50 text-amber-700 ring-1 ring-amber-200";
  } else {
    classes = "bg-red-50 text-red-700 ring-1 ring-red-200";
  }

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold font-mono tracking-tight ${classes}`}
    >
      {Math.round(score)}%
    </span>
  );
}

function VerifiedBadge({ isVerified }: { isVerified: boolean }) {
  if (isVerified) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700 ring-1 ring-emerald-200">
        <svg
          className="h-3 w-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M5 13l4 4L19 7"
          />
        </svg>
        Verified
      </span>
    );
  }

  return (
    <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-500">
      Unverified
    </span>
  );
}

export function LookupList({ items, onRowClick }: LookupListProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[#0f172a]">
            <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-[0.08em] text-white/85">
              Query
            </th>
            <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-[0.08em] text-white/85">
              Matched Code
            </th>
            <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-[0.08em] text-white/85">
              Confidence
            </th>
            <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-[0.08em] text-white/85">
              Status
            </th>
            <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-[0.08em] text-white/85">
              Date
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr
              key={item.id}
              onClick={() => onRowClick(item.id)}
              className={`group cursor-pointer border-b border-slate-100 transition-all duration-150 hover:bg-emerald-50/50 hover:border-l-[3px] hover:border-l-emerald-500 ${
                index % 2 === 1 ? "bg-slate-50/60" : "bg-white"
              }`}
            >
              <td className="px-5 py-3.5">
                <div className="max-w-xs truncate font-medium text-slate-900">
                  {item.query_text}
                </div>
                {item.query_language && (
                  <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                    {item.query_language}
                  </span>
                )}
              </td>
              <td className="px-5 py-3.5">
                {item.matched_hs_code ? (
                  <div>
                    <span className="font-mono text-[13px] font-bold text-emerald-700 tracking-tight">
                      {item.matched_hs_code}
                    </span>
                    {item.matched_description_vn && (
                      <div className="max-w-xs truncate text-[11px] text-slate-500 mt-0.5">
                        {item.matched_description_vn}
                      </div>
                    )}
                  </div>
                ) : (
                  <span className="text-slate-400">—</span>
                )}
              </td>
              <td className="px-5 py-3.5">
                <ConfidenceBadge score={item.confidence_score} />
              </td>
              <td className="px-5 py-3.5">
                <VerifiedBadge isVerified={item.is_verified} />
              </td>
              <td className="px-5 py-3.5 whitespace-nowrap text-[12px] text-slate-500 font-medium">
                {new Date(item.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
