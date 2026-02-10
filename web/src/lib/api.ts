/**
 * API client for communicating with FastAPI backend.
 * Uses fetch with credentials for auth cookie handling.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }
}

export const apiClient = new ApiClient(API_URL);
export type { ApiResponse, ApiError };

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
