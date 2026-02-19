"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { apiClient } from "@/lib/api";

interface HSCodeAutocompleteItem {
  id: number;
  code: string;
  description_vn: string;
  description_en: string;
}

interface CorrectionPanelProps {
  isOpen: boolean;
  onClose: () => void;
  lookupId: number;
  currentHsCode: string;
  currentDescription: string;
}

export function CorrectionPanel({
  isOpen,
  onClose,
  lookupId,
  currentHsCode,
  currentDescription,
}: CorrectionPanelProps) {
  const { data: session, status: authStatus } = useSession();
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState<HSCodeAutocompleteItem[]>([]);
  const [selectedHsCode, setSelectedHsCode] = useState<HSCodeAutocompleteItem | null>(null);
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Reset state when panel opens
  useEffect(() => {
    if (isOpen) {
      setSearchQuery("");
      setSuggestions([]);
      setSelectedHsCode(null);
      setNotes("");
      setError(null);
      setShowSuccess(false);
      setShowConfirm(false);
    }
  }, [isOpen]);

  // Autocomplete search with debounce
  const searchHsCodes = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await apiClient.get<HSCodeAutocompleteItem[]>(
        `/api/hs-codes/autocomplete?q=${encodeURIComponent(query)}&limit=10`
      );
      if (response.success && response.data) {
        setSuggestions(response.data);
      }
    } catch (error) {
      console.error('Autocomplete search failed:', error);
      setSuggestions([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setSelectedHsCode(null);
    setError(null);

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      searchHsCodes(value);
    }, 300);
  };

  const handleSelectHsCode = (item: HSCodeAutocompleteItem) => {
    setSelectedHsCode(item);
    setSearchQuery(`${item.code} - ${item.description_vn || item.description_en}`);
    setSuggestions([]);
  };

  const handleSubmitClick = () => {
    if (!selectedHsCode) {
      setError("Vui long chon ma HS dung");
      return;
    }
    setShowConfirm(true);
  };

  const handleConfirmedSubmit = async () => {
    setShowConfirm(false);
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await apiClient.post<unknown>("/api/corrections", {
        lookup_id: lookupId,
        correct_hs_code_id: selectedHsCode!.id,
        notes: notes.trim() || undefined,
      });

      if (response.success) {
        setShowSuccess(true);
        setTimeout(() => {
          onClose();
        }, 2000);
      } else if (response.error) {
        if (response.error.status === 429) {
          setError("Da vuot qua gioi han - vui long thu lai sau");
        } else if (response.error.status === 409) {
          if (response.error.detail?.includes("Chinh sua dang cho duyet")) {
            setError("Chinh sua dang cho duyet");
          } else if (response.error.detail?.includes("Tra cuu nay da duoc chinh sua")) {
            setError("Tra cuu nay da duoc chinh sua");
          } else {
            setError("Ket qua nay da duoc sua doi roi");
          }
        } else if (response.error.status === 400 && response.error.detail?.includes("same as the current match")) {
          setError("Vui long chon ma HS khac - ma nay giong voi ket qua hien tai");
        } else {
          setError(response.error.detail || "Khong the gui de xuat sua doi");
        }
      }
    } catch {
      setError("Khong the gui de xuat sua doi. Vui long thu lai.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const isAuthenticated = authStatus !== "loading" && !!session?.user;
  const isAuthLoading = authStatus === "loading";

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 backdrop-blur-[2px] z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed top-0 right-0 h-full w-full max-w-md bg-white border-l border-slate-200 shadow-[0_8px_24px_rgba(0,0,0,0.08)] z-50 overflow-y-auto animate-in slide-in-from-right">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-[15px] font-bold text-slate-900 tracking-tight">De xuat sua doi</h2>
            <button
              type="button"
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            >
              &times;
            </button>
          </div>

          {/* Auth loading state */}
          {isAuthLoading && (
            <div className="flex items-center justify-center py-16">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-200 border-t-emerald-600" />
            </div>
          )}

          {/* Login prompt for unauthenticated users */}
          {!isAuthLoading && !isAuthenticated && (
            <div className="flex flex-col items-center justify-center py-12 px-4">
              <div className="w-14 h-14 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center mb-5">
                <svg
                  className="w-6 h-6 text-slate-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
                  />
                </svg>
              </div>
              <p className="text-[13px] text-slate-500 text-center mb-4 leading-relaxed">
                Dang nhap de gui chinh sua
              </p>
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-emerald-600 text-white rounded-lg text-[13px] font-semibold hover:bg-emerald-700 transition-colors shadow-sm"
              >
                Dang nhap
              </Link>
            </div>
          )}

          {/* Authenticated correction form */}
          {!isAuthLoading && isAuthenticated && (
            <>
              {/* Success toast */}
              {showSuccess && (
                <div className="mb-4 p-3 bg-emerald-50 text-emerald-800 rounded-lg text-[13px] font-medium border border-emerald-100 flex items-center gap-2.5">
                  <span className="relative flex h-2 w-2 shrink-0">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
                  </span>
                  Chinh sua da duoc gui, dang cho duyet
                </div>
              )}

              {/* Current suggestion (read-only) */}
              <div className="mb-6 p-4 rounded-xl bg-slate-50 border border-slate-200">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Ket qua hien tai</p>
                <p className="font-mono font-bold text-emerald-700 text-[14px] tracking-tight">{currentHsCode}</p>
                <p className="text-[12.5px] text-slate-500 mt-1">{currentDescription}</p>
              </div>

              {/* HS Code autocomplete search */}
              <div className="mb-4">
                <label className="block text-[12px] font-semibold text-slate-600 mb-2">
                  Ma HS dung
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    placeholder="Tim theo ma hoac mo ta..."
                    className="w-full px-3 py-2.5 border-[1.5px] border-slate-200 rounded-lg bg-white text-[13px] font-medium text-slate-900 placeholder:text-slate-400 outline-none transition-all duration-200 focus:border-emerald-500 focus:shadow-[0_0_0_3px_rgba(16,185,129,0.1)]"
                    disabled={showSuccess}
                  />
                  {isSearching && (
                    <span className="absolute right-3 top-3 text-slate-400 text-[12px]">
                      ...
                    </span>
                  )}
                </div>

                {/* Suggestions dropdown */}
                {suggestions.length > 0 && !selectedHsCode && (
                  <div className="mt-1 border border-slate-200 rounded-lg bg-white shadow-[0_4px_12px_rgba(0,0,0,0.06)] max-h-60 overflow-y-auto">
                    {suggestions.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => handleSelectHsCode(item)}
                        className="w-full px-3 py-2.5 text-left hover:bg-emerald-50 transition-colors duration-150 border-b border-slate-100 last:border-b-0"
                      >
                        <span className="font-mono text-[12px] font-bold text-emerald-700">
                          {item.code}
                        </span>
                        <p className="text-[11px] text-slate-500 truncate mt-0.5">
                          {item.description_vn || item.description_en}
                        </p>
                      </button>
                    ))}
                  </div>
                )}

                {selectedHsCode && (
                  <p className="mt-1.5 text-[11px] font-semibold text-emerald-600">
                    Da chon: {selectedHsCode.code}
                  </p>
                )}
              </div>

              {/* Optional notes */}
              <div className="mb-6">
                <label className="block text-[12px] font-semibold text-slate-600 mb-2">
                  Ghi chu (khong bat buoc)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value.slice(0, 200))}
                  placeholder="Ly do can sua doi..."
                  className="w-full px-3 py-2.5 border-[1.5px] border-slate-200 rounded-lg bg-white text-[13px] text-slate-900 placeholder:text-slate-400 outline-none transition-all duration-200 focus:border-emerald-500 focus:shadow-[0_0_0_3px_rgba(16,185,129,0.1)] resize-none"
                  rows={3}
                  maxLength={200}
                  disabled={showSuccess}
                />
                <p className="text-[11px] text-slate-400 mt-1 text-right">
                  {notes.length}/200
                </p>
              </div>

              {/* Error message */}
              {error && (
                <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-[13px] font-medium border border-red-100">
                  {error}
                </div>
              )}

              {/* Submit button */}
              <button
                type="button"
                onClick={handleSubmitClick}
                disabled={!selectedHsCode || isSubmitting || showSuccess}
                className="w-full px-4 py-2.5 bg-emerald-600 text-white rounded-lg text-[13px] font-semibold hover:bg-emerald-700 transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
              >
                {isSubmitting ? "Dang gui..." : "Gui de xuat sua doi"}
              </button>
            </>
          )}
        </div>

        {/* Confirmation dialog */}
        {showConfirm && selectedHsCode && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] z-50 flex items-center justify-center p-4">
            <div className="bg-white border border-slate-200 rounded-xl shadow-[0_8px_24px_rgba(0,0,0,0.08)] max-w-md w-full p-6">
              <h3 className="text-[15px] font-bold text-slate-900 tracking-tight mb-3">Xac nhan sua doi</h3>
              <p className="text-[13px] text-slate-500 mb-4 leading-relaxed">
                Ban co chac chan muon gui de xuat sua doi nay khong? Chinh sua se duoc xem xet truoc khi ap dung.
              </p>
              <div className="bg-slate-50 rounded-lg p-3 mb-4 border border-slate-200">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Ma HS moi:</p>
                <p className="font-mono font-bold text-emerald-700 text-[14px]">{selectedHsCode.code}</p>
                <p className="text-[12.5px] text-slate-500 mt-1">{selectedHsCode.description_vn || selectedHsCode.description_en}</p>
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowConfirm(false)}
                  className="flex-1 px-4 py-2.5 border-[1.5px] border-slate-200 rounded-lg text-[13px] font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Huy
                </button>
                <button
                  type="button"
                  onClick={handleConfirmedSubmit}
                  className="flex-1 px-4 py-2.5 bg-emerald-600 text-white rounded-lg text-[13px] font-semibold hover:bg-emerald-700 transition-colors shadow-sm"
                >
                  Xac nhan
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
