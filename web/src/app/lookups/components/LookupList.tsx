"use client";

import type { LookupListItem } from "@/types/lookup";

interface LookupListProps {
  items: LookupListItem[];
  onRowClick: (id: number) => void;
}

function ConfidenceBadge({ score }: { score: number | null }) {
  if (score === null) {
    return <span className="text-sm text-muted-foreground">—</span>;
  }

  let colorClass: string;
  if (score >= 80) {
    colorClass = "bg-green-100 text-green-800";
  } else if (score >= 50) {
    colorClass = "bg-yellow-100 text-yellow-800";
  } else {
    colorClass = "bg-red-100 text-red-800";
  }

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colorClass}`}
    >
      {Math.round(score)}%
    </span>
  );
}

function VerifiedBadge({ isVerified }: { isVerified: boolean }) {
  if (isVerified) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
        <svg
          className="h-3 w-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
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
    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
      Unverified
    </span>
  );
}

export function LookupList({ items, onRowClick }: LookupListProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="px-4 py-3 font-medium">Query</th>
            <th className="px-4 py-3 font-medium">Matched Code</th>
            <th className="px-4 py-3 font-medium">Confidence</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Date</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={item.id}
              onClick={() => onRowClick(item.id)}
              className="cursor-pointer border-b transition-colors hover:bg-muted/50"
            >
              <td className="px-4 py-3">
                <div className="max-w-xs truncate font-medium">
                  {item.query_text}
                </div>
                {item.query_language && (
                  <span className="text-xs text-muted-foreground">
                    {item.query_language.toUpperCase()}
                  </span>
                )}
              </td>
              <td className="px-4 py-3">
                {item.matched_hs_code ? (
                  <div>
                    <span className="font-mono font-medium">
                      {item.matched_hs_code}
                    </span>
                    {item.matched_description_vn && (
                      <div className="max-w-xs truncate text-xs text-muted-foreground">
                        {item.matched_description_vn}
                      </div>
                    )}
                  </div>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </td>
              <td className="px-4 py-3">
                <ConfidenceBadge score={item.confidence_score} />
              </td>
              <td className="px-4 py-3">
                <VerifiedBadge isVerified={item.is_verified} />
              </td>
              <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                {new Date(item.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
