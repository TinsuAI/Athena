/**
 * API client for communicating with FastAPI backend.
 * Uses fetch with credentials for auth cookie handling.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
}

interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiError | null;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    const data: ApiResponse<T> = await response.json();
    return data;
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: "GET" });
  }

  async post<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  async put<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  }

  async patch<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }
}

export const apiClient = new ApiClient(API_URL);
export type { ApiResponse, ApiError };

// Browse API
import type {
  BrowseSectionItem,
  BrowseChaptersResponse,
  BrowseChapterDetailResponse,
  PaginatedBrowseSearchResponse,
} from "@/types/browse";

export async function getBrowseSections(): Promise<BrowseSectionItem[]> {
  const response = await apiClient.get<BrowseSectionItem[]>(
    "/api/browse/sections"
  );
  if (!response.success || !response.data) {
    throw new Error(response.error?.detail || "Failed to fetch sections");
  }
  return response.data;
}

export async function getBrowseChapters(
  sectionId: number
): Promise<BrowseChaptersResponse> {
  const response = await apiClient.get<BrowseChaptersResponse>(
    `/api/browse/chapters?section_id=${sectionId}`
  );
  if (!response.success || !response.data) {
    throw new Error(response.error?.detail || "Failed to fetch chapters");
  }
  return response.data;
}

export async function getBrowseChapterDetail(
  chapterCode: string
): Promise<BrowseChapterDetailResponse> {
  const response = await apiClient.get<BrowseChapterDetailResponse>(
    `/api/browse/chapters/${chapterCode}`
  );
  if (!response.success || !response.data) {
    throw new Error(
      response.error?.detail || "Failed to fetch chapter detail"
    );
  }
  return response.data;
}

export async function searchBrowse(
  query: string,
  chapter?: string,
  limit: number = 50,
  offset: number = 0
): Promise<PaginatedBrowseSearchResponse> {
  const params = new URLSearchParams({
    q: query,
    limit: String(limit),
    offset: String(offset),
  });
  if (chapter) {
    params.set("chapter", chapter);
  }
  const response = await apiClient.get<PaginatedBrowseSearchResponse>(
    `/api/browse/search?${params.toString()}`
  );
  if (!response.success || !response.data) {
    throw new Error(response.error?.detail || "Failed to search tariff codes");
  }
  return response.data;
}

// Lookup History API
import type {
  LookupDetail,
  PaginatedLookupListResponse,
} from "@/types/lookup";

export async function getLookups(
  limit: number = 20,
  offset: number = 0,
  verified?: boolean
): Promise<PaginatedLookupListResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (verified !== undefined) {
    params.set("verified", String(verified));
  }
  const response = await apiClient.get<PaginatedLookupListResponse>(
    `/api/lookups?${params.toString()}`
  );
  if (!response.success || !response.data) {
    throw new Error(response.error?.detail || "Failed to fetch lookups");
  }
  return response.data;
}

export async function getLookupDetail(id: number): Promise<LookupDetail> {
  const response = await apiClient.get<LookupDetail>(`/api/lookups/${id}`);
  if (!response.success || !response.data) {
    throw new Error(response.error?.detail || "Failed to fetch lookup detail");
  }
  return response.data;
}

// Favorites API
import type { Favorite } from "@/types/favorite";

export async function getFavorites(): Promise<Favorite[]> {
  const response = await apiClient.get<Favorite[]>("/api/favorites");
  if (!response.success || !response.data) {
    throw new Error(response.error?.detail || "Failed to fetch favorites");
  }
  return response.data;
}

export async function addFavorite(hsCodeId: number): Promise<Favorite> {
  const response = await apiClient.post<Favorite>("/api/favorites", {
    hs_code_id: hsCodeId,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error?.detail || "Failed to add favorite");
  }
  return response.data;
}

export async function updateFavoriteNotes(
  favoriteId: number,
  notes: string | null
): Promise<Favorite> {
  const response = await apiClient.patch<Favorite>(
    `/api/favorites/${favoriteId}`,
    { notes }
  );
  if (!response.success || !response.data) {
    throw new Error(response.error?.detail || "Failed to update notes");
  }
  return response.data;
}

export async function removeFavorite(favoriteId: number): Promise<void> {
  const response = await apiClient.delete<{ deleted: boolean }>(
    `/api/favorites/${favoriteId}`
  );
  if (!response.success) {
    throw new Error(response.error?.detail || "Failed to remove favorite");
  }
}

// Search History API
import type { SearchHistoryItem } from "@/types/search-history";

export async function getSearchHistory(
  limit: number = 20,
  offset: number = 0
): Promise<{ items: SearchHistoryItem[]; total: number }> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const response = await apiClient.get<{
    items: SearchHistoryItem[];
    total: number;
  }>(`/api/history?${params.toString()}`);
  if (!response.success || !response.data) {
    throw new Error(
      response.error?.detail || "Failed to fetch search history"
    );
  }
  return response.data;
}

export async function recordSearchHistory(
  query: string,
  selectedHsCodeId: number | null
): Promise<void> {
  await apiClient.post("/api/history", {
    query,
    selected_hs_code_id: selectedHsCodeId,
  });
  // Fire-and-forget — no return value needed
}

// Search API
import type { SearchResult } from "@/types/hs-code";

export interface SearchOptions {
  query: string;
  model?: string;
  signal?: AbortSignal;
}

export async function searchHsCodes(
  query: string,
  signal?: AbortSignal,
  model?: string
): Promise<SearchResult> {
  const url = `${API_URL}/api/search`;

  const body: { query: string; model?: string } = { query };
  if (model) {
    body.model = model;
  }

  const response = await fetch(url, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal,
  });

  const data: ApiResponse<SearchResult> = await response.json();

  if (!data.success || !data.data) {
    throw new Error(data.error?.detail || "Search failed");
  }

  return data.data;
}
