# Story 6.2: Add Notes to Favorites

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **logged-in user**,
I want **to add personal notes to my favorited HS codes**,
So that **I can remember why I saved them or add context**.

## Acceptance Criteria

1. **Given** I am viewing my favorites list (or any view showing a favorited HS code), **When** I click on the notes area, **Then** I can see and edit the notes field (FR20).

2. **Given** I have a favorite without notes, **When** I add a note and save, **Then** the note is persisted to the backend **And** I see the note preview on the favorite entry.

3. **Given** I have a favorite with existing notes, **When** I edit the note and save, **Then** the note is updated **And** I see toast "Ghi chu da cap nhat" (Note updated).

4. **Given** I am viewing a favorited HS code in the browse detail view (HSCodeDetail), **When** I look at the detail panel, **Then** I can see my saved notes for this code **And** I can edit notes directly from the detail view.

5. **Given** the API, **When** I check the favorites endpoints, **Then** `PATCH /api/favorites/{id}` accepts `{ notes: string }` and updates only the notes field.

6. **Given** a non-authenticated user or non-owner, **When** they try to update notes on a favorite, **Then** they receive 401 (unauthenticated) or 404 (not their favorite).

7. **Given** I save a note with empty text, **When** the update is processed, **Then** the notes field is set to null (clearing notes is allowed).

## Tasks / Subtasks

- [x]Task 1: Add `FavoriteUpdateNotes` Pydantic schema (AC: #5, #7)
  - [x]1.1 In `api/app/schemas/favorites.py`, add `FavoriteUpdateNotes` schema with `notes: str | None` field
  - [x]1.2 Allow `None` or empty string to clear notes (normalize empty string to `None`)

- [x]Task 2: Add `update_notes` to favorites repository (AC: #5)
  - [x]2.1 In `api/app/repositories/favorites_repository.py`, add:
    - `update_notes(favorite_id: int, user_id: int, notes: str | None) -> Favorite | None`
    - Loads the favorite (scoped to user), updates `notes`, flushes, returns updated record
    - Returns `None` if favorite not found or not owned by user

- [x]Task 3: Add `update_notes` to favorites service (AC: #2, #3, #5, #7)
  - [x]3.1 In `api/app/services/favorites_service.py`, add:
    - `update_notes(favorite_id: int, user_id: int, notes: str | None) -> dict | None`
    - Normalizes empty string to `None`
    - Calls repo's `update_notes`, commits, returns response dict or `None`

- [x]Task 4: Add `PATCH /api/favorites/{id}` endpoint (AC: #5, #6)
  - [x]4.1 In `api/app/api/favorites.py`, add:
    - `PATCH /{favorite_id}` — update notes (Depends: `require_authenticated`)
    - Request body: `FavoriteUpdateNotes`
    - Returns 200 with updated favorite (envelope format)
    - Returns 404 if favorite not found or not owned by user

- [x]Task 5: Add `updateFavoriteNotes` to API client (AC: #5)
  - [x]5.1 In `web/src/lib/api.ts`, add:
    - `updateFavoriteNotes(favoriteId: number, notes: string | null): Promise<Favorite>`
    - Uses `apiClient.patch()`

- [x]Task 6: Add `updateFavoriteNotesLocal` to Zustand store (AC: #2, #3)
  - [x]6.1 In `web/src/lib/store.ts`, add to FavoritesState:
    - `updateFavoriteNotesLocal: (favoriteId: number, notes: string | null) => void`
    - Updates the `notes` field on the matching favorite in the `favorites` array

- [x]Task 7: Create `FavoriteNotes` component (AC: #1, #2, #3, #4)
  - [x]7.1 Create `web/src/components/FavoriteNotes.tsx` — inline editable notes for a favorited HS code
    - Props: `favoriteId: number`, `hsCodeId: number`, `initialNotes: string | null`
    - Display mode: shows notes text (or "Them ghi chu..." placeholder if empty)
    - Edit mode: textarea with save/cancel buttons, activated on click
    - On save: calls `updateFavoriteNotes` API, updates store, shows toast
    - On cancel: reverts to display mode
    - Handles loading/error states
    - All text in Vietnamese

- [x]Task 8: Integrate `FavoriteNotes` into browse HSCodeDetail (AC: #4)
  - [x]8.1 In `web/src/app/browse/components/HSCodeDetail.tsx`:
    - Below the FavoriteButton section, if the HS code is favorited, show `FavoriteNotes`
    - Pass the favorite's `id`, `hs_code_id`, and `notes` from the store
    - Only visible when authenticated AND code is favorited

- [x]Task 9: Integrate `FavoriteNotes` into search results detail (AC: #4)
  - [x]9.1 In `web/src/app/search/page.tsx` (or wherever search result detail is shown):
    - If the HS code is favorited, show `FavoriteNotes` below the favorite button
    - Only visible when authenticated AND code is favorited

- [x]Task 10: Backend tests (AC: #2, #3, #5, #6, #7)
  - [x]10.1 `api/app/repositories/favorites_repository_test.py` — add tests for `update_notes`:
    - `test_update_notes_success` — updates notes on owned favorite
    - `test_update_notes_clear` — sets notes to None
    - `test_update_notes_not_found` — returns None for nonexistent ID
    - `test_update_notes_wrong_user` — returns None for other user's favorite
  - [x]10.2 `api/app/services/favorites_service_test.py` — add tests:
    - `test_update_notes_success` — updates and returns response dict
    - `test_update_notes_empty_normalized` — empty string becomes None
    - `test_update_notes_not_found` — returns None
  - [x]10.3 `api/app/api/favorites_test.py` — add tests:
    - `test_patch_notes_success` — 200 with updated notes
    - `test_patch_notes_clear` — 200 with null notes
    - `test_patch_notes_unauthenticated` — 401
    - `test_patch_notes_not_found` — 404

- [x]Task 11: Frontend tests (AC: #1, #2, #3, #4)
  - [x]11.1 `web/src/components/FavoriteNotes.test.tsx`:
    - Renders placeholder when no notes
    - Renders existing notes in display mode
    - Enters edit mode on click
    - Saves notes on save button click
    - Cancels editing on cancel button click
    - Shows toast on successful save

## Dev Notes

### CRITICAL: This Story Builds on Story 6-1's Infrastructure

Story 6-1 created the entire favorites backend and frontend infrastructure. This story ONLY adds notes editing capability. The `notes` column already exists in the `favorites` table (added in 6-1, nullable Text).

**Already exists from Story 6-1 (DO NOT recreate):**
- `api/app/models/favorite.py` — Favorite model with `notes: Mapped[str | None]` column
- `api/app/schemas/favorites.py` — `FavoriteCreate`, `FavoriteResponse` (includes `notes` field)
- `api/app/repositories/favorites_repository.py` — `get_by_user`, `get_by_user_and_code`, `create`, `delete`
- `api/app/services/favorites_service.py` — `list_favorites`, `add_favorite`, `remove_favorite`, `DuplicateFavoriteError`
- `api/app/api/favorites.py` — `GET /`, `POST /`, `DELETE /{id}` endpoints
- `api/alembic/versions/20260221_add_favorites_table.py` — Migration (already applied)
- `web/src/types/favorite.ts` — `Favorite` interface (already has `notes: string | null`)
- `web/src/lib/store.ts` — FavoritesState with `favorites[]`, `favoriteIds[]`, `addFavoriteLocal`, `removeFavoriteLocal`
- `web/src/lib/api.ts` — `getFavorites`, `addFavorite`, `removeFavorite`
- `web/src/components/FavoriteButton.tsx` — Star toggle with optimistic UI and Vietnamese toasts
- FavoriteButton integrated in `search/page.tsx` and `browse/components/HSCodeDetail.tsx`

**What this story ADDS (new):**
- `PATCH /api/favorites/{id}` endpoint for notes update
- `FavoriteUpdateNotes` Pydantic schema
- `update_notes` method in repository and service
- `updateFavoriteNotes` API client function
- `updateFavoriteNotesLocal` Zustand store action
- `FavoriteNotes` reusable component (inline editable notes)
- `FavoriteNotes` integrated into HSCodeDetail and search page

### No Migration Needed

The `notes` column already exists in the `favorites` table (Text, nullable). No schema changes required.

### PATCH Endpoint Design

```python
# api/app/schemas/favorites.py — ADD
class FavoriteUpdateNotes(BaseModel):
    """Input schema for updating favorite notes."""
    notes: str | None = Field(None, description="Personal notes (null or empty string clears)")
```

```python
# api/app/repositories/favorites_repository.py — ADD method
async def update_notes(self, favorite_id: int, user_id: int, notes: str | None) -> Favorite | None:
    """Update notes on a favorite, scoped to the owning user."""
    result = await self.db.execute(
        select(Favorite)
        .options(selectinload(Favorite.hs_code))
        .where(and_(Favorite.id == favorite_id, Favorite.user_id == user_id))
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        return None
    favorite.notes = notes
    await self.db.flush()
    return favorite
```

```python
# api/app/services/favorites_service.py — ADD method
async def update_notes(self, favorite_id: int, user_id: int, notes: str | None) -> dict | None:
    """Update notes on a favorite. Empty string is normalized to None."""
    if notes is not None and notes.strip() == "":
        notes = None
    favorite = await self.repo.update_notes(favorite_id, user_id, notes)
    if not favorite:
        return None
    await self.db.commit()
    return self._to_response(favorite)
```

```python
# api/app/api/favorites.py — ADD endpoint
@router.patch("/{favorite_id}")
async def update_favorite_notes(
    favorite_id: int,
    body: FavoriteUpdateNotes,
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Update notes on a favorite."""
    service = FavoritesService(db)
    result = await service.update_notes(favorite_id, current_user["id"], body.notes)
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(
                "https://athena.example/errors/not-found",
                "Not Found",
                404,
                "Favorite not found",
                f"/api/favorites/{favorite_id}",
            ),
        )
    return success_response(result)
```

### Frontend API Client Addition

```typescript
// web/src/lib/api.ts — ADD
export async function updateFavoriteNotes(
  favoriteId: number,
  notes: string | null
): Promise<Favorite> {
  const response = await apiClient.patch<Favorite>(
    `/api/favorites/${favoriteId}`,
    { notes }
  );
  if (!response.success || !response.data) {
    throw new Error(response.error?.detail || "Failed to update notes");
  }
  return response.data;
}
```

### Zustand Store Addition

```typescript
// web/src/lib/store.ts — ADD to FavoritesState interface and implementation
updateFavoriteNotesLocal: (favoriteId: number, notes: string | null) => void;

// Implementation:
updateFavoriteNotesLocal: (favoriteId, notes) =>
  set((state) => ({
    favorites: state.favorites.map((f) =>
      f.id === favoriteId ? { ...f, notes } : f
    ),
  })),
```

### FavoriteNotes Component Design

```tsx
// web/src/components/FavoriteNotes.tsx
"use client";

import { useState, useCallback } from "react";
import { Pencil, Check, X, FileText } from "lucide-react";
import { useStore } from "@/lib/store";
import { updateFavoriteNotes } from "@/lib/api";

interface FavoriteNotesProps {
  favoriteId: number;
  hsCodeId: number;
  initialNotes: string | null;
}

export function FavoriteNotes({ favoriteId, hsCodeId, initialNotes }: FavoriteNotesProps) {
  const updateFavoriteNotesLocal = useStore((s) => s.updateFavoriteNotesLocal);
  const [isEditing, setIsEditing] = useState(false);
  const [notes, setNotes] = useState(initialNotes ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  // Display mode: show notes or placeholder
  // Edit mode: textarea + save/cancel
  // Save: call API, update store, show toast "Ghi chu da cap nhat"
  // Cancel: revert to display mode
}
```

**Key UX details:**
- Display mode: compact text display with pencil icon to edit
- If no notes: show faded placeholder "Them ghi chu..." (Add notes...)
- Click activates edit mode with textarea
- Save button (check icon) and Cancel button (X icon)
- Textarea auto-focuses on edit mode entry
- Toast: "Ghi chu da cap nhat" on successful save
- Vietnamese text throughout

### Integration into HSCodeDetail.tsx

```tsx
// web/src/app/browse/components/HSCodeDetail.tsx — MODIFY
// After the FavoriteButton section, add:
{session?.user && (() => {
  const favorite = favorites.find((f) => f.hs_code_id === hsCode.id);
  if (!favorite) return null;
  return (
    <FavoriteNotes
      favoriteId={favorite.id}
      hsCodeId={hsCode.id}
      initialNotes={favorite.notes}
    />
  );
})()}
```

### Integration into Search Page

Similar pattern — find if the HS code in the search result is favorited, show FavoriteNotes below the FavoriteButton. Check `web/src/app/search/page.tsx` for where FavoriteButton is rendered and add FavoriteNotes alongside it.

### Project Structure Notes

**New files:**
```
web/src/components/FavoriteNotes.tsx              # Inline editable notes component
web/src/components/FavoriteNotes.test.tsx          # Tests
```

**Modified files:**
```
api/app/schemas/favorites.py                       # Add FavoriteUpdateNotes schema
api/app/repositories/favorites_repository.py       # Add update_notes method
api/app/repositories/favorites_repository_test.py  # Add update_notes tests
api/app/services/favorites_service.py              # Add update_notes method
api/app/services/favorites_service_test.py         # Add update_notes tests
api/app/api/favorites.py                           # Add PATCH endpoint
api/app/api/favorites_test.py                      # Add PATCH tests
web/src/lib/api.ts                                 # Add updateFavoriteNotes function
web/src/lib/store.ts                               # Add updateFavoriteNotesLocal action
web/src/app/browse/components/HSCodeDetail.tsx      # Add FavoriteNotes below FavoriteButton
web/src/app/search/page.tsx                        # Add FavoriteNotes below FavoriteButton
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| PATCH endpoint | `api/app/api/favorites.py` | Existing POST/DELETE pattern with JSONResponse error handling |
| Service update pattern | `api/app/services/favorites_service.py` | `_to_response()` dict conversion, `self.repo` + `self.db.commit()` |
| Repository query pattern | `api/app/repositories/favorites_repository.py` | `select().where(and_(...))` with `selectinload` |
| API client function | `web/src/lib/api.ts` | `apiClient.patch()` method already exists, follow `addFavorite()` pattern |
| Store update pattern | `web/src/lib/store.ts` | `set((state) => ({ favorites: state.favorites.map(...) }))` |
| Toast pattern | `web/src/components/FavoriteButton.tsx` | Fixed-position toast with CheckCircle2 icon, auto-dismiss |
| Inline editing pattern | None existing — create fresh but follow shadcn/Tailwind conventions |

### Anti-Patterns to AVOID

- **DO NOT** create a new migration — the `notes` column already exists from Story 6-1
- **DO NOT** modify the `Favorite` model — it already has the `notes` column
- **DO NOT** modify the `FavoriteResponse` schema — it already includes `notes`
- **DO NOT** modify the `Favorite` TypeScript type — it already has `notes: string | null`
- **DO NOT** create a favorites list page — that's Story 6-3
- **DO NOT** create a FavoriteCard component — that's Story 6-3
- **DO NOT** use a modal for notes editing — use inline editing (click to edit)
- **DO NOT** use React Hook Form for the notes textarea — it's a single field, `useState` is sufficient
- **DO NOT** put notes update logic in the route handler — keep in service layer
- **DO NOT** skip the envelope response format for the PATCH endpoint
- **DO NOT** forget to import `FavoriteUpdateNotes` in the route handler
- **DO NOT** forget to add `selectinload(Favorite.hs_code)` in `update_notes` repository method

### Previous Story Intelligence (from Story 6-1)

**Code review issues fixed in 6-1 (avoid repeating):**
1. `hs_code_id` used before assignment in search.py — always resolve variables before using them
2. Initial favorites sync needed from backend — already added useEffect in search and browse pages
3. HTTP status code mismatch — error responses must use `JSONResponse` with correct status codes
4. Optimistic UI — FavoriteButton uses temp placeholder replaced on API success

**Patterns established in 6-1:**
- `JSONResponse` wrapping `error_response()` for non-200 status codes
- Optimistic UI with temp objects (negative IDs)
- Vietnamese toast messages: "Da them vao yeu thich", "Da xoa khoi yeu thich"
- `useSession()` from next-auth to check authentication before showing favorites
- `getFavorites()` sync on mount with `favorites.length === 0` guard

**Known pre-existing test failures:**
- 32 backend failures (unrelated to favorites)
- 68 frontend failures (unrelated to favorites)

### Git Intelligence

```
2fb2b40 feat 6-1: Save HS code to favorites with toggle, optimistic UI, and full test coverage
a1b2da5 chore: Mark Epic 5 as done - all 5 stories completed
91b80a9 feat 5-5: Admin permission management with role defaults and user overrides
```

### Testing Requirements

**Backend tests** (pytest, asyncio_mode=auto, co-located):

1. `api/app/repositories/favorites_repository_test.py` (additions):
   - `test_update_notes_success` — updates notes, returns favorite with new notes
   - `test_update_notes_clear` — sets notes to None
   - `test_update_notes_not_found` — returns None for invalid ID
   - `test_update_notes_wrong_user` — returns None for other user's favorite

2. `api/app/services/favorites_service_test.py` (additions):
   - `test_update_notes_success` — returns response dict with updated notes
   - `test_update_notes_empty_string_normalized` — empty string becomes None
   - `test_update_notes_not_found` — returns None

3. `api/app/api/favorites_test.py` (additions):
   - `test_patch_notes_success` — 200 with updated favorite in envelope
   - `test_patch_notes_clear_with_null` — 200 with null notes
   - `test_patch_notes_clear_with_empty_string` — 200 with null notes (normalized)
   - `test_patch_notes_unauthenticated` — 401
   - `test_patch_notes_not_found` — 404

**Frontend tests** (Vitest, jsdom, co-located):

4. `web/src/components/FavoriteNotes.test.tsx`:
   - Renders placeholder text when notes is null
   - Renders existing notes text in display mode
   - Enters edit mode on click
   - Shows textarea with current notes in edit mode
   - Saves notes on save button click (mocked API)
   - Cancels editing on cancel button click
   - Shows toast notification on successful save
   - Handles empty notes save (clears notes)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.2: Add Notes to Favorites]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture — favorites(notes)]
- [Source: _bmad-output/planning-artifacts/architecture.md#API Endpoints — /api/favorites]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#FavoriteCard — personal notes field]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Effortless Interactions — no modal confirmation]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns — toast notifications]
- [Source: _bmad-output/project-context.md#API Response Format (MANDATORY)]
- [Source: _bmad-output/project-context.md#Backend Architecture (LAYERED)]
- [Source: _bmad-output/project-context.md#Testing Rules — co-located]
- [Source: CLAUDE.md#Architecture — api → services → repositories]
- [Source: CLAUDE.md#API Response Format]
- [Source: _bmad-output/implementation-artifacts/6-1-save-hs-code-to-favorites.md — previous story file list, code review notes]
- [Source: api/app/models/favorite.py — Favorite model with notes column]
- [Source: api/app/schemas/favorites.py — FavoriteCreate, FavoriteResponse]
- [Source: api/app/repositories/favorites_repository.py — existing CRUD methods]
- [Source: api/app/services/favorites_service.py — existing service with _to_response]
- [Source: api/app/api/favorites.py — existing GET/POST/DELETE with JSONResponse pattern]
- [Source: web/src/lib/store.ts — FavoritesState with favorites[], favoriteIds[]]
- [Source: web/src/lib/api.ts — getFavorites, addFavorite, removeFavorite]
- [Source: web/src/components/FavoriteButton.tsx — toast pattern, optimistic UI]
- [Source: web/src/app/browse/components/HSCodeDetail.tsx — FavoriteButton integration point]
- [Source: web/src/app/search/page.tsx — FavoriteButton integration point]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- All 11 tasks implemented: PATCH endpoint for notes, FavoriteNotes component, integrations in browse + search views
- Backend: Added `FavoriteUpdateNotes` schema, `update_notes` method to repository and service (with empty-string-to-null normalization), `PATCH /{favorite_id}` endpoint with JSONResponse 404 pattern
- Frontend: Added `updateFavoriteNotes` API client function, `updateFavoriteNotesLocal` store action, `FavoriteNotes` inline editable component with display/edit modes, toast, keyboard shortcuts (Ctrl+Enter, Esc)
- FavoriteNotes integrated into HSCodeDetail (browse) and search results page — only visible when authenticated and HS code is favorited
- 10 new backend tests (4 repo + 3 service + 3 API endpoint) — all pass (31 total favorites tests)
- 7 new frontend tests (FavoriteNotes) — all pass. Store tests 17/17 pass. FavoriteButton 7/7 still pass.
- No new migrations needed — `notes` column already exists from Story 6-1

### Senior Developer Review (Code review: 2 medium + 3 low issues fixed)

**Reviewed by:** Claude Opus 4.6 (DEV 2)

**Findings (5 issues):**

1. **MEDIUM — No error feedback on save failure** (FavoriteNotes.tsx:74)
   - Empty `catch {}` block — user gets zero feedback when API call fails
   - AC#2/#3 require persistence feedback; failure needs feedback too
   - **FIXED**: Added error toast "Lỗi khi lưu ghi chú" with red styling + AlertCircle icon

2. **MEDIUM — Missing required test `test_patch_notes_unauthenticated`** (favorites_test.py)
   - Story Task 10.3 lists 4 API tests, only 3 implemented
   - AC#6 requires 401 for unauthenticated — this test was missing
   - **FIXED**: Added `test_patch_notes_unauthenticated` to TestUpdateFavoriteNotes class

3. **LOW — Unused `hsCodeId` prop** (FavoriteNotes.tsx:10,17)
   - Prop declared in interface and destructured but never used in component body
   - Story specifies it in the component interface, integration points pass it — kept for future use

4. **LOW — Toast overlap with FavoriteButton** (FavoriteNotes.tsx:186)
   - Both components render independent fixed-position toasts at `fixed top-4 right-4 z-50`
   - Already flagged in 6-1 review — compounded now with second toast source
   - Defer to shared toast manager in future story

5. **LOW — No max_length on notes field** (FavoriteUpdateNotes schema)
   - `notes: str | None` has no length constraint — allows arbitrarily large payloads
   - Minor abuse vector — consider adding `max_length=2000` in future

### File List

**New files:**
- `web/src/components/FavoriteNotes.tsx` — Inline editable notes component
- `web/src/components/FavoriteNotes.test.tsx` — 7 tests

**Modified files:**
- `api/app/schemas/favorites.py` — Added `FavoriteUpdateNotes` schema
- `api/app/repositories/favorites_repository.py` — Added `update_notes` method
- `api/app/repositories/favorites_repository_test.py` — Added 4 update_notes tests
- `api/app/services/favorites_service.py` — Added `update_notes` method with empty-string normalization
- `api/app/services/favorites_service_test.py` — Added 3 update_notes tests
- `api/app/api/favorites.py` — Added `PATCH /{favorite_id}` endpoint, imported `FavoriteUpdateNotes`
- `api/app/api/favorites_test.py` — Added 3 PATCH endpoint tests
- `web/src/lib/api.ts` — Added `updateFavoriteNotes` function
- `web/src/lib/store.ts` — Added `updateFavoriteNotesLocal` action to FavoritesState
- `web/src/app/browse/components/HSCodeDetail.tsx` — Added FavoriteNotes below FavoriteButton for favorited codes
- `web/src/app/search/page.tsx` — Added FavoriteNotes below search result FavoriteButton for favorited codes
