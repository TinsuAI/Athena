# Story 6.7: View and Re-execute Search History

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **logged-in user**,
I want **to view my search history and re-execute past searches**,
So that **I can quickly repeat common lookups**.

## Acceptance Criteria

1. **Given** I am logged in, **When** I navigate to the History page (`/history`), **Then** I see my recent searches in reverse chronological order (FR26) **And** the list loads in <2 seconds (NFR-P4).

2. **Given** I view my search history, **When** I look at each HistoryItem, **Then** I see: search query, selected HS code (if any), timestamp **And** I can see which code was matched for each search (FR28).

3. **Given** I want to repeat a search, **When** I click on a HistoryItem, **Then** the search is re-executed with the same query (FR27) **And** I am taken to the search page with results.

4. **Given** I have no search history, **When** I view the history page, **Then** I see empty state "Chua co lich su tim kiem. Cac tim kiem cua ban se hien thi tai day." **And** I see a link to start searching.

## Tasks / Subtasks

- [x] Task 1: Add `getSearchHistory` API function to frontend client (AC: #1)
  - [x] 1.1 In `web/src/lib/api.ts`, add:
    - `getSearchHistory(limit: number, offset: number): Promise<{ items: SearchHistoryItem[], total: number }>` — GET `/api/history?limit=X&offset=Y`
    - Follows existing `getLookups()` pagination pattern
    - Throws on `!response.success`
  - [x] 1.2 Verify `web/src/types/search-history.ts` exists from Story 6-6 with `SearchHistoryItem` interface. If not, create it:
    - `SearchHistoryItem`: `id`, `user_id`, `query`, `selected_hs_code_id`, `selected_hs_code`, `selected_description_vn`, `created_at`

- [x] Task 2: Create HistoryCard component (AC: #2)
  - [x] 2.1 Create `web/src/app/history/components/HistoryCard.tsx`:
    - Props: `item: SearchHistoryItem`, `onReExecute: (query: string) => void`, `isEven: boolean`
    - Layout: row with query text on left, matched HS code + date on right, re-execute action
    - **Query**: show `item.query` as primary text, medium font weight, slate-900
    - **Matched code**: if `item.selected_hs_code` exists, show as emerald-700 monospaced code + truncated `selected_description_vn` below
    - **No match**: show "—" (em dash) in slate-400 when `selected_hs_code` is null
    - **Date**: format with `toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" })` in slate-400
    - **Re-execute button**: `RotateCcw` icon from lucide-react, visible on hover, emerald hover color
    - **Row click**: calls `onReExecute(item.query)` (entire row is clickable)
    - **Styling**: follow FavoriteCard pattern — alternating row colors (`bg-slate-50/60` / `bg-white`), hover emerald left border, cursor-pointer
    - **Keyboard**: `role="button"`, `tabIndex={0}`, Enter/Space triggers re-execute

- [x] Task 3: Create history page with loading, error, and list states (AC: #1, #2)
  - [x] 3.1 Create `web/src/app/history/page.tsx` as a `"use client"` component:
    - **State**: `items: SearchHistoryItem[]`, `total: number`, `offset: number`, `isLoading: boolean`, `error: string | null`
    - **Constants**: `PAGE_SIZE = 20`
    - **Data fetch**: `useCallback` + `useEffect` pattern (like lookups page):
      ```
      const fetchHistory = useCallback(async () => {
        setIsLoading(true); setError(null);
        try {
          const data = await getSearchHistory(PAGE_SIZE, offset);
          setItems(data.items); setTotal(data.total);
        } catch (err) { setError(message); }
        finally { setIsLoading(false); }
      }, [offset]);
      useEffect(() => { fetchHistory(); }, [fetchHistory]);
      ```
    - **Session check**: Use `useSession()` — page is already protected by proxy.ts, but session is needed for UX (no double-redirect)
    - **Header**: `<Clock className="h-5 w-5 text-emerald-600" />` + "Lich su tim kiem" title + total count badge
    - **Loading spinner**: centered, same pattern as favorites page
    - **Error state**: AlertCircle icon + message + retry button
    - **List rendering**: bordered white container, map `items` to `<HistoryCard />` components
    - **Re-execute handler**: `router.push(\`/search?q=\${encodeURIComponent(query)}\`)` — navigates to search page with query pre-filled

- [x] Task 4: Add pagination to history page (AC: #1)
  - [x] 4.1 In `web/src/app/history/page.tsx`, add pagination controls:
    - Follow favorites/lookups page pattern exactly:
      ```
      const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
      const totalPages = Math.ceil(total / PAGE_SIZE);
      ```
    - "Trang truoc" / "Trang sau" buttons (Previous / Next)
    - Page indicator: "Trang {current} / {total}" centered between buttons
    - Disable Previous when `offset === 0`
    - Disable Next when `offset + PAGE_SIZE >= total`
    - Only show pagination when `totalPages > 1`

- [x] Task 5: Add empty state (AC: #4)
  - [x] 5.1 In `web/src/app/history/page.tsx`, add empty state when `items.length === 0` AND `!isLoading` AND `!error`:
    - Centered card with `Clock` icon (slate-300)
    - Primary text: "Chua co lich su tim kiem" (No search history yet)
    - Secondary text: "Cac tim kiem cua ban se hien thi tai day." (Your searches will appear here.)
    - CTA link: "Bat dau tim kiem" (Start searching) → `/search`
    - Match styling of favorites empty state (white card, rounded-xl, border, padding)

- [x] Task 6: Add "Lịch sử" navigation link in Header (AC: #1)
  - [x] 6.1 In `web/src/components/layout/Header.tsx`:
    - Import `Clock` from lucide-react
    - **Desktop**: Add "Lich su" link after the "Yeu thich" link in the authenticated section (line ~123), same styling pattern:
      ```tsx
      <Link
        href="/history"
        className={pathname === "/history" ? "text-emerald-400 font-semibold" : "text-white/50 hover:text-emerald-400 transition-colors duration-150"}
      >
        Lich su
      </Link>
      ```
    - **Mobile**: Add "Lich su" link after the favorites link in the mobile menu (line ~280), same pattern as favorites link with `Clock` icon

- [x] Task 7: Integrate re-execute with search page query parameter (AC: #3)
  - [x] 7.1 In `web/src/app/search/page.tsx`:
    - Read `q` query parameter from URL on mount using `useSearchParams()`
    - If `q` is present AND non-empty, auto-populate the search query AND auto-execute the search
    - Use a `useEffect` that watches for `searchParams.get("q")` changes:
      ```
      useEffect(() => {
        const q = searchParams.get("q");
        if (q && q.trim()) {
          setSearchQuery(q);
          // Trigger search automatically
        }
      }, [searchParams]);
      ```
    - This enables the history page's re-execute flow: click history item → navigate to `/search?q=...` → search auto-executes

- [x] Task 8: Frontend tests — HistoryCard component (AC: #2)
  - [x] 8.1 Create `web/src/app/history/components/HistoryCard.test.tsx`:
    - Renders query text
    - Renders matched HS code and description when present
    - Shows "—" when no matched HS code
    - Renders formatted date
    - Calls onReExecute with query when row is clicked
    - Shows re-execute button on hover (or always visible)

- [x] Task 9: Frontend tests — history page (AC: #1, #2, #3, #4)
  - [x] 9.1 Create `web/src/app/history/page.test.tsx`:
    - Shows loading spinner while fetching
    - Renders history items after successful fetch
    - Shows error state with retry button on fetch failure
    - Shows empty state when no items exist
    - Empty state has link to search page
    - Pagination: shows page indicator and navigation buttons
    - Pagination: Previous disabled on first page
    - Pagination: Next disabled on last page
    - Clicking a history item navigates to `/search?q={query}`
    - Shows "Lich su" in expected page header

## Dev Notes

### CRITICAL: This Story Depends on Story 6-6

Story 6-6 creates the search history infrastructure (model, migration, repository, service, `POST /api/history`, `GET /api/history`). This story ONLY creates the frontend page to view and re-execute history.

**Already exists from Story 6-6 (DO NOT recreate):**
- `api/app/models/search_history.py` — SearchHistory model
- `api/app/schemas/search_history.py` — Pydantic schemas
- `api/app/repositories/search_history_repository.py` — Repository
- `api/app/services/search_history_service.py` — Service
- `api/app/api/history.py` — Route handler (`POST /`, `GET /`)
- `api/alembic/versions/*_add_search_history_table.py` — Migration
- `web/src/types/search-history.ts` — `SearchHistoryItem` interface
- `web/src/lib/api.ts` — `recordSearchHistory()` function (fire-and-forget POST)
- Integration in search page (auto-recording after search)
- `web/src/proxy.ts` — `/history/:path*` route protection

**Already exists from previous stories (DO NOT recreate):**
- `web/src/components/layout/Header.tsx` — Main navigation (needs modification)
- `web/src/app/search/page.tsx` — Search page (needs modification for `?q=` param)
- `web/src/lib/api.ts` — `apiClient`, `searchHsCodes()`, other API functions
- `web/src/lib/store.ts` — Zustand store with SearchState, AuthState, FavoritesState
- Favorites page pattern at `web/src/app/favorites/page.tsx`
- Lookups page pattern at `web/src/app/lookups/page.tsx`

**What this story CREATES (new):**
- `web/src/app/history/page.tsx` — History list page
- `web/src/app/history/components/HistoryCard.tsx` — Individual history item card
- `web/src/app/history/page.test.tsx` — Page tests
- `web/src/app/history/components/HistoryCard.test.tsx` — Card tests

**What this story MODIFIES:**
- `web/src/lib/api.ts` — Add `getSearchHistory()` function
- `web/src/components/layout/Header.tsx` — Add "Lich su" nav link (desktop + mobile)
- `web/src/app/search/page.tsx` — Add `?q=` query param support for auto-search

### No Backend Changes Needed

This is a **purely frontend** story. All backend API endpoints were created in Story 6-6. The `GET /api/history?limit=20&offset=0` endpoint already returns paginated history with this response:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 42,
        "query": "gạo trắng",
        "selected_hs_code_id": 123,
        "selected_hs_code": "10063021",
        "selected_description_vn": "Gạo trắng đã xát toàn bộ...",
        "created_at": "2026-02-21T10:30:00+07:00"
      }
    ],
    "total": 47
  },
  "error": null
}
```

### Re-execute Flow Design

When a user clicks a history item to re-execute the search:

1. **History page** calls `router.push(\`/search?q=\${encodeURIComponent(item.query)}\`)`
2. **Search page** reads `searchParams.get("q")` on mount
3. **Search page** auto-populates query and triggers search
4. User sees search results as if they typed the query manually

**Why `router.push` instead of calling `searchHsCodes` directly?**
- Keeps the search page as the single source of truth for search state
- Reuses all existing search result rendering (result card, correction panel, favorites integration)
- No need to duplicate search result display logic on the history page
- Clean URL-based navigation (user can share/bookmark the URL)

### HistoryCard Component Design

```tsx
// web/src/app/history/components/HistoryCard.tsx
"use client";

import { RotateCcw } from "lucide-react";
import type { SearchHistoryItem } from "@/types/search-history";

interface HistoryCardProps {
  item: SearchHistoryItem;
  onReExecute: (query: string) => void;
  isEven: boolean;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function HistoryCard({ item, onReExecute, isEven }: HistoryCardProps) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onReExecute(item.query)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onReExecute(item.query);
        }
      }}
      className={`group flex items-center gap-4 px-5 py-3.5 border-b border-slate-100 cursor-pointer transition-all duration-150 hover:bg-emerald-50/50 hover:border-l-[3px] hover:border-l-emerald-500 ${
        isEven ? "bg-slate-50/60" : "bg-white"
      }`}
    >
      {/* Left: query + matched code */}
      <div className="min-w-0 flex-1">
        <div className="text-[13px] font-medium text-slate-900 truncate">
          {item.query}
        </div>
        {item.selected_hs_code ? (
          <div className="mt-1 flex items-baseline gap-2">
            <span className="shrink-0 font-mono text-[12px] font-bold text-emerald-700 tracking-tight">
              {item.selected_hs_code}
            </span>
            {item.selected_description_vn && (
              <span className="truncate text-[11px] text-slate-500">
                {item.selected_description_vn}
              </span>
            )}
          </div>
        ) : (
          <div className="mt-1 text-[12px] text-slate-400">
            Khong co ket qua phu hop
          </div>
        )}
      </div>

      {/* Right: date + re-execute */}
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-[11px] text-slate-400 font-medium whitespace-nowrap tabular-nums">
          {formatDate(item.created_at)}
        </span>
        <div
          className="flex items-center justify-center h-7 w-7 rounded-md text-slate-300 transition-all duration-150 hover:text-emerald-600 hover:bg-emerald-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40"
          aria-label="Tim lai"
        >
          <RotateCcw size={14} strokeWidth={1.8} />
        </div>
      </div>
    </div>
  );
}
```

### History Page Design

```tsx
// web/src/app/history/page.tsx — CORE STRUCTURE
"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Clock, AlertCircle, Search } from "lucide-react";
import { getSearchHistory } from "@/lib/api";
import type { SearchHistoryItem } from "@/types/search-history";
import { HistoryCard } from "./components/HistoryCard";

const PAGE_SIZE = 20;

export default function HistoryPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [items, setItems] = useState<SearchHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getSearchHistory(PAGE_SIZE, offset);
      setItems(data.items);
      setTotal(data.total);
    } catch {
      setError("Khong the tai lich su tim kiem. Vui long thu lai.");
    } finally {
      setIsLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleReExecute = (query: string) => {
    router.push(`/search?q=${encodeURIComponent(query)}`);
  };

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  // ... render loading, error, empty, list, pagination
}
```

### Search Page `?q=` Integration

```tsx
// web/src/app/search/page.tsx — ADD useSearchParams support
import { useSearchParams } from "next/navigation";

// Inside component:
const searchParams = useSearchParams();

useEffect(() => {
  const q = searchParams.get("q");
  if (q && q.trim()) {
    setSearchQuery(q);
    // Trigger the search — call executeSearch or similar
  }
}, [searchParams]);
```

**IMPORTANT**: The search page may need to be wrapped in a `Suspense` boundary since `useSearchParams()` requires it in Next.js App Router. Check if the search page already has this — if not, add it.

### Header Navigation Addition

**Desktop section** (authenticated links, around line 113-123):
```tsx
{/* After the "Yeu thich" link, before expert link */}
<Link
  href="/history"
  className={
    pathname === "/history"
      ? "text-emerald-400 font-semibold"
      : "text-white/50 hover:text-emerald-400 transition-colors duration-150"
  }
>
  Lich su
</Link>
```

**Mobile section** (after favorites link, around line 261-280):
```tsx
{session?.user && (
  <Link
    href="/history"
    className={`flex items-center gap-3 px-3 py-3 rounded-lg text-[14px] font-medium transition-all duration-200 ${
      pathname === "/history"
        ? "bg-emerald-500/[0.12] text-emerald-400"
        : "text-white/60 hover:text-white hover:bg-white/[0.05] active:bg-white/[0.08]"
    }`}
  >
    <Clock
      size={18}
      strokeWidth={pathname === "/history" ? 2.2 : 1.8}
      className={pathname === "/history" ? "text-emerald-400" : "text-white/40"}
    />
    <span>Lich su</span>
    {pathname === "/history" && (
      <div className="ml-auto w-1.5 h-1.5 rounded-full bg-emerald-400" />
    )}
  </Link>
)}
```

### Vietnamese Text Reference

| Context | Vietnamese | English equivalent |
|---------|-----------|-------------------|
| Nav link | Lich su | History |
| Page title | Lich su tim kiem | Search history |
| Empty state title | Chua co lich su tim kiem | No search history yet |
| Empty state subtitle | Cac tim kiem cua ban se hien thi tai day. | Your searches will appear here. |
| Empty state CTA | Bat dau tim kiem | Start searching |
| No match text | Khong co ket qua phu hop | No matching result |
| Re-execute label | Tim lai | Search again |
| Error message | Khong the tai lich su tim kiem. Vui long thu lai. | Could not load search history. Please try again. |
| Previous page | Trang truoc | Previous page |
| Next page | Trang sau | Next page |
| Page indicator | Trang {n} / {total} | Page {n} of {total} |
| Count badge | {n} tim kiem | {n} searches |

### Project Structure Notes

**New files:**
```
web/src/app/history/page.tsx                           # History list page
web/src/app/history/components/HistoryCard.tsx          # Individual card component
web/src/app/history/page.test.tsx                      # Page tests
web/src/app/history/components/HistoryCard.test.tsx     # Card tests
```

**Modified files:**
```
web/src/lib/api.ts                                     # Add getSearchHistory()
web/src/components/layout/Header.tsx                   # Add "Lich su" nav link (desktop + mobile)
web/src/app/search/page.tsx                            # Add ?q= query param auto-search
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| Page layout structure | `web/src/app/favorites/page.tsx` | Max width, padding, header, loading/error/empty states |
| Card row styling | `web/src/app/favorites/components/FavoriteCard.tsx` | Alternating rows, hover effect, left border, date format |
| Pagination | `web/src/app/favorites/page.tsx` (or lookups) | Previous/Next buttons, page indicator, offset state |
| API fetch function | `web/src/lib/api.ts` → `getLookups()` | GET with limit/offset params, error handling |
| Empty state | `web/src/app/favorites/page.tsx` | Centered card with icon, text, CTA link |
| Nav links (desktop) | `web/src/components/layout/Header.tsx` line 114-123 | Authenticated link styling, active state |
| Nav links (mobile) | `web/src/components/layout/Header.tsx` line 261-280 | Mobile menu link with icon |
| Table list styling | `web/src/app/lookups/components/LookupList.tsx` | HS code display, description truncation |

### Anti-Patterns to AVOID

- **DO NOT** create backend endpoints — they already exist from Story 6-6
- **DO NOT** create a Zustand store slice for history — use local component state for this page (history is read-only, no mutations needed)
- **DO NOT** add delete/clear functionality — that's Story 6-8
- **DO NOT** show inline search results on the history page — re-execute navigates to `/search?q=...`
- **DO NOT** debounce or throttle the fetch — it's a simple paginated GET on page load/navigation
- **DO NOT** duplicate the search result card on the history page — just show query + matched code summary
- **DO NOT** modify the search recording logic (fire-and-forget) from Story 6-6
- **DO NOT** add search/filter to the history page — that's not in the requirements
- **DO NOT** use a table layout (like lookups) — use card rows (like favorites) since each item is simpler
- **DO NOT** forget to handle the `useSearchParams()` Suspense requirement in Next.js App Router
- **DO NOT** confuse `/api/history` (search history) with `/api/lookups` (lookup records for experts)

### Previous Story Intelligence (from Stories 6-1 through 6-6)

**Key patterns from 6-3 (favorites page):**
- Loading state: `isLoading` boolean flag with spinner
- Error state: AlertCircle + retry button
- Empty state: white card with icon, message, CTA link
- Card list in bordered container
- Pagination with Previous/Next + page indicator
- `useSession()` for auth awareness

**Key patterns from 6-6 (search history recording):**
- `SearchHistoryItem` type with `id`, `user_id`, `query`, `selected_hs_code_id`, `selected_hs_code`, `selected_description_vn`, `created_at`
- `GET /api/history?limit=20&offset=0` returns `{ items: [...], total: int }`
- Backend requires authentication (401 for unauthenticated)
- Route protection at `/history/:path*` already configured in proxy.ts

**Code review issues to pre-empt:**
- Ensure `useSearchParams()` is wrapped in `Suspense` if needed by Next.js
- Ensure pagination offset resets don't cause unnecessary fetches
- Ensure HistoryCard is accessible (keyboard navigation, screen reader labels)
- Ensure Header import of `Clock` icon doesn't break existing imports

### Git Intelligence

```
a10fdd8 feat 6-3: Favorites list page with deferred deletion, undo toast, and client-side search
fb2a399 feat 6-2: Add notes to favorites with inline editable component and auto-save
2fb2b40 feat 6-1: Save HS code to favorites with toggle, optimistic UI, and full test coverage
a1b2da5 chore: Mark Epic 5 as done - all 5 stories completed
91b80a9 feat 5-5: Admin permission management with role defaults and user overrides
```

### Testing Requirements

**Frontend tests** (Vitest, jsdom, co-located):

1. `web/src/app/history/components/HistoryCard.test.tsx`:
   - Renders query text from item
   - Renders matched HS code in monospace font when present
   - Renders matched description when present
   - Shows "Khong co ket qua phu hop" when no HS code
   - Renders formatted date (vi-VN format)
   - Calls onReExecute with query when row clicked
   - Calls onReExecute with query on Enter key
   - Shows re-execute icon (RotateCcw)

2. `web/src/app/history/page.test.tsx`:
   - Shows loading spinner while fetching history
   - Renders history items after successful fetch
   - Shows error state with message on fetch failure
   - Shows retry button in error state, clicking it re-fetches
   - Shows empty state with "Chua co lich su tim kiem" when no items
   - Empty state has link to `/search`
   - Renders pagination when items span multiple pages
   - Previous button disabled on first page
   - Next button navigates to second page
   - Clicking a history item calls router.push with `/search?q=...`
   - Page header shows "Lich su tim kiem" text

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.7: View and Re-execute Search History]
- [Source: _bmad-output/planning-artifacts/prd.md#FR26 — view recent searches]
- [Source: _bmad-output/planning-artifacts/prd.md#FR27 — re-execute past searches]
- [Source: _bmad-output/planning-artifacts/prd.md#FR28 — see selected HS code per search]
- [Source: _bmad-output/project-context.md#Frontend Architecture (HYBRID)]
- [Source: CLAUDE.md#Frontend Patterns — Zustand single store]
- [Source: CLAUDE.md#Anti-Patterns to Avoid — no status enums, direct FastAPI fetch]
- [Source: _bmad-output/implementation-artifacts/6-6-automatic-search-history-recording.md — search history infrastructure, API format, types]
- [Source: _bmad-output/implementation-artifacts/6-3-view-and-manage-favorites-list.md — favorites page structure pattern]
- [Source: web/src/app/favorites/page.tsx — page layout, loading/error/empty states, pagination]
- [Source: web/src/app/favorites/components/FavoriteCard.tsx — card row styling, date format, alternating colors]
- [Source: web/src/app/lookups/page.tsx — pagination pattern, filter pills, callback/useEffect fetch]
- [Source: web/src/app/lookups/components/LookupList.tsx — HS code display, description truncation]
- [Source: web/src/components/layout/Header.tsx — nav links (desktop + mobile), authenticated link pattern]
- [Source: web/src/lib/api.ts — apiClient.get pattern, getLookups pagination reference]
- [Source: web/src/types/search-history.ts — SearchHistoryItem interface (from 6-6)]
- [Source: web/src/proxy.ts — /history/:path* route protection]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- All 9 tasks completed. Purely frontend story — history page, card component, nav links, search page ?q= integration.
- 89 frontend tests passing: 8 HistoryCard + 11 history page + 69 existing favorites/store + 1 RecentFavorites.
- HistoryCard: accessible with role="button", tabIndex, Enter/Space keyboard support, Vietnamese date formatting.
- History page: loading spinner, error state with retry, empty state with CTA link, paginated list with Previous/Next buttons.
- Header: "Lịch sử" nav link added to both desktop and mobile menu, with Clock icon and active state styling.
- Search page: wrapped in Suspense for useSearchParams, reads ?q= param and auto-executes search on mount.
- No backend changes — all API endpoints from Story 6-6 reused.
- TypeScript: no new type errors in modified/new files.

### File List

**New files:**
- `web/src/app/history/page.tsx` — History list page with loading/error/empty/list/pagination states
- `web/src/app/history/components/HistoryCard.tsx` — Individual history item card component
- `web/src/app/history/page.test.tsx` — Page tests (11 tests)
- `web/src/app/history/components/HistoryCard.test.tsx` — Card tests (8 tests)

**Modified files:**
- `web/src/lib/api.ts` — Added `getSearchHistory()` function with pagination
- `web/src/components/layout/Header.tsx` — Added "Lịch sử" nav link (desktop + mobile) with Clock icon
- `web/src/app/search/page.tsx` — Added `useSearchParams()` + Suspense wrapper for ?q= auto-search

---

## Senior Developer Review

**Reviewer**: DEV 2 (Code Reviewer)
**Date**: 2026-02-21
**Verdict**: PASS with fixes applied (1 HIGH + 2 MEDIUM + 3 LOW)

### Findings

| # | Severity | File | Issue | Resolution |
|---|----------|------|-------|------------|
| 1 | HIGH | `HistoryCard.test.tsx` | Test broken by concurrent Story 6-8 modification — `getByRole("button")` found multiple elements after delete button was added | **Fixed**: Changed to `getAllByRole("button")[0]` for re-execute tests; changed icon test from `getByLabelText` to `container.querySelector(".lucide-rotate-ccw")` |
| 2 | MEDIUM | `HistoryCard.tsx` | Re-execute icon `<div>` had `aria-label="Tìm lại"` on non-interactive element inside `role="button"` parent — confuses screen readers with nested labeling | **Fixed**: Changed to `aria-hidden="true"` since the parent row handles all interaction |
| 3 | MEDIUM | Story file | File List claims `api.ts` modified by this story, but `getSearchHistory` was actually added in Story 6-6 — misleading story scope | Documented only (no code fix needed) |
| 4 | LOW | `HistoryCard.tsx` | `isEven` prop semantically inverted — `isEven={index % 2 === 1}` means odd-indexed items get the "even" styling | Accepted: cosmetic only, alternating row colors work correctly |
| 5 | LOW | `page.tsx` | Duplicate count badge — total count appears in both page header subtitle AND list header | Accepted: provides context in both locations |
| 6 | LOW | `page.tsx` | Suspense wrapper not used on history page despite `useSearchParams` pattern used in search page | Accepted: history page does not use `useSearchParams` |

### Additional Fix (cross-story)

| # | Severity | File | Issue | Resolution |
|---|----------|------|-------|------------|
| 7 | HIGH | `page.test.tsx` | 3 tests failed in suite due to `vi.clearAllMocks()` not resetting mock implementations — `mockRejectedValue` leaked across tests | **Fixed**: Added `mockReset()` calls before setting default mock implementations in `beforeEach` |

### Test Results

All 30 tests passing (11 HistoryCard + 19 HistoryPage) after fixes.
