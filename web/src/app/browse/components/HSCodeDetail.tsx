"use client";

import type { BrowseHSCodeItem, BrowseFTARateItem } from "@/types/browse";

interface HSCodeDetailProps {
  hsCode: BrowseHSCodeItem;
}

function formatRate(rate: number | string | null): string {
  if (rate === null || rate === undefined) return "—";
  if (typeof rate === "number") return `${rate}%`;
  return rate;
}

function FTARateTable({
  rates,
  label,
}: {
  rates: BrowseFTARateItem[];
  label: string;
}) {
  if (rates.length === 0) return null;

  return (
    <div>
      <div className="flex items-center gap-2 mb-2.5 text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
        {label}
        <span className="flex-1 h-px bg-border" />
      </div>
      <div className="overflow-x-auto rounded-md border border-border overflow-hidden">
        <table className="w-full text-xs" data-testid={`fta-table-${label.toLowerCase().replace(/\s+/g, "-")}`}>
          <thead>
            <tr className="bg-slate-900 text-white/85">
              <th className="px-2 sm:px-3.5 py-2 sm:py-2.5 text-left text-[9px] sm:text-[10px] font-bold uppercase tracking-wider border-b-2 border-primary whitespace-nowrap">Hiệp định</th>
              <th className="px-2 sm:px-3.5 py-2 sm:py-2.5 text-left text-[9px] sm:text-[10px] font-bold uppercase tracking-wider border-b-2 border-primary whitespace-nowrap">Thuế suất</th>
              <th className="px-2 sm:px-3.5 py-2 sm:py-2.5 text-left text-[9px] sm:text-[10px] font-bold uppercase tracking-wider border-b-2 border-primary whitespace-nowrap">Điều kiện</th>
              <th className="px-2 sm:px-3.5 py-2 sm:py-2.5 text-left text-[9px] sm:text-[10px] font-bold uppercase tracking-wider border-b-2 border-primary whitespace-nowrap">Năm</th>
              <th className="px-2 sm:px-3.5 py-2 sm:py-2.5 text-left text-[9px] sm:text-[10px] font-bold uppercase tracking-wider border-b-2 border-primary whitespace-nowrap">Văn bản pháp lý</th>
            </tr>
          </thead>
          <tbody>
            {rates.map((rate, idx) => (
              <tr key={idx} className="border-b border-border/50 last:border-b-0 hover:bg-emerald-50/50 even:bg-secondary/50 transition-colors">
                <td className="px-2 sm:px-3.5 py-2 sm:py-2.5">
                  <span className="font-mono font-bold text-accent-foreground text-[11.5px] tracking-wide">
                    {rate.agreement_code}
                  </span>
                </td>
                <td className="px-2 sm:px-3.5 py-2 sm:py-2.5">
                  <span className="font-mono font-bold text-primary">
                    {formatRate(rate.preferential_rate)}
                  </span>
                </td>
                <td className="px-2 sm:px-3.5 py-2 sm:py-2.5 text-muted-foreground text-[10px] sm:text-[11.5px]">
                  {rate.conditions ? (
                    <span className="font-medium text-foreground bg-amber-100 px-1.5 py-0.5 rounded text-[10.5px]">
                      {rate.conditions}
                    </span>
                  ) : (
                    "\u2014"
                  )}
                </td>
                <td className="px-2 sm:px-3.5 py-2 sm:py-2.5">{rate.rate_year ?? "\u2014"}</td>
                <td className="px-2 sm:px-3.5 py-2 sm:py-2.5">
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {rate.legal_document || "\u2014"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function HSCodeDetail({ hsCode }: HSCodeDetailProps) {
  const importRates = hsCode.fta_rates.filter((r) => !r.is_export);
  const exportRates = hsCode.fta_rates.filter((r) => r.is_export);

  return (
    <div
      className="bg-gradient-to-b from-accent to-card border-t border-primary/20 pl-10 pr-3 py-3 sm:px-5 sm:py-5 sm:pl-[134px] space-y-3 sm:space-y-4 animate-in slide-in-from-top-2 duration-250"
      data-testid="hs-code-detail"
    >
      {/* Detail fields grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        {hsCode.description_en && (
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Mô tả tiếng Anh</span>
            <div className="text-xs sm:text-[13px] font-medium text-foreground px-2.5 sm:px-3 py-2 bg-card rounded-md border border-border">
              {hsCode.description_en}
            </div>
          </div>
        )}
        {hsCode.unit && (
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Đơn vị tính</span>
            <div className="text-[13px] font-medium text-foreground px-3 py-2 bg-card rounded-md border border-border font-mono">
              {hsCode.unit}
            </div>
          </div>
        )}
        {hsCode.special_consumption_tax && (
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Thuế tiêu thụ đặc biệt</span>
            <div className="text-xs sm:text-[13px] font-medium text-foreground px-2.5 sm:px-3 py-2 bg-card rounded-md border border-border">
              {hsCode.special_consumption_tax}
            </div>
          </div>
        )}
        {hsCode.environmental_tax && (
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Thuế bảo vệ môi trường</span>
            <div className="text-xs sm:text-[13px] font-medium text-foreground px-2.5 sm:px-3 py-2 bg-card rounded-md border border-border">
              {hsCode.environmental_tax}
            </div>
          </div>
        )}
        {hsCode.vat_reduction && (
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Giảm thuế GTGT</span>
            <div className="text-xs sm:text-[13px] font-medium text-foreground px-2.5 sm:px-3 py-2 bg-card rounded-md border border-border">
              {hsCode.vat_reduction}
            </div>
          </div>
        )}
      </div>

      {hsCode.policy_notes && (
        <div className="flex flex-col gap-1">
          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Ghi chú chính sách</span>
          <div className="text-xs sm:text-[13px] text-foreground px-2.5 sm:px-3 py-2 bg-card rounded-md border border-border">
            {hsCode.policy_notes}
          </div>
        </div>
      )}

      <FTARateTable rates={importRates} label="Thuế ưu đãi NK theo FTA" />
      <FTARateTable rates={exportRates} label="Thuế ưu đãi XK theo FTA" />
    </div>
  );
}
