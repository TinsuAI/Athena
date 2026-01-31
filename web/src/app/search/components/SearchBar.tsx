"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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

    // Expose the input ref to parent components
    useImperativeHandle(ref, () => inputRef.current!, []);

    // Auto-focus on mount
    useEffect(() => {
      if (autoFocus && inputRef.current) {
        inputRef.current.focus();
      }
    }, [autoFocus]);

    // Handle keyboard events
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
      <div className={cn("flex gap-2", className)}>
        <div className="relative flex-1">
          {/* Search icon */}
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            <Search className="h-5 w-5" aria-hidden="true" />
          </div>

          {/* Search input */}
          <Input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="h-12 pl-10 pr-10 text-base md:text-lg"
            aria-label="Search HS codes"
            data-testid="search-input"
          />

          {/* Clear button - only visible when there's text */}
          {value && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleClearClick}
              className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
              data-testid="clear-button"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Search button */}
        <Button
          type="button"
          onClick={handleSearchClick}
          disabled={!value.trim() || isLoading}
          className="h-12 px-6"
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
        </Button>
      </div>
    );
  }
);
