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

export interface LookupDetailHSCode {
  code: string;
  description_vn: string | null;
  description_en: string | null;
  duty_rate: string | null;
  vat_rate: string | null;
}

export interface LookupDetail {
  id: number;
  query_text: string;
  query_language: string | null;
  matched_hs_code: LookupDetailHSCode | null;
  correct_hs_code: LookupDetailHSCode | null;
  classification_data: { material: string; function: string } | null;
  practical_notes: string[] | null;
  process_logs:
    | {
        step: string;
        status: string;
        message: string;
        duration_ms: number;
        details?: Record<string, unknown>;
      }[]
    | null;
  nlm_raw_response: string | null;
  confidence_score: number | null;
  search_method: string;
  is_verified: boolean;
  verified_at: string | null;
  notes: string | null;
  created_at: string;
}
