/**
 * Zustand store with slices for state management.
 */

import { create } from "zustand";
import type { SearchResult } from "@/types/hs-code";
import type { User } from "@/types/user";
import type { Favorite } from "@/types/favorite";

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
  user: User | null;
  setIsAuthenticated: (isAuthenticated: boolean) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

interface FavoritesState {
  favorites: Favorite[];
  favoriteIds: number[];
  isFavoritesLoading: boolean;
  favoritesError: string | null;
  setFavorites: (favorites: Favorite[]) => void;
  addFavoriteLocal: (favorite: Favorite) => void;
  removeFavoriteLocal: (favoriteId: number) => void;
  setIsFavoritesLoading: (loading: boolean) => void;
  setFavoritesError: (error: string | null) => void;
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
  user: null,
  setIsAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
  setUser: (user) => set({ user, isAuthenticated: user !== null }),
  logout: () => set({ user: null, isAuthenticated: false }),

  // Favorites slice (backend-synced)
  favorites: [],
  favoriteIds: [],
  isFavoritesLoading: false,
  favoritesError: null,
  setFavorites: (favorites) =>
    set({
      favorites,
      favoriteIds: favorites.map((f) => f.hs_code_id),
    }),
  addFavoriteLocal: (favorite) =>
    set((state) => {
      const favorites = [...state.favorites, favorite];
      return {
        favorites,
        favoriteIds: favorites.map((f) => f.hs_code_id),
      };
    }),
  removeFavoriteLocal: (favoriteId) =>
    set((state) => {
      const favorites = state.favorites.filter((f) => f.id !== favoriteId);
      return {
        favorites,
        favoriteIds: favorites.map((f) => f.hs_code_id),
      };
    }),
  setIsFavoritesLoading: (isFavoritesLoading) => set({ isFavoritesLoading }),
  setFavoritesError: (favoritesError) => set({ favoritesError }),
}));
