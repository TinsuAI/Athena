/**
 * Zustand store with slices for state management.
 */

import { create } from "zustand";
import type { SearchResult } from "@/types/hs-code";

interface SearchState {
  searchQuery: string;
  searchResult: SearchResult | null;
  isSearching: boolean;
  searchError: string | null;
  llmModel: string;
  setSearchQuery: (query: string) => void;
  setSearchResult: (result: SearchResult | null) => void;
  setIsSearching: (isSearching: boolean) => void;
  setSearchError: (error: string | null) => void;
  setLlmModel: (model: string) => void;
  clearSearch: () => void;
}

interface AuthState {
  isAuthenticated: boolean;
  setIsAuthenticated: (isAuthenticated: boolean) => void;
}

interface FavoritesState {
  favoriteIds: string[];
  addFavorite: (id: string) => void;
  removeFavorite: (id: string) => void;
}

interface AppStore extends SearchState, AuthState, FavoritesState {}

export const useStore = create<AppStore>((set) => ({
  // Search slice
  searchQuery: "",
  searchResult: null,
  isSearching: false,
  searchError: null,
  llmModel: "openai/gpt-4o-mini",
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  setSearchResult: (searchResult) => set({ searchResult, searchError: null }),
  setIsSearching: (isSearching) => set({ isSearching }),
  setSearchError: (searchError) => set({ searchError }),
  setLlmModel: (llmModel) => set({ llmModel }),
  clearSearch: () =>
    set({
      searchQuery: "",
      searchResult: null,
      searchError: null,
    }),

  // Auth slice
  isAuthenticated: false,
  setIsAuthenticated: (isAuthenticated) => set({ isAuthenticated }),

  // Favorites slice
  favoriteIds: [],
  addFavorite: (id) =>
    set((state) => ({
      favoriteIds: [...state.favoriteIds, id],
    })),
  removeFavorite: (id) =>
    set((state) => ({
      favoriteIds: state.favoriteIds.filter((fId) => fId !== id),
    })),
}));
