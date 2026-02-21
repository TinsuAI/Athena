/**
 * HS Code related type definitions.
 */

export interface HsCode {
  id: string;
  code: string;
  description: string;
  chapter: string;
  heading: string;
  subheading: string;
  duty_rate: string | null;
  unit_of_quantity: string | null;
}

export interface Classification {
  material: string;
  function: string;
}

/**
 * A single log entry from search processing
 */
export interface ProcessLogEntry {
  step: string;
  status: "started" | "completed" | "failed" | "skipped";
  message: string;
  duration_ms?: number;
  details?: Record<string, unknown>;
}

/**
 * Search result from the API - single best match
 */
export interface SearchResult {
  hs_code: string;
  hs_code_id?: number | null;
  description: string;
  duty_rate: string;
  vat_rate: string;
  classification: Classification;
  practical_notes: string[];
  confidence: number;
  process_logs?: ProcessLogEntry[];
  source?: string;
  is_verified?: boolean;
  verified_by?: string | null;
  verified_at?: string | null;
  lookup_id?: number | null;
  nlm_raw_response?: string | null;
}

/**
 * Legacy type for compatibility
 * @deprecated Use SearchResult instead
 */
export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}
