"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Pencil, Check, X, Loader2, CheckCircle2, AlertCircle, FileText } from "lucide-react";
import { useStore } from "@/lib/store";
import { updateFavoriteNotes } from "@/lib/api";

interface FavoriteNotesProps {
  favoriteId: number;
  hsCodeId: number;
  initialNotes: string | null;
}

export function FavoriteNotes({
  favoriteId,
  hsCodeId,
  initialNotes,
}: FavoriteNotesProps) {
  const updateFavoriteNotesLocal = useStore((s) => s.updateFavoriteNotesLocal);

  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(initialNotes ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sync initialNotes when it changes externally
  useEffect(() => {
    if (!isEditing) {
      setDraft(initialNotes ?? "");
    }
  }, [initialNotes, isEditing]);

  // Auto-dismiss toast
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2000);
    return () => clearTimeout(timer);
  }, [toast]);

  // Auto-focus and auto-resize textarea on edit mode
  useEffect(() => {
    if (isEditing && textareaRef.current) {
      const ta = textareaRef.current;
      ta.focus();
      ta.selectionStart = ta.value.length;
      ta.style.height = "auto";
      ta.style.height = `${Math.max(ta.scrollHeight, 56)}px`;
    }
  }, [isEditing]);

  const handleEdit = useCallback(() => {
    if (isSaving) return;
    setDraft(initialNotes ?? "");
    setIsEditing(true);
  }, [initialNotes, isSaving]);

  const handleCancel = useCallback(() => {
    setDraft(initialNotes ?? "");
    setIsEditing(false);
  }, [initialNotes]);

  const handleSave = useCallback(async () => {
    if (isSaving) return;
    setIsSaving(true);

    const notesToSave = draft.trim() === "" ? null : draft.trim();

    try {
      await updateFavoriteNotes(favoriteId, notesToSave);
      updateFavoriteNotesLocal(favoriteId, notesToSave);
      setIsEditing(false);
      setToast("Ghi chú đã cập nhật");
    } catch {
      // Keep editing on error so user doesn't lose their text
      setToast("Lỗi khi lưu ghi chú");
    } finally {
      setIsSaving(false);
    }
  }, [favoriteId, draft, isSaving, updateFavoriteNotesLocal]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        handleCancel();
      }
      // Ctrl/Cmd + Enter to save
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        handleSave();
      }
    },
    [handleCancel, handleSave]
  );

  const handleTextareaInput = useCallback(() => {
    if (textareaRef.current) {
      const ta = textareaRef.current;
      ta.style.height = "auto";
      ta.style.height = `${Math.max(ta.scrollHeight, 56)}px`;
    }
  }, []);

  const hasNotes = initialNotes !== null && initialNotes.trim() !== "";

  return (
    <>
      <div className="group/notes relative" data-testid="favorite-notes">
        {isEditing ? (
          /* ─── Edit Mode ─── */
          <div className="rounded-lg border border-emerald-300 bg-white shadow-sm shadow-emerald-100/50 transition-all duration-200">
            <textarea
              ref={textareaRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onInput={handleTextareaInput}
              onKeyDown={handleKeyDown}
              disabled={isSaving}
              placeholder="Nhập ghi chú cá nhân..."
              aria-label="Ghi chú yêu thích"
              className="w-full resize-none rounded-t-lg border-0 bg-transparent px-3 py-2.5 text-xs leading-relaxed text-slate-700 placeholder:text-slate-300 focus:outline-none disabled:opacity-50"
              rows={2}
            />
            <div className="flex items-center justify-between border-t border-emerald-100 px-2.5 py-1.5">
              <span className="text-[10px] text-slate-300 font-medium select-none">
                Ctrl+Enter lưu · Esc hủy
              </span>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={isSaving}
                  aria-label="Hủy chỉnh sửa"
                  className="inline-flex items-center justify-center rounded-md p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 disabled:pointer-events-none disabled:opacity-40"
                >
                  <X size={13} strokeWidth={2} />
                </button>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={isSaving}
                  aria-label="Lưu ghi chú"
                  className="inline-flex items-center justify-center rounded-md p-1.5 text-emerald-600 transition-colors hover:bg-emerald-50 hover:text-emerald-700 disabled:pointer-events-none disabled:opacity-40"
                >
                  {isSaving ? (
                    <Loader2 size={13} className="animate-spin" />
                  ) : (
                    <Check size={13} strokeWidth={2.5} />
                  )}
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* ─── Display Mode ─── */
          <button
            type="button"
            onClick={handleEdit}
            className="flex w-full items-start gap-2 rounded-lg border border-transparent px-2.5 py-2 text-left transition-all duration-150 hover:border-slate-200 hover:bg-slate-50/70"
            aria-label={hasNotes ? "Chỉnh sửa ghi chú" : "Thêm ghi chú"}
          >
            <FileText
              size={12}
              strokeWidth={1.5}
              className={`mt-0.5 shrink-0 ${hasNotes ? "text-emerald-500" : "text-slate-300"}`}
            />
            {hasNotes ? (
              <span className="text-xs leading-relaxed text-slate-600 whitespace-pre-wrap break-words">
                {initialNotes}
              </span>
            ) : (
              <span className="text-xs text-slate-300 italic">
                Thêm ghi chú...
              </span>
            )}
            <Pencil
              size={10}
              strokeWidth={1.5}
              className="ml-auto mt-0.5 shrink-0 text-slate-300 opacity-0 transition-opacity group-hover/notes:opacity-100"
            />
          </button>
        )}
      </div>

      {/* Toast notification */}
      {toast && (() => {
        const isError = toast.startsWith("Lỗi");
        return (
          <div className={`fixed top-4 right-4 z-50 flex items-center gap-2.5 rounded-xl border px-4 py-3 shadow-lg animate-in slide-in-from-top-2 duration-300 ${isError ? "border-red-200 bg-red-50" : "border-emerald-200 bg-emerald-50"}`}>
            {isError ? (
              <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
            ) : (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            )}
            <span className={`text-sm font-semibold ${isError ? "text-red-800" : "text-emerald-800"}`}>
              {toast}
            </span>
          </div>
        );
      })()}
    </>
  );
}
