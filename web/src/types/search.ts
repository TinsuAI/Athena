/**
 * Search related type definitions.
 */

export interface SearchQuery {
  q: string;
  limit?: number;
  offset?: number;
  chapter?: string;
}

export interface SearchFilters {
  chapter: string | null;
  minConfidence: number;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  searched_at: string;
  result_count: number;
}
