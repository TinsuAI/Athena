"use client";

import { useState, useCallback, useEffect, useRef } from "react";
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
    setSearchQuery(`${item.code} - ${item.description_en}`);
    setSuggestions([]);
  };

  const handleSubmitClick = () => {
    if (!selectedHsCode) {
      setError("Please select the correct HS code");
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
        correct_hs_code_id: selectedHsCode.id,
        notes: notes.trim() || undefined,
      });

      if (response.success) {
        setShowSuccess(true);
        setTimeout(() => {
          onClose();
        }, 2000);
      } else if (response.error) {
        if (response.error.status === 429) {
          setError("Rate limit reached - please try again later");
        } else if (response.error.status === 409) {
          setError("This lookup has already been corrected");
        } else if (response.error.status === 400 && response.error.detail?.includes("same as the current match")) {
          setError("Please select a different HS code - this is the same as the current match");
        } else {
          setError(response.error.detail || "Failed to submit correction");
        }
      }
    } catch {
      setError("Failed to submit correction. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed top-0 right-0 h-full w-full max-w-md bg-background border-l shadow-lg z-50 overflow-y-auto animate-in slide-in-from-right">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Suggest Correction</h2>
            <button
              type="button"
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground"
            >
              &times;
            </button>
          </div>

          {/* Success toast */}
          {showSuccess && (
            <div className="mb-4 p-3 bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-200 rounded-lg text-sm">
              Thanks! Your correction will help improve search quality
            </div>
          )}

          {/* Current suggestion (read-only) */}
          <div className="mb-6 p-4 rounded-lg bg-muted/50 border">
            <p className="text-xs text-muted-foreground mb-1">Current suggestion</p>
            <p className="font-mono font-bold text-primary">{currentHsCode}</p>
            <p className="text-sm text-muted-foreground mt-1">{currentDescription}</p>
          </div>

          {/* HS Code autocomplete search */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">
              Correct HS Code
            </label>
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder="Search by code or description..."
                className="w-full px-3 py-2 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                disabled={showSuccess}
              />
              {isSearching && (
                <span className="absolute right-3 top-2.5 text-muted-foreground text-sm">
                  ...
                </span>
              )}
            </div>

            {/* Suggestions dropdown */}
            {suggestions.length > 0 && !selectedHsCode && (
              <div className="mt-1 border rounded-lg bg-background shadow-md max-h-60 overflow-y-auto">
                {suggestions.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleSelectHsCode(item)}
                    className="w-full px-3 py-2 text-left hover:bg-muted/50 transition-colors border-b last:border-b-0"
                  >
                    <span className="font-mono text-sm font-medium">
                      {item.code}
                    </span>
                    <p className="text-xs text-muted-foreground truncate">
                      {item.description_en}
                    </p>
                  </button>
                ))}
              </div>
            )}

            {selectedHsCode && (
              <p className="mt-1 text-xs text-green-600 dark:text-green-400">
                Selected: {selectedHsCode.code}
              </p>
            )}
          </div>

          {/* Optional notes */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              Notes (optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value.slice(0, 200))}
              placeholder="Why this correction is needed..."
              className="w-full px-3 py-2 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              rows={3}
              maxLength={200}
              disabled={showSuccess}
            />
            <p className="text-xs text-muted-foreground mt-1 text-right">
              {notes.length}/200
            </p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 bg-destructive/10 text-destructive rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Submit button */}
          <button
            type="button"
            onClick={handleSubmitClick}
            disabled={!selectedHsCode || isSubmitting || showSuccess}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? "Submitting..." : "Submit Correction"}
          </button>
        </div>

        {/* Confirmation dialog */}
        {showConfirm && selectedHsCode && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-background border rounded-lg shadow-xl max-w-md w-full p-6">
              <h3 className="text-lg font-semibold mb-3">Confirm Correction</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Are you sure you want to submit this correction? This will permanently mark the lookup as verified.
              </p>
              <div className="bg-muted/50 rounded p-3 mb-4">
                <p className="text-xs text-muted-foreground mb-1">New HS code:</p>
                <p className="font-mono font-bold">{selectedHsCode.code}</p>
                <p className="text-sm text-muted-foreground mt-1">{selectedHsCode.description_en}</p>
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowConfirm(false)}
                  className="flex-1 px-4 py-2 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmedSubmit}
                  className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
