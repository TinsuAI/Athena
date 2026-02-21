/**
 * Search history item from the API.
 */
export interface SearchHistoryItem {
  id: number;
  user_id: number;
  query: string;
  selected_hs_code_id: number | null;
  selected_hs_code: string | null;
  selected_description_vn: string | null;
  created_at: string;
}
