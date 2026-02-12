"use client";

import { useState, useRef, useEffect, useCallback } from "react";

interface ModelOption {
  value: string;
  label: string;
  context?: number;
  pricing?: string;
}

interface OpenRouterModel {
  id: string;
  name: string;
  context_length: number;
  pricing: {
    prompt: string;
    completion: string;
  };
}

// Fallback models in case OpenRouter API fails
const FALLBACK_MODELS: ModelOption[] = [
  { value: "openai/gpt-4o-mini", label: "GPT-4o Mini" },
  { value: "openai/gpt-4o", label: "GPT-4o" },
  { value: "anthropic/claude-3.5-sonnet", label: "Claude 3.5 Sonnet" },
  { value: "anthropic/claude-3-haiku", label: "Claude 3 Haiku" },
  { value: "google/gemini-pro-1.5", label: "Gemini Pro 1.5" },
];

// Cache for OpenRouter models
let modelsCache: ModelOption[] | null = null;
let fetchPromise: Promise<ModelOption[]> | null = null;

async function fetchOpenRouterModels(): Promise<ModelOption[]> {
  // Return cached models if available
  if (modelsCache) {
    return modelsCache;
  }

  // If already fetching, wait for that promise
  if (fetchPromise) {
    return fetchPromise;
  }

  fetchPromise = (async () => {
    try {
      const response = await fetch("https://openrouter.ai/api/v1/models");
      if (!response.ok) {
        throw new Error("Failed to fetch models");
      }

      const data = await response.json();
      const models: ModelOption[] = data.data.map((model: OpenRouterModel) => ({
        value: model.id,
        label: model.name,
        context: model.context_length,
        pricing: model.pricing?.prompt ? `$${parseFloat(model.pricing.prompt) * 1000000}/M tokens` : undefined,
      }));

      // Sort by name
      models.sort((a, b) => a.label.localeCompare(b.label));

      modelsCache = models;
      return models;
    } catch (error) {
      console.error("Failed to fetch OpenRouter models:", error);
      return FALLBACK_MODELS;
    } finally {
      fetchPromise = null;
    }
  })();

  return fetchPromise;
}

interface ModelSelectProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function ModelSelect({ value, onChange, placeholder = "Search models..." }: ModelSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [models, setModels] = useState<ModelOption[]>(FALLBACK_MODELS);
  const [isLoading, setIsLoading] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch models on mount
  useEffect(() => {
    fetchOpenRouterModels().then((fetchedModels) => {
      setModels(fetchedModels);
      setIsLoading(false);
    });
  }, []);

  // Filter models based on search query
  const filteredModels = models.filter((model) =>
    model.value.toLowerCase().includes(searchQuery.toLowerCase()) ||
    model.label.toLowerCase().includes(searchQuery.toLowerCase())
  ).slice(0, 50); // Limit to 50 results for performance

  // Check if the search query is a custom model (not in the list)
  const isCustomModel = searchQuery.trim() !== "" &&
    !models.some((m) => m.value === searchQuery.trim());

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearchQuery("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Reset highlighted index when filtered results change
  useEffect(() => {
    setHighlightedIndex(0);
  }, [filteredModels.length]);

  const handleSelect = useCallback((modelValue: string) => {
    onChange(modelValue);
    setSearchQuery("");
    setIsOpen(false);
    inputRef.current?.blur();
  }, [onChange]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const totalItems = filteredModels.length + (isCustomModel ? 1 : 0);

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setIsOpen(true);
        setHighlightedIndex((prev) => (prev + 1) % totalItems);
        break;
      case "ArrowUp":
        e.preventDefault();
        setIsOpen(true);
        setHighlightedIndex((prev) => (prev - 1 + totalItems) % totalItems);
        break;
      case "Enter":
        e.preventDefault();
        if (isOpen && totalItems > 0) {
          if (highlightedIndex < filteredModels.length) {
            handleSelect(filteredModels[highlightedIndex].value);
          } else if (isCustomModel) {
            handleSelect(searchQuery.trim());
          }
        } else if (searchQuery.trim()) {
          handleSelect(searchQuery.trim());
        }
        break;
      case "Escape":
        setIsOpen(false);
        setSearchQuery("");
        inputRef.current?.blur();
        break;
      case "Tab":
        setIsOpen(false);
        setSearchQuery("");
        break;
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setIsOpen(true);
  };

  const handleFocus = () => {
    setIsOpen(true);
    setSearchQuery("");
  };

  // Get display value for input
  const currentModel = models.find((m) => m.value === value);
  const displayValue = isOpen ? searchQuery : (currentModel?.label || value);

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={displayValue}
        onChange={handleInputChange}
        onFocus={handleFocus}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="w-full px-3 py-2.5 border-[1.5px] border-slate-200 rounded-lg bg-white text-[13px] font-medium text-slate-900 pr-8 outline-none transition-all duration-200 focus:border-emerald-500 focus:shadow-[0_0_0_3px_rgba(16,185,129,0.1)]"
      />
      {/* Dropdown arrow / loading indicator */}
      <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground">
        {isLoading ? (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        ) : (
          <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
            <path d="M2 4L6 8L10 4" stroke="currentColor" strokeWidth="1.5" fill="none" />
          </svg>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && (filteredModels.length > 0 || isCustomModel) && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 py-1 bg-white border border-slate-200 rounded-lg shadow-[0_4px_12px_rgba(0,0,0,0.06)] max-h-72 overflow-y-auto"
        >
          {filteredModels.map((model, index) => (
            <button
              key={model.value}
              type="button"
              onClick={() => handleSelect(model.value)}
              onMouseEnter={() => setHighlightedIndex(index)}
              className={`w-full px-3 py-2 text-left text-[13px] transition-colors duration-150 ${
                highlightedIndex === index
                  ? "bg-emerald-50 text-emerald-900"
                  : "hover:bg-slate-50"
              } ${value === model.value ? "font-medium" : ""}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="truncate">{model.label}</div>
                  <div className="text-xs text-muted-foreground truncate">{model.value}</div>
                </div>
                <div className="flex items-center gap-2 ml-2 shrink-0">
                  {model.context && (
                    <span className="text-xs text-muted-foreground">
                      {Math.round(model.context / 1000)}k
                    </span>
                  )}
                  {value === model.value && (
                    <span className="text-emerald-600 font-bold">✓</span>
                  )}
                </div>
              </div>
            </button>
          ))}

          {/* Custom model option */}
          {isCustomModel && (
            <>
              {filteredModels.length > 0 && (
                <div className="border-t my-1" />
              )}
              <button
                type="button"
                onClick={() => handleSelect(searchQuery.trim())}
                onMouseEnter={() => setHighlightedIndex(filteredModels.length)}
                className={`w-full px-3 py-2 text-left text-[13px] transition-colors duration-150 ${
                  highlightedIndex === filteredModels.length
                    ? "bg-emerald-50 text-emerald-900"
                    : "hover:bg-slate-50"
                }`}
              >
                <span className="text-muted-foreground">Use custom: </span>
                <span className="font-medium">{searchQuery.trim()}</span>
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
