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

export interface SearchResult {
  hs_code: HsCode;
  confidence: number;
  match_type: "exact" | "vector" | "fuzzy";
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}
