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
 * Search result from the API - single best match
 */
export interface SearchResult {
  hs_code: string;
  description: string;
  duty_rate: string;
  vat_rate: string;
  classification: Classification;
  practical_notes: string[];
  confidence: number;
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
