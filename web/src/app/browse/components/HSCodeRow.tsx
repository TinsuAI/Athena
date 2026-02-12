"use client";

import { ChevronDown } from "lucide-react";
import type { BrowseHSCodeItem } from "@/types/browse";
import { HSCodeDetail } from "./HSCodeDetail";

interface HSCodeRowProps {
  hsCode: BrowseHSCodeItem;
  isExpanded: boolean;
  onToggle: () => void;
  highlighted?: boolean;
}

function formatRate(rate: number | string | null): string {
  if (rate === null || rate === undefined) return "\u2014";
  if (typeof rate === "number") return `${rate}%`;
  return rate;
}

function getRateClass(rate: number | string | null, type: "import" | "vat" | "export"): string {
  const formatted = formatRate(rate);
  if (formatted === "0%") return "text-accent-foreground bg-emerald-50";
  if (type === "export") return "text-muted-foreground bg-transparent";
  if (type === "import") return "text-blue-800 bg-blue-50";
  if (type === "vat") return "text-amber-800 bg-amber-50";
  return "text-muted-foreground";
}

export function HSCodeRow({ hsCode, isExpanded, onToggle, highlighted }: HSCodeRowProps) {
  return (
    <div
      id={`hs-code-${hsCode.code}`}
      data-testid={`hs-code-row-${hsCode.code}`}
      className={`border-b border-border/30 last:border-b-0 ${highlighted ? "animate-highlight-fade" : ""}`}
    >
      <button
        onClick={onToggle}
        className={`relative grid w-full grid-cols-[1fr_90px_70px_70px_36px] items-center gap-2 px-5 py-[9px] pl-[134px] text-left transition-all hover:bg-emerald-50/50 before:absolute before:left-0 before:top-0 before:bottom-0 before:w-[3px] before:transition-colors ${
          isExpanded
            ? "bg-accent before:bg-primary"
            : "even:bg-secondary/50 before:bg-transparent hover:before:bg-primary"
        }`}
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="font-mono text-xs font-bold text-accent-foreground whitespace-nowrap tracking-tight" data-testid="hs-code-value">
            {hsCode.code}
          </span>
          <span className="truncate text-xs text-foreground">{hsCode.description_vn}</span>
        </div>
        <span className={`font-mono text-xs font-semibold text-center py-[3px] rounded ${getRateClass(hsCode.duty_rate, "import")}`} data-testid="duty-rate">
          {formatRate(hsCode.duty_rate)}
        </span>
        <span className={`font-mono text-xs font-semibold text-center py-[3px] rounded ${getRateClass(hsCode.vat_rate, "vat")}`} data-testid="vat-rate">
          {formatRate(hsCode.vat_rate)}
        </span>
        <span className={`font-mono text-xs font-semibold text-center py-[3px] rounded ${getRateClass(hsCode.export_duty_rate, "export")}`} data-testid="export-rate">
          {formatRate(hsCode.export_duty_rate)}
        </span>
        <span className={`flex items-center justify-center text-muted-foreground transition-all duration-200 ${isExpanded ? "text-primary rotate-180" : ""}`}>
          <ChevronDown className="h-3 w-3" />
        </span>
      </button>
      {isExpanded && <HSCodeDetail hsCode={hsCode} />}
    </div>
  );
}
