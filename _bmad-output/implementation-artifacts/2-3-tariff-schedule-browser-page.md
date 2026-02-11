# Story 2.3: Tariff Schedule Browser Page

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want **a web page where I can browse the full tariff schedule with hierarchy and FTA rates**,
So that **I no longer need to open the Excel file to find and explore HS codes**.

## Background

Story 2-1 expanded the data import to capture all rate data (export duty, TTDB, BVMT, VAT reduction, FTA conditions, RCEP yearly rates, export FTA rates). Story 2-2 created the browse API endpoints that serve the hierarchy data. This story builds the frontend page at `/browse` that consumes those API endpoints.

**Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-11.md`

**Dependencies:** Story 2-2 must be complete (done).

**FRs covered:** FR8 (browse hierarchically), FR54 (collapsible tree with inline rates), FR55 (export duty rates), FR56 (special consumption tax), FR57 (environmental tax), FR58 (VAT reduction), FR59 (search/filter within browser), FR60 (jump to chapter), FR61 (section/chapter notes)

## Acceptance Criteria

1. **AC1: Section List on Page Load**
   - **Given** I navigate to `/browse`
   - **When** the page loads
   - **Then** I see all HS sections as expandable items showing section roman numeral, section name (VN), and chapter count
   - **And** the page title is "Tariff Schedule Browser" or equivalent Vietnamese title
   - **And** a navigation link to `/browse` exists in the Header component

2. **AC2: Section Expansion Shows Chapters**
   - **Given** I am viewing sections
   - **When** I click/expand a section
   - **Then** I see all chapters within that section with chapter code (2-digit), name (VN), and HS code count
   - **And** section notes (VN) are displayed as an expandable info panel below the section header
   - **And** chapters are ordered by chapter_code

3. **AC3: Chapter Expansion Shows Full Hierarchy with Inline Rates**
   - **Given** I am viewing chapters
   - **When** I click/expand a chapter
   - **Then** I see the full hierarchy: headings (4-digit) -> subheadings (6-digit) -> 8-digit HS codes
   - **And** chapter notes (VN) are displayed as an expandable panel
   - **And** each HS code row shows inline: code (monospace), description_vn, import duty rate, VAT rate, export duty rate

4. **AC4: HS Code Expansion Shows Full Detail**
   - **Given** I am viewing HS code rows
   - **When** I click/expand an HS code row
   - **Then** I see: English description, unit, all FTA rates (grouped by import/export), special consumption tax, environmental tax, VAT reduction, policy notes
   - **And** FTA rates are displayed in a table with columns: Agreement, Rate, Conditions
   - **And** import and export FTA rates are separated into labeled groups

5. **AC5: Jump-to-Chapter Quick Selector**
   - **Given** I want to find a specific chapter quickly
   - **When** I use the "Jump to chapter" dropdown
   - **Then** I can select any of the 98 chapters (showing code + name)
   - **And** the browser scrolls/navigates to that chapter's section and expands it

6. **AC6: Search Within Tariff Browser**
   - **Given** I want to search within the tariff browser
   - **When** I type in the browse search bar (min 2 characters)
   - **Then** results show matching HS codes from `GET /api/browse/search`
   - **And** each result shows: code, description_vn, hierarchy path (Section > Chapter > Heading), inline rates
   - **And** results are paginated
   - **And** I can optionally filter by chapter

7. **AC7: Responsive Layout**
   - **Given** I am on a desktop device (1024px+)
   - **When** I view the browse page
   - **Then** the full tree is displayed with rate columns visible
   - **Given** I am on a tablet device (768px-1023px)
   - **When** I view the browse page
   - **Then** the layout is stacked with horizontal scroll for rate columns

8. **AC8: Performance — Lazy Loading**
   - **Given** a chapter has many HS codes (some chapters have 600+)
   - **When** I expand it
   - **Then** the chapter detail loads from the API on demand (not preloaded)
   - **And** a loading indicator shows during fetch
   - **And** the page remains responsive

9. **AC9: Empty/Error States**
   - **Given** the browse API returns an error
   - **When** the page renders
   - **Then** I see a user-friendly error message with retry option
   - **Given** a search returns no results
   - **When** results are displayed
   - **Then** I see "No HS codes match your search"

10. **AC10: Backward Compatibility**
    - **Given** the browse page is added
    - **When** I navigate to existing pages (`/search`, `/lookups`, `/lookups/[id]`)
    - **Then** all existing functionality is unchanged (no regressions)

## Tasks / Subtasks

- [ ] Task 1: Create Browse Page Structure (AC: #1, #10)
  - [ ] 1.1 Create `web/src/app/browse/page.tsx` — main page (client component)
  - [ ] 1.2 Create `web/src/app/browse/loading.tsx` — loading skeleton
  - [ ] 1.3 Create `web/src/app/browse/error.tsx` — error boundary
  - [ ] 1.4 Add `/browse` navigation link to Header component (`web/src/components/layout/Header.tsx`)

- [ ] Task 2: Define TypeScript Types (AC: #1-#6)
  - [ ] 2.1 Create `web/src/types/browse.ts` with all browse API response types
  - [ ] 2.2 Types: `BrowseSectionItem`, `BrowseChapterItem`, `BrowseChaptersResponse`, `BrowseChapterDetailResponse`, `BrowseHeadingItem`, `BrowseSubheadingItem`, `BrowseHSCodeItem`, `BrowseFTARateItem`, `BrowseSearchResultItem`, `PaginatedBrowseSearchResponse`

- [ ] Task 3: Add Browse API Functions to API Client (AC: #1-#6)
  - [ ] 3.1 Add `getBrowseSections()` to `web/src/lib/api.ts`
  - [ ] 3.2 Add `getBrowseChapters(sectionId)` to `web/src/lib/api.ts`
  - [ ] 3.3 Add `getBrowseChapterDetail(chapterCode)` to `web/src/lib/api.ts`
  - [ ] 3.4 Add `searchBrowse(query, chapter?, limit?, offset?)` to `web/src/lib/api.ts`

- [ ] Task 4: Build SectionList Component (AC: #1, #2)
  - [ ] 4.1 Create `web/src/app/browse/components/SectionList.tsx`
  - [ ] 4.2 Render all sections as expandable/collapsible rows
  - [ ] 4.3 Show section_roman, name_vn, chapter_count
  - [ ] 4.4 On expand: fetch chapters via `getBrowseChapters(sectionId)` and display
  - [ ] 4.5 Show section notes (notes_vn) as expandable info panel
  - [ ] 4.6 Use chevron icon for expand/collapse state

- [ ] Task 5: Build ChapterView Component (AC: #3)
  - [ ] 5.1 Create `web/src/app/browse/components/ChapterView.tsx`
  - [ ] 5.2 Show chapter_code, name_vn, hs_code_count as expandable row
  - [ ] 5.3 On expand: fetch full chapter detail via `getBrowseChapterDetail(chapterCode)`
  - [ ] 5.4 Show loading indicator during fetch
  - [ ] 5.5 Render headings -> subheadings -> HS codes tree
  - [ ] 5.6 Show chapter notes (notes_vn) as expandable panel

- [ ] Task 6: Build HSCodeRow Component (AC: #3, #4)
  - [ ] 6.1 Create `web/src/app/browse/components/HSCodeRow.tsx`
  - [ ] 6.2 Display inline: code (monospace), description_vn, duty_rate, vat_rate, export_duty_rate
  - [ ] 6.3 On expand: show HSCodeDetail with full data

- [ ] Task 7: Build HSCodeDetail Expandable Panel (AC: #4)
  - [ ] 7.1 Create `web/src/app/browse/components/HSCodeDetail.tsx`
  - [ ] 7.2 Show: description_en, unit, policy_notes
  - [ ] 7.3 Show special_consumption_tax, environmental_tax, vat_reduction where non-null
  - [ ] 7.4 Render FTA rates table grouped by import (is_export=false) and export (is_export=true)
  - [ ] 7.5 FTA table columns: Agreement Code, Rate, Conditions, Year (if RCEP), Legal Document

- [ ] Task 8: Build ChapterJumper Dropdown (AC: #5)
  - [ ] 8.1 Create `web/src/app/browse/components/ChapterJumper.tsx`
  - [ ] 8.2 Dropdown listing all 98 chapters (code + name_vn)
  - [ ] 8.3 On select: find the section containing that chapter, expand the section, expand the chapter, scroll into view

- [ ] Task 9: Build BrowseSearch Component (AC: #6)
  - [ ] 9.1 Create `web/src/app/browse/components/BrowseSearch.tsx`
  - [ ] 9.2 Search input with debounce (300ms)
  - [ ] 9.3 Call `GET /api/browse/search` with query and optional chapter filter
  - [ ] 9.4 Display results with hierarchy path + inline rates
  - [ ] 9.5 Pagination controls (load more or page buttons)
  - [ ] 9.6 Empty state: "No HS codes match your search"

- [ ] Task 10: Write Tests (AC: #1-#10)
  - [ ] 10.1 Create `web/src/app/browse/components/SectionList.test.tsx`
  - [ ] 10.2 Create `web/src/app/browse/components/ChapterView.test.tsx`
  - [ ] 10.3 Create `web/src/app/browse/components/HSCodeRow.test.tsx`
  - [ ] 10.4 Create `web/src/app/browse/components/BrowseSearch.test.tsx`
  - [ ] 10.5 Test section list renders with counts
  - [ ] 10.6 Test section expansion fetches and shows chapters
  - [ ] 10.7 Test chapter expansion fetches and shows hierarchy
  - [ ] 10.8 Test HS code row inline rates display
  - [ ] 10.9 Test search with results and empty state
  - [ ] 10.10 Verify existing tests still pass (no regressions)

## Dev Notes

### Critical Architecture Patterns (MUST FOLLOW)

**Frontend Patterns — This story is FRONTEND ONLY:**
```
/browse page (client component)
├── SectionList → calls GET /api/browse/sections
│   ├── section expand → calls GET /api/browse/chapters?section_id={id}
│   │   └── ChapterView → calls GET /api/browse/chapters/{chapter_code}
│   │       └── headings → subheadings → HSCodeRow
│   │           └── HSCodeDetail (expand inline, no API call — data already in chapter response)
├── ChapterJumper (uses sections data already loaded)
└── BrowseSearch → calls GET /api/browse/search?q={text}
```

**Data Fetching — Direct to FastAPI with CORS:**
```typescript
// Use the existing apiClient from web/src/lib/api.ts
// NEVER use Next.js API routes for data
import { apiClient } from '@/lib/api';

const sections = await apiClient.get<BrowseSectionItem[]>('/api/browse/sections');
```

**State Management — Use local useState (NOT Zustand for this page):**
- The browse page state is page-local, not global
- Use `useState` for: expanded sections, loaded chapters, loaded chapter details, search query, search results
- Use `useCallback` for fetch functions
- Use boolean flags for loading states (`isLoadingSections`, `isLoadingChapters`, etc.)
- NEVER use status enums

**Client Component Directive:**
```typescript
'use client';
// All browse components are client components (interactive expand/collapse/search)
```

### Existing Code to Reference (READ THESE FIRST)

**Pattern file: `web/src/app/lookups/page.tsx`** — Follow this page pattern:
- Client component with `"use client"`
- useState for local state (items, loading, error, pagination)
- useCallback for data fetching
- useEffect to trigger fetch on mount/dependency changes
- Try/catch with error state
- Loading skeleton display

**Pattern file: `web/src/app/search/page.tsx`** — Follow this search pattern:
- Uses Zustand store for search state
- AbortController for request cancellation
- Keyboard shortcuts via `useKeyboardShortcuts` hook
- Debounced input handling

**Pattern file: `web/src/app/search/components/SearchBar.tsx`** — Follow this input pattern:
- ForwardRef component
- Props: value, onChange, onSearch, onClear, isLoading, placeholder, autoFocus
- Keyboard handling: Enter=search, Escape=clear
- Icons from `lucide-react` (Search, X, Loader2)
- Data-testid attributes for testing

**Pattern file: `web/src/app/lookups/components/LookupList.tsx`** — Follow this list pattern:
- Functional component receiving data as props
- Table/list with columns
- Badge components for status (confidence colors, verified)
- onClick handler for row navigation

**Pattern file: `web/src/lib/api.ts`** — API client:
- `ApiClient` class with `get<T>(url)`, `post<T>(url, body)` methods
- Envelope response format: `{ success, data, error }`
- Credentials included for auth cookie handling
- Functions: `getLookups(limit, offset, verified?)`, `getLookupDetail(id)`, `searchHsCodes(query, signal?, model?)`
- Add new browse functions following same pattern

**Pattern file: `web/src/components/layout/Header.tsx`** — Navigation:
- Client component with navigation links to `/search` and `/lookups`
- Add `/browse` link between `/search` and `/lookups`

### Browse API Endpoints Reference (Story 2-2 Output)

**GET /api/browse/sections** → `ApiResponse<BrowseSectionItem[]>`
```json
{"success": true, "data": [
  {"id": 1, "section_number": 1, "section_roman": "I", "name_vn": "Động vật sống...", "name_en": "Live animals...", "chapter_count": 5}
]}
```

**GET /api/browse/chapters?section_id=1** → `ApiResponse<BrowseChaptersResponse>`
```json
{"success": true, "data": {
  "section_notes_vn": "...", "section_notes_en": "...",
  "chapters": [{"id": 1, "chapter_code": "01", "name_vn": "...", "name_en": "...", "heading_count": 6, "hs_code_count": 48}]
}}
```

**GET /api/browse/chapters/01** → `ApiResponse<BrowseChapterDetailResponse>`
```json
{"success": true, "data": {
  "id": 1, "chapter_code": "01", "name_vn": "...", "notes_vn": "...", "notes_en": "...",
  "headings": [{"id": 1, "heading_code": "0101", "name_vn": "...",
    "subheadings": [{"id": 1, "subheading_code": "010121", "name_vn": "...", "indent_level": 1,
      "hs_codes": [{"id": 1, "code": "01012100", "description_vn": "...", "description_en": "...",
        "unit": "con", "duty_rate": 5.0, "vat_rate": 5.0, "export_duty_rate": null,
        "special_consumption_tax": null, "environmental_tax": null, "vat_reduction": null,
        "policy_notes": "...",
        "fta_rates": [{"agreement_code": "CPTPP", "preferential_rate": 0.0, "conditions": "...",
          "rate_year": null, "is_export": false, "legal_document": "...", "effective_date": "..."}]
      }]
    }]
  }]
}}
```

**GET /api/browse/search?q=copper&chapter=74&limit=50&offset=0** → `ApiResponse<PaginatedBrowseSearchResponse>`
```json
{"success": true, "data": {
  "items": [{"id": 123, "code": "74181000", "description_vn": "...", "description_en": "...",
    "unit": "kg", "duty_rate": 30.0, "vat_rate": 10.0, "export_duty_rate": null,
    "section_roman": "XV", "chapter_code": "74", "heading_code": "7418"}],
  "total": 1, "limit": 50, "offset": 0
}}
```

### TypeScript Type Definitions Guide

Create `web/src/types/browse.ts`:
```typescript
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
```

### Component Architecture Guide

**Page layout (`browse/page.tsx`):**
```
┌─────────────────────────────────────────────────┐
│ Tariff Schedule Browser              [Jump ▾]   │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🔍 Search within tariff schedule...         │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ ▸ I — Động vật sống... (5 chapters)             │
│ ▾ II — Sản phẩm thực vật (14 chapters)         │
│   ├── 06 — Cây sống... (48 codes)              │
│   ├── 07 — Rau và ... (142 codes)              │
│   ▾ 08 — Quả và ... (96 codes)                 │
│   │   ├── 0801 — Dừa, quả ...                  │
│   │   │   ├── 080111 — Dừa đã ...              │
│   │   │   │   08011100  Đã lột... 25% 10%  0%  │
│   │   │   │   ▾ 08011190  Loại... 15% 10%  0%  │
│   │   │   │   │ EN: Other coconuts...           │
│   │   │   │   │ Unit: kg                        │
│   │   │   │   │ ┌─ Import FTA Rates ─────────┐ │
│   │   │   │   │ │ CPTPP  0%  (conditions...)  │ │
│   │   │   │   │ │ EVFTA  5%  (conditions...)  │ │
│   │   │   │   │ └────────────────────────────┘ │
│   │   │   ...                                   │
│   ├── 09 — Cà phê... (63 codes)               │
│   ...                                            │
│ ▸ III — Mỡ và dầu... (3 chapters)              │
│ ...                                              │
└─────────────────────────────────────────────────┘
```

**Data loading strategy (CRITICAL — lazy loading per level):**
1. Page mount → `GET /api/browse/sections` (loads all 20 sections)
2. Section expand → `GET /api/browse/chapters?section_id={id}` (loads chapters for that section)
3. Chapter expand → `GET /api/browse/chapters/{code}` (loads FULL hierarchy for that chapter including all HS codes + FTA rates)
4. HS code expand → no API call needed (data already in chapter response)
5. Search → `GET /api/browse/search?q={text}` (separate search flow)

**Caching strategy:**
- Cache loaded chapters data in component state (Map<sectionId, BrowseChaptersResponse>)
- Cache loaded chapter details in component state (Map<chapterCode, BrowseChapterDetailResponse>)
- Don't re-fetch if already cached (check before API call)

### UI Component Patterns

**Expand/Collapse Pattern:**
```typescript
// Use a Set<string> to track expanded items
const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set());
const [expandedChapters, setExpandedChapters] = useState<Set<string>>(new Set());
const [expandedHSCodes, setExpandedHSCodes] = useState<Set<string>>(new Set());

const toggleSection = (id: number) => {
  setExpandedSections(prev => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    return next;
  });
};
```

**Expand/Collapse Icon:**
```typescript
import { ChevronRight, ChevronDown } from 'lucide-react';
// Use ChevronRight for collapsed, ChevronDown for expanded
```

**Rate Display:**
```typescript
// Display rates inline, handling null/undefined
const formatRate = (rate: number | string | null): string => {
  if (rate === null || rate === undefined) return '—';
  if (typeof rate === 'number') return `${rate}%`;
  return rate; // Already string (e.g., special_consumption_tax)
};
```

**Monospace HS Code Display:**
```typescript
<span className="font-mono text-sm">{code}</span>
```

### Testing Requirements

**Co-locate tests with source files:**
- `web/src/app/browse/components/SectionList.test.tsx`
- `web/src/app/browse/components/ChapterView.test.tsx`
- `web/src/app/browse/components/HSCodeRow.test.tsx`
- `web/src/app/browse/components/BrowseSearch.test.tsx`

**Use Vitest with jsdom following existing patterns.**

**Test scenarios:**
1. SectionList renders 20 sections with chapter counts
2. Section expand triggers API call and renders chapters
3. Chapter expand triggers API call and renders hierarchy
4. HSCodeRow shows inline rate columns
5. HSCodeDetail shows FTA rates table with import/export grouping
6. ChapterJumper dropdown lists all chapters
7. BrowseSearch triggers API call on input with debounce
8. BrowseSearch shows empty state for no results
9. Loading states display correctly
10. Error states display correctly with retry

**Run after implementation:**
```bash
docker-compose -f docker-compose.dev.yml exec web npm run test:run  # Frontend tests
docker-compose -f docker-compose.dev.yml exec api pytest             # Verify no backend regressions
```

### Previous Story Intelligence (from Story 2-2)

**Key learnings from Story 2-2 code review:**
- Story 2-2 created 4 browse API endpoints: sections, chapters, chapter detail, search
- Data counts: 11,871 HS codes, 270,746 import FTA rates, 2,514 export FTA rates
- 21 sections (NOT 20 — count from actual data), 98 chapters
- Chapter detail endpoint returns FULL hierarchy in one response (headings -> subheadings -> hs_codes -> fta_rates) — no need for separate HS code fetch
- Search endpoint uses code prefix + description ilike (not pg_trgm similarity)
- BrowseChaptersResponse wraps chapters list + section notes (notes_vn, notes_en)
- Schemas use `from_attributes=True` pattern

**Previous code review patterns to avoid:**
- Not testing error/edge cases
- Forgetting loading states
- Not handling null values in optional fields (export_duty_rate, special_consumption_tax, etc.)
- Missing keyboard accessibility

### Git Intelligence (Recent Commits)

| Commit | Description | Relevance |
|--------|-------------|-----------|
| f4ff03f | 2-2 done | Browse API endpoints complete — these are the endpoints this story consumes |
| 626cd8e | 2-1 done | Data model expanded — DB has all rate fields |
| 63e6eb3 | new epic 2 | Epic 2 created |
| 62b1c38 | 1-13 done | Lookup detail page — frontend pattern reference |
| ad58766 | 1-12 done | Lookup list page — pagination pattern reference |

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Frontend | Next.js | 16+ | App Router, React 19, TypeScript |
| State | useState/useCallback | React 19 | Local state only for this page |
| Styling | Tailwind CSS | Latest | Utility-first |
| Icons | lucide-react | Latest | ChevronRight, ChevronDown, Search, X, Loader2, Info |
| UI | shadcn/ui | Latest | Use existing Button, Input, Card components |
| Testing | Vitest | Latest | jsdom environment |

### Anti-Patterns (NEVER DO)

- **NEVER** use Next.js API routes to proxy browse endpoints — call FastAPI directly via apiClient
- **NEVER** use Zustand store for browse page state — this is page-local state only
- **NEVER** preload all chapter details on mount — lazy load on expand only
- **NEVER** use status enums for loading states — use boolean flags (`isLoading`, `isError`)
- **NEVER** put tests in a separate `/tests` directory — co-locate with components
- **NEVER** use camelCase for API response field names in TypeScript types — match API snake_case
- **NEVER** include `embedding` field in any browse types — it's 3072 floats, massive payload (API already excludes it)
- **NEVER** fetch all sections + chapters + details on page load — progressive loading only
- **NEVER** modify existing API endpoints, schemas, or backend code — this is frontend ONLY
- **NEVER** modify existing pages (`/search`, `/lookups`) — only add `/browse` page and update Header nav

### Project Structure Notes

**Files to CREATE:**
```
web/src/app/browse/page.tsx                          # Main page
web/src/app/browse/loading.tsx                       # Loading skeleton
web/src/app/browse/error.tsx                         # Error boundary
web/src/app/browse/components/SectionList.tsx        # Section list
web/src/app/browse/components/SectionList.test.tsx   # Section list tests
web/src/app/browse/components/ChapterView.tsx        # Chapter tree view
web/src/app/browse/components/ChapterView.test.tsx   # Chapter view tests
web/src/app/browse/components/HSCodeRow.tsx          # HS code row with inline rates
web/src/app/browse/components/HSCodeRow.test.tsx     # HS code row tests
web/src/app/browse/components/HSCodeDetail.tsx       # Expanded HS code detail
web/src/app/browse/components/ChapterJumper.tsx      # Jump-to-chapter dropdown
web/src/app/browse/components/BrowseSearch.tsx       # Search within browser
web/src/app/browse/components/BrowseSearch.test.tsx  # Search tests
web/src/types/browse.ts                              # TypeScript types
```

**Files to MODIFY:**
```
web/src/components/layout/Header.tsx  # Add /browse nav link
web/src/lib/api.ts                    # Add browse API functions
```

**Files that MUST NOT be modified:**
```
web/src/app/search/**          — Search page unchanged
web/src/app/lookups/**         — Lookup pages unchanged
web/src/lib/store.ts           — Zustand store unchanged
api/**                         — No backend changes (Story 2-2 already done)
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.3]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-11.md]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend-Architecture]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Navigation-Patterns]
- [Source: _bmad-output/project-context.md#Frontend-Architecture]
- [Source: _bmad-output/implementation-artifacts/2-2-tariff-browse-api-endpoints.md — Browse API reference]
- [Source: web/src/app/lookups/page.tsx — Page pattern to follow]
- [Source: web/src/app/lookups/components/LookupList.tsx — List component pattern]
- [Source: web/src/app/search/components/SearchBar.tsx — Search input pattern]
- [Source: web/src/components/layout/Header.tsx — Navigation pattern]
- [Source: web/src/lib/api.ts — API client pattern]
- [Source: web/src/types/lookup.ts — TypeScript type definition pattern]
- [Source: api/app/schemas/browse.py — Backend schema reference for type alignment]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

### File List
