import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { HistoryCard } from "./HistoryCard";
import type { SearchHistoryItem } from "@/types/search-history";

const baseItem: SearchHistoryItem = {
  id: 1,
  user_id: 10,
  query: "laptop xách tay",
  selected_hs_code_id: 100,
  selected_hs_code: "84713000",
  selected_description_vn: "Máy tính xách tay có khối lượng không quá 10 kg",
  created_at: "2026-02-21T10:30:00+07:00",
};

describe("HistoryCard", () => {
  it("renders query text", () => {
    render(
      <HistoryCard
        item={baseItem}
        onReExecute={vi.fn()}
        onDelete={vi.fn()}
        isEven={false}
      />
    );
    expect(screen.getByText("laptop xách tay")).toBeInTheDocument();
  });

  it("renders matched HS code in monospace font", () => {
    render(
      <HistoryCard
        item={baseItem}
        onReExecute={vi.fn()}
        onDelete={vi.fn()}
        isEven={false}
      />
    );
    const hsCode = screen.getByText("84713000");
    expect(hsCode).toBeInTheDocument();
    expect(hsCode.className).toContain("font-mono");
  });

  it("renders matched description when present", () => {
    render(
      <HistoryCard
        item={baseItem}
        onReExecute={vi.fn()}
        onDelete={vi.fn()}
        isEven={false}
      />
    );
    expect(
      screen.getByText("Máy tính xách tay có khối lượng không quá 10 kg")
    ).toBeInTheDocument();
  });

  it("shows no-match text when selected_hs_code is null", () => {
    const noMatchItem: SearchHistoryItem = {
      ...baseItem,
      selected_hs_code_id: null,
      selected_hs_code: null,
      selected_description_vn: null,
    };
    render(
      <HistoryCard
        item={noMatchItem}
        onReExecute={vi.fn()}
        onDelete={vi.fn()}
        isEven={false}
      />
    );
    expect(
      screen.getByText("Không có kết quả phù hợp")
    ).toBeInTheDocument();
  });

  it("renders formatted date in Vietnamese locale", () => {
    render(
      <HistoryCard
        item={baseItem}
        onReExecute={vi.fn()}
        onDelete={vi.fn()}
        isEven={false}
      />
    );
    expect(screen.getByText("21/02/2026")).toBeInTheDocument();
  });

  it("calls onReExecute with query when row is clicked", () => {
    const onReExecute = vi.fn();
    render(
      <HistoryCard
        item={baseItem}
        onReExecute={onReExecute}
        onDelete={vi.fn()}
        isEven={false}
      />
    );
    fireEvent.click(screen.getByText("laptop xách tay"));
    expect(onReExecute).toHaveBeenCalledWith("laptop xách tay");
  });

  it("calls onReExecute with query on Enter key", () => {
    const onReExecute = vi.fn();
    render(
      <HistoryCard
        item={baseItem}
        onReExecute={onReExecute}
        onDelete={vi.fn()}
        isEven={false}
      />
    );
    fireEvent.keyDown(screen.getAllByRole("button")[0], { key: "Enter" });
    expect(onReExecute).toHaveBeenCalledWith("laptop xách tay");
  });

  it("shows re-execute icon", () => {
    const { container } = render(
      <HistoryCard
        item={baseItem}
        onReExecute={vi.fn()}
        onDelete={vi.fn()}
        isEven={false}
      />
    );
    expect(container.querySelector(".lucide-rotate-ccw")).toBeInTheDocument();
  });

  it("shows delete button", () => {
    render(
      <HistoryCard
        item={baseItem}
        onReExecute={vi.fn()}
        onDelete={vi.fn()}
        isEven={false}
      />
    );
    expect(screen.getByLabelText("Xóa khỏi lịch sử")).toBeInTheDocument();
  });

  it("calls onDelete with item ID when delete button is clicked", () => {
    const onDelete = vi.fn();
    render(
      <HistoryCard
        item={baseItem}
        onReExecute={vi.fn()}
        onDelete={onDelete}
        isEven={false}
      />
    );
    fireEvent.click(screen.getByLabelText("Xóa khỏi lịch sử"));
    expect(onDelete).toHaveBeenCalledWith(1);
  });

  it("delete click does NOT trigger onReExecute", () => {
    const onReExecute = vi.fn();
    const onDelete = vi.fn();
    render(
      <HistoryCard
        item={baseItem}
        onReExecute={onReExecute}
        onDelete={onDelete}
        isEven={false}
      />
    );
    fireEvent.click(screen.getByLabelText("Xóa khỏi lịch sử"));
    expect(onDelete).toHaveBeenCalledWith(1);
    expect(onReExecute).not.toHaveBeenCalled();
  });
});
