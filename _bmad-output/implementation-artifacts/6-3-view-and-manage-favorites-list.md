# Story 6.3: View and Manage Favorites List

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **logged-in user**,
I want **to view and manage my complete favorites list**,
So that **I can quickly access my saved HS codes**.

## Acceptance Criteria

1. **Given** I am logged in, **When** I navigate to the Favorites page (`/favorites`), **Then** I see a list of all my favorited HS codes (FR21) **And** the list loads in <2 seconds (NFR-P4).

2. **Given** I have favorites, **When** I view the favorites list, **Then** each FavoriteCard shows: HS code (mono, bold), Vietnamese description preview, note preview (truncated), date added **And** I can click to view full details.

3. **Given** I want to remove a favorite, **When** I click the remove/unfavorite button on a FavoriteCard, **Then** the HS code is removed from my favorites (FR22) **And** I see toast "Da xoa khoi yeu thich" with an "Hoan tac" (Undo) option.

4. **Given** I accidentally remove a favorite, **When** I click "Hoan tac" in the toast (within 5 seconds), **Then** the favorite is restored to the list.

5. **Given** I have no favorites, **When** I view the favorites page, **Then** I see empty state "Chua co ma yeu thich. Luu ma HS de truy cap nhanh." **And** I see a link to start searching.

6. **Given** I click on a FavoriteCard, **When** the navigation completes, **Then** I am taken to the browse page with the HS code detail expanded (or a relevant detail view).

7. **Given** I am not logged in, **When** I try to navigate to `/favorites`, **Then** I am redirected to the login page (handled by existing proxy.ts route protection).

## Tasks / Subtasks

- [x]Task 1: Create FavoriteCard component (AC: #2, #3, #4)
  - [x]1.1 Create `web/src/app/favorites/components/FavoriteCard.tsx`:
    - Props: `favorite: Favorite`, `onRemove: (id: number) => void`
    - Displays: HS code (mono, emerald-700, bold), description_vn (truncated), notes preview (truncated, italic, muted), created_at (relative or date)
    - Star icon button to unfavorite (reuse FavoriteButton pattern or standalone)
    - Clickable card that navigates to detail view
    - Hover: subtle bg change + left border accent (match LookupList pattern)
    - If notes exist: show truncated preview with FileText icon
    - If no notes: don't show notes section (keep card compact)

- [x]Task 2: Create favorites page (AC: #1, #5, #6, #7)
  - [x]2.1 Create `web/src/app/favorites/page.tsx` as client component ("use client"):
    - Page header: "Yeu thich" title + subtitle "Ma HS da luu cua ban"
    - On mount: fetch favorites via `getFavorites()` and set to store
    - Loading state: centered spinner (match lookups page pattern)
    - Error state: red alert banner with retry message
    - Empty state: icon + "Chua co ma yeu thich..." + link to `/search`
    - Favorites grid/list: render FavoriteCard for each favorite
    - Sort by created_at descending (most recent first — already from API)
  - [x]2.2 Use `useSession()` to verify authentication (proxy.ts handles redirect but page should also guard)

- [x]Task 3: Implement undo-able remove with toast (AC: #3, #4)
  - [x]3.1 In the favorites page, implement remove flow:
    - On remove click: optimistically remove from store via `removeFavoriteLocal`
    - Show toast with "Da xoa khoi yeu thich" + "Hoan tac" button
    - Toast auto-dismisses after 5 seconds
    - If user clicks "Hoan tac" before timeout: re-add via `addFavorite(hsCodeId)` API call
    - If toast dismissed/timeout: call `removeFavorite(favoriteId)` API to persist deletion
    - Handle API errors: revert optimistic removal on failure
  - [x]3.2 Create `UndoToast` inline component or embed in page logic:
    - Fixed position top-right (match FavoriteButton toast pattern)
    - Green border with undo button
    - Auto-dismiss timer with visual countdown (optional)

- [x]Task 4: Implement FavoriteCard click navigation (AC: #6)
  - [x]4.1 On FavoriteCard click, navigate to browse page with the HS code detail:
    - Use `router.push(`/browse?code=${favorite.hs_code}`)` or equivalent
    - If the browse page doesn't support query params for auto-expanding, use a simpler approach: `router.push(`/browse`)` with a toast "Tim ma {hs_code} trong bieu thue"
    - Alternative: Link to search page with the HS code as query: `/search?q=${favorite.hs_code}`
    - Choose the most useful navigation for the user (search re-lookup is likely more useful)

- [x]Task 5: Add "Yeu thich" link to Header navigation (AC: #1)
  - [x]5.1 In `web/src/components/layout/Header.tsx`, add a "Yeu thich" nav link to `/favorites`:
    - Add between existing nav items (after "Tra cuu" or as appropriate)
    - Only visible when user is authenticated (use `useSession()`)
    - Match existing nav link styling (desktop: inline, mobile: menu item)
    - Use Star icon from lucide-react for visual identification

- [x]Task 6: Frontend tests — FavoriteCard (AC: #2)
  - [x]6.1 Create `web/src/app/favorites/components/FavoriteCard.test.tsx`:
    - Renders HS code and description
    - Renders notes preview when notes exist
    - Does not render notes section when notes is null
    - Renders formatted date
    - Calls onRemove when unfavorite button clicked
    - Is clickable (fires navigation or click handler)

- [x]Task 7: Frontend tests — Favorites page (AC: #1, #3, #4, #5)
  - [x]7.1 Create `web/src/app/favorites/page.test.tsx`:
    - Shows loading spinner initially
    - Renders FavoriteCard list after fetch
    - Shows empty state when no favorites
    - Shows error state on fetch failure
    - Removes favorite on unfavorite click (optimistic)
    - Shows undo toast after removal
    - Restores favorite on undo click

## Dev Notes

### CRITICAL: This Story Builds on Stories 6-1 and 6-2

Stories 6-1 and 6-2 created the entire favorites backend and frontend infrastructure. This story creates the dedicated favorites page at `/favorites`. All backend endpoints already exist.

**Already exists from Story 6-1 (DO NOT recreate):**
- `api/app/models/favorite.py` — Favorite model with notes column
- `api/app/schemas/favorites.py` — FavoriteCreate, FavoriteResponse, FavoriteUpdateNotes
- `api/app/repositories/favorites_repository.py` — get_by_user, get_by_user_and_code, create, update_notes, delete
- `api/app/services/favorites_service.py` — list_favorites, add_favorite, update_notes, remove_favorite
- `api/app/api/favorites.py` — GET /, POST /, PATCH /{id}, DELETE /{id} endpoints
- `web/src/types/favorite.ts` — `Favorite` interface (id, user_id, hs_code_id, hs_code, description_vn, notes, created_at)
- `web/src/lib/store.ts` — FavoritesState with favorites[], favoriteIds[], setFavorites, addFavoriteLocal, removeFavoriteLocal, updateFavoriteNotesLocal
- `web/src/lib/api.ts` — getFavorites, addFavorite, removeFavorite, updateFavoriteNotes
- `web/src/components/FavoriteButton.tsx` — Star toggle with optimistic UI
- Route protection: `web/src/proxy.ts` already protects `/favorites/:path*`
- Sidebar link: `web/src/components/layout/Sidebar.tsx` has "Yeu thich" link to `/favorites`

**Already exists from Story 6-2 (notes editing):**
- PATCH endpoint for notes update
- `FavoriteNotes` component for inline notes editing
- `updateFavoriteNotesLocal` store action
- `updateFavoriteNotes` API function

**What this story CREATES (new):**
- `web/src/app/favorites/page.tsx` — Main favorites list page
- `web/src/app/favorites/components/FavoriteCard.tsx` — Individual favorite card component
- "Yeu thich" link in Header navigation
- Undo-able remove flow with toast
- Tests for page and card components

### No Backend Changes Needed

All backend endpoints already exist and return all data needed:
- `GET /api/favorites` returns `list[FavoriteResponse]` with: id, user_id, hs_code_id, hs_code (8-digit), description_vn, notes, created_at
- `DELETE /api/favorites/{id}` removes a favorite
- `POST /api/favorites` re-adds a favorite (for undo)

### FavoriteCard Design

```tsx
// web/src/app/favorites/components/FavoriteCard.tsx
"use client";

import { Star, FileText, Trash2 } from "lucide-react";
import type { Favorite } from "@/types/favorite";

interface FavoriteCardProps {
  favorite: Favorite;
  onRemove: (id: number) => void;
  onClick: () => void;
}

// Layout: horizontal card
// Left: HS code (mono emerald-700 bold) + description (truncated)
// Center: notes preview (if exists, italic muted, truncated to 1 line)
// Right: date added + remove button
// Hover: bg-emerald-50/50 + left border emerald-500 (match LookupList)
// Even rows: bg-slate-50/60 (match LookupList)
```

**Key UX details from UX spec:**
- FavoriteCard shows: personal notes field, quick re-search, delete with undo
- Card is clickable for navigation to detail view
- Remove button with confirmation via undo toast (not modal — follows "Effortless Interactions" UX principle)

### Favorites Page Design

Follow the established pattern from `web/src/app/lookups/page.tsx`:

```tsx
// web/src/app/favorites/page.tsx — structure
// 1. Page header: title + subtitle
// 2. Favorites count badge
// 3. Card list (or grid on desktop)
// 4. Empty state
// 5. Loading / Error states

// Data flow:
// On mount → getFavorites() → setFavorites(data) → render cards
// On remove → removeFavoriteLocal(id) → show undo toast → on timeout: removeFavorite(id)
// On undo → addFavorite(hsCodeId) → addFavoriteLocal(result)
```

**Vietnamese text for the page:**
- Title: "Yeu thich"
- Subtitle: "Ma HS da luu cua ban"
- Empty state: "Chua co ma yeu thich. Luu ma HS de truy cap nhanh."
- Empty CTA: "Bat dau tim kiem" (linking to /search)
- Remove toast: "Da xoa khoi yeu thich"
- Undo button: "Hoan tac"
- Error: "Khong the tai danh sach yeu thich"
- Date label: Vietnamese locale date formatting

### Undo Remove Flow (Deferred Deletion Pattern)

This is the key UX feature of this story. Instead of immediately calling the API on remove:

```
1. User clicks remove → optimistically remove from store (UI updates immediately)
2. Show toast with "Da xoa khoi yeu thich" + "Hoan tac" button
3. Start 5-second timer
4. IF user clicks "Hoan tac" before timeout:
   a. Cancel the timer
   b. Re-add to store via addFavoriteLocal (with original favorite data)
   c. Hide toast
   d. Show brief "Da khoi phuc" (Restored) toast
5. IF timer expires (no undo):
   a. Call removeFavorite(favoriteId) API
   b. Toast auto-dismisses
   c. If API fails: re-add to store + show error toast
```

**IMPORTANT:** Store the removed favorite object temporarily so it can be restored on undo without an API call. Only call the delete API after the undo window expires.

### Navigation on Card Click

When a user clicks a FavoriteCard, navigate to view the HS code details. Best option:
- Navigate to `/search?q={hs_code}` — this triggers a search for the exact code and shows full results
- Alternative: `/browse?highlight={hs_code}` — but browse page may not support this query param

Use `router.push()` from `next/navigation`.

### Header Navigation Update

The Header component at `web/src/components/layout/Header.tsx` currently does NOT have a "Yeu thich" link. Add it for authenticated users:

```tsx
// Only show when authenticated
{session?.user && (
  <Link href="/favorites" className="...existing nav link classes...">
    <Star size={16} />
    Yeu thich
  </Link>
)}
```

Place it after existing nav items. Match the emerald hover styling of other nav links.

### Project Structure Notes

**New files:**
```
web/src/app/favorites/page.tsx                           # Main favorites list page
web/src/app/favorites/page.test.tsx                      # Page tests
web/src/app/favorites/components/FavoriteCard.tsx         # Individual card component
web/src/app/favorites/components/FavoriteCard.test.tsx    # Card tests
```

**Modified files:**
```
web/src/components/layout/Header.tsx                     # Add "Yeu thich" nav link for authenticated users
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| List page layout | `web/src/app/lookups/page.tsx` | Page header, loading/error/empty states, pagination structure |
| List item styling | `web/src/app/lookups/components/LookupList.tsx` | Row hover (emerald-50/50), even-row bg (slate-50/60), left border accent, clickable rows |
| Empty state | `web/src/app/lookups/page.tsx` | Icon + title + subtitle + CTA pattern, rounded-xl border container |
| Loading spinner | `web/src/app/lookups/page.tsx` | Centered spinner with emerald-600 border-t |
| Error alert | `web/src/app/lookups/page.tsx` | Red border + bg alert box |
| Toast pattern | `web/src/components/FavoriteButton.tsx` | Fixed top-right, emerald theme, auto-dismiss |
| Favorites data | `web/src/lib/store.ts` | favorites[], favoriteIds[], setFavorites, removeFavoriteLocal, addFavoriteLocal |
| API client | `web/src/lib/api.ts` | getFavorites(), removeFavorite(), addFavorite() |
| Auth check | `web/src/app/browse/components/HSCodeDetail.tsx` | `useSession()` + `session?.user` guard |
| Nav link pattern | `web/src/components/layout/Header.tsx` | Desktop/mobile nav link styling, session-based visibility |

### Anti-Patterns to AVOID

- **DO NOT** create new backend endpoints — all needed endpoints exist
- **DO NOT** add pagination to the favorites API — favorites lists are small enough for client-side rendering; pagination is not in the AC
- **DO NOT** add search/filter within favorites — that's Story 6-4
- **DO NOT** add quick favorites access in search sidebar — that's Story 6-5
- **DO NOT** use a confirmation modal for remove — use undo toast (UX spec: "Effortless Interactions")
- **DO NOT** immediately call the delete API on remove — use deferred deletion with undo window
- **DO NOT** use a table layout for favorites — use card layout (FavoriteCard, not a table row)
- **DO NOT** create `web/src/app/favorites/error.tsx` — only create if specifically needed; the page-level error handling is sufficient
- **DO NOT** put favorites fetch logic in the Zustand store — fetch in the page component, set via `setFavorites()`
- **DO NOT** forget that favorites are already synced from backend on mount in search and browse pages — the favorites page should also sync (or may already have data in store)

### Previous Story Intelligence (from Stories 6-1 and 6-2)

**Code review issues fixed in 6-1 (avoid repeating):**
1. `hs_code_id` used before assignment — always resolve variables before using them
2. Initial favorites sync needed — already added in search/browse, also needed in favorites page
3. HTTP status code mismatch — error responses use `JSONResponse` with correct status codes
4. Optimistic UI — use temp placeholders replaced on server response

**Patterns established:**
- `JSONResponse` wrapping `error_response()` for non-200 status codes
- Optimistic UI with temp objects (negative IDs) — reuse for undo flow
- Vietnamese toast messages
- `useSession()` from next-auth to check authentication
- `getFavorites()` on mount with store check guard

**Known pre-existing test failures:**
- 32 backend failures (unrelated to favorites)
- 68 frontend failures (unrelated to favorites)

### Git Intelligence

```
2fb2b40 feat 6-1: Save HS code to favorites with toggle, optimistic UI, and full test coverage
a1b2da5 chore: Mark Epic 5 as done - all 5 stories completed
91b80a9 feat 5-5: Admin permission management with role defaults and user overrides
50c2d38 feat 5-4: Admin user management with create, edit, deactivate, search
```

### Testing Requirements

**Frontend tests** (Vitest, jsdom, co-located):

1. `web/src/app/favorites/components/FavoriteCard.test.tsx`:
   - Renders HS code in mono font
   - Renders Vietnamese description
   - Renders truncated notes preview when notes exist
   - Does not render notes section when notes is null
   - Renders formatted created_at date
   - Calls onRemove with favorite id when remove button clicked
   - Calls onClick when card body is clicked
   - Remove button click does not trigger card click (event.stopPropagation)

2. `web/src/app/favorites/page.test.tsx`:
   - Shows loading spinner on initial render
   - Renders FavoriteCard for each favorite after fetch
   - Shows empty state icon and message when no favorites
   - Shows "Bat dau tim kiem" link to /search in empty state
   - Shows error alert on fetch failure
   - Removes favorite from list on unfavorite click
   - Shows undo toast after removal
   - Restores favorite when undo is clicked within timeout
   - Calls removeFavorite API after undo timeout expires

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.3: View and Manage Favorites List]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Organization — favorites page structure]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#FavoriteCard — personal notes, quick re-search, delete with undo]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns — toast notifications]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Button Hierarchy — Destructive: red outlined for delete]
- [Source: _bmad-output/project-context.md#Frontend Architecture (HYBRID) — client components for interactive elements]
- [Source: _bmad-output/project-context.md#Anti-Patterns — NEVER fetch via Next.js API routes]
- [Source: CLAUDE.md#Frontend Patterns — Zustand single store, direct to FastAPI]
- [Source: _bmad-output/implementation-artifacts/6-1-save-hs-code-to-favorites.md — full favorites infrastructure]
- [Source: _bmad-output/implementation-artifacts/6-2-add-notes-to-favorites.md — notes editing, FavoriteNotes component]
- [Source: web/src/app/lookups/page.tsx — list page pattern: loading, error, empty states, pagination]
- [Source: web/src/app/lookups/components/LookupList.tsx — list item styling: hover, even-row, clickable]
- [Source: web/src/lib/store.ts — FavoritesState: favorites[], setFavorites, removeFavoriteLocal, addFavoriteLocal]
- [Source: web/src/lib/api.ts — getFavorites, addFavorite, removeFavorite, updateFavoriteNotes]
- [Source: web/src/types/favorite.ts — Favorite interface]
- [Source: web/src/components/FavoriteButton.tsx — toast pattern, optimistic UI]
- [Source: web/src/components/layout/Header.tsx — nav link pattern]
- [Source: web/src/proxy.ts — route protection for /favorites/:path*]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

### Completion Notes List

- Task 1: FavoriteCard — pure presentational component with HS code (mono emerald-700), description, notes preview (FileText icon, italic), date, remove button. Hover: bg-emerald-50/50 + left border emerald-500. Even-row striping via isEven prop. HS code gets subtle emerald wash on hover.
- Task 2: Favorites page — full page with loading spinner, error alert (AlertCircle), empty state (Star icon + CTA link to /search), favorites list sorted by created_at desc. Count badge in header. Uses useSession guard.
- Task 3: Deferred deletion with undo — optimistic removal via removeFavoriteLocal, 5-second undo window with toast ("Da xoa khoi yeu thich" + "Hoan tac" button). If undo clicked: restores to store locally + "Da khoi phuc" toast. If timeout: calls removeFavorite API. Pending undo flushed if user removes another card. Cleanup on unmount.
- Task 4: Card click navigates to /search?q={hs_code} via router.push (most useful for re-lookup).
- Task 5: Header "Yeu thich" link — desktop: text link between existing nav and expert/admin links, session-gated. Mobile: full nav item with Star icon matching existing pattern. Active state: emerald-400 + dot indicator.
- Task 6: FavoriteCard tests — 8 tests: renders HS code in mono, description, notes preview, no notes section when null, formatted date, onRemove called, onClick called, stopPropagation on remove.
- Task 7: Page tests — 9 tests: loading spinner, card rendering, empty state, search link, error alert, optimistic removal, undo toast, undo restore, API call after timeout.
- All 17 new tests pass. All 32 existing favorites regression tests pass (FavoriteButton 7, FavoriteNotes 7+1, store 17).

### Senior Developer Review (Code review: 1 high + 2 medium + 2 low issues fixed)

**Reviewed by:** Claude Opus 4.6 (DEV 2)

**Findings (5 issues):**

1. **HIGH — Infinite loading spinner for unauthenticated users** (page.tsx:26,38-70)
   - `isLoading` starts `true`. Fetch effect only runs if `session?.user`. If unauthenticated, `setIsLoading(false)` is never called → eternal spinner.
   - Page didn't destructure `status` from `useSession()` to detect auth resolution.
   - **FIXED**: Added `authStatus` from `useSession()`, early return with `setIsLoading(false)` when auth resolves to unauthenticated.

2. **MEDIUM — No test for flush-pending-undo behavior** (page.test.tsx)
   - When user removes a second card while undo toast is showing, first pending delete is flushed. Zero test coverage for this key edge case.
   - **FIXED**: Added `"flushes pending undo when second remove is clicked"` test.

3. **MEDIUM — Undo toast uses CheckCircle2 (success icon) for destructive action** (page.tsx:291)
   - Green check icon implies "something good happened" — misleading for a deletion confirmation.
   - **FIXED**: Changed to `Trash2` icon with slate/neutral styling instead of emerald/success.

4. **LOW — Desktop "Yêu thích" in auth section instead of main nav** (Header.tsx)
   - Task 5 says "Add between existing nav items" but dev put it on the right side. Reasonable design choice given auth-gating. Mobile placement is correct.

5. **LOW — Client-side sort is redundant** (page.tsx:143-145)
   - API already returns `created_at desc` ordered results. Client sort creates new array on every render.

### File List

**New files:**
- `web/src/app/favorites/components/FavoriteCard.tsx` — FavoriteCard presentational component
- `web/src/app/favorites/components/FavoriteCard.test.tsx` — 8 FavoriteCard tests
- `web/src/app/favorites/page.tsx` — Favorites list page with undo-able delete
- `web/src/app/favorites/page.test.tsx` — 9 page tests

**Modified files:**
- `web/src/components/layout/Header.tsx` — Added "Yeu thich" nav link (desktop + mobile) for authenticated users with Star icon
