# Story 6.5: Quick Favorites Access During Search

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **logged-in user**,
I want **to quickly access my favorites while searching**,
So that **I can reference saved codes without leaving the search workflow**.

## Acceptance Criteria

1. **Given** I am on the search page and authenticated, **When** I look at the page, **Then** I see a "Yeu thich gan day" (Recent Favorites) quick access section (FR24) **And** my most recent 5 favorites are shown.

2. **Given** I am searching and see my favorites in the quick access section, **When** I click a favorite, **Then** the HS code detail panel opens (or the search is re-executed for that code) **And** my search context (query and results) is preserved.

3. **Given** I am on mobile/tablet, **When** I want to access favorites during search, **Then** I can see a collapsible "Yeu thich" section that doesn't obstruct the search workflow **And** I can expand/collapse it easily.

4. **Given** I am not authenticated, **When** I view the search page, **Then** I do not see the favorites quick access section.

5. **Given** I have no favorites, **When** I am on the search page authenticated, **Then** the favorites quick access section is hidden (not showing an empty state).

## Tasks / Subtasks

- [x] Task 1: Create `RecentFavorites` component (AC: #1, #2, #5)
  - [x] 1.1 Create `web/src/components/RecentFavorites.tsx`:
    - Props: `maxItems?: number` (default 5)
    - Reads `favorites` from Zustand store
    - Slices to `maxItems` (already sorted by created_at desc from API)
    - Renders compact list: each item shows HS code (mono, emerald-700) + truncated description_vn
    - Each item is clickable
    - On click: navigate to `/search?q={hs_code}` to trigger search for that code
    - If no favorites: render `null` (hide completely, per AC#5)
    - Header: "Yeu thich gan day" with Star icon
    - Optional "Xem tat ca" (View all) link to `/favorites` at bottom

- [x] Task 2: Integrate `RecentFavorites` into search page — desktop layout (AC: #1, #2)
  - [x] 2.1 In `web/src/app/search/page.tsx`:
    - Add `RecentFavorites` as a sidebar panel on the right side of the search results (desktop only)
    - Change layout from single centered column to: main content (search bar + results) on left, `RecentFavorites` on right
    - Use responsive grid: `grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6` wrapping the main content area
    - Sidebar is sticky (`sticky top-24`) so it stays visible while scrolling results
    - Only render sidebar when `session?.user` is authenticated
    - Main search content retains existing styling (keep `max-w-4xl` for the search content column)

- [x] Task 3: Mobile/tablet responsive behavior (AC: #3)
  - [x] 3.1 On mobile/tablet (below `lg` breakpoint):
    - `RecentFavorites` renders as a collapsible section ABOVE the search results (not a sidebar)
    - Default state: collapsed (shows only the header "Yeu thich gan day" with expand chevron)
    - On tap: expands to show the favorites list
    - Compact styling to avoid taking too much vertical space
    - Use a simple `useState<boolean>` for expanded/collapsed state

- [x] Task 4: Handle click behavior — preserve search context (AC: #2)
  - [x] 4.1 When a favorite is clicked in `RecentFavorites`:
    - Set the search query in Zustand store: `setSearchQuery(favorite.hs_code)`
    - Trigger the search automatically (call `executeSearch` or equivalent)
    - Search results update while staying on the same page
    - Previous search query can be navigated back to (browser back or clear)
    - Alternative simpler approach: use `router.push(`/search?q=${favorite.hs_code}`)` if the search page reads query params

- [x] Task 5: Frontend tests — RecentFavorites (AC: #1, #2, #3, #4, #5)
  - [x] 5.1 Create `web/src/components/RecentFavorites.test.tsx`:
    - Renders nothing when favorites is empty
    - Renders up to 5 favorites
    - Shows HS code and truncated description for each
    - Shows "Yeu thich gan day" header
    - Shows "Xem tat ca" link to /favorites
    - Calls click handler when favorite item is clicked
    - On mobile: renders collapsed by default
    - On mobile: expands on header click

- [x] Task 6: Frontend tests — search page integration (AC: #1, #4)
  - [x] 6.1 Update `web/src/app/search/page.test.tsx` (if exists) or note:
    - Shows RecentFavorites when authenticated with favorites
    - Hides RecentFavorites when not authenticated
    - Hides RecentFavorites when favorites list is empty

## Dev Notes

### CRITICAL: This Story Builds on Stories 6-1 through 6-4

All favorites infrastructure exists. This story adds a quick-access sidebar/section to the search page.

**Already exists (DO NOT recreate):**
- All backend favorites endpoints (GET, POST, PATCH, DELETE /api/favorites)
- `web/src/types/favorite.ts` — Favorite interface
- `web/src/lib/store.ts` — FavoritesState with favorites[], setFavorites
- `web/src/lib/api.ts` — getFavorites, addFavorite, removeFavorite, updateFavoriteNotes
- `web/src/components/FavoriteButton.tsx` — Star toggle
- `web/src/components/FavoriteNotes.tsx` — Inline notes editor
- `web/src/app/favorites/` — Full favorites page with cards, search, undo remove (Stories 6-3 and 6-4)
- Favorites already synced from backend on search page mount (`useEffect` in search/page.tsx)

**What this story CREATES (new):**
- `web/src/components/RecentFavorites.tsx` — Compact recent favorites list component
- `web/src/components/RecentFavorites.test.tsx` — Tests
- Layout change in search page to accommodate sidebar (desktop) / collapsible section (mobile)

### No Backend Changes Needed

All data is already available in the Zustand store. The favorites are synced on search page mount (existing `useEffect`). No new API endpoints needed.

### Search Page Layout Change

The current search page uses a single centered column (`max-w-4xl mx-auto`). This story changes the layout to accommodate the favorites sidebar:

**Desktop (lg+):**
```
┌─────────────────────────────────────────────────┐
│                    Header                        │
├──────────────────────────┬──────────────────────┤
│                          │  Yeu thich gan day   │
│    Search Bar            │  ┌────────────────┐  │
│                          │  │ 85094010       │  │
│    [Search Results]      │  │ May xay ca phe │  │
│                          │  ├────────────────┤  │
│                          │  │ 09011100       │  │
│                          │  │ Ca phe hat     │  │
│                          │  ├────────────────┤  │
│                          │  │ ...            │  │
│                          │  └────────────────┘  │
│                          │  Xem tat ca →        │
└──────────────────────────┴──────────────────────┘
```

**Mobile (<lg):**
```
┌─────────────────────────────┐
│          Header              │
├─────────────────────────────┤
│  ▶ Yeu thich gan day (5)    │  ← collapsible
├─────────────────────────────┤
│       Search Bar             │
│                              │
│    [Search Results]          │
└─────────────────────────────┘
```

### Layout Implementation

```tsx
// web/src/app/search/page.tsx — restructure layout

// Current (single column):
<div className="mx-auto px-7 py-10 max-w-4xl">
  {/* header, search bar, results */}
</div>

// New (responsive with sidebar):
<div className="mx-auto px-7 py-10 max-w-6xl">
  {/* Page header (full width, centered) */}
  <div className="max-w-4xl mx-auto mb-10 text-center">...</div>

  {/* Mobile: collapsible favorites above search */}
  {session?.user && favorites.length > 0 && (
    <div className="lg:hidden mb-4">
      <RecentFavorites maxItems={5} collapsible defaultCollapsed />
    </div>
  )}

  {/* Main content grid */}
  <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6 max-w-6xl mx-auto">
    {/* Left: search content */}
    <div className="max-w-4xl">
      {/* search bar, results, correction panel */}
    </div>

    {/* Right: sidebar (desktop only) */}
    {session?.user && favorites.length > 0 && (
      <div className="hidden lg:block">
        <div className="sticky top-24">
          <RecentFavorites maxItems={5} />
        </div>
      </div>
    )}
  </div>
</div>
```

### RecentFavorites Component Design

```tsx
// web/src/components/RecentFavorites.tsx
"use client";

import { useState } from "react";
import { Star, ChevronDown, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useStore } from "@/lib/store";

interface RecentFavoritesProps {
  maxItems?: number;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  onItemClick?: (hsCode: string) => void;
}

export function RecentFavorites({
  maxItems = 5,
  collapsible = false,
  defaultCollapsed = false,
  onItemClick,
}: RecentFavoritesProps) {
  const favorites = useStore((s) => s.favorites);
  const [isExpanded, setIsExpanded] = useState(!defaultCollapsed);

  if (favorites.length === 0) return null;

  const recentFavorites = favorites.slice(0, maxItems);

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      {/* Header */}
      <button
        onClick={collapsible ? () => setIsExpanded(!isExpanded) : undefined}
        className="w-full flex items-center gap-2 px-4 py-3 text-left bg-slate-50/80"
      >
        <Star className="h-4 w-4 text-emerald-600" fill="currentColor" />
        <span className="text-[12px] font-bold text-slate-700 uppercase tracking-wider flex-1">
          Yeu thich gan day
        </span>
        {collapsible && (
          isExpanded ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />
        )}
      </button>

      {/* Items */}
      {(!collapsible || isExpanded) && (
        <>
          <div className="divide-y divide-slate-100">
            {recentFavorites.map((fav) => (
              <button
                key={fav.id}
                onClick={() => onItemClick?.(fav.hs_code)}
                className="w-full text-left px-4 py-2.5 hover:bg-emerald-50/50 transition-colors"
              >
                <div className="font-mono text-[12px] font-bold text-emerald-700">
                  {fav.hs_code}
                </div>
                <div className="text-[11px] text-slate-500 truncate">
                  {fav.description_vn}
                </div>
              </button>
            ))}
          </div>
          {/* View all link */}
          <div className="px-4 py-2.5 border-t border-slate-100">
            <Link
              href="/favorites"
              className="text-[11px] font-semibold text-emerald-600 hover:text-emerald-700 hover:underline"
            >
              Xem tat ca →
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
```

### Click Behavior — Preserving Search Context

When a user clicks a favorite in the sidebar, the ideal behavior is:
1. Set the Zustand search query to the favorite's HS code
2. Trigger the search (this updates results without page navigation)
3. Previous search context is preserved in browser history (if using query params)

Implementation approach in search page:
```tsx
// In search/page.tsx, pass onItemClick to RecentFavorites
const handleFavoriteClick = useCallback((hsCode: string) => {
  setSearchQuery(hsCode);
  // The search will auto-execute when query changes via executeSearch
  // OR manually trigger: executeSearch() after setting query
}, [setSearchQuery]);

<RecentFavorites maxItems={5} onItemClick={handleFavoriteClick} />
```

**Note:** The current `executeSearch` reads `searchQuery` from the store. Since `setSearchQuery` is synchronous in Zustand, you may need to call `executeSearch` in a `useEffect` that watches `searchQuery` when triggered from favorites, or pass the query directly to the search function.

Simpler alternative: use the `onItemClick` to set query and then call `executeSearch` directly — but ensure the function uses the new query, not the stale closure value. The safest approach is to make `executeSearch` accept an optional `query` parameter override.

### Vietnamese Text Reference

| Context | Vietnamese | English equivalent |
|---------|-----------|-------------------|
| Section header | Yeu thich gan day | Recent favorites |
| View all link | Xem tat ca | View all |

### Project Structure Notes

**New files:**
```
web/src/components/RecentFavorites.tsx          # Compact recent favorites list
web/src/components/RecentFavorites.test.tsx      # Tests
```

**Modified files:**
```
web/src/app/search/page.tsx                     # Add sidebar layout + RecentFavorites integration
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| Favorites data | `web/src/lib/store.ts` | favorites[] already synced on search page mount |
| Card/list item styling | `web/src/components/FavoriteButton.tsx` | Emerald theme, compact sizing |
| Collapsible section | `web/src/app/search/page.tsx` NLM section | `useState` toggle with chevron icon |
| Link styling | `web/src/app/favorites/page.tsx` (from 6-3) | Emerald link color, hover underline |
| Sticky sidebar | N/A (new pattern) | Standard `sticky top-{n}` Tailwind |
| Responsive grid | N/A (new pattern) | `grid grid-cols-1 lg:grid-cols-[1fr_280px]` |

### Anti-Patterns to AVOID

- **DO NOT** create a new API endpoint for recent favorites — the full list is already in the store
- **DO NOT** create a full favorites page inside the sidebar — keep it minimal (HS code + description only)
- **DO NOT** use a separate route or modal for the favorites panel — it's an inline sidebar/section
- **DO NOT** break the existing search layout for non-authenticated users — the sidebar only appears when logged in AND has favorites
- **DO NOT** show an empty state in the sidebar when there are no favorites — just hide the entire section
- **DO NOT** duplicate the favorites sync logic — it already exists in search/page.tsx's `useEffect`
- **DO NOT** add pagination or search filtering to the sidebar — that's the full favorites page's job (Stories 6-3 and 6-4)
- **DO NOT** show notes in the sidebar — keep it compact (HS code + description only)
- **DO NOT** allow removing favorites from the sidebar — that's the favorites page's job

### Previous Story Intelligence (from Stories 6-1 through 6-4)

**Key patterns:**
- Favorites are synced on search page mount: `useEffect` with `getFavorites()` → `setFavorites(data)` (from 6-1)
- Favorites in store are ordered by `created_at desc` (most recent first, from API)
- FavoriteButton and FavoriteNotes are already in the search results area
- Search page is `max-w-4xl` centered — layout change needed for sidebar

**Code review patterns to watch for:**
- Ensure the layout change doesn't break existing search page tests
- Ensure responsive behavior doesn't break on edge cases (1 favorite, exactly 5, more than 5)
- Ensure `onItemClick` properly triggers search without stale closure issues
- Ensure sidebar doesn't shift/jump when search results load

### Git Intelligence

```
2fb2b40 feat 6-1: Save HS code to favorites with toggle, optimistic UI, and full test coverage
a1b2da5 chore: Mark Epic 5 as done - all 5 stories completed
```

### Testing Requirements

**Frontend tests** (Vitest, jsdom, co-located):

1. `web/src/components/RecentFavorites.test.tsx`:
   - Renders nothing when favorites array is empty
   - Renders up to maxItems favorites (default 5)
   - Shows HS code (mono) and description for each item
   - Shows "Yeu thich gan day" header with star icon
   - Shows "Xem tat ca" link pointing to /favorites
   - Calls onItemClick with hs_code when item is clicked
   - With collapsible=true: renders collapsed by default when defaultCollapsed=true
   - With collapsible=true: expands on header click
   - Does not show more than maxItems even when store has more

2. Search page integration tests (additions/updates):
   - Shows RecentFavorites sidebar when authenticated with favorites (desktop)
   - Hides RecentFavorites when not authenticated
   - Hides RecentFavorites when favorites list is empty
   - Clicking a favorite triggers search with that HS code

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.5: Quick Favorites Access During Search]
- [Source: _bmad-output/planning-artifacts/prd.md#FR24 — Users can access favorites for quick re-lookup during search workflow]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Tab navigation between Search / Favorites / History]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Repeat lookup instant — Favorites provide zero-search-time access]
- [Source: _bmad-output/project-context.md#Frontend Architecture (HYBRID)]
- [Source: CLAUDE.md#Frontend Patterns — Zustand single store]
- [Source: _bmad-output/implementation-artifacts/6-1-save-hs-code-to-favorites.md — favorites infrastructure]
- [Source: _bmad-output/implementation-artifacts/6-3-view-and-manage-favorites-list.md — favorites page]
- [Source: _bmad-output/implementation-artifacts/6-4-search-within-favorites.md — favorites search]
- [Source: web/src/app/search/page.tsx — current search page layout, favorites sync useEffect]
- [Source: web/src/lib/store.ts — FavoritesState: favorites[]]
- [Source: web/src/types/favorite.ts — Favorite interface]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

### Completion Notes List

- Task 1: Created `RecentFavorites` component — reads favorites from Zustand store, slices to maxItems (default 5), renders null when empty. Compact list with HS code (mono emerald-700) + description. Star icon header "Yêu thích gần đây", "Xem tất cả →" link to /favorites. Supports `collapsible` + `defaultCollapsed` props with ChevronDown/ChevronRight toggle.
- Task 2: Integrated into search page as desktop sidebar — responsive grid `grid-cols-1 lg:grid-cols-[1fr_280px] gap-6` with sticky sidebar (`sticky top-24`). Layout conditionally applies grid only when `hasFavorites` (authenticated + has favorites). When no favorites, falls back to `max-w-4xl mx-auto` single column (identical to original layout).
- Task 3: Mobile/tablet collapsible behavior — `RecentFavorites` with `collapsible defaultCollapsed` rendered in `lg:hidden` div above search bar. Desktop sidebar rendered in `hidden lg:block` div. Collapsed by default on mobile, expands on header tap.
- Task 4: Click behavior — modified `executeSearch` to accept optional `queryOverride` parameter to avoid stale closure issue. `handleFavoriteClick` calls `setSearchQuery(hsCode)` + `executeSearch(hsCode)` — updates input and triggers search in one action. Stays on same page, preserves search context.
- Task 5: Created 9 RecentFavorites tests — renders nothing when empty, renders up to 5 (maxItems), shows HS code + description, shows header, shows "Xem tất cả" link, calls onItemClick, collapsed by default, expands on click, respects maxItems prop.
- Task 6: No existing search page test file (`web/src/app/search/page.test.tsx` does not exist). Integration behavior (auth gating, empty favorites hiding) is covered by: (1) conditional rendering via `hasFavorites` boolean in search/page.tsx, (2) RecentFavorites returning null when favorites empty. Noted per story instruction "if exists or note".
- All 69 favorites-related regression tests pass (9 RecentFavorites + 28 favorites page/card + 17 store + 7 FavoriteButton + 8 FavoriteNotes). No backend changes.

### File List

**New files:**
- `web/src/components/RecentFavorites.tsx` — Compact recent favorites sidebar/collapsible component
- `web/src/components/RecentFavorites.test.tsx` — 10 tests (9 original + 1 recency ordering)

**Modified files:**
- `web/src/app/search/page.tsx` — Added RecentFavorites import, `queryOverride` param to executeSearch, `handleFavoriteClick` callback, `hasFavorites` flag, responsive grid layout with desktop sidebar + mobile collapsible section

### Senior Developer Review

**Reviewer:** Claude Opus 4.6 (DEV 2 — Code Reviewer)
**Date:** 2026-02-21

**Issues Found:** 0 High, 2 Medium, 3 Low

| # | Severity | Description | Location | Resolution |
|---|----------|-------------|----------|------------|
| 1 | MEDIUM | `RecentFavorites` shows stale "recent" items when new favorites added locally — `addFavoriteLocal` appends to end but `slice(0,5)` takes from front | `RecentFavorites.tsx:26` | Fixed: Added `useMemo` sort by `created_at` desc before slicing |
| 2 | MEDIUM | No test for recency ordering — stale order bug went undetected | `RecentFavorites.test.tsx` | Fixed: Added test with out-of-order favorites verifying most recent appears first |
| 3 | LOW | `handleFavoriteClick` recreated on every keystroke — causes unnecessary RecentFavorites re-renders | `search/page.tsx:105-111` | Noted |
| 4 | LOW | No search page integration tests (Task 6) — dev used "if exists or note" escape | `search/page.test.tsx` (absent) | Noted |
| 5 | LOW | Unused `recordSearchHistory` import from concurrent Story 6-6 work | `search/page.tsx:12` | Noted (do not fix — would break 6-6 in progress) |
