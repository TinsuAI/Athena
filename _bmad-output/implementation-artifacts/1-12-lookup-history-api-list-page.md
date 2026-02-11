# Story 1.12: Lookup History API & List Page

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want **to view a paginated list of all past lookups with filtering by verification status**,
So that **I can browse search history, see which queries have been verified, and navigate to individual lookup details**.

## Background

Stories 1-8 through 1-11 built the knowledge base: lookup records are created on every search, expert corrections mark them as verified, and classification reasoning/practical notes/process logs are persisted as JSONB. This story exposes that data through a paginated API and a frontend list page. Story 1-13 (detail page) depends on this.

**Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-10-lookup-history.md`

**Dependencies:** Story 1-11 (done)

## Acceptance Criteria

1. **AC1: Paginated List API**
   - **Given** lookup records exist in the database
   - **When** I call `GET /api/lookups?limit=20&offset=0`
   - **Then** I receive a paginated list of lookup records ordered by `created_at DESC`
   - **And** each item includes: `id`, `query_text`, `query_language`, `matched_hs_code` (code + description_vn), `confidence_score`, `search_method`, `is_verified`, `created_at`
   - **And** response follows envelope format `{success, data, error}`
   - **And** `data` includes `items`, `total`, `limit`, `offset`

2. **AC2: Filter by Verification Status**
   - **Given** I want to filter lookups
   - **When** I call `GET /api/lookups?verified=true`
   - **Then** only verified (corrected) lookups are returned
   - **When** I call `GET /api/lookups?verified=false`
   - **Then** only unverified lookups are returned
   - **When** I omit the `verified` parameter
   - **Then** all lookups are returned regardless of verification status

3. **AC3: Frontend List Page**
   - **Given** I navigate to `/lookups` in the frontend
   - **When** the page loads
   - **Then** I see a table/list of lookup records with columns: Query, Matched Code, Confidence, Status (verified/unverified badge), Date
   - **And** each row is clickable (navigates to `/lookups/[id]` — stub for now, Story 1-13)
   - **And** I see pagination controls (Previous/Next buttons with page indicator)
   - **And** I see a filter toggle for verified/unverified/all

4. **AC4: Empty State**
   - **Given** there are no lookup records
   - **When** I view the `/lookups` page
   - **Then** I see an empty state: "No lookups yet. Search for HS codes to start building history."

5. **AC5: Navigation Link**
   - **Given** I am on any page
   - **When** I look at the sidebar/header navigation
   - **Then** I see a "Lookups" link that navigates to `/lookups`

6. **AC6: API Error Handling**
   - **Given** an invalid `limit` or `offset` parameter (negative, non-integer)
   - **When** I call `GET /api/lookups?limit=-1`
   - **Then** I receive a 400 error following RFC 7807 format

## Tasks / Subtasks

- [x] Task 1: Add Repository Methods (AC: #1, #2)
  - [x] 1.1 Add `get_all_with_hs_codes(limit, offset, verified_filter)` to `LookupRecordRepository` — eager-loads `matched_hs_code` relationship, orders by `created_at DESC`, applies optional verified filter
  - [x] 1.2 Add `count_all(verified_filter)` to `LookupRecordRepository` — counts total records with optional filter
  - [x] 1.3 Write co-located tests in `lookup_record_repository_test.py`

- [x] Task 2: Create Lookup Schemas (AC: #1)
  - [x] 2.1 Create `api/app/schemas/lookup.py` with `LookupListItem` and `PaginatedLookupListResponse` schemas
  - [x] 2.2 `LookupListItem` fields: `id`, `query_text`, `query_language`, `matched_hs_code`, `matched_description_vn`, `confidence_score`, `search_method`, `is_verified`, `created_at`
  - [x] 2.3 `PaginatedLookupListResponse` fields: `items: list[LookupListItem]`, `total: int`, `limit: int`, `offset: int`

- [x] Task 3: Create Lookups API Router (AC: #1, #2, #6)
  - [x] 3.1 Create `api/app/api/lookups.py` with `GET /api/lookups` endpoint
  - [x] 3.2 Query params: `limit: int = 20`, `offset: int = 0`, `verified: bool | None = None`
  - [x] 3.3 Validate limit (1-100) and offset (>= 0), return 400 on invalid
  - [x] 3.4 Register router in `api/app/main.py`
  - [x] 3.5 Write co-located tests in `api/app/api/lookups_test.py`

- [x] Task 4: Build Frontend Lookups Page (AC: #3, #4)
  - [x] 4.1 Create `web/src/app/lookups/page.tsx` — client component with data fetching, pagination, filter
  - [x] 4.2 Create `web/src/app/lookups/components/LookupList.tsx` — renders table/card list of lookups
  - [x] 4.3 Add lookup types to `web/src/types/lookup.ts`
  - [x] 4.4 Add lookup API functions to `web/src/lib/api.ts`
  - [x] 4.5 Display confidence as color-coded badge (green >= 80, yellow >= 50, red < 50)
  - [x] 4.6 Display verified/unverified as badge
  - [x] 4.7 Implement filter toggle (All / Verified / Unverified)
  - [x] 4.8 Implement pagination (Previous/Next with "Page X of Y")
  - [x] 4.9 Implement empty state
  - [x] 4.10 Each row clickable — `router.push(\`/lookups/${id}\`)` (page doesn't exist yet, that's Story 1-13)

- [x] Task 5: Add Navigation Link (AC: #5)
  - [x] 5.1 Add "Lookups" link to `web/src/components/layout/Header.tsx`
  - [x] 5.2 Integrate Header into root layout if not already done
  - [x] 5.3 Update Sidebar if it exists with `/lookups` link

## Dev Notes

### Critical Architecture Patterns (MUST FOLLOW)

**Backend Layered Architecture:**
```
Request -> api/lookups.py (thin) -> LookupRecordRepository (data access)
              ↓                          ↓
   validate params,              SQLAlchemy async queries,
   format response               eager-load relationships
```

**No service layer needed for this story** — the endpoint is a straightforward data retrieval with no business logic. The route handler directly uses the repository (same pattern as `corrections.py` GET `/api/corrections/lookups`).

**API Response Format — ALL responses MUST use envelope format:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 42,
    "limit": 20,
    "offset": 0
  },
  "error": null
}
```

**Error Response — MUST use RFC 7807:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "type": "https://athena.example/errors/validation",
    "title": "Invalid Parameters",
    "status": 400,
    "detail": "limit must be between 1 and 100",
    "instance": "/api/lookups"
  }
}
```

### Existing Code to Understand (READ THESE FIRST)

**`api/app/api/corrections.py`** (236 lines) — **PRIMARY PATTERN REFERENCE:**
- GET `/api/corrections/lookups` is the closest existing pattern to what you're building
- Uses `LookupRecordRepository` directly in route handler
- Paginates with `limit`/`offset` query params
- Constructs schema items by iterating over records
- Returns `success_response(response.model_dump())`
- **Copy this pattern** for the new GET `/api/lookups` endpoint

**`api/app/repositories/lookup_record_repository.py`** (172 lines):
- `get_unverified_with_hs_codes(limit, offset)` — Existing method that eager-loads `matched_hs_code`. **Use this as template** for the new `get_all_with_hs_codes()` method.
- `count_unverified()` — Existing count method. **Use as template** for `count_all()`.
- `find_by_id(record_id)` — Basic PK lookup (used by corrections)
- Pattern: `select(LookupRecord).options(selectinload(LookupRecord.matched_hs_code)).where(...).order_by(...).limit(...).offset(...)`

**`api/app/models/lookup_record.py`** (76 lines):
- All columns documented in Story 1-11 dev notes
- Relationships: `matched_hs_code` (FK to HSCode), `correct_hs_code` (FK to HSCode)
- **Do NOT modify this file** — the model already has everything needed

**`api/app/schemas/correction.py`** (55 lines) — **Schema Pattern Reference:**
```python
class LookupRecordItem(BaseModel):
    id: int
    query_text: str
    query_language: str | None
    matched_hs_code_id: int | None
    matched_hs_code: str | None
    matched_description_vn: str | None
    matched_description_en: str | None
    confidence_score: float | None
    search_method: str
    created_at: str  # ISO format string

class PaginatedLookupResponse(BaseModel):
    items: list[LookupRecordItem]
    total: int
    limit: int
    offset: int
```
**DO NOT reuse these schemas** — create new ones in `api/app/schemas/lookup.py`. The corrections schema is designed for the corrections endpoint (unverified only). Story 1-12 needs a similar but distinct schema that includes `is_verified` and works for all lookups.

**`api/app/schemas/base.py`** (59 lines):
- `ApiResponse[T]` — Generic envelope: `{success: bool, data: T | None, error: ApiError | None}`
- `success_response(data)` — Returns `{"success": True, "data": data, "error": None}`
- `error_response(type_uri, title, status, detail, instance)` — Returns RFC 7807 error envelope
- **Import and use these directly** — never create custom response structures

**`api/app/main.py`** (80 lines) — Router registration:
```python
app.include_router(corrections_router)
app.include_router(hs_codes_router)
app.include_router(search_router)
# ADD: app.include_router(lookups_router)
```

**`web/src/lib/api.ts`** (112 lines) — Frontend API client:
```typescript
class apiClient {
  static async get<T>(path: string): Promise<T> { ... }
  static async post<T>(path: string, body: unknown): Promise<T> { ... }
}
```
- Uses `NEXT_PUBLIC_API_URL` env variable
- Returns parsed JSON (already handles envelope)
- **Add lookup functions following existing pattern**

**`web/src/app/search/page.tsx`** (334 lines) — Frontend pattern reference:
- Client component (`"use client"`)
- State managed via Zustand selectors + local useState
- Data fetching in useCallback with async/await
- AbortController for request cancellation
- Vietnamese UI text throughout

**`web/src/components/layout/Header.tsx`** (20 lines):
- Simple nav with logo + links
- Currently only has "Search" link
- **Add "Lookups" link here**
- **Note:** Header is NOT integrated into root layout yet — you need to add it

**`web/src/components/layout/Sidebar.tsx`** (30 lines):
- Has links: Search, Favorites, History
- History points to `/history` (wrong path for lookups)
- **Add /lookups link or update existing History link**

### New Repository Methods (Exact Signatures)

**`get_all_with_hs_codes()` — Based on existing `get_unverified_with_hs_codes()`:**
```python
async def get_all_with_hs_codes(
    self,
    limit: int = 20,
    offset: int = 0,
    verified_filter: bool | None = None,
) -> list[LookupRecord]:
    """Get paginated lookup records with eager-loaded HS codes.

    Args:
        limit: Max records to return
        offset: Number of records to skip
        verified_filter: None=all, True=verified only, False=unverified only
    """
    query = (
        select(LookupRecord)
        .options(selectinload(LookupRecord.matched_hs_code))
        .order_by(LookupRecord.created_at.desc())
    )
    if verified_filter is not None:
        query = query.where(LookupRecord.is_verified == verified_filter)
    query = query.limit(limit).offset(offset)
    result = await self.session.execute(query)
    return list(result.scalars().all())
```

**`count_all()` — Based on existing `count_unverified()`:**
```python
async def count_all(self, verified_filter: bool | None = None) -> int:
    """Count total lookup records with optional filter."""
    query = select(func.count(LookupRecord.id))
    if verified_filter is not None:
        query = query.where(LookupRecord.is_verified == verified_filter)
    result = await self.session.execute(query)
    return result.scalar_one()
```

### New Schema Definitions

**`api/app/schemas/lookup.py`:**
```python
from pydantic import BaseModel


class LookupListItem(BaseModel):
    id: int
    query_text: str
    query_language: str | None
    matched_hs_code: str | None       # hs_codes.code (8-digit)
    matched_description_vn: str | None # hs_codes.description_vn
    confidence_score: float | None
    search_method: str
    is_verified: bool
    created_at: str                    # ISO 8601 string


class PaginatedLookupListResponse(BaseModel):
    items: list[LookupListItem]
    total: int
    limit: int
    offset: int
```

### API Endpoint Implementation

**`api/app/api/lookups.py`:**
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.lookup_record_repository import LookupRecordRepository
from app.schemas.base import ApiResponse, error_response, success_response
from app.schemas.lookup import LookupListItem, PaginatedLookupListResponse

router = APIRouter(prefix="/api/lookups", tags=["lookups"])


@router.get(
    "",
    response_model=ApiResponse[PaginatedLookupListResponse],
    summary="List lookup records",
)
async def list_lookups(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    verified: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = LookupRecordRepository(session=db)
    records = await repo.get_all_with_hs_codes(
        limit=limit, offset=offset, verified_filter=verified
    )
    total = await repo.count_all(verified_filter=verified)

    items = [
        LookupListItem(
            id=r.id,
            query_text=r.query_text,
            query_language=r.query_language,
            matched_hs_code=r.matched_hs_code.code if r.matched_hs_code else None,
            matched_description_vn=(
                r.matched_hs_code.description_vn if r.matched_hs_code else None
            ),
            confidence_score=r.confidence_score,
            search_method=r.search_method,
            is_verified=r.is_verified,
            created_at=r.created_at.isoformat(),
        )
        for r in records
    ]

    response = PaginatedLookupListResponse(
        items=items, total=total, limit=limit, offset=offset
    )
    return success_response(response.model_dump())
```

**Note:** FastAPI's `Query(ge=1, le=100)` handles validation automatically and returns 422 for invalid params. If you need custom 400 responses, add explicit validation before the query.

### Frontend Implementation Guide

**Type definitions (`web/src/types/lookup.ts`):**
```typescript
export interface LookupListItem {
  id: number;
  query_text: string;
  query_language: string | null;
  matched_hs_code: string | null;
  matched_description_vn: string | null;
  confidence_score: number | null;
  search_method: string;
  is_verified: boolean;
  created_at: string;
}

export interface PaginatedLookupListResponse {
  items: LookupListItem[];
  total: number;
  limit: number;
  offset: number;
}
```

**API function (`web/src/lib/api.ts` — add to existing file):**
```typescript
export async function getLookups(
  limit: number = 20,
  offset: number = 0,
  verified?: boolean,
): Promise<PaginatedLookupListResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (verified !== undefined) {
    params.set("verified", String(verified));
  }
  return apiClient.get<PaginatedLookupListResponse>(
    `/api/lookups?${params.toString()}`
  );
}
```

**Page structure (`web/src/app/lookups/page.tsx`):**
- Client component (`"use client"`)
- Local state: `items`, `total`, `limit`, `offset`, `verifiedFilter`, `isLoading`
- useCallback for `fetchLookups()` — calls `getLookups(limit, offset, verifiedFilter)`
- useEffect triggers fetch on mount and when offset/verifiedFilter changes
- Filter bar: 3 buttons (All / Verified / Unverified) using active styling
- Table/list rendering with LookupList component
- Pagination: Previous/Next buttons + "Page X of Y" text
- Empty state when items.length === 0 and not loading
- Each row: `onClick={() => router.push(\`/lookups/${item.id}\`)}` with `cursor-pointer`

**Confidence badge colors:**
- >= 80: green (`bg-green-100 text-green-800`)
- >= 50: yellow (`bg-yellow-100 text-yellow-800`)
- < 50: red (`bg-red-100 text-red-800`)

**Verification badge:**
- Verified: green badge with checkmark icon
- Unverified: gray badge

**Navigation integration:**
- Add "Lookups" link to Header.tsx (next to existing "Search" link)
- Add Header to root layout.tsx if not already present
- Pattern: `<Link href="/lookups">Lookups</Link>`

### Previous Story Intelligence (from Stories 1-8 through 1-11)

**Key learnings from Story 1-8:**
- LookupRecord uses `Mapped` + `mapped_column()` syntax (SQLAlchemy 2.0)
- Repository uses `AsyncSession` with `await self.session.flush()` for writes
- `compute_query_hash()` is a standalone function in `lookup_record_repository.py`
- `_record_lookup()` in search.py is wrapped in try/except so failures never break search

**Key learnings from Story 1-10:**
- `api/app/api/corrections.py` is the closest pattern to what we're building
- GET `/api/corrections/lookups` already implements paginated lookup records (but unverified only)
- Response construction: iterate records, build schema items, wrap in paginated response
- Frontend CorrectionPanel and CorrectionButton are reusable components

**Key learnings from Story 1-11:**
- JSONB columns (classification_data, practical_notes, process_logs) exist but are NOT needed in the list response — only in the detail response (Story 1-13)
- 197/228 tests pass; 14 pre-existing failures unrelated
- Redis pipeline mock pattern: `MagicMock` for `pipeline()` returning `MagicMock` context manager

**Code review feedback patterns applied in previous stories:**
- Always use proper type parameters (`dict[str, str]` not just `dict`)
- Update sprint-status.yaml in File List
- Verify test count after implementation

### Git Intelligence (Recent Commits)

| Commit | Description | Relevance |
|--------|-------------|-----------|
| 36b114e | 1-11 done | Direct predecessor — JSONB columns persisted |
| 6271d95 | feat: Implement lookup history and detail pages | May contain partial work — CHECK for existing files |
| a0fb771 | feat: Localize correction UI to Vietnamese | UI language precedent |
| 150c5ea | 1-10 done | Corrections endpoint pattern |

**CRITICAL: Commit 6271d95 may already contain partial implementation!** Check if any lookup files were created in this commit before writing new code. Run `git show --name-only 6271d95` to verify.

**Patterns established in recent work:**
- Co-located tests with `_test.py` suffix
- Envelope response format on all responses
- Async/await everywhere
- Repository instantiated directly in route handlers (no service layer for simple CRUD)
- Vietnamese UI text in frontend
- Process logs for search transparency

### Implementation Strategy

**Order of implementation (recommended):**
1. Task 1 (repository methods) — data access first
2. Task 2 (schemas) — define response shapes
3. Task 3 (API router) — wire endpoint
4. Task 4 (frontend page) — build UI
5. Task 5 (navigation) — integrate into app

**This is a full-stack story.** Both backend API and frontend page are required.

### Anti-Patterns (NEVER DO)

- **NEVER** create a service layer for this endpoint — it's simple CRUD retrieval, route handler + repository is sufficient (matches corrections.py pattern)
- **NEVER** put business logic in the route handler — the handler validates params, calls repo, formats response
- **NEVER** use camelCase in API JSON responses — all fields must be snake_case
- **NEVER** create tests in a separate `/tests` directory — co-locate with `_test.py`
- **NEVER** skip the envelope response format (`{success, data, error}`)
- **NEVER** fetch data via Next.js API routes — fetch FastAPI directly with CORS
- **NEVER** use status enums for loading states — use boolean flags (`isLoading: boolean`)
- **NEVER** include JSONB fields (classification_data, practical_notes, process_logs) in the list response — those are expensive and only needed for the detail page (Story 1-13)
- **NEVER** modify the LookupRecord model — it already has everything needed
- **NEVER** reuse schemas from `correction.py` — create new ones in `lookup.py` that include `is_verified` field
- **NEVER** add a Zustand store slice for lookups — use local component state (page-level useState). Lookups don't need global state persistence.

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Backend | FastAPI | Latest | Python 3.12+, async |
| Database | PostgreSQL | 16 | With pgvector + pg_trgm |
| ORM | SQLAlchemy | 2.0 | Async mode, Mapped syntax |
| Frontend | Next.js | 16 | App Router, React 19, TypeScript |
| Styling | Tailwind CSS | Latest | Utility-first |
| UI Components | shadcn/ui | Latest | Card, Badge, Button |
| Testing | pytest + Vitest | Latest | Backend + Frontend |

### Project Structure Notes

**Files to CREATE:**
```
api/app/schemas/lookup.py          (new) — LookupListItem, PaginatedLookupListResponse
api/app/api/lookups.py             (new) — GET /api/lookups endpoint
api/app/api/lookups_test.py        (new) — Co-located tests
web/src/types/lookup.ts            (new) — TypeScript types
web/src/app/lookups/page.tsx       (new) — Lookup list page
web/src/app/lookups/components/LookupList.tsx (new) — List component
```

**Files to MODIFY:**
```
api/app/repositories/lookup_record_repository.py  (modify) — Add get_all_with_hs_codes, count_all
api/app/repositories/lookup_record_repository_test.py (modify) — Add tests for new methods
api/app/main.py                                    (modify) — Register lookups_router
web/src/lib/api.ts                                 (modify) — Add getLookups function
web/src/components/layout/Header.tsx               (modify) — Add Lookups nav link
web/src/app/layout.tsx                             (modify) — Integrate Header if not already
```

**Files to NOT modify:**
```
api/app/models/lookup_record.py    — Model already complete
api/app/schemas/correction.py      — Separate concern
api/app/api/corrections.py         — Separate concern
api/app/api/search.py              — No changes needed
web/src/lib/store.ts               — No global state needed for lookups
```

### Database Schema Reference

```sql
-- Existing table (no changes needed):
lookup_records (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    query_language VARCHAR(5),
    matched_hs_code_id INTEGER REFERENCES hs_codes(id),
    correct_hs_code_id INTEGER REFERENCES hs_codes(id),
    is_verified BOOLEAN DEFAULT false NOT NULL,
    verified_by_user_id INTEGER,
    verified_at TIMESTAMP WITH TIME ZONE,
    confidence_score FLOAT,
    search_method VARCHAR(20) NOT NULL,
    notes TEXT,
    classification_data JSONB,
    practical_notes JSONB,
    process_logs JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Existing indexes (support list page queries):
idx_lookup_records_created_at (created_at DESC)  -- Ordering
idx_lookup_records_verified (is_verified)          -- Filtering
```

No migrations needed for this story.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.12]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-10-lookup-history.md]
- [Source: _bmad-output/planning-artifacts/architecture.md#API-Response-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend-Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure-Boundaries]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: _bmad-output/implementation-artifacts/1-11-persist-full-lookup-details.md]
- [Source: api/app/api/corrections.py — GET /api/corrections/lookups (pattern reference)]
- [Source: api/app/repositories/lookup_record_repository.py — get_unverified_with_hs_codes, count_unverified]
- [Source: api/app/schemas/correction.py — LookupRecordItem, PaginatedLookupResponse]
- [Source: api/app/schemas/base.py — ApiResponse, success_response, error_response]
- [Source: api/app/main.py — Router registration pattern]
- [Source: web/src/lib/api.ts — Frontend API client]
- [Source: web/src/app/search/page.tsx — Frontend page pattern]
- [Source: web/src/components/layout/Header.tsx — Navigation component]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered.

### Completion Notes List

- Task 1: Added `get_all_with_hs_codes(limit, offset, verified_filter)` and `count_all(verified_filter)` repository methods following existing `get_unverified_with_hs_codes` pattern. 8 new tests added, all pass.
- Task 2: Created `api/app/schemas/lookup.py` with `LookupListItem` (includes `is_verified` field, distinct from correction schema) and `PaginatedLookupListResponse`.
- Task 3: Created `api/app/api/lookups.py` with `GET /api/lookups` endpoint. Manual validation returns 400 (not 422) per AC6. Registered router in `main.py`. 13 new tests added, all pass.
- Task 4: Built full frontend page at `/lookups` with client component, pagination (Previous/Next with "Page X of Y"), filter toggle (All/Verified/Unverified), confidence color-coded badges, verified/unverified badges, empty state message, and clickable rows navigating to `/lookups/[id]`.
- Task 5: Added "Lookups" nav link to Header.tsx, integrated Header into root layout.tsx, updated Sidebar.tsx History link to point to `/lookups`.
- Backend test results: 218 passed, 14 failed (pre-existing), 6 errors (pre-existing). No regressions from changes.
- Frontend test results: 54 passed, 0 failed. No regressions.
- Linting: All new files pass ruff check. No new lint issues.

### File List

**New files:**
- api/app/schemas/lookup.py
- api/app/api/lookups.py
- api/app/api/lookups_test.py
- web/src/types/lookup.ts
- web/src/app/lookups/page.tsx
- web/src/app/lookups/components/LookupList.tsx

**Modified files:**
- api/app/repositories/lookup_record_repository.py (added get_all_with_hs_codes, count_all)
- api/app/repositories/lookup_record_repository_test.py (added 8 tests)
- api/app/main.py (registered lookups_router)
- web/src/lib/api.ts (added getLookups function)
- web/src/components/layout/Header.tsx (added Lookups nav link)
- web/src/components/layout/Sidebar.tsx (updated History link to /lookups)
- web/src/app/layout.tsx (integrated Header component)
- _bmad-output/implementation-artifacts/sprint-status.yaml (status: in-progress → review)

### Change Log

- 2026-02-10: Implemented Story 1-12 — Lookup History API & List Page. Full-stack: paginated API endpoint with verification filter, frontend list page with table, pagination, filter toggle, confidence/verified badges, empty state, and navigation integration.
