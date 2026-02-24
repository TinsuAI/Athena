# Story 9.3: Import History & Quality Dashboard

Status: done

## Story

As an **admin**,
I want **to see a history of customs data imports and knowledge base quality stats**,
So that **I can track what has been imported, monitor KB growth, and identify data quality issues**.

## Acceptance Criteria

1. **Given** I am logged in as an admin
   **When** I navigate to the customs data import page
   **Then** I see a history section showing past imports:
   - Source file name
   - Import date
   - Records imported / duplicates / errors
   - Imported by (admin user email)

2. **Given** imports have been completed
   **When** I view the quality dashboard section
   **Then** I see:
   - Total verified KB records (breakdown by search_method: customs_import, notebooklm, expert_correction)
   - Top HS chapters by KB coverage (chapters with the most verified lookup_records)
   - Recent import activity (last 5 imports)

3. **Given** no imports have been completed yet
   **When** I view the history section
   **Then** I see an empty state message: "Chua co du lieu nhap khau nao" (No import data yet)

4. **Given** the quality dashboard is loaded
   **When** I view the stats
   **Then** data loads within 2 seconds and stats are accurate against the database

## Tasks / Subtasks

- [x] Task 1: Create `customs_import_batches` table model and migration (AC: #1)
  - [x] 1.1 Create `api/app/models/customs_import_batch.py` with SQLAlchemy model: `CustomsImportBatch` (id, file_name, company_name, imported_by_user_id FK->users.id, total_rows, records_imported, duplicates_skipped, unmatched_codes, errors_count, started_at, completed_at)
  - [x] 1.2 Register model in `api/app/models/__init__.py`
  - [x] 1.3 Create Alembic migration `api/alembic/versions/20260224_add_customs_import_batches_table.py` with down_revision = `"add_site_settings_table"`
  - [x] 1.4 Add index on `imported_by_user_id` for efficient history queries

- [x] Task 2: Update `CustomsImportService.import_rows()` to record batch metadata (AC: #1)
  - [x] 2.1 Modify `import_rows()` in `api/app/services/customs_import_service.py` to accept `imported_by_user_id: int | None` parameter
  - [x] 2.2 At start of import, create a `CustomsImportBatch` record with `started_at=func.now()`, file_name, company_name, imported_by_user_id
  - [x] 2.3 After import completes, update the batch record with counts (total_rows, records_imported, duplicates_skipped, unmatched_codes count, errors count) and `completed_at=func.now()`
  - [x] 2.4 Return the batch ID in `ImportResult` (add `batch_id: int | None = None` field)
  - [x] 2.5 Update `api/app/api/customs_import.py` execute endpoint to pass `current_user.get("id")` (user ID) to `import_rows()`

- [x] Task 3: Create repository for import batch queries (AC: #1, #2)
  - [x] 3.1 Create `api/app/repositories/customs_import_repository.py` with `CustomsImportRepository` class
  - [x] 3.2 Implement `get_import_history(limit, offset)` — returns paginated list of batches with user email via join on users table
  - [x] 3.3 Implement `get_kb_stats()` — returns dict with: total verified records, breakdown by search_method (GROUP BY search_method WHERE is_verified=true), top 10 HS chapters by KB coverage (JOIN through full FK chain: hs_codes -> hs_subheadings -> hs_headings -> hs_chapters)
  - [x] 3.4 Implement `get_recent_imports(limit=5)` — returns last N batches for dashboard

- [x] Task 4: Create backend API endpoints (AC: #1, #2)
  - [x] 4.1 Add `GET /api/admin/customs-import/history` endpoint to `api/app/api/customs_import.py` — accepts `limit` (default 20) and `offset` (default 0) query params, requires admin role, returns paginated history
  - [x] 4.2 Add `GET /api/admin/customs-import/stats` endpoint — requires admin role, returns KB quality stats (total verified, breakdown by method, top chapters, recent imports)
  - [x] 4.3 Add Pydantic schemas: `ImportBatchResponse`, `KBStatsResponse`, `SearchMethodBreakdown`, `ChapterCoverage` in `api/app/schemas/customs_import.py`

- [x] Task 5: Add import history and stats sections to frontend (AC: #1, #2, #3)
  - [x] 5.1 Add a tabbed or sectioned layout to `web/src/app/admin/customs-import/page.tsx` with two sections: "Nhap du lieu" (Import Data — existing upload flow) and "Lich su & Thong ke" (History & Stats)
  - [x] 5.2 Implement history table: file_name, import date (formatted), records imported, duplicates, errors, imported by (email). Paginated or scrollable.
  - [x] 5.3 Implement stats cards: Total verified KB records, breakdown by method (customs_import, notebooklm, expert_correction), top chapters chart/list
  - [x] 5.4 Implement empty state for history section
  - [x] 5.5 Load history and stats via `fetch` with `credentials: "include"` on component mount

- [x] Task 6: Write backend tests (AC: all)
  - [x] 6.1 Add tests in `api/app/repositories/customs_import_repository_test.py` — history retrieval, stats aggregation (10 tests)
  - [x] 6.2 Update `api/app/services/customs_import_service_test.py` — test that import_rows creates batch record and populates counts (3 tests)
  - [x] 6.3 Add tests in `api/app/api/customs_import_test.py` — test history and stats endpoints (5 tests)

## Dev Notes

### Critical Architecture Compliance

- **Backend layering (STRICT):**
  - Route handlers in `api/app/api/customs_import.py` are THIN — validate input, call service/repository, format response.
  - Repository `customs_import_repository.py` contains ONLY database queries (history, stats aggregation).
  - Service `customs_import_service.py` contains ALL business logic (batch record creation during import).
- **API response format (MANDATORY):** All responses use envelope: `{"success": true, "data": {...}, "error": null}`. Use `success_response()` and `error_response()` from `app.schemas.base`.
- **Auth:** All endpoints require admin role via `Depends(require_admin)`.
- **No trailing slashes** on API routes (project convention from commit `1927c0c`).
- **snake_case** for all API JSON fields. Never camelCase.
- **Tests co-located** with source files, same directory.

### Existing Code to Reuse (DO NOT Reinvent)

| What | Where | How to Use |
|------|-------|------------|
| `CustomsImportService` | `api/app/services/customs_import_service.py` | MODIFY: add batch tracking to `import_rows()` |
| `ImportResult` dataclass | `api/app/services/customs_import_service.py` | MODIFY: add `batch_id` field |
| `require_admin` | `api/app/core/auth.py` | FastAPI dependency for admin-only endpoints |
| `get_db_session` | `api/app/api/deps.py` | FastAPI dependency for database session |
| `success_response`, `error_response` | `api/app/schemas/base.py` | Envelope response helpers |
| Existing customs_import router | `api/app/api/customs_import.py` | ADD new GET endpoints to existing router |
| Existing Pydantic schemas | `api/app/schemas/customs_import.py` | ADD new response schemas to existing file |
| `LookupRecord` model | `api/app/models/lookup_record.py` | Query for KB stats (search_method, is_verified) |
| `HSCode` model, `HSChapter` model | `api/app/models/hs_code.py`, `api/app/models/hs_chapter.py` | JOIN for chapter coverage stats |
| `User` model | `api/app/models/user.py` | JOIN for imported_by email in history |
| Admin layout | `web/src/app/admin/layout.tsx` | Already handles auth check + redirect for non-admins |
| `StatCard` component | `web/src/app/admin/customs-import/page.tsx` | Already exists in the customs import page — REUSE for stats display |
| Existing customs import page | `web/src/app/admin/customs-import/page.tsx` | MODIFY: add history/stats sections below the import workflow |

### New Table Schema: `customs_import_batches`

```sql
CREATE TABLE customs_import_batches (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(500) NOT NULL,
    company_name VARCHAR(255),
    imported_by_user_id INTEGER REFERENCES users(id),
    total_rows INTEGER NOT NULL DEFAULT 0,
    records_imported INTEGER NOT NULL DEFAULT 0,
    duplicates_skipped INTEGER NOT NULL DEFAULT 0,
    unmatched_codes INTEGER NOT NULL DEFAULT 0,
    errors_count INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX idx_customs_import_batches_user ON customs_import_batches(imported_by_user_id);
```

### Alembic Migration Pattern

```python
# down_revision MUST be "add_site_settings_table" (latest migration)
revision: str = "add_customs_import_batches_table"
down_revision: Union[str, None] = "add_site_settings_table"
```

### KB Stats Query Pattern

```python
# Breakdown by search_method
SELECT search_method, COUNT(*) as count
FROM lookup_records
WHERE is_verified = true
GROUP BY search_method

# Top chapters by coverage (join via substring of 8-digit code -> 2-digit chapter_code)
SELECT hc.chapter_code, hc.name_vn, COUNT(lr.id) as record_count
FROM lookup_records lr
JOIN hs_codes hsc ON lr.correct_hs_code_id = hsc.id
JOIN hs_chapters hc ON SUBSTRING(hsc.code, 1, 2) = hc.chapter_code
WHERE lr.is_verified = true
GROUP BY hc.chapter_code, hc.name_vn
ORDER BY record_count DESC
LIMIT 10
```

**IMPORTANT:** The HS code hierarchy uses `hs_chapters.code` (2-digit string like "85") which maps to the first 2 digits of `hs_codes.code` (8-digit string like "85076000"). Use `SUBSTRING(hsc.code, 1, 2)` or `hsc.code[:2]` in SQLAlchemy to join. Check if `hs_codes` has a direct FK to `hs_chapters` or if you need to join by substring.

### HS Code Hierarchy FK Chain (CRITICAL)

There is NO direct FK from `hs_codes` to `hs_chapters`. The hierarchy is:
`hs_codes.subheading_id` -> `hs_subheadings.heading_id` -> `hs_headings.chapter_id` -> `hs_chapters.id`

You MUST join through all 3 intermediate tables. Column names:
- `hs_chapters.chapter_code` (String(2)), `hs_chapters.name_vn` (Text)
- `hs_headings.chapter_id` (FK to hs_chapters.id)
- `hs_subheadings.heading_id` (FK to hs_headings.id)
- `hs_codes.subheading_id` (FK to hs_subheadings.id)

```python
from app.models.hs_code import HSCode
from app.models.hs_subheading import HSSubheading
from app.models.hs_heading import HSHeading
from app.models.hs_chapter import HSChapter

# Join through full hierarchy: lookup_records -> hs_codes -> subheadings -> headings -> chapters
query = (
    select(
        HSChapter.chapter_code,
        HSChapter.name_vn,
        func.count(LookupRecord.id).label("record_count")
    )
    .join(HSCode, LookupRecord.correct_hs_code_id == HSCode.id)
    .join(HSSubheading, HSCode.subheading_id == HSSubheading.id)
    .join(HSHeading, HSSubheading.heading_id == HSHeading.id)
    .join(HSChapter, HSHeading.chapter_id == HSChapter.id)
    .where(LookupRecord.is_verified == true())
    .group_by(HSChapter.chapter_code, HSChapter.name_vn)
    .order_by(func.count(LookupRecord.id).desc())
    .limit(10)
)
```

**ALTERNATIVE (simpler):** Since `hs_codes.code` is an 8-digit string where the first 2 digits are the chapter code, you can use `func.substr(HSCode.code, 1, 2)` to join directly to `hs_chapters.chapter_code` without traversing the FK chain. This may be faster for aggregation queries:

```python
query = (
    select(
        HSChapter.chapter_code,
        HSChapter.name_vn,
        func.count(LookupRecord.id).label("record_count")
    )
    .join(HSCode, LookupRecord.correct_hs_code_id == HSCode.id)
    .join(HSChapter, func.substr(HSCode.code, 1, 2) == HSChapter.chapter_code)
    .where(LookupRecord.is_verified == true())
    .group_by(HSChapter.chapter_code, HSChapter.name_vn)
    .order_by(func.count(LookupRecord.id).desc())
    .limit(10)
)
```

Choose the FK chain approach for correctness, or the substring approach for simplicity. Both are valid.

### API Response Schemas

```python
class ImportBatchResponse(BaseModel):
    id: int
    file_name: str
    company_name: str | None
    imported_by_email: str | None  # from user join
    total_rows: int
    records_imported: int
    duplicates_skipped: int
    unmatched_codes: int
    errors_count: int
    started_at: str  # ISO format
    completed_at: str | None  # ISO format

class SearchMethodBreakdown(BaseModel):
    search_method: str
    count: int

class ChapterCoverage(BaseModel):
    chapter_code: str
    name_vn: str  # Column is name_vn on hs_chapters, NOT description_vi
    record_count: int

class KBStatsResponse(BaseModel):
    total_verified: int
    breakdown_by_method: list[SearchMethodBreakdown]
    top_chapters: list[ChapterCoverage]
    recent_imports: list[ImportBatchResponse]
```

### Endpoint Specifications

```
GET /api/admin/customs-import/history
  Query params: limit (int, default 20), offset (int, default 0)
  Response: {"success": true, "data": {"items": [...ImportBatchResponse], "total": int}}

GET /api/admin/customs-import/stats
  Response: {"success": true, "data": KBStatsResponse}
```

### UI Language — Vietnamese (MANDATORY)

All frontend UI text MUST be in Vietnamese:
- Tab/Section: "Nhap du lieu" (Import Data), "Lich su & Thong ke" (History & Stats)
- History section title: "Lich su nhap du lieu" (Import History)
- Stats section title: "Thong ke co so kien thuc" (Knowledge Base Statistics)
- Total verified: "Tong ban ghi da xac minh" (Total Verified Records)
- By method breakdown: "Phan loai theo nguon" (Breakdown by Source)
  - customs_import: "Nhap hai quan" (Customs Import)
  - notebooklm: "NotebookLM AI"
  - expert_correction: "Chuyen gia xac nhan" (Expert Verified)
- Top chapters: "Chuong co nhieu du lieu nhat" (Chapters with Most Data)
- Recent imports: "Nhap gan day" (Recent Imports)
- Empty state: "Chua co du lieu nhap khau nao" (No import data yet)
- Table headers: "Tep nguon" (Source File), "Ngay nhap" (Import Date), "Da nhap" (Imported), "Trung lap" (Duplicates), "Loi" (Errors), "Nguoi nhap" (Imported By)

### Frontend Design Approach

- Extend the existing customs import page by adding sections below the current upload workflow
- Use a simple heading separator or tab-like toggle between "Import" and "History & Stats" views
- Reuse the existing `StatCard` component already defined in the page for KB stats display
- History table follows the same design pattern as the sample rows table in the preview step
- Load data with `useEffect` on component mount — use `fetch` with `credentials: "include"`
- Do NOT use `apiClient` from `web/src/lib/api.ts` (it sets Content-Type: application/json; fine for GET requests but keep consistent with existing page patterns using raw fetch)

### Project Structure Notes

```
api/app/
  models/
    customs_import_batch.py          # NEW: CustomsImportBatch model
    __init__.py                      # MODIFY: register new model
  repositories/
    customs_import_repository.py     # NEW: history + stats queries
    customs_import_repository_test.py # NEW: co-located tests
  services/
    customs_import_service.py        # MODIFY: add batch tracking to import_rows()
    customs_import_service_test.py   # MODIFY: add batch tracking tests
  api/
    customs_import.py                # MODIFY: add history + stats GET endpoints
    customs_import_test.py           # MODIFY: add history + stats endpoint tests
  schemas/
    customs_import.py                # MODIFY: add new response schemas
  alembic/versions/
    20260224_add_customs_import_batches_table.py  # NEW: migration

web/src/app/
  admin/
    customs-import/
      page.tsx                       # MODIFY: add history table + stats section
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 9, Story 9-3]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-24.md]
- [Source: api/app/services/customs_import_service.py] (CustomsImportService.import_rows — modify for batch tracking)
- [Source: api/app/api/customs_import.py] (existing router — add GET endpoints)
- [Source: api/app/schemas/customs_import.py] (existing schemas — add new response types)
- [Source: api/app/models/lookup_record.py] (LookupRecord model — query for stats)
- [Source: api/app/models/hs_code.py] (HSCode model — chapter_id FK for chapter coverage)
- [Source: api/app/models/hs_chapter.py] (HSChapter model — code, description_vi)
- [Source: api/alembic/versions/20260223_add_site_settings_table.py] (latest migration — down_revision chain)
- [Source: web/src/app/admin/customs-import/page.tsx] (existing page — extend with history/stats)
- [Source: CLAUDE.md] (architecture, conventions, anti-patterns)

### Previous Story Intelligence (Story 9-1 and 9-2)

**Story 9-1 (Parser & Import Service):**
- `CustomsImportService.import_rows()` does batch insert with `session.add_all()` + `session.flush()` in 500-record batches, then `session.commit()` at the end
- `ImportResult` dataclass has: total_rows, records_imported, duplicates_skipped, unmatched_codes (list[dict]), errors (list[dict])
- The commit happens inside the service (moved there during 9-2 code review — HIGH-2 fix)
- 48 tests in customs_import_service_test.py (after code review)

**Story 9-2 (Admin API & UI):**
- Two POST endpoints: `/upload` (preview) and `/execute` (import) with `require_admin`
- Execute endpoint passes `current_user.get("email", "admin_upload")` as company_name
- `current_user` is a dict from JWT with keys: `sub` (user ID int), `email`, `role`, `name`
- Frontend uses raw `fetch` with `FormData` for file uploads, `credentials: "include"`
- `StatCard` component and `StepIndicator` already defined in the page
- Code review fixed: schemas wired up, commit moved to service, duplication extracted, f-string logging fixed
- 62 total tests (8 API + 54 service) after code review

**Key insight for 9-3:** The `import_rows()` method currently does NOT track batch metadata. You need to create a `CustomsImportBatch` record at the start of import and update it with counts at the end. The batch record creation should happen inside `import_rows()` (service layer owns all business logic). The route handler just passes the user ID.

### Git Intelligence

Recent commits:
- `e8dc80b` — Story 9-2 (admin bulk import API & UI)
- `28df32b` — Story 9-1 (parser + import service)
- `cdee68f` — Site settings management (latest admin feature, good reference for admin patterns)
- Convention: no trailing slashes, co-located tests, Vietnamese UI, ruff-clean, admin pages are client components

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- Fixed variable shadowing bug in `import_rows()`: inner loop variable `batch` was overwriting the outer `CustomsImportBatch` variable `batch`. Renamed to `import_batch` (outer) and `chunk` (inner) to prevent runtime attribute errors.
- Service test flush mock: `session.flush()` as `AsyncMock` does not auto-assign IDs to ORM objects. Tests use a custom `mock_flush` side_effect to simulate ID assignment after flush.

### Completion Notes List

- All 6 tasks complete with all subtasks
- 80 total tests passing: 13 API (5 new) + 57 service (3 new batch tracking) + 10 repository (all new)
- Used FK chain approach (hs_codes -> hs_subheadings -> hs_headings -> hs_chapters) for chapter coverage stats, per story Dev Notes
- Frontend uses tabbed layout with TabSwitcher component, HistoryStatsSection component with stats cards, top chapters list, recent imports, full history table with pagination, and empty state
- All Vietnamese UI labels per story specification

### Senior Developer Review (AI)

**Reviewer:** Claude Sonnet 4.6 | **Date:** 2026-02-24

**Outcome:** Approved with fixes applied (2 HIGH + 2 MEDIUM issues fixed, 2 LOW noted)

**Issues Fixed:**
- [HIGH-1] `api/app/services/customs_import_service.py` lines 396,470: Replaced `func.now()` (SQL expression) with `datetime.now(timezone.utc)` on `import_batch.completed_at`. Assigning a SQL function expression to a `Mapped[datetime | None]` ORM attribute is a type violation caught by mypy strict mode and results in the in-memory attribute holding a SQL expression object after commit. Added `from datetime import datetime, timezone` import.
- [HIGH-2] `api/app/services/customs_import_service_test.py`: Added `session.add = MagicMock()` to 7 tests in `TestCustomsImportServiceImport` that call `import_rows()`. Story 9-3 added `self.session.add(import_batch)` (synchronous call) to `import_rows()`. Old tests used `session = AsyncMock()` which auto-creates `session.add` as an `AsyncMock`. Calling an AsyncMock without `await` returns an unawaited coroutine that generates `RuntimeWarning: coroutine was never awaited` in Python 3.12.
- [MEDIUM-1] `web/src/app/admin/customs-import/page.tsx`: Added `if (!res.ok) throw new Error(...)` before `res.json()` in both `fetchStats` and `fetchHistory`. Without this, non-2xx responses with non-JSON bodies (e.g., HTML 401 pages) cause `res.json()` to throw, which is caught but the error type is confusing. Now correctly throws on HTTP errors before attempting JSON parsing.
- [MEDIUM-2] `web/src/app/admin/customs-import/page.tsx`: Moved `HISTORY_PAGE_SIZE` from inside `HistoryStatsSection` function body to module level (line 89). Was being recreated on every render unnecessarily.

**Issues Noted (LOW - not blocking):**
- [LOW-1] Code duplication between `get_import_history` and `get_recent_imports` in the repository — share identical SELECT columns and row-mapping logic. Acceptable for now.
- [LOW-2] `started_at: str | None = None` in `ImportBatchResponse` schema is overly permissive — the DB column is NOT NULL so it will always be present. Low risk since the repo serializes it correctly.

### Change Log

- Created `api/app/models/customs_import_batch.py` (NEW) - CustomsImportBatch SQLAlchemy model
- Modified `api/app/models/__init__.py` - registered CustomsImportBatch
- Created `api/alembic/versions/20260224_add_customs_import_batches_table.py` (NEW) - migration
- Modified `api/app/services/customs_import_service.py` - added batch tracking to import_rows(), batch_id to ImportResult, fixed variable shadowing (batch -> import_batch/chunk)
- Created `api/app/repositories/customs_import_repository.py` (NEW) - history, stats, recent imports queries
- Modified `api/app/schemas/customs_import.py` - added ImportBatchResponse, KBStatsResponse, SearchMethodBreakdown, ChapterCoverage schemas, batch_id to CustomsImportResultResponse
- Modified `api/app/api/customs_import.py` - added GET /history and GET /stats endpoints, pass imported_by_user_id to import_rows()
- Modified `web/src/app/admin/customs-import/page.tsx` - added TabSwitcher, HistoryStatsSection with stats cards, top chapters, recent imports, full history table, pagination, empty state
- Created `api/app/repositories/customs_import_repository_test.py` (NEW) - 10 tests
- Modified `api/app/services/customs_import_service_test.py` - added TestBatchTracking class with 3 tests
- Modified `api/app/api/customs_import_test.py` - added TestHistoryEndpoint (3 tests) and TestStatsEndpoint (2 tests)

### File List

**New files:**
- `api/app/models/customs_import_batch.py`
- `api/alembic/versions/20260224_add_customs_import_batches_table.py`
- `api/app/repositories/customs_import_repository.py`
- `api/app/repositories/customs_import_repository_test.py`

**Modified files:**
- `api/app/models/__init__.py`
- `api/app/services/customs_import_service.py`
- `api/app/schemas/customs_import.py`
- `api/app/api/customs_import.py`
- `api/app/api/customs_import_test.py`
- `api/app/services/customs_import_service_test.py`
- `web/src/app/admin/customs-import/page.tsx`
