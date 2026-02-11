export interface LookupListItem {
  id: number;
  query_text: string;
  query_language: string | null;
  matched_hs_code: string | null;
  matched_description_vn: string | null;
  confidence_score: number | null;
  search_method: string;
  is_verified: boolean;
  created_at: string;
}

export interface PaginatedLookupListResponse {
  items: LookupListItem[];
  total: number;
  limit: number;
  offset: number;
}
