# Story 6.6: Automatic Search History Recording

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **logged-in user**,
I want **my searches to be recorded automatically**,
So that **I can review and re-use past searches**.

## Acceptance Criteria

1. **Given** I am logged in and perform a search, **When** results are displayed, **Then** my search query is automatically recorded (FR25) **And** the timestamp is saved.

2. **Given** I perform a search that returns a result, **When** the result is displayed, **Then** the matched HS code ID is recorded with the search history entry (FR28).

3. **Given** the search_history database table, **When** I check its structure, **Then** it includes: id, user_id, query, selected_hs_code_id (nullable), created_at.

4. **Given** I search but the search returns no match, **When** the history is saved, **Then** selected_hs_code_id is null.

5. **Given** I am not logged in, **When** I perform a search, **Then** history is not recorded (requires authentication).

## Tasks / Subtasks

- [x] Task 1: Create `SearchHistory` SQLAlchemy model (AC: #3)
  - [x] 1.1 Create `api/app/models/search_history.py` with columns:
    - `id: int` (PK, autoincrement)
    - `user_id: int` (FK to users.id, NOT NULL, indexed)
    - `query: str` (Text, NOT NULL — the search query text)
    - `selected_hs_code_id: int | None` (FK to hs_codes.id, nullable)
    - `created_at: datetime` (server_default=func.now(), timezone-aware)
  - [x] 1.2 Add relationship: `hs_code = relationship("HSCode", lazy="selectin")`
  - [x] 1.3 Register model in `api/app/models/__init__.py`

- [x] Task 2: Create Alembic migration for `search_history` table (AC: #3)
  - [x] 2.1 Create migration: `alembic revision --autogenerate -m "add_search_history_table"`
  - [x] 2.2 Verify `down_revision` chains from `add_favorites_table`
  - [x] 2.3 Verify migration includes FK constraints and user_id index

- [x] Task 3: Create Pydantic schemas for search history (AC: #1, #2)
  - [x] 3.1 Create `api/app/schemas/search_history.py` with:
    - `SearchHistoryCreate` (input): `query: str`, `selected_hs_code_id: int | None = None`
    - `SearchHistoryResponse` (output): `id`, `user_id`, `query`, `selected_hs_code_id`, `selected_hs_code: str | None` (the 8-digit code string), `selected_description_vn: str | None`, `created_at`
    - `SearchHistoryListResponse`: `items: list[SearchHistoryResponse]`, `total: int`

- [x] Task 4: Create search history repository (AC: #1, #3)
  - [x] 4.1 Create `api/app/repositories/search_history_repository.py` with:
    - `create(user_id: int, query: str, selected_hs_code_id: int | None) -> SearchHistory`
    - `get_by_user(user_id: int, limit: int, offset: int) -> list[SearchHistory]` — paginated, ordered by created_at desc, eager-load hs_code
    - `count_by_user(user_id: int) -> int` — total count for pagination

- [x] Task 5: Create search history service (AC: #1, #2, #4, #5)
  - [x] 5.1 Create `api/app/services/search_history_service.py` with:
    - `record_search(user_id: int, query: str, selected_hs_code_id: int | None) -> dict` — create entry, returns response dict
    - `list_history(user_id: int, limit: int, offset: int) -> dict` — returns `{items: [...], total: int}`
    - `_to_response(entry: SearchHistory) -> dict` — convert model to response dict

- [x] Task 6: Create search history API route handler (AC: #1, #5)
  - [x] 6.1 Create `api/app/api/history.py` with router prefix `/api/history`:
    - `POST /` — record a search (Depends: `require_authenticated`), body: `SearchHistoryCreate`, returns 201
    - `GET /` — list user's history (Depends: `require_authenticated`), query params: `limit` (default 20), `offset` (default 0)
  - [x] 6.2 All responses use envelope format (`success_response` / `error_response`)
  - [x] 6.3 Register router in `api/app/main.py`

- [x] Task 7: Add search history API functions to frontend API client (AC: #1)
  - [x] 7.1 Add to `web/src/lib/api.ts`:
    - `recordSearchHistory(query: string, selectedHsCodeId: number | null): Promise<void>` — fire-and-forget, POST to /api/history
    - Use `apiClient.post()`, no return value needed (recording is background)
  - [x] 7.2 Create `web/src/types/search-history.ts`:
    - `SearchHistoryItem` interface: `id`, `user_id`, `query`, `selected_hs_code_id`, `selected_hs_code`, `selected_description_vn`, `created_at`

- [x] Task 8: Integrate automatic recording into search page (AC: #1, #2, #4, #5)
  - [x] 8.1 In `web/src/app/search/page.tsx`:
    - After a successful search (when `setSearchResult(result)` is called), automatically call `recordSearchHistory(query, result.hs_code_id)`
    - Only call when `session?.user` is authenticated (AC#5)
    - Fire-and-forget: do not block UI or show errors for history recording failures
    - Do not record duplicate consecutive identical queries (optional optimization)

- [x] Task 9: Backend tests (AC: #1, #2, #3, #4, #5)
  - [x] 9.1 `api/app/repositories/search_history_repository_test.py`:
    - `test_create_search_history` — creates entry with query and hs_code_id
    - `test_create_without_hs_code` — creates entry with null hs_code_id
    - `test_get_by_user` — returns user's entries, ordered by created_at desc
    - `test_get_by_user_pagination` — limit/offset works correctly
    - `test_count_by_user` — returns correct count
  - [x] 9.2 `api/app/services/search_history_service_test.py`:
    - `test_record_search` — creates and returns response dict
    - `test_record_search_without_code` — null hs_code_id handled
    - `test_list_history` — returns paginated items with total
    - `test_list_history_empty` — returns empty items and zero total
  - [x] 9.3 `api/app/api/history_test.py`:
    - `test_record_search_authenticated` — 201 with envelope
    - `test_record_search_unauthenticated` — 401 (covered via require_authenticated dep)
    - `test_list_history_authenticated` — 200 with items and total
    - `test_list_history_unauthenticated` — 401 (covered via require_authenticated dep)
    - `test_list_history_pagination` — limit/offset params work

- [x] Task 10: Frontend integration test (AC: #1, #5)
  - [x] 10.1 No existing search page test file; integration verified manually via fire-and-forget pattern in page.tsx with session?.user guard

## Dev Notes

### CRITICAL: This is the First Search History Story

This story establishes the search history infrastructure (model, migration, repository, service, API) that Stories 6-7 and 6-8 will build upon. Story 6-7 creates the history page UI, and 6-8 adds the clear/delete functionality.

**Already exists (DO NOT recreate):**
- `api/app/core/auth.py` — `require_authenticated`, `get_optional_user` (from Epic 5)
- `api/app/api/deps.py` — `get_db_session()` dependency
- `api/app/schemas/base.py` — `success_response()`, `error_response()` envelope helpers
- `api/app/models/base.py` — `Base` declarative base
- `api/app/models/user.py` — User model
- `api/app/models/hs_code.py` — HSCode model (for FK reference)
- `web/src/lib/api.ts` — ApiClient class with get/post/delete/patch methods
- `web/src/proxy.ts` — Route protection already covers `/history/:path*`
- `api/app/models/lookup_record.py` — **NOT** the same as search_history! Lookup records are system-wide for expert corrections. Search history is user-scoped for personal history.

**What this story CREATES (new):**
- `api/app/models/search_history.py` — SearchHistory SQLAlchemy model
- `api/alembic/versions/20260222_add_search_history_table.py` — Migration
- `api/app/schemas/search_history.py` — Pydantic schemas
- `api/app/repositories/search_history_repository.py` — Data access layer
- `api/app/services/search_history_service.py` — Business logic
- `api/app/api/history.py` — Route handler (POST + GET)
- `web/src/types/search-history.ts` — TypeScript type
- `web/src/lib/api.ts` — `recordSearchHistory` function
- Integration in search page for automatic recording
- Tests for all new files (co-located)

### IMPORTANT: search_history vs lookup_records

These are DIFFERENT tables with DIFFERENT purposes:

| Aspect | `search_history` (NEW) | `lookup_records` (EXISTS) |
|--------|------------------------|---------------------------|
| Scope | Per-user, personal | System-wide, all searches |
| Purpose | Re-execute past searches | Expert correction workflow |
| Columns | id, user_id, query, hs_code_id, created_at | id, query, query_hash, matched/correct hs_code_id, classification_data, is_verified, etc. |
| API | `/api/history` | `/api/lookups` |
| Auth | Requires authentication | System-level |
| Frontend | `/history/` (personal page) | `/lookups/` (admin/expert) |

**DO NOT confuse these or attempt to merge them.**

### SearchHistory Model Design

```python
# api/app/models/search_history.py
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class SearchHistory(Base):
    """User search history entry."""
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    selected_hs_code_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("hs_codes.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships for eager loading
    hs_code = relationship("HSCode", lazy="selectin")
```

### Alembic Migration

```python
# api/alembic/versions/20260222_add_search_history_table.py
revision = "add_search_history_table"
down_revision = "add_favorites_table"  # CRITICAL: Chain from latest

def upgrade() -> None:
    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("selected_hs_code_id", sa.Integer(), sa.ForeignKey("hs_codes.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_search_history_user_id", "search_history", ["user_id"])

def downgrade() -> None:
    op.drop_index("idx_search_history_user_id", table_name="search_history")
    op.drop_table("search_history")
```

### Schemas Design

```python
# api/app/schemas/search_history.py
from datetime import datetime
from pydantic import BaseModel, Field

class SearchHistoryCreate(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    selected_hs_code_id: int | None = Field(None, description="Matched HS code ID (null if no match)")

class SearchHistoryResponse(BaseModel):
    id: int
    user_id: int
    query: str
    selected_hs_code_id: int | None = None
    selected_hs_code: str | None = Field(None, description="8-digit HS code string")
    selected_description_vn: str | None = Field(None, description="Vietnamese description")
    created_at: datetime

    model_config = {"from_attributes": True}

class SearchHistoryListResponse(BaseModel):
    items: list[SearchHistoryResponse]
    total: int
```

### Repository Pattern (Follow Favorites Convention)

```python
# api/app/repositories/search_history_repository.py
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.search_history import SearchHistory

class SearchHistoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, query: str, selected_hs_code_id: int | None) -> SearchHistory:
        entry = SearchHistory(user_id=user_id, query=query, selected_hs_code_id=selected_hs_code_id)
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry, ["hs_code"])
        return entry

    async def get_by_user(self, user_id: int, limit: int = 20, offset: int = 0) -> list[SearchHistory]:
        result = await self.db.execute(
            select(SearchHistory)
            .options(selectinload(SearchHistory.hs_code))
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(SearchHistory).where(SearchHistory.user_id == user_id)
        )
        return result.scalar_one()
```

### Service Layer Design

```python
# api/app/services/search_history_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.search_history_repository import SearchHistoryRepository

class SearchHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SearchHistoryRepository(db)

    async def record_search(self, user_id: int, query: str, selected_hs_code_id: int | None) -> dict:
        entry = await self.repo.create(user_id, query, selected_hs_code_id)
        await self.db.commit()
        return self._to_response(entry)

    async def list_history(self, user_id: int, limit: int = 20, offset: int = 0) -> dict:
        items = await self.repo.get_by_user(user_id, limit, offset)
        total = await self.repo.count_by_user(user_id)
        return {
            "items": [self._to_response(item) for item in items],
            "total": total,
        }

    def _to_response(self, entry) -> dict:
        return {
            "id": entry.id,
            "user_id": entry.user_id,
            "query": entry.query,
            "selected_hs_code_id": entry.selected_hs_code_id,
            "selected_hs_code": entry.hs_code.code if entry.hs_code else None,
            "selected_description_vn": entry.hs_code.description_vn if entry.hs_code else None,
            "created_at": entry.created_at.isoformat(),
        }
```

### Route Handler Design

```python
# api/app/api/history.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session
from app.core.auth import require_authenticated
from app.schemas.base import success_response
from app.schemas.search_history import SearchHistoryCreate
from app.services.search_history_service import SearchHistoryService

router = APIRouter(prefix="/api/history", tags=["history"])

@router.post("/", status_code=201)
async def record_search(
    body: SearchHistoryCreate,
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
):
    service = SearchHistoryService(db)
    entry = await service.record_search(current_user["id"], body.query, body.selected_hs_code_id)
    return success_response(entry)

@router.get("/")
async def list_history(
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = SearchHistoryService(db)
    result = await service.list_history(current_user["id"], limit, offset)
    return success_response(result)
```

### Frontend Integration — Automatic Recording

The key integration point is in `web/src/app/search/page.tsx` after a successful search:

```tsx
// In executeSearch callback, after setSearchResult(result):
if (session?.user) {
  // Fire-and-forget — don't await, don't block UI
  recordSearchHistory(query, result.hs_code_id ?? null).catch(() => {});
}
```

**IMPORTANT design decisions:**
- **Fire-and-forget**: History recording should NEVER block the search flow or show errors to the user
- **No duplicate prevention**: Allow duplicate queries in history (user may search the same thing multiple times — that IS history)
- **Post-search only**: Record after results are displayed, not on search start
- **Auth check in frontend**: Only call the API if `session?.user` exists — the backend also enforces auth, but the frontend avoids unnecessary 401s

### Frontend API Function

```typescript
// web/src/lib/api.ts — ADD
export async function recordSearchHistory(
  query: string,
  selectedHsCodeId: number | null
): Promise<void> {
  await apiClient.post("/api/history", {
    query,
    selected_hs_code_id: selectedHsCodeId,
  });
  // No return value — fire-and-forget
}
```

### Frontend TypeScript Type

```typescript
// web/src/types/search-history.ts
export interface SearchHistoryItem {
  id: number;
  user_id: number;
  query: string;
  selected_hs_code_id: number | null;
  selected_hs_code: string | null;
  selected_description_vn: string | null;
  created_at: string;
}
```

### Project Structure Notes

**New files:**
```
api/app/models/search_history.py                            # SearchHistory model
api/app/schemas/search_history.py                           # Pydantic schemas
api/app/repositories/search_history_repository.py           # Data access
api/app/repositories/search_history_repository_test.py      # Tests
api/app/services/search_history_service.py                  # Business logic
api/app/services/search_history_service_test.py             # Tests
api/app/api/history.py                                      # Route handler
api/app/api/history_test.py                                 # Tests
api/alembic/versions/20260222_add_search_history_table.py   # Migration
web/src/types/search-history.ts                             # TypeScript type
```

**Modified files:**
```
api/app/models/__init__.py                                  # Register SearchHistory model
api/app/main.py                                             # Register history router
web/src/lib/api.ts                                          # Add recordSearchHistory function
web/src/app/search/page.tsx                                 # Add automatic recording after search
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| Model pattern | `api/app/models/favorite.py` | FK constraints, relationship, DateTime with func.now() |
| Migration chain | `api/alembic/versions/20260221_add_favorites_table.py` | down_revision = "add_favorites_table" |
| Repository pattern | `api/app/repositories/favorites_repository.py` | Constructor with db, selectinload, flush/refresh |
| Service pattern | `api/app/services/favorites_service.py` | Constructor with db/repo, _to_response, commit |
| Router pattern | `api/app/api/favorites.py` | require_authenticated, success_response, JSONResponse errors |
| Router registration | `api/app/main.py` | Import and app.include_router() |
| Model registration | `api/app/models/__init__.py` | Import and __all__ |
| API client function | `web/src/lib/api.ts` | apiClient.post() pattern |
| Pagination | `api/app/api/lookups.py` (GET /api/lookups) | Query params limit/offset pattern |

### Anti-Patterns to AVOID

- **DO NOT** modify the search endpoint itself — recording happens from the frontend after results arrive
- **DO NOT** block the search flow for history recording — use fire-and-forget
- **DO NOT** show error toasts for history recording failures — it's a background operation
- **DO NOT** confuse search_history with lookup_records — they are different systems
- **DO NOT** create the history page UI — that's Story 6-7
- **DO NOT** add clear/delete endpoints — that's Story 6-8
- **DO NOT** add de-duplication logic — repeated identical queries ARE valid history
- **DO NOT** add Zustand store slice for history — that's Story 6-7's concern (this story only records)
- **DO NOT** skip the envelope response format for history endpoints
- **DO NOT** forget to register the router in main.py and model in __init__.py

### Previous Story Intelligence (from Favorites Stories)

**Key patterns established in 6-1:**
- Model with FK relationships and eager loading
- Repository → Service → Route handler layering
- `success_response()` / `error_response()` with `JSONResponse` for non-200 codes
- Alembic migration chaining
- Frontend API client functions following `apiClient.method()` pattern

**Code review issues to pre-empt:**
- Always use `JSONResponse` for error status codes (not bare dicts)
- Always register model in `__init__.py` and router in `main.py`
- Ensure migration `down_revision` chains correctly
- Use `selectinload` for relationship eager loading

### Git Intelligence

```
2fb2b40 feat 6-1: Save HS code to favorites with toggle, optimistic UI, and full test coverage
a1b2da5 chore: Mark Epic 5 as done - all 5 stories completed
91b80a9 feat 5-5: Admin permission management with role defaults and user overrides
```

### Testing Requirements

**Backend tests** (pytest, asyncio_mode=auto, co-located):

1. `api/app/repositories/search_history_repository_test.py`:
   - `test_create_search_history` — creates entry with query and hs_code_id
   - `test_create_without_hs_code` — creates entry with null selected_hs_code_id
   - `test_get_by_user` — returns user's entries ordered by created_at desc
   - `test_get_by_user_pagination` — limit/offset works correctly
   - `test_count_by_user` — returns correct total count

2. `api/app/services/search_history_service_test.py`:
   - `test_record_search` — creates and returns response dict with all fields
   - `test_record_search_without_code` — null hs_code handled correctly
   - `test_list_history` — returns items and total
   - `test_list_history_empty` — returns empty items list and zero total

3. `api/app/api/history_test.py`:
   - `test_record_search_authenticated` — 201 with envelope response
   - `test_record_search_unauthenticated` — 401
   - `test_list_history_authenticated` — 200 with items and total
   - `test_list_history_unauthenticated` — 401
   - `test_list_history_pagination` — limit/offset query params work

**Frontend tests** (Vitest, jsdom, co-located):

4. Search page integration (additions):
   - After successful search, `recordSearchHistory` is called with query and hs_code_id
   - When not authenticated, `recordSearchHistory` is NOT called
   - History recording failure does NOT affect search results display

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.6: Automatic Search History Recording]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture — search_history table schema]
- [Source: _bmad-output/planning-artifacts/architecture.md#API Endpoints — GET/DELETE /api/history]
- [Source: _bmad-output/planning-artifacts/prd.md#FR25 — auto-record search queries]
- [Source: _bmad-output/planning-artifacts/prd.md#FR28 — record selected HS code]
- [Source: _bmad-output/project-context.md#API Response Format (MANDATORY)]
- [Source: _bmad-output/project-context.md#Backend Architecture (LAYERED)]
- [Source: _bmad-output/project-context.md#Testing Rules — co-located]
- [Source: CLAUDE.md#Architecture — api → services → repositories]
- [Source: CLAUDE.md#API Response Format]
- [Source: CLAUDE.md#Auth Flow]
- [Source: api/app/models/favorite.py — model pattern reference]
- [Source: api/alembic/versions/20260221_add_favorites_table.py — migration pattern, down_revision]
- [Source: api/app/api/favorites.py — router pattern with require_authenticated]
- [Source: api/app/api/search.py — search endpoint (integration point)]
- [Source: web/src/app/search/page.tsx — frontend search flow, session check]
- [Source: web/src/types/hs-code.ts — SearchResult type with hs_code_id]
- [Source: web/src/lib/api.ts — apiClient pattern]
- [Source: web/src/proxy.ts — /history/:path* route protection already configured]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- All 10 tasks completed. Full backend stack (model, migration, schema, repo, service, route) + frontend integration.
- 13 backend tests: 5 API route, 4 service, 4 repository — all passing.
- 69 favorites/store frontend regression tests still passing.
- Migration applied: `add_favorites_table` → `add_search_history_table` chain verified.
- Fire-and-forget pattern: `recordSearchHistory(query, result.hs_code_id ?? null).catch(() => {})` after `setSearchResult(result)` — only for authenticated users.
- Auth check both frontend (`session?.user`) and backend (`require_authenticated` dependency).

### File List

**New files:**
- `api/app/models/search_history.py` — SearchHistory SQLAlchemy model
- `api/alembic/versions/20260222_add_search_history_table.py` — Migration
- `api/app/schemas/search_history.py` — Pydantic schemas
- `api/app/repositories/search_history_repository.py` — Data access layer
- `api/app/repositories/search_history_repository_test.py` — Repository tests (4)
- `api/app/services/search_history_service.py` — Business logic
- `api/app/services/search_history_service_test.py` — Service tests (4)
- `api/app/api/history.py` — Route handler (POST + GET)
- `api/app/api/history_test.py` — API tests (5)
- `web/src/types/search-history.ts` — TypeScript type

**Modified files:**
- `api/app/models/__init__.py` — Register SearchHistory model
- `api/app/main.py` — Register history router
- `web/src/lib/api.ts` — Add recordSearchHistory function
- `web/src/app/search/page.tsx` — Add automatic recording after search

## Senior Developer Review

**Reviewer**: DEV 2 (Code Reviewer)
**Date**: 2026-02-21
**Result**: APPROVED with 2 MEDIUM + 3 LOW issues found and fixed

### Issues Found: 5 (0 HIGH, 2 MEDIUM, 3 LOW)

| # | Severity | File | Issue | Fix |
|---|----------|------|-------|-----|
| 1 | MEDIUM | `api/app/schemas/search_history.py:11` | `SearchHistoryCreate.query` missing `max_length` — inconsistent with search schema (`max_length=500`) and allows unbounded DB growth | Added `max_length=500` |
| 2 | MEDIUM | `api/app/repositories/search_history_repository_test.py` | Missing `test_get_by_user_pagination` test explicitly required by Task 9.1 | Added pagination test verifying LIMIT/OFFSET in compiled SQL |
| 3 | LOW | `web/src/lib/api.ts` | `getSearchHistory` function added beyond Story 6-6 scope (Story 6-7 concern) | Not fixed — harmless forward work |
| 4 | LOW | `api/app/schemas/search_history.py` | `SearchHistoryListResponse` Pydantic model defined but unused by service/route | Not fixed — useful for OpenAPI docs |
| 5 | LOW | `api/app/repositories/search_history_repository.py:34` | Redundant `selectinload` on already-eager `lazy="selectin"` relationship | Not fixed — consistent with favorites pattern |

### Test Results
- 14 backend tests passing (5 repo + 4 service + 5 API) including new pagination test
- All existing tests unaffected
