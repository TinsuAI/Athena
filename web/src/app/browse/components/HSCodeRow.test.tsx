import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { HSCodeRow } from "./HSCodeRow";
import type { BrowseHSCodeItem } from "@/types/browse";

const mockHSCode: BrowseHSCodeItem = {
  id: 1,
  code: "01012100",
  description_vn: "Ngựa thuần chủng để nhân giống",
  description_en: "Pure-bred breeding horses",
  unit: "con",
  duty_rate: 5.0,
  vat_rate: 10.0,
  export_duty_rate: null,
  special_consumption_tax: "20%",
  environmental_tax: null,
  vat_reduction: "8%",
  policy_notes: "Policy note here",
  fta_rates: [
    {
      agreement_code: "CPTPP",
      preferential_rate: 0.0,
      conditions: "Form CPTPP",
      rate_year: null,
      is_export: false,
      legal_document: "NĐ 57/2019",
      effective_date: "2019-01-14",
    },
    {
      agreement_code: "EVFTA",
      preferential_rate: 2.5,
      conditions: "Form EUR.1",
      rate_year: null,
      is_export: false,
      legal_document: "NĐ 111/2020",
      effective_date: "2020-08-01",
    },
    {
      agreement_code: "RCEP-CN",
      preferential_rate: 3.0,
      conditions: null,
      rate_year: 2024,
      is_export: true,
      legal_document: "NĐ 129/2022",
      effective_date: "2022-01-01",
    },
  ],
};

describe("HSCodeRow", () => {
  it("renders HS code in monospace", () => {
    render(
      <HSCodeRow hsCode={mockHSCode} isExpanded={false} onToggle={vi.fn()} />
    );

    const codeEl = screen.getByTestId("hs-code-value");
    expect(codeEl).toHaveTextContent("01012100");
    expect(codeEl.className).toContain("font-mono");
  });

  it("displays inline duty rates", () => {
    render(
      <HSCodeRow hsCode={mockHSCode} isExpanded={false} onToggle={vi.fn()} />
    );

    expect(screen.getByTestId("duty-rate")).toHaveTextContent("5%");
    expect(screen.getByTestId("vat-rate")).toHaveTextContent("10%");
    expect(screen.getByTestId("export-rate")).toHaveTextContent("—");
  });

  it("displays description", () => {
    render(
      <HSCodeRow hsCode={mockHSCode} isExpanded={false} onToggle={vi.fn()} />
    );

    expect(
      screen.getByText("Ngựa thuần chủng để nhân giống")
    ).toBeInTheDocument();
  });

  it("calls onToggle when clicked", () => {
    const onToggle = vi.fn();
    render(
      <HSCodeRow hsCode={mockHSCode} isExpanded={false} onToggle={onToggle} />
    );

    fireEvent.click(screen.getByRole("button"));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("does not show detail panel when collapsed", () => {
    render(
      <HSCodeRow hsCode={mockHSCode} isExpanded={false} onToggle={vi.fn()} />
    );

    expect(screen.queryByTestId("hs-code-detail")).not.toBeInTheDocument();
  });

  it("shows detail panel when expanded", () => {
    render(
      <HSCodeRow hsCode={mockHSCode} isExpanded={true} onToggle={vi.fn()} />
    );

    expect(screen.getByTestId("hs-code-detail")).toBeInTheDocument();
  });

  describe("expanded detail content", () => {
    it("shows English description", () => {
      render(
        <HSCodeRow hsCode={mockHSCode} isExpanded={true} onToggle={vi.fn()} />
      );

      expect(
        screen.getByText("Pure-bred breeding horses")
      ).toBeInTheDocument();
    });

    it("shows unit", () => {
      render(
        <HSCodeRow hsCode={mockHSCode} isExpanded={true} onToggle={vi.fn()} />
      );

      expect(screen.getByText("con")).toBeInTheDocument();
    });

    it("shows special consumption tax when present", () => {
      render(
        <HSCodeRow hsCode={mockHSCode} isExpanded={true} onToggle={vi.fn()} />
      );

      expect(screen.getByText("20%")).toBeInTheDocument();
    });

    it("shows VAT reduction when present", () => {
      render(
        <HSCodeRow hsCode={mockHSCode} isExpanded={true} onToggle={vi.fn()} />
      );

      expect(screen.getByText("8%")).toBeInTheDocument();
    });

    it("shows policy notes when present", () => {
      render(
        <HSCodeRow hsCode={mockHSCode} isExpanded={true} onToggle={vi.fn()} />
      );

      expect(screen.getByText("Policy note here")).toBeInTheDocument();
    });

    it("shows import FTA rates table", () => {
      render(
        <HSCodeRow hsCode={mockHSCode} isExpanded={true} onToggle={vi.fn()} />
      );

      expect(screen.getByText("Import FTA Rates")).toBeInTheDocument();
      expect(screen.getByText("CPTPP")).toBeInTheDocument();
      expect(screen.getByText("EVFTA")).toBeInTheDocument();
    });

    it("shows export FTA rates table", () => {
      render(
        <HSCodeRow hsCode={mockHSCode} isExpanded={true} onToggle={vi.fn()} />
      );

      expect(screen.getByText("Export FTA Rates")).toBeInTheDocument();
      expect(screen.getByText("RCEP-CN")).toBeInTheDocument();
    });

    it("separates import and export FTA rates correctly", () => {
      render(
        <HSCodeRow hsCode={mockHSCode} isExpanded={true} onToggle={vi.fn()} />
      );

      const importTable = screen.getByTestId("fta-table-import-fta-rates");
      const exportTable = screen.getByTestId("fta-table-export-fta-rates");

      // Import table should have CPTPP and EVFTA
      expect(importTable).toHaveTextContent("CPTPP");
      expect(importTable).toHaveTextContent("EVFTA");
      expect(importTable).not.toHaveTextContent("RCEP-CN");

      // Export table should have RCEP-CN
      expect(exportTable).toHaveTextContent("RCEP-CN");
      expect(exportTable).not.toHaveTextContent("CPTPP");
    });
  });

  describe("null value handling", () => {
    it("displays dash for null export duty rate", () => {
      render(
        <HSCodeRow hsCode={mockHSCode} isExpanded={false} onToggle={vi.fn()} />
      );

      expect(screen.getByTestId("export-rate")).toHaveTextContent("—");
    });

    it("does not show environmental tax when null", () => {
      render(
        <HSCodeRow hsCode={mockHSCode} isExpanded={true} onToggle={vi.fn()} />
      );

      expect(screen.queryByText("Environmental Tax:")).not.toBeInTheDocument();
    });
  });
});
