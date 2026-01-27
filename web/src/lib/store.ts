/**
 * Zustand store with slices for state management.
 */

import { create } from "zustand";

interface SearchState {
  query: string;
  isLoading: boolean;
  setQuery: (query: string) => void;
  setIsLoading: (isLoading: boolean) => void;
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
  query: "",
  isLoading: false,
  setQuery: (query) => set({ query }),
  setIsLoading: (isLoading) => set({ isLoading }),

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
