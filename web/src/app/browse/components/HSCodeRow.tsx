"use client";

import { ChevronRight, ChevronDown } from "lucide-react";
import type { BrowseHSCodeItem } from "@/types/browse";
import { HSCodeDetail } from "./HSCodeDetail";

interface HSCodeRowProps {
  hsCode: BrowseHSCodeItem;
  isExpanded: boolean;
  onToggle: () => void;
}

function formatRate(rate: number | string | null): string {
  if (rate === null || rate === undefined) return "—";
  if (typeof rate === "number") return `${rate}%`;
  return rate;
}

export function HSCodeRow({ hsCode, isExpanded, onToggle }: HSCodeRowProps) {
  return (
    <div data-testid={`hs-code-row-${hsCode.code}`}>
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-2 px-2 py-1.5 text-left text-sm hover:bg-muted/50 transition-colors"
        aria-expanded={isExpanded}
      >
        {isExpanded ? (
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        )}
        <span className="font-mono text-sm font-medium w-20" data-testid="hs-code-value">
          {hsCode.code}
        </span>
        <span className="flex-1 truncate text-sm">{hsCode.description_vn}</span>
        <span className="shrink-0 w-14 text-right text-sm tabular-nums" data-testid="duty-rate">
          {formatRate(hsCode.duty_rate)}
        </span>
        <span className="shrink-0 w-14 text-right text-sm tabular-nums" data-testid="vat-rate">
          {formatRate(hsCode.vat_rate)}
        </span>
        <span className="shrink-0 w-14 text-right text-sm tabular-nums" data-testid="export-rate">
          {formatRate(hsCode.export_duty_rate)}
        </span>
      </button>
      {isExpanded && <HSCodeDetail hsCode={hsCode} />}
    </div>
  );
}
