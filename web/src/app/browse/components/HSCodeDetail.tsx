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
      <h4 className="mb-1 text-sm font-semibold">{label}</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm" data-testid={`fta-table-${label.toLowerCase().replace(/\s+/g, "-")}`}>
          <thead>
            <tr className="border-b text-left text-muted-foreground">
              <th className="px-2 py-1.5 font-medium">Agreement</th>
              <th className="px-2 py-1.5 font-medium">Rate</th>
              <th className="px-2 py-1.5 font-medium">Conditions</th>
              <th className="px-2 py-1.5 font-medium">Year</th>
              <th className="px-2 py-1.5 font-medium">Legal Document</th>
            </tr>
          </thead>
          <tbody>
            {rates.map((rate, idx) => (
              <tr key={idx} className="border-b last:border-b-0">
                <td className="px-2 py-1.5 font-medium">
                  {rate.agreement_code}
                </td>
                <td className="px-2 py-1.5">
                  {formatRate(rate.preferential_rate)}
                </td>
                <td className="px-2 py-1.5 text-muted-foreground">
                  {rate.conditions || "—"}
                </td>
                <td className="px-2 py-1.5">{rate.rate_year ?? "—"}</td>
                <td className="px-2 py-1.5 text-muted-foreground">
                  {rate.legal_document || "—"}
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
      className="space-y-3 border-t bg-muted/30 px-4 py-3"
      data-testid="hs-code-detail"
    >
      {hsCode.description_en && (
        <div>
          <span className="text-xs font-medium text-muted-foreground">EN: </span>
          <span className="text-sm">{hsCode.description_en}</span>
        </div>
      )}

      <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        {hsCode.unit && (
          <div>
            <span className="font-medium text-muted-foreground">Unit: </span>
            {hsCode.unit}
          </div>
        )}
        {hsCode.special_consumption_tax && (
          <div>
            <span className="font-medium text-muted-foreground">
              Special Consumption Tax:{" "}
            </span>
            {hsCode.special_consumption_tax}
          </div>
        )}
        {hsCode.environmental_tax && (
          <div>
            <span className="font-medium text-muted-foreground">
              Environmental Tax:{" "}
            </span>
            {hsCode.environmental_tax}
          </div>
        )}
        {hsCode.vat_reduction && (
          <div>
            <span className="font-medium text-muted-foreground">
              VAT Reduction:{" "}
            </span>
            {hsCode.vat_reduction}
          </div>
        )}
      </div>

      {hsCode.policy_notes && (
        <div>
          <span className="text-xs font-medium text-muted-foreground">
            Policy Notes:{" "}
          </span>
          <span className="text-sm">{hsCode.policy_notes}</span>
        </div>
      )}

      <FTARateTable rates={importRates} label="Import FTA Rates" />
      <FTARateTable rates={exportRates} label="Export FTA Rates" />
    </div>
  );
}
