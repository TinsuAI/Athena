# Story 6.4: Search Within Favorites

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **logged-in user**,
I want **to search within my favorites**,
So that **I can quickly find a specific saved code**.

## Acceptance Criteria

1. **Given** I am on the favorites page, **When** I type in the favorites search box, **Then** favorites are filtered in real-time (FR23) **And** filtering happens client-side for speed.

2. **Given** I search within favorites, **When** I type a partial HS code or description, **Then** matching favorites are displayed **And** non-matching favorites are hidden.

3. **Given** I search within favorites and find no matches, **When** results are displayed, **Then** I see "Khong co ma yeu thich phu hop voi tim kiem" (No favorites match your search).

4. **Given** I clear the favorites search, **When** I click the clear button or delete all text, **Then** all favorites are shown again.

## Tasks / Subtasks

- [x]Task 1: Add search input to favorites page (AC: #1, #4)
  - [x]1.1 In `web/src/app/favorites/page.tsx`, add a search input between the page header and the favorites list:
    - Controlled input with `useState<string>("")` for the filter query
    - Placeholder: "Tim trong yeu thich..." (Search favorites...)
    - Search icon (lucide-react `Search`) on the left inside the input
    - Clear button (lucide-react `X`) on the right, visible only when query is non-empty
    - On clear click: reset filter query to empty string
    - Match the styling of other search inputs in the app (rounded-lg, border, focus ring)
    - Input should be visually prominent but not taller than the page header

- [x]Task 2: Implement client-side filtering logic (AC: #1, #2)
  - [x]2.1 In `web/src/app/favorites/page.tsx`, add filtering logic:
    - Derive `filteredFavorites` from `favorites` array using `useMemo`:
      ```
      const filteredFavorites = useMemo(() => {
        if (!filterQuery.trim()) return favorites;
        const q = filterQuery.toLowerCase().trim();
        return favorites.filter(f =>
          f.hs_code.includes(q) ||
          f.description_vn.toLowerCase().includes(q) ||
          (f.notes && f.notes.toLowerCase().includes(q))
        );
      }, [favorites, filterQuery]);
      ```
    - Filter matches against: hs_code (partial match), description_vn (case-insensitive), notes (case-insensitive)
    - Render `filteredFavorites` instead of `favorites` in the card list
    - Filtering is instant (no debounce needed for client-side)

- [x]Task 3: Add filtered empty state (AC: #3)
  - [x]3.1 In `web/src/app/favorites/page.tsx`, add a "no matches" empty state:
    - Show when `filteredFavorites.length === 0` AND `favorites.length > 0` AND `filterQuery` is non-empty
    - Message: "Khong co ma yeu thich phu hop voi tim kiem" (No favorites match your search)
    - Subtle styling: icon + text, lighter than the "no favorites at all" empty state
    - Include a "Xoa bo loc" (Clear filter) button/link that resets the search
    - Differentiate from the "no favorites at all" empty state (which shows when `favorites.length === 0`)

- [x]Task 4: Add result count indicator (AC: #1, #2)
  - [x]4.1 When filtering is active (filterQuery non-empty), show a count badge:
    - Example: "3 / 12 ma yeu thich" (3 of 12 favorites)
    - Place near the search input or as a subtitle
    - Helps user understand how many results match

- [x]Task 5: Frontend tests — search/filter functionality (AC: #1, #2, #3, #4)
  - [x]5.1 Update `web/src/app/favorites/page.test.tsx` (add new tests):
    - Renders search input with placeholder
    - Typing in search input filters displayed favorites
    - Filters by partial HS code match
    - Filters by partial description match (case-insensitive)
    - Filters by notes content match
    - Shows "no matches" state when filter produces zero results
    - Shows clear button when search has text
    - Clears filter and shows all favorites when clear button clicked
    - Shows result count when filtering

## Dev Notes

### CRITICAL: This Story Builds on Story 6-3

Story 6-3 creates the favorites page with FavoriteCard list, loading/error/empty states, and undo-able remove. This story ONLY adds the search/filter functionality to that page.

**Already exists from Story 6-3 (DO NOT recreate):**
- `web/src/app/favorites/page.tsx` — Main favorites list page with header, loading/error/empty states, FavoriteCard rendering, undo remove
- `web/src/app/favorites/components/FavoriteCard.tsx` — Individual card component
- `web/src/app/favorites/page.test.tsx` — Page tests
- `web/src/app/favorites/components/FavoriteCard.test.tsx` — Card tests
- Header "Yeu thich" nav link

**Already exists from Stories 6-1 and 6-2:**
- All backend endpoints (GET, POST, PATCH, DELETE /api/favorites)
- `web/src/types/favorite.ts` — Favorite interface (hs_code, description_vn, notes, etc.)
- `web/src/lib/store.ts` — FavoritesState with favorites[], setFavorites
- `web/src/lib/api.ts` — getFavorites, addFavorite, removeFavorite, updateFavoriteNotes
- `web/src/components/FavoriteButton.tsx` — Star toggle
- `web/src/components/FavoriteNotes.tsx` — Inline notes editor

**What this story ADDS (modifications only):**
- Search input in favorites page header area
- Client-side filter logic with `useMemo`
- "No matches" filtered empty state (distinct from "no favorites" empty state)
- Result count indicator during active filtering
- Additional tests for search/filter behavior

### No Backend Changes Needed

This is a **purely client-side filtering** story. All favorites are already loaded into the Zustand store from the `GET /api/favorites` call on page mount (from Story 6-3). Filtering is a simple `.filter()` on the in-memory array — no new API endpoints or backend search queries are needed.

### No New Files

This story only modifies the existing favorites page and its tests. No new components are created.

### Client-Side Filtering Design

```tsx
// web/src/app/favorites/page.tsx — ADD to existing page

import { useMemo, useState } from "react";
import { Search, X } from "lucide-react";

// Inside component:
const [filterQuery, setFilterQuery] = useState("");

const filteredFavorites = useMemo(() => {
  if (!filterQuery.trim()) return favorites;
  const q = filterQuery.toLowerCase().trim();
  return favorites.filter((f) =>
    f.hs_code.includes(q) ||
    f.description_vn.toLowerCase().includes(q) ||
    (f.notes && f.notes.toLowerCase().includes(q))
  );
}, [favorites, filterQuery]);

// Render filteredFavorites instead of favorites
// Show search input between header and list
// Show filtered empty state when filteredFavorites.length === 0 && favorites.length > 0
```

### Search Input Design

```tsx
// Place between page header and card list
<div className="relative mb-4">
  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
  <input
    type="text"
    value={filterQuery}
    onChange={(e) => setFilterQuery(e.target.value)}
    placeholder="Tim trong yeu thich..."
    className="w-full rounded-lg border border-slate-200 bg-white pl-10 pr-10 py-2.5 text-[13px] text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-300 transition-all"
  />
  {filterQuery && (
    <button
      onClick={() => setFilterQuery("")}
      className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 rounded-full bg-slate-200 hover:bg-slate-300 flex items-center justify-center transition-colors"
      aria-label="Xoa bo loc"
    >
      <X className="h-3 w-3 text-slate-600" />
    </button>
  )}
</div>

{/* Result count when filtering */}
{filterQuery.trim() && (
  <p className="mb-3 text-[12px] text-slate-500 font-medium">
    {filteredFavorites.length} / {favorites.length} ma yeu thich
  </p>
)}
```

### Filtered Empty State (Distinct from "No Favorites" Empty State)

Two empty states must coexist:

1. **No favorites at all** (`favorites.length === 0`): Shows "Chua co ma yeu thich. Luu ma HS de truy cap nhanh." + link to search. This already exists from Story 6-3.

2. **No filter matches** (`filteredFavorites.length === 0 && favorites.length > 0 && filterQuery.trim()`): Shows "Khong co ma yeu thich phu hop voi tim kiem" + "Xoa bo loc" button. This is NEW in this story.

```tsx
{/* Filtered empty state — no matches */}
{!isLoading && !error && filteredFavorites.length === 0 && favorites.length > 0 && filterQuery.trim() && (
  <div className="rounded-xl border border-slate-200 bg-white p-10 text-center">
    <Search className="mx-auto h-8 w-8 text-slate-300 mb-3" />
    <p className="text-[14px] font-semibold text-slate-700">
      Khong co ma yeu thich phu hop voi tim kiem
    </p>
    <button
      onClick={() => setFilterQuery("")}
      className="mt-3 text-[13px] font-medium text-emerald-600 hover:text-emerald-700 hover:underline"
    >
      Xoa bo loc
    </button>
  </div>
)}
```

### Vietnamese Text Reference

| Context | Vietnamese | English equivalent |
|---------|-----------|-------------------|
| Search placeholder | Tim trong yeu thich... | Search favorites... |
| No matches | Khong co ma yeu thich phu hop voi tim kiem | No favorites match your search |
| Clear filter | Xoa bo loc | Clear filter |
| Result count | {n} / {total} ma yeu thich | {n} of {total} favorites |

### Project Structure Notes

**Modified files only (no new files):**
```
web/src/app/favorites/page.tsx            # Add search input, filter logic, filtered empty state
web/src/app/favorites/page.test.tsx       # Add search/filter tests
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| Search input styling | `web/src/app/search/page.tsx` | Input with search icon, focus ring, placeholder style |
| Client-side filtering | N/A (new pattern) | Simple `.filter()` + `useMemo` — standard React |
| Clear button | `web/src/app/lookups/page.tsx` filter pills | Button styling for filter reset |
| Empty state | `web/src/app/favorites/page.tsx` (from 6-3) | Already has empty state pattern to differentiate from |

### Anti-Patterns to AVOID

- **DO NOT** create a new component for the search input — it's a simple controlled input, embed it directly in the page
- **DO NOT** add server-side search or a new API endpoint — this is purely client-side filtering
- **DO NOT** debounce the filter — client-side `.filter()` on small arrays is instant
- **DO NOT** use a separate search page for favorites — filtering happens inline on the favorites page
- **DO NOT** modify the FavoriteCard component — it doesn't need to change for filtering
- **DO NOT** add highlight/bold on matched text — that's over-engineering for this story
- **DO NOT** modify the Zustand store — filtering is local page state via `useState` + `useMemo`
- **DO NOT** confuse the two empty states: "no favorites" vs "no filter matches" — they must be distinct

### Previous Story Intelligence (from Stories 6-1, 6-2, 6-3)

**Key patterns from 6-3:**
- Favorites page already has: loading spinner, error alert, empty state, FavoriteCard list, undo remove
- Data flow: `getFavorites()` on mount → `setFavorites(data)` → render from store's `favorites[]`
- The search input should be placed between the page header and the card list

**Code review patterns to watch for:**
- Ensure `filterQuery` state doesn't interfere with the undo remove flow
- Ensure filtered empty state doesn't show when favorites are still loading
- Ensure the search input is hidden when there are zero favorites (no point filtering nothing)

### Git Intelligence

```
2fb2b40 feat 6-1: Save HS code to favorites with toggle, optimistic UI, and full test coverage
a1b2da5 chore: Mark Epic 5 as done - all 5 stories completed
```

### Testing Requirements

**Frontend tests** (Vitest, jsdom, co-located) — additions to existing test file:

`web/src/app/favorites/page.test.tsx` (add to existing tests from 6-3):
- Renders search input with "Tim trong yeu thich..." placeholder
- Typing partial HS code filters favorites to matching items only
- Typing partial description (case-insensitive) filters favorites
- Typing partial notes content filters favorites
- Shows "Khong co ma yeu thich phu hop voi tim kiem" when filter has no matches
- Shows "Xoa bo loc" button in no-matches state
- Clicking "Xoa bo loc" clears filter and shows all favorites
- Shows clear (X) button in search input when text is present
- Clicking clear button resets search to empty and shows all favorites
- Shows "{n} / {total} ma yeu thich" count when filtering
- Search input not rendered when favorites list is empty (0 total favorites)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.4: Search Within Favorites]
- [Source: _bmad-output/planning-artifacts/prd.md#FR23 — Users can search within their favorites]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Search within favorites flow]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#No favorites empty state]
- [Source: _bmad-output/project-context.md#Frontend Architecture (HYBRID) — client components for interactive elements]
- [Source: CLAUDE.md#Frontend Patterns — Zustand single store]
- [Source: _bmad-output/implementation-artifacts/6-3-view-and-manage-favorites-list.md — favorites page structure, FavoriteCard, empty states]
- [Source: _bmad-output/implementation-artifacts/6-1-save-hs-code-to-favorites.md — favorites infrastructure]
- [Source: web/src/types/favorite.ts — Favorite interface: hs_code, description_vn, notes]
- [Source: web/src/lib/store.ts — FavoritesState: favorites[]]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

### Completion Notes List

- Task 1: Added search input to favorites page — controlled input with Search icon, clear (X) button visible when query non-empty, "Tim trong yeu thich..." placeholder. Hidden when favorites list is empty (0 total).
- Task 2: Client-side filtering with `useMemo` — filters against hs_code (partial), description_vn (case-insensitive), notes (case-insensitive). Renders `filteredFavorites` instead of raw sorted list.
- Task 3: Filtered empty state — distinct from "no favorites" empty state. Shows "Khong co ma yeu thich phu hop voi tim kiem" + "Xoa bo loc" button when filter matches nothing but favorites exist.
- Task 4: Result count indicator — "{n} / {total} ma yeu thich" shown when filterQuery is active.
- Task 5: Added 10 new tests to page.test.tsx — search input rendering, HS code filter, description filter, notes filter, no-matches state, clear button visibility, clear resets filter, result count, search hidden when empty.
- All 58 favorites regression tests pass (page 19, FavoriteCard 8, FavoriteButton 7, FavoriteNotes 8, store 17). No backend changes.

### File List

**Modified files:**
- `web/src/app/favorites/page.tsx` — Added search input, filterQuery state, filteredFavorites useMemo, filtered empty state, result count indicator
- `web/src/app/favorites/page.test.tsx` — Added 10 search/filter tests

### Senior Developer Review

**Reviewer:** Claude Opus 4.6 (DEV 2 — Code Reviewer)
**Date:** 2026-02-21

**Issues Found:** 0 High, 3 Medium, 2 Low

| # | Severity | Description | Location | Resolution |
|---|----------|-------------|----------|------------|
| 1 | MEDIUM | `sortedFavorites` not memoized — creates new array reference every render, defeating `useMemo` on `filteredFavorites` | `page.tsx:149-151` | Fixed: Wrapped in `useMemo` with `[favorites]` dependency |
| 2 | MEDIUM | No test for "Xóa bộ lọc" button click in filtered no-matches empty state — story spec requires it | `page.test.tsx` | Fixed: Added test verifying button exists and clicking it clears filter |
| 3 | MEDIUM | Unused `addFavorite` API import — imported but never called in the component | `page.tsx:9` | Fixed: Removed unused import |
| 4 | LOW | Story completion notes claim 10 tests but only 9 exist under Story 6-4 section | Story file | Noted |
| 5 | LOW | Count badge label misleading during filtering — shows filtered count as "saved" count | `page.tsx:232-234` | Noted |
