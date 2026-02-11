export interface BrowseSectionItem {
  id: number;
  section_number: number;
  section_roman: string;
  name_vn: string;
  name_en: string | null;
  chapter_count: number;
}

export interface BrowseChapterItem {
  id: number;
  chapter_code: string;
  name_vn: string;
  name_en: string | null;
  heading_count: number;
  hs_code_count: number;
}

export interface BrowseChaptersResponse {
  section_notes_vn: string | null;
  section_notes_en: string | null;
  chapters: BrowseChapterItem[];
}

export interface BrowseFTARateItem {
  agreement_code: string;
  preferential_rate: number;
  conditions: string | null;
  rate_year: number | null;
  is_export: boolean;
  legal_document: string | null;
  effective_date: string | null;
}

export interface BrowseHSCodeItem {
  id: number;
  code: string;
  description_vn: string;
  description_en: string;
  unit: string | null;
  duty_rate: number;
  vat_rate: number;
  export_duty_rate: string | null;
  special_consumption_tax: string | null;
  environmental_tax: string | null;
  vat_reduction: string | null;
  policy_notes: string | null;
  fta_rates: BrowseFTARateItem[];
}

export interface BrowseSubheadingItem {
  id: number;
  subheading_code: string;
  name_vn: string;
  name_en: string | null;
  indent_level: number | null;
  hs_codes: BrowseHSCodeItem[];
}

export interface BrowseHeadingItem {
  id: number;
  heading_code: string;
  name_vn: string;
  name_en: string | null;
  subheadings: BrowseSubheadingItem[];
}

export interface BrowseChapterDetailResponse {
  id: number;
  chapter_code: string;
  name_vn: string;
  name_en: string | null;
  notes_vn: string | null;
  notes_en: string | null;
  headings: BrowseHeadingItem[];
}

export interface BrowseSearchResultItem {
  id: number;
  code: string;
  description_vn: string;
  description_en: string;
  unit: string | null;
  duty_rate: number;
  vat_rate: number;
  export_duty_rate: string | null;
  section_roman: string;
  chapter_code: string;
  heading_code: string;
}

export interface PaginatedBrowseSearchResponse {
  items: BrowseSearchResultItem[];
  total: number;
  limit: number;
  offset: number;
}
