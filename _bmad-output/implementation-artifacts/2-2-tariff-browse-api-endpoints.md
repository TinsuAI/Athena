# Story 2.2: Tariff Browse API Endpoints

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **dedicated API endpoints for browsing the tariff hierarchy with inline rate data**,
So that **the frontend tariff browser page can efficiently load and display the schedule**.

## Background

Story 2-1 expanded the data import to capture all rate data (export duty, TTDB, BVMT, VAT reduction, FTA conditions, RCEP yearly rates, export FTA rates). The database now contains 11,871 HS codes with full rate data and 270,746+ FTA rates across 21+ agreement codes. This story creates the read-only API layer for the tariff schedule browser (Story 2-3 will build the frontend).

**Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-11.md`

**Dependencies:** Story 2-1 must be complete (done).

**FRs covered:** FR8 (browse hierarchically), FR54 (collapsible tree with inline rates), FR59 (search/filter within browser), FR60 (jump to chapter), FR61 (section/chapter notes)

## Acceptance Criteria

1. **AC1: List All Sections**
   - **Given** the API is running
   - **When** I call `GET /api/browse/sections`
   - **Then** I receive all HS sections with: `id`, `section_number`, `section_roman`, `name_vn`, `name_en`, `chapter_count`
   - **And** response follows envelope format `{success, data, error}`
   - **And** sections are ordered by `section_number`

2. **AC2: List Chapters by Section**
   - **Given** a section exists
   - **When** I call `GET /api/browse/chapters?section_id={id}`
   - **Then** I receive all chapters in that section with: `id`, `chapter_code`, `name_vn`, `name_en`, `heading_count`, `hs_code_count`
   - **And** `notes_vn` and `notes_en` for the section are included in the response
   - **And** chapters are ordered by `chapter_code`

3. **AC3: Full Chapter Detail with Hierarchy and Rates**
   - **Given** a chapter exists (e.g., chapter_code "01")
   - **When** I call `GET /api/browse/chapters/{chapter_code}`
   - **Then** I receive the full chapter hierarchy: chapter -> headings -> subheadings -> HS codes
   - **And** chapter `notes_vn` and `notes_en` are included
   - **And** each HS code includes: `code`, `description_vn`, `description_en`, `unit`, `duty_rate`, `vat_rate`, `export_duty_rate`, `special_consumption_tax`, `environmental_tax`, `vat_reduction`, `policy_notes`
   - **And** each HS code includes nested FTA rates: `agreement_code`, `preferential_rate`, `conditions`, `rate_year`, `is_export`, `legal_document`, `effective_date`

4. **AC4: Browse Search**
   - **Given** I want to search within the tariff browser
   - **When** I call `GET /api/browse/search?q={text}`
   - **Then** I receive matching HS codes via pg_trgm text search on `description_vn`/`description_en` + exact code prefix match
   - **And** optional `chapter` query param narrows results to a specific chapter
   - **And** each result includes hierarchy path: section_roman, chapter_code, heading_code
   - **And** each result includes inline rates: `duty_rate`, `vat_rate`, `export_duty_rate`
   - **And** results are paginated (default limit=50)

5. **AC5: Error Handling**
   - **Given** I call `GET /api/browse/chapters/{code}` with a non-existent chapter code
   - **When** the response is returned
   - **Then** I receive a 404 error following RFC 7807 format
   - **Given** I call `GET /api/browse/chapters?section_id=99999`
   - **When** the section doesn't exist
   - **Then** I receive a 404 error following RFC 7807 format

6. **AC6: Performance**
   - **Given** the full tariff data is loaded
   - **When** I call any browse endpoint
   - **Then** response time is <500ms for sections/chapters list
   - **And** response time is <2s for full chapter detail (largest chapters have ~600 codes)

7. **AC7: Backward Compatibility**
   - **Given** the browse endpoints are added
   - **When** I run existing search, lookup, and correction features
   - **Then** all existing functionality is unchanged (no regressions)

## Tasks / Subtasks

- [ ] Task 1: Create Browse Response Schemas (AC: #1, #2, #3, #4)
  - [ ] 1.1 Create `api/app/schemas/browse.py` with all response models
  - [ ] 1.2 `BrowseSectionItem` — section list item with chapter_count
  - [ ] 1.3 `BrowseChapterItem` — chapter list item with heading_count, hs_code_count
  - [ ] 1.4 `BrowseChaptersResponse` — chapters list + section notes
  - [ ] 1.5 `BrowseHSCodeItem` — HS code with all rate fields + nested FTA rates
  - [ ] 1.6 `BrowseFTARateItem` — FTA rate with all fields (rate_year, is_export, etc.)
  - [ ] 1.7 `BrowseSubheadingItem` — subheading with nested HS codes
  - [ ] 1.8 `BrowseHeadingItem` — heading with nested subheadings
  - [ ] 1.9 `BrowseChapterDetailResponse` — full chapter hierarchy with notes
  - [ ] 1.10 `BrowseSearchResultItem` — search result with hierarchy path + inline rates
  - [ ] 1.11 `PaginatedBrowseSearchResponse` — search results with pagination

- [ ] Task 2: Create Browse Repository (AC: #1, #2, #3, #4, #6)
  - [ ] 2.1 Create `api/app/repositories/browse_repository.py`
  - [ ] 2.2 `get_all_sections()` — all sections with chapter count via subquery
  - [ ] 2.3 `get_chapters_by_section(section_id)` — chapters with heading_count and hs_code_count subqueries
  - [ ] 2.4 `get_section_by_id(section_id)` — single section for notes
  - [ ] 2.5 `get_chapter_by_code(chapter_code)` — full chapter with eager-loaded hierarchy (headings -> subheadings -> hs_codes -> fta_rates)
  - [ ] 2.6 `search_codes(query, chapter_code, limit, offset)` — pg_trgm search + exact code prefix with hierarchy path
  - [ ] 2.7 `count_search_results(query, chapter_code)` — count for pagination

- [ ] Task 3: Create Browse Service (AC: #1, #2, #3, #4, #5)
  - [ ] 3.1 Create `api/app/services/browse_service.py`
  - [ ] 3.2 `list_sections()` — returns section list
  - [ ] 3.3 `list_chapters(section_id)` — validates section exists, returns chapters + section notes
  - [ ] 3.4 `get_chapter_detail(chapter_code)` — validates chapter exists, returns full hierarchy
  - [ ] 3.5 `search(query, chapter_code, limit, offset)` — input validation, delegates to repo

- [ ] Task 4: Create Browse Route Handler (AC: #1, #2, #3, #4, #5)
  - [ ] 4.1 Create `api/app/api/browse.py` with APIRouter(prefix="/api/browse")
  - [ ] 4.2 `GET /api/browse/sections` — list all sections
  - [ ] 4.3 `GET /api/browse/chapters` — list chapters by section_id query param
  - [ ] 4.4 `GET /api/browse/chapters/{chapter_code}` — full chapter detail
  - [ ] 4.5 `GET /api/browse/search` — search within tariff browser

- [ ] Task 5: Register Router in main.py (AC: #7)
  - [ ] 5.1 Import and include browse_router in `api/app/main.py`

- [ ] Task 6: Write Tests (AC: #1-#7)
  - [ ] 6.1 Create `api/app/api/browse_test.py` — route handler tests
  - [ ] 6.2 Create `api/app/repositories/browse_repository_test.py` — repository tests
  - [ ] 6.3 Create `api/app/services/browse_service_test.py` — service tests
  - [ ] 6.4 Test all 4 endpoints with valid data
  - [ ] 6.5 Test error cases (404 for missing section/chapter)
  - [ ] 6.6 Test search with chapter filter, empty results, code prefix match
  - [ ] 6.7 Verify existing tests still pass (no regressions)

## Dev Notes

### Critical Architecture Patterns (MUST FOLLOW)

**Backend Layered Architecture — This story creates ALL THREE layers:**
```
Route handlers (api/browse.py)  →  Service (services/browse_service.py)  →  Repository (repositories/browse_repository.py)
     THIN only:                       ALL business logic:                     ONLY database queries:
  validate query params,              validate section/chapter exists,        SELECT with JOINs,
  call service,                       404 error decisions,                    subquery counts,
  format response                     orchestrate repo calls                  eager loading
```

**Response Format — ALL endpoints MUST use:**
```python
from app.schemas.base import success_response, error_response

# Success:
return success_response(data)  # → {"success": true, "data": {...}, "error": null}

# Error (RFC 7807):
return error_response(
    type_uri="https://athena.example/errors/not-found",
    title="Not Found",
    status=404,
    detail="Chapter '99' not found",
    instance="/api/browse/chapters/99"
)
```

**Naming Conventions:**
- Database/API JSON: `snake_case` — `chapter_code`, `hs_code_count`, `duty_rate`
- Python functions: `snake_case` — `get_chapter_detail()`
- Python classes: `PascalCase` — `BrowseService`, `BrowseRepository`
- Test files: Co-located with `_test.py` suffix

### Existing Code to Reference (READ THESE FIRST)

**Pattern file: `api/app/api/hs_codes.py` (89 lines)** — Follow this exact route handler pattern:
- Uses `APIRouter(prefix="/api/hs-codes", tags=["hs-codes"])`
- Dependency injection: `db: AsyncSession = Depends(get_db)`
- Creates service instance per request: `service = HSCodeService(db)`
- Returns `success_response(data)` or `error_response(...)`
- Uses Pydantic `model_validate()` + `model_dump()` for serialization

**Pattern file: `api/app/repositories/hs_code_repository.py` (111 lines)** — Follow this repo pattern:
- Class takes `AsyncSession` in `__init__`
- Uses `select()`, `selectinload()`, `func.count()` from SQLAlchemy
- Returns model instances or None
- Uses `result.scalar_one_or_none()` or `list(result.scalars().all())`

**Pattern file: `api/app/services/hs_code_service.py` (89 lines)** — Follow this service pattern:
- Class takes `AsyncSession` in `__init__`, creates repository internally
- Contains validation logic (e.g., `validate_hs_code_format()`)
- Delegates DB queries to repository

**Pattern file: `api/app/schemas/hs_code.py` (53 lines)** — Follow this schema pattern:
- Pydantic `BaseModel` with `Field(description="...")`
- `model_config = {"from_attributes": True}` for ORM mapping
- All fields use `snake_case`

**Pattern file: `api/app/main.py` (83 lines)** — Router registration:
```python
from app.api.browse import router as browse_router
app.include_router(browse_router)
```

### Database Model Reference (Exact Column Names)

**HSSection** (`hs_sections`) — 20 sections:
- `id`, `section_number` (int, unique), `section_roman` (str, e.g., "I"), `name_vn`, `name_en`, `notes_vn`, `notes_en`, `created_at`
- Relationship: `chapters` → list[HSChapter]

**HSChapter** (`hs_chapters`) — 98 chapters:
- `id`, `chapter_code` (str(2), unique, indexed), `section_id` (FK), `name_vn`, `name_en`, `notes_vn`, `notes_en`, `created_at`
- Relationships: `section` → HSSection, `headings` → list[HSHeading]

**HSHeading** (`hs_headings`) — 1,269 headings:
- `id`, `heading_code` (str(4), unique, indexed), `chapter_id` (FK), `name_vn`, `name_en`, `created_at`
- Relationships: `chapter` → HSChapter, `subheadings` → list[HSSubheading]

**HSSubheading** (`hs_subheadings`) — 5,786 subheadings:
- `id`, `subheading_code` (str(6), unique, indexed), `heading_id` (FK), `name_vn`, `name_en`, `indent_level`, `created_at`
- Relationships: `heading` → HSHeading, `hs_codes` → list[HSCode]

**HSCode** (`hs_codes`) — 11,871 codes:
- `id`, `code` (str(8), unique, indexed), `subheading_id` (FK), `description_vn`, `description_en`, `unit`, `duty_rate` (DECIMAL), `vat_rate` (DECIMAL), `export_duty_rate` (VARCHAR), `special_consumption_tax` (VARCHAR), `environmental_tax` (VARCHAR), `vat_reduction` (VARCHAR), `policy_notes` (TEXT), `indent_level`, `embedding` (Vector(3072)), `data_version_id` (FK), `created_at`
- Relationship: `fta_rates` → list[FTARate], `subheading` → HSSubheading

**FTARate** (`fta_rates`) — 270,746+ rates:
- `id`, `hs_code_id` (FK, indexed), `agreement_code` (str(20), indexed), `preferential_rate` (DECIMAL), `conditions` (TEXT), `rate_year` (INTEGER, indexed), `is_export` (BOOLEAN, indexed), `legal_document` (VARCHAR), `effective_date` (VARCHAR), `created_at`
- Relationship: `hs_code` → HSCode

### Schema Design Guide

**BrowseSectionItem:**
```python
class BrowseSectionItem(BaseModel):
    id: int
    section_number: int
    section_roman: str
    name_vn: str
    name_en: str | None
    chapter_count: int  # Computed via subquery, NOT from_attributes

    model_config = {"from_attributes": True}
```

**BrowseChapterItem:**
```python
class BrowseChapterItem(BaseModel):
    id: int
    chapter_code: str
    name_vn: str
    name_en: str | None
    heading_count: int   # Computed via subquery
    hs_code_count: int   # Computed via subquery

    model_config = {"from_attributes": True}
```

**BrowseChaptersResponse** (wraps chapters + section notes):
```python
class BrowseChaptersResponse(BaseModel):
    section_notes_vn: str | None
    section_notes_en: str | None
    chapters: list[BrowseChapterItem]
```

**BrowseFTARateItem** (all FTA fields for browse):
```python
class BrowseFTARateItem(BaseModel):
    agreement_code: str
    preferential_rate: float
    conditions: str | None
    rate_year: int | None
    is_export: bool
    legal_document: str | None
    effective_date: str | None

    model_config = {"from_attributes": True}
```

**BrowseHSCodeItem** (full rates inline):
```python
class BrowseHSCodeItem(BaseModel):
    id: int
    code: str
    description_vn: str
    description_en: str
    unit: str | None
    duty_rate: float
    vat_rate: float
    export_duty_rate: str | None
    special_consumption_tax: str | None
    environmental_tax: str | None
    vat_reduction: str | None
    policy_notes: str | None
    fta_rates: list[BrowseFTARateItem]

    model_config = {"from_attributes": True}
```

**BrowseSubheadingItem / BrowseHeadingItem** (nested):
```python
class BrowseSubheadingItem(BaseModel):
    id: int
    subheading_code: str
    name_vn: str
    name_en: str | None
    indent_level: int | None
    hs_codes: list[BrowseHSCodeItem]

    model_config = {"from_attributes": True}

class BrowseHeadingItem(BaseModel):
    id: int
    heading_code: str
    name_vn: str
    name_en: str | None
    subheadings: list[BrowseSubheadingItem]

    model_config = {"from_attributes": True}
```

**BrowseChapterDetailResponse:**
```python
class BrowseChapterDetailResponse(BaseModel):
    id: int
    chapter_code: str
    name_vn: str
    name_en: str | None
    notes_vn: str | None
    notes_en: str | None
    headings: list[BrowseHeadingItem]

    model_config = {"from_attributes": True}
```

**BrowseSearchResultItem:**
```python
class BrowseSearchResultItem(BaseModel):
    id: int
    code: str
    description_vn: str
    description_en: str
    unit: str | None
    duty_rate: float
    vat_rate: float
    export_duty_rate: str | None
    # Hierarchy path
    section_roman: str
    chapter_code: str
    heading_code: str

    model_config = {"from_attributes": True}

class PaginatedBrowseSearchResponse(BaseModel):
    items: list[BrowseSearchResultItem]
    total: int
    limit: int
    offset: int
```

### Repository Query Patterns

**Sections with chapter count (subquery):**
```python
from sqlalchemy import func, select
from app.models.hs_section import HSSection
from app.models.hs_chapter import HSChapter

chapter_count_subquery = (
    select(func.count(HSChapter.id))
    .where(HSChapter.section_id == HSSection.id)
    .correlate(HSSection)
    .scalar_subquery()
)
stmt = (
    select(HSSection, chapter_count_subquery.label("chapter_count"))
    .order_by(HSSection.section_number)
)
```
Note: When using computed columns (subqueries), you can't use `from_attributes` directly. You'll need to manually construct the schema from the row tuple.

**Chapters with counts (subqueries):**
```python
from app.models.hs_heading import HSHeading
from app.models.hs_subheading import HSSubheading
from app.models.hs_code import HSCode

heading_count = (
    select(func.count(HSHeading.id))
    .where(HSHeading.chapter_id == HSChapter.id)
    .correlate(HSChapter)
    .scalar_subquery()
)
# hs_code_count needs a join through heading -> subheading -> hs_code
hs_code_count = (
    select(func.count(HSCode.id))
    .join(HSSubheading, HSCode.subheading_id == HSSubheading.id)
    .join(HSHeading, HSSubheading.heading_id == HSHeading.id)
    .where(HSHeading.chapter_id == HSChapter.id)
    .correlate(HSChapter)
    .scalar_subquery()
)
```

**Full chapter with eager loading (critical for performance):**
```python
from sqlalchemy.orm import selectinload

stmt = (
    select(HSChapter)
    .where(HSChapter.chapter_code == chapter_code)
    .options(
        selectinload(HSChapter.headings)
        .selectinload(HSHeading.subheadings)
        .selectinload(HSSubheading.hs_codes)
        .selectinload(HSCode.fta_rates)
    )
)
```
This single query with nested `selectinload` will emit 5 SELECT statements (one per level) but avoids N+1 problems. This is the same pattern used in `search_repository.py`.

**Browse search with pg_trgm:**
```python
from sqlalchemy import or_, text

# For pg_trgm similarity search (existing pattern from search_repository.py):
stmt = (
    select(HSCode)
    .join(HSSubheading, HSCode.subheading_id == HSSubheading.id)
    .join(HSHeading, HSSubheading.heading_id == HSHeading.id)
    .join(HSChapter, HSHeading.chapter_id == HSChapter.id)
    .join(HSSection, HSChapter.section_id == HSSection.id)
    .where(
        or_(
            HSCode.code.startswith(query),  # Exact code prefix
            HSCode.description_vn.ilike(f"%{query}%"),  # VN description
            HSCode.description_en.ilike(f"%{query}%"),  # EN description
        )
    )
)
# Add optional chapter filter:
if chapter_code:
    stmt = stmt.where(HSChapter.chapter_code == chapter_code)
```

### Route Handler Guide

**`api/app/api/browse.py`:**
```python
router = APIRouter(prefix="/api/browse", tags=["browse"])

@router.get("/sections", response_model=ApiResponse[list[BrowseSectionItem]])
async def list_sections(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    service = BrowseService(db)
    sections = await service.list_sections()
    return success_response(sections)

@router.get("/chapters", response_model=ApiResponse[BrowseChaptersResponse])
async def list_chapters(
    section_id: int = Query(..., description="Section ID to filter chapters"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = BrowseService(db)
    result = await service.list_chapters(section_id)
    if result is None:
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="Section Not Found",
            status=404,
            detail=f"Section with id {section_id} not found",
            instance=f"/api/browse/chapters?section_id={section_id}",
        )
    return success_response(result)

@router.get("/chapters/{chapter_code}", response_model=ApiResponse[BrowseChapterDetailResponse])
async def get_chapter_detail(
    chapter_code: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = BrowseService(db)
    chapter = await service.get_chapter_detail(chapter_code)
    if chapter is None:
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="Chapter Not Found",
            status=404,
            detail=f"Chapter '{chapter_code}' not found",
            instance=f"/api/browse/chapters/{chapter_code}",
        )
    return success_response(chapter)

@router.get("/search", response_model=ApiResponse[PaginatedBrowseSearchResponse])
async def search_browse(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    chapter: str | None = Query(default=None, description="Optional chapter code filter"),
    limit: int = Query(default=50, ge=1, le=200, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = BrowseService(db)
    result = await service.search(q, chapter, limit, offset)
    return success_response(result)
```

### Testing Requirements

**Co-locate tests with source files:**
- `api/app/api/browse_test.py` — route handler tests
- `api/app/repositories/browse_repository_test.py` — repository tests
- `api/app/services/browse_service_test.py` — service tests

**Use pytest with async fixtures following existing patterns.**

**Test the following scenarios:**
1. `GET /api/browse/sections` — returns all 20 sections with chapter counts
2. `GET /api/browse/chapters?section_id=1` — returns chapters for section 1
3. `GET /api/browse/chapters?section_id=99999` — returns 404
4. `GET /api/browse/chapters/01` — returns full chapter 01 detail with hierarchy
5. `GET /api/browse/chapters/99` — returns 404 for non-existent chapter
6. `GET /api/browse/search?q=copper` — returns matching HS codes with hierarchy path
7. `GET /api/browse/search?q=01012100` — returns exact code match
8. `GET /api/browse/search?q=copper&chapter=74` — filtered to chapter 74
9. `GET /api/browse/search?q=xyznonexistent` — empty results

**Run after implementation:**
```bash
docker-compose -f docker-compose.dev.yml exec api pytest  # All backend tests
```

Target: All existing tests still pass + new browse tests pass.

### Previous Story Intelligence (from Story 2-1)

**Key learnings:**
- Story 2-1 added 4 columns to `hs_codes` (export_duty_rate, special_consumption_tax, environmental_tax, vat_reduction) — all VARCHAR, nullable
- Story 2-1 added 4 columns to `fta_rates` (rate_year, is_export, legal_document, effective_date)
- Data counts after 2-1: 11,871 HS codes, 270,746 import FTA rates, 2,514 export FTA rates
- 1,532 codes have export_duty_rate, 718 have TTDB, 134 have BVMT, 1,561 have VAT reduction
- Code review found 11 issues (1 CRITICAL) — watch for: wrong data extraction locations, missing index declarations in models, test coverage gaps
- 37 parser tests passing, 84/84 backward compatibility tests

**Previous code review patterns to avoid:**
- Missing proper type annotations (use `dict[str, Any]` not `dict`)
- Forgetting `from_attributes=True` on schemas
- Not testing error/edge cases
- Not eager-loading relationships (N+1 queries)

### Git Intelligence (Recent Commits)

| Commit | Description | Relevance |
|--------|-------------|-----------|
| 626cd8e | 2-1 done | Previous story complete — data model expanded |
| 63e6eb3 | new epic 2 | Epic 2 added to epics.md |
| 62b1c38 | 1-13 done | 227 backend tests baseline |
| ad58766 | 1-12 done | Lookup list page pattern (pagination) |

### Performance Considerations

- **Sections endpoint:** Simple query, no joins needed — fast (<100ms)
- **Chapters endpoint:** Uses 2 correlated subqueries for counts — add appropriate indexes if slow
- **Chapter detail:** The `selectinload` chain will emit 5 SELECTs. Largest chapters (~600 HS codes) with FTA rates could return large payloads. This is acceptable for MVP; consider caching in Story 2-3 if needed
- **Search endpoint:** Uses `ILIKE` for text search. For production scale, consider pg_trgm index on `description_vn` (already exists from search_repository setup) and `description_en`

### Anti-Patterns (NEVER DO)

- **NEVER** put business logic (404 decisions, validation) in route handlers — delegate to service
- **NEVER** use camelCase in API JSON responses — all fields are `snake_case`
- **NEVER** put tests in a separate `/tests` directory — co-locate with source
- **NEVER** skip the envelope response format — use `success_response()` / `error_response()`
- **NEVER** use `lazy` loading in queries — always use `selectinload()` for relationships
- **NEVER** modify existing API endpoints or schemas — this is a NEW router only
- **NEVER** include the `embedding` field in browse responses — it's 3072 floats per code, massive payload
- **NEVER** create Next.js API routes — the frontend fetches from FastAPI directly
- **NEVER** hardcode section/chapter counts — always compute from database

### Project Structure Notes

**Files to CREATE:**
```
api/app/schemas/browse.py                       # Response schemas
api/app/repositories/browse_repository.py       # Database queries
api/app/services/browse_service.py              # Business logic
api/app/api/browse.py                           # Route handlers
api/app/api/browse_test.py                      # Route tests
api/app/repositories/browse_repository_test.py  # Repository tests
api/app/services/browse_service_test.py         # Service tests
```

**Files to MODIFY:**
```
api/app/main.py  # Add browse_router import and include_router()
```

**Files that MUST NOT be modified:**
```
api/app/api/search.py          — Search endpoint unchanged
api/app/api/lookups.py         — Lookup endpoints unchanged
api/app/api/corrections.py     — Corrections unchanged
api/app/api/hs_codes.py        — HS codes endpoint unchanged
api/app/schemas/search.py      — Search schema unchanged
api/app/schemas/hs_code.py     — HS code schema unchanged
api/app/models/*.py            — No model changes (data already expanded in 2-1)
api/app/repositories/search_repository.py — Search repo unchanged
web/src/**                     — No frontend changes (Story 2-3)
```

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Backend | FastAPI | Latest | Python 3.12+, async |
| Database | PostgreSQL | 16 | With pgvector + pg_trgm |
| ORM | SQLAlchemy | 2.0 | Async mode, Mapped syntax |
| Validation | Pydantic | v2 | `from_attributes=True` |
| Testing | pytest | Latest | `asyncio_mode = "auto"` |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.2]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-11.md]
- [Source: _bmad-output/planning-artifacts/architecture.md#Backend-Architecture]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: api/app/api/hs_codes.py — Route handler pattern to follow]
- [Source: api/app/repositories/hs_code_repository.py — Repository pattern to follow]
- [Source: api/app/services/hs_code_service.py — Service pattern to follow]
- [Source: api/app/schemas/hs_code.py — Schema pattern to follow]
- [Source: api/app/schemas/base.py — Envelope response helpers]
- [Source: api/app/main.py — Router registration pattern]
- [Source: api/app/models/hs_section.py — Section model with notes_vn/notes_en]
- [Source: api/app/models/hs_chapter.py — Chapter model with notes_vn/notes_en]
- [Source: api/app/models/hs_heading.py — Heading model]
- [Source: api/app/models/hs_subheading.py — Subheading model with indent_level]
- [Source: api/app/models/hs_code.py — HS code model with all rate fields]
- [Source: api/app/models/fta_rate.py — FTA rate model with all fields]
- [Source: _bmad-output/implementation-artifacts/2-1-expand-tariff-import.md — Previous story context]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

### File List
