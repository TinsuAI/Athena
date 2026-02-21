import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FavoriteCard } from "./FavoriteCard";
import type { Favorite } from "@/types/favorite";

const baseFavorite: Favorite = {
  id: 1,
  user_id: 10,
  hs_code_id: 100,
  hs_code: "01012100",
  description_vn: "Ngựa thuần chủng để nhân giống",
  notes: "Ghi chú cho mã HS này",
  created_at: "2026-02-20T10:30:00+07:00",
};

describe("FavoriteCard", () => {
  it("renders HS code in mono font", () => {
    render(
      <FavoriteCard
        favorite={baseFavorite}
        onRemove={vi.fn()}
        onClick={vi.fn()}
        isEven={false}
      />
    );
    const hsCode = screen.getByText("01012100");
    expect(hsCode).toBeInTheDocument();
    expect(hsCode.className).toContain("font-mono");
  });

  it("renders Vietnamese description", () => {
    render(
      <FavoriteCard
        favorite={baseFavorite}
        onRemove={vi.fn()}
        onClick={vi.fn()}
        isEven={false}
      />
    );
    expect(
      screen.getByText("Ngựa thuần chủng để nhân giống")
    ).toBeInTheDocument();
  });

  it("renders truncated notes preview when notes exist", () => {
    render(
      <FavoriteCard
        favorite={baseFavorite}
        onRemove={vi.fn()}
        onClick={vi.fn()}
        isEven={false}
      />
    );
    expect(
      screen.getByText("Ghi chú cho mã HS này")
    ).toBeInTheDocument();
  });

  it("does not render notes section when notes is null", () => {
    const noNotesFav = { ...baseFavorite, notes: null };
    render(
      <FavoriteCard
        favorite={noNotesFav}
        onRemove={vi.fn()}
        onClick={vi.fn()}
        isEven={false}
      />
    );
    expect(
      screen.queryByText("Ghi chú cho mã HS này")
    ).not.toBeInTheDocument();
  });

  it("renders formatted date", () => {
    render(
      <FavoriteCard
        favorite={baseFavorite}
        onRemove={vi.fn()}
        onClick={vi.fn()}
        isEven={false}
      />
    );
    // Vietnamese locale date format: dd/mm/yyyy
    expect(screen.getByText("20/02/2026")).toBeInTheDocument();
  });

  it("calls onRemove with favorite id when remove button clicked", () => {
    const onRemove = vi.fn();
    render(
      <FavoriteCard
        favorite={baseFavorite}
        onRemove={onRemove}
        onClick={vi.fn()}
        isEven={false}
      />
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Xóa khỏi yêu thích" })
    );
    expect(onRemove).toHaveBeenCalledWith(1);
  });

  it("calls onClick when card body is clicked", () => {
    const onClick = vi.fn();
    render(
      <FavoriteCard
        favorite={baseFavorite}
        onRemove={vi.fn()}
        onClick={onClick}
        isEven={false}
      />
    );
    // Click on the card (the outer div with role="button")
    fireEvent.click(screen.getByText("01012100"));
    expect(onClick).toHaveBeenCalled();
  });

  it("remove button click does not trigger card click", () => {
    const onClick = vi.fn();
    const onRemove = vi.fn();
    render(
      <FavoriteCard
        favorite={baseFavorite}
        onRemove={onRemove}
        onClick={onClick}
        isEven={false}
      />
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Xóa khỏi yêu thích" })
    );
    expect(onRemove).toHaveBeenCalled();
    expect(onClick).not.toHaveBeenCalled();
  });
});
