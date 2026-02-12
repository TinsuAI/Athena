"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  onClear: () => void;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

export const SearchBar = forwardRef<HTMLInputElement, SearchBarProps>(
  function SearchBar(
    {
      value,
      onChange,
      onSearch,
      onClear,
      isLoading = false,
      placeholder = 'Search HS codes... Press "/" to focus',
      className,
      autoFocus = true,
    },
    ref
  ) {
    const inputRef = useRef<HTMLInputElement>(null);

    useImperativeHandle(ref, () => inputRef.current!, []);

    useEffect(() => {
      if (autoFocus && inputRef.current) {
        inputRef.current.focus();
      }
    }, [autoFocus]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Escape") {
        onClear();
        inputRef.current?.focus();
      } else if (e.key === "Enter" && value.trim()) {
        e.preventDefault();
        onSearch();
      }
    };

    const handleClearClick = () => {
      onClear();
      inputRef.current?.focus();
    };

    const handleSearchClick = () => {
      if (value.trim()) {
        onSearch();
      }
    };

    return (
      <div className={cn("flex gap-3", className)}>
        <div className="relative flex-1">
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
            <Search className="h-[18px] w-[18px]" aria-hidden="true" />
          </div>

          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="w-full h-12 pl-11 pr-10 text-[15px] font-medium bg-white border-[1.5px] border-slate-200 rounded-lg text-slate-900 placeholder:text-slate-400 placeholder:font-normal transition-all duration-200 outline-none focus:border-emerald-500 focus:shadow-[0_0_0_3px_rgba(16,185,129,0.1)]"
            aria-label="Search HS codes"
            data-testid="search-input"
          />

          {value && (
            <button
              type="button"
              onClick={handleClearClick}
              className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7 flex items-center justify-center rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              aria-label="Clear search"
              data-testid="clear-button"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <button
          type="button"
          onClick={handleSearchClick}
          disabled={!value.trim() || isLoading}
          className="h-12 px-7 bg-emerald-600 hover:bg-emerald-700 text-white text-[13px] font-semibold rounded-lg transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm hover:shadow-md active:scale-[0.98]"
          data-testid="search-button"
        >
          {isLoading ? (
            <Loader2
              className="h-5 w-5 animate-spin motion-reduce:animate-none"
              aria-label="Searching..."
              data-testid="search-spinner"
            />
          ) : (
            "Search"
          )}
        </button>
      </div>
    );
  }
);
