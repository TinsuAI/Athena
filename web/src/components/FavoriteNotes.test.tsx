import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock store
const mockStore = {
  updateFavoriteNotesLocal: vi.fn(),
};

vi.mock("@/lib/store", () => ({
  useStore: (selector: (state: typeof mockStore) => unknown) =>
    selector(mockStore),
}));

// Mock API
const mockUpdateFavoriteNotes = vi.fn();

vi.mock("@/lib/api", () => ({
  updateFavoriteNotes: (...args: unknown[]) =>
    mockUpdateFavoriteNotes(...args),
}));

import { FavoriteNotes } from "./FavoriteNotes";

describe("FavoriteNotes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders placeholder when no notes", () => {
    render(
      <FavoriteNotes favoriteId={1} hsCodeId={100} initialNotes={null} />
    );
    expect(screen.getByText("Thêm ghi chú...")).toBeInTheDocument();
  });

  it("renders existing notes in display mode", () => {
    render(
      <FavoriteNotes
        favoriteId={1}
        hsCodeId={100}
        initialNotes="My saved note"
      />
    );
    expect(screen.getByText("My saved note")).toBeInTheDocument();
  });

  it("enters edit mode on click", () => {
    render(
      <FavoriteNotes favoriteId={1} hsCodeId={100} initialNotes={null} />
    );
    fireEvent.click(screen.getByRole("button", { name: "Thêm ghi chú" }));
    expect(
      screen.getByRole("textbox", { name: "Ghi chú yêu thích" })
    ).toBeInTheDocument();
  });

  it("saves notes on save button click", async () => {
    mockUpdateFavoriteNotes.mockResolvedValue({
      id: 1,
      user_id: 10,
      hs_code_id: 100,
      hs_code: "01012100",
      description_vn: "Test",
      notes: "New note",
      created_at: "2026-02-21",
    });

    render(
      <FavoriteNotes favoriteId={1} hsCodeId={100} initialNotes={null} />
    );

    // Enter edit mode
    fireEvent.click(screen.getByRole("button", { name: "Thêm ghi chú" }));

    // Type note
    const textarea = screen.getByRole("textbox", {
      name: "Ghi chú yêu thích",
    });
    fireEvent.change(textarea, { target: { value: "New note" } });

    // Click save
    fireEvent.click(screen.getByRole("button", { name: "Lưu ghi chú" }));

    await waitFor(() => {
      expect(mockUpdateFavoriteNotes).toHaveBeenCalledWith(1, "New note");
      expect(mockStore.updateFavoriteNotesLocal).toHaveBeenCalledWith(
        1,
        "New note"
      );
    });
  });

  it("cancels editing on cancel button click", () => {
    render(
      <FavoriteNotes
        favoriteId={1}
        hsCodeId={100}
        initialNotes="Original note"
      />
    );

    // Enter edit mode
    fireEvent.click(
      screen.getByRole("button", { name: "Chỉnh sửa ghi chú" })
    );

    // Modify text
    const textarea = screen.getByRole("textbox", {
      name: "Ghi chú yêu thích",
    });
    fireEvent.change(textarea, { target: { value: "Modified" } });

    // Click cancel
    fireEvent.click(
      screen.getByRole("button", { name: "Hủy chỉnh sửa" })
    );

    // Should show original note
    expect(screen.getByText("Original note")).toBeInTheDocument();
  });

  it("shows toast on successful save", async () => {
    mockUpdateFavoriteNotes.mockResolvedValue({
      id: 1,
      user_id: 10,
      hs_code_id: 100,
      hs_code: "01012100",
      description_vn: "Test",
      notes: "Saved note",
      created_at: "2026-02-21",
    });

    render(
      <FavoriteNotes favoriteId={1} hsCodeId={100} initialNotes={null} />
    );

    fireEvent.click(screen.getByRole("button", { name: "Thêm ghi chú" }));
    const textarea = screen.getByRole("textbox", {
      name: "Ghi chú yêu thích",
    });
    fireEvent.change(textarea, { target: { value: "Saved note" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu ghi chú" }));

    await waitFor(() => {
      expect(
        screen.getByText("Ghi chú đã cập nhật")
      ).toBeInTheDocument();
    });
  });

  it("shows error toast on save failure", async () => {
    mockUpdateFavoriteNotes.mockRejectedValue(new Error("Network error"));

    render(
      <FavoriteNotes favoriteId={1} hsCodeId={100} initialNotes={null} />
    );

    fireEvent.click(screen.getByRole("button", { name: "Thêm ghi chú" }));
    const textarea = screen.getByRole("textbox", {
      name: "Ghi chú yêu thích",
    });
    fireEvent.change(textarea, { target: { value: "Test note" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu ghi chú" }));

    await waitFor(() => {
      expect(screen.getByText("Lỗi khi lưu ghi chú")).toBeInTheDocument();
    });

    // Should stay in edit mode so user doesn't lose text
    expect(
      screen.getByRole("textbox", { name: "Ghi chú yêu thích" })
    ).toBeInTheDocument();
  });

  it("saves empty notes as null", async () => {
    mockUpdateFavoriteNotes.mockResolvedValue({
      id: 1,
      user_id: 10,
      hs_code_id: 100,
      hs_code: "01012100",
      description_vn: "Test",
      notes: null,
      created_at: "2026-02-21",
    });

    render(
      <FavoriteNotes
        favoriteId={1}
        hsCodeId={100}
        initialNotes="Existing note"
      />
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Chỉnh sửa ghi chú" })
    );
    const textarea = screen.getByRole("textbox", {
      name: "Ghi chú yêu thích",
    });
    fireEvent.change(textarea, { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu ghi chú" }));

    await waitFor(() => {
      expect(mockUpdateFavoriteNotes).toHaveBeenCalledWith(1, null);
      expect(mockStore.updateFavoriteNotesLocal).toHaveBeenCalledWith(
        1,
        null
      );
    });
  });
});
