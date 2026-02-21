/**
 * Favorite type for user bookmarked HS codes.
 */
export interface Favorite {
  id: number;
  user_id: number;
  hs_code_id: number;
  hs_code: string;
  description_vn: string;
  notes: string | null;
  created_at: string;
}
