# Story 1.13: Lookup Detail Page

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want **to view the full details of a past lookup including classification reasoning, practical notes, and process logs**,
So that **I can review the complete search analysis and submit corrections if the result was wrong**.

## Background

Stories 1-8 through 1-12 built the knowledge base infrastructure: every search creates a lookup record, expert corrections mark them as verified, classification reasoning/practical notes/process logs are persisted as JSONB (Story 1-11), and a paginated list page with filtering exists (Story 1-12). The list page rows already link to `/lookups/[id]` — this story creates the detail page that receives those clicks.

**Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-10-lookup-history.md`

**Dependencies:** Stories 1-11 (done), 1-12 (review)

## Acceptance Criteria

1. **AC1: Detail API Endpoint**
   - **Given** a lookup record exists with persisted data
   - **When** I call `GET /api/lookups/{id}`
   - **Then** I receive the full lookup record including:
     - `query_text`, `query_language`, `created_at`
     - matched HS code with `code`, `description_vn`, `description_en`, `duty_rate`, `vat_rate`
     - correct HS code (if corrected) with same fields
     - `classification_data` (material + function reasoning)
     - `practical_notes` (list of strings)
     - `process_logs` (list of step objects with `step`, `status`, `message`, `duration_ms`, `details`)
     - `is_verified`, `verified_at`, `notes`
     - `confidence_score`, `search_method`
   - **And** response follows envelope format `{success, data, error}`

2. **AC2: 404 for Missing Lookup**
   - **Given** a lookup record does not exist
   - **When** I call `GET /api/lookups/99999`
   - **Then** I receive an error response following RFC 7807 format with `status: 404` in the envelope (HTTP status is always 200 per architecture)

3. **AC3: Frontend Detail Page**
   - **Given** I navigate to `/lookups/[id]` in the frontend
   - **When** the page loads
   - **Then** I see the full lookup detail with sections:
     - **Query**: original search text with language badge
     - **Matched Result**: HS code, description, duty/VAT rates, confidence badge
     - **Classification Reasoning**: material and function analysis (rendered as readable text)
     - **Practical Notes**: list of import notes
     - **Process Log**: collapsible timeline of search steps with durations
     - **Correction**: status badge (verified/unverified) and correction button

4. **AC4: Correction Flow on Detail Page**
   - **Given** I am viewing an unverified lookup
   - **When** I click "Suggest Correction" (Reuse CorrectionButton/CorrectionPanel from search page)
   - **Then** the CorrectionPanel opens and I can submit a correction that immediately verifies the lookup

5. **AC5: Verified Lookup Display**
   - **Given** I am viewing a verified (corrected) lookup
   - **When** I see the correction section
   - **Then** I see the correct HS code with description, verification date, and correction notes
   - **And** the "Suggest Correction" button is replaced with a "Corrected" badge

6. **AC6: Breadcrumb Navigation**
   - **Given** I am on the detail page
   - **When** I look at the breadcrumb
   - **Then** I see "Lookups > Lookup #123" with "Lookups" linking back to `/lookups`

7. **AC7: Navigation from List**
   - **Given** I am on the `/lookups` list page
   - **When** I click on any row
   - **Then** I navigate to `/lookups/[id]` and see the detail page (already wired in Story 1-12)

## Tasks / Subtasks

- [x] Task 1: Add Repository Method (AC: #1, #2)
  - [x] 1.1 Add `find_by_id_with_details(record_id)` to `LookupRecordRepository` — eager-loads both `matched_hs_code` and `correct_hs_code` relationships (with their `fta_rates` if needed)
  - [x] 1.2 Write co-located tests in `lookup_record_repository_test.py`

- [x] Task 2: Create Detail Schema (AC: #1)
  - [x] 2.1 Add `LookupDetailHSCode` schema to `api/app/schemas/lookup.py` — fields: `code`, `description_vn`, `description_en`, `duty_rate`, `vat_rate`
  - [x] 2.2 Add `LookupDetailResponse` schema to `api/app/schemas/lookup.py` — all fields including `classification_data`, `practical_notes`, `process_logs`, both HS code objects, correction metadata

- [x] Task 3: Add Detail API Endpoint (AC: #1, #2)
  - [x] 3.1 Add `GET /api/lookups/{id}` endpoint to `api/app/api/lookups.py`
  - [x] 3.2 Return 404 RFC 7807 error for missing records
  - [x] 3.3 Write co-located tests in `api/app/api/lookups_test.py`

- [x] Task 4: Add Frontend Types and API Function (AC: #3)
  - [x] 4.1 Add `LookupDetail` and `LookupDetailHSCode` types to `web/src/types/lookup.ts`
  - [x] 4.2 Add `getLookupDetail(id: number)` function to `web/src/lib/api.ts`

- [x] Task 5: Build Frontend Detail Page (AC: #3, #4, #5, #6, #7)
  - [x] 5.1 Create `web/src/app/lookups/[id]/page.tsx` — client component with data fetching, loading/error states
  - [x] 5.2 Build query section — displays original search text with language badge
  - [x] 5.3 Build matched result section — HS code, descriptions, duty/VAT rates, confidence badge
  - [x] 5.4 Build classification reasoning section — material and function analysis as readable text
  - [x] 5.5 Build practical notes section — rendered as formatted list
  - [x] 5.6 Build process log section — collapsible timeline with step names, statuses, durations
  - [x] 5.7 Build correction section — verified badge or CorrectionButton (reuse from search page)
  - [x] 5.8 Implement CorrectionPanel integration (reuse `web/src/app/search/components/CorrectionPanel.tsx`)
  - [x] 5.9 Add breadcrumb: "Lookups > Lookup #123"
  - [x] 5.10 Handle correction success — refresh page data after correction submitted

## Dev Notes

### Critical Architecture Patterns (MUST FOLLOW)

**Backend Layered Architecture:**
```
Request -> api/lookups.py (thin) -> LookupRecordRepository (data access)
              |                          |
   validate path param,           SQLAlchemy async query,
   call repo, format response     eager-load relationships
```

**No service layer needed** — straightforward data retrieval. Route handler uses repository directly (same pattern as existing `GET /api/lookups` list endpoint and `corrections.py`).

**API Response Format — ALL responses MUST use envelope format:**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "query_text": "Thanh treo khan bang dong",
    "classification_data": { "material": "...", "function": "..." },
    "practical_notes": ["note1", "note2"],
    "process_logs": [{ "step": "...", "status": "...", "duration_ms": 123 }],
    "matched_hs_code": { "code": "7418.20.00", "description_vn": "...", "duty_rate": "30%", "vat_rate": "10%" },
    "correct_hs_code": null,
    "is_verified": false,
    "confidence_score": 95.0,
    "search_method": "ai_full_pipeline"
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
    "type": "https://athena.example/errors/not-found",
    "title": "Lookup Not Found",
    "status": 404,
    "detail": "No lookup record with id 99999 exists.",
    "instance": "/api/lookups/99999"
  }
}
```

### Existing Code to Understand (READ THESE FIRST)

**`api/app/api/lookups.py`** — **PRIMARY FILE TO EXTEND:**
- Already has `GET /api/lookups` list endpoint (from Story 1-12)
- Uses `LookupRecordRepository` directly in route handler
- Pattern: validate params → call repo → build schema → return `success_response()`
- **Add the detail endpoint to this same file**

**`api/app/repositories/lookup_record_repository.py`** (~200 lines):
- `find_by_id(record_id)` — Exists but does NOT eager-load HS code relationships. Returns basic `LookupRecord` or `None`.
- `get_all_with_hs_codes(limit, offset, verified_filter)` — Uses `selectinload(LookupRecord.matched_hs_code)`. **Use this pattern** for the new eager-load method, but load BOTH `matched_hs_code` and `correct_hs_code`.
- Pattern: `select(LookupRecord).options(selectinload(...)).where(...)`

**`api/app/models/lookup_record.py`** (~76 lines):
- Two relationships: `matched_hs_code` (FK `matched_hs_code_id`) and `correct_hs_code` (FK `correct_hs_code_id`)
- JSONB columns: `classification_data`, `practical_notes`, `process_logs` — all `Mapped[dict | None]`
- Correction fields: `is_verified`, `verified_at`, `verified_by_user_id`, `notes`
- **DO NOT modify this file** — model already has everything needed

**`api/app/schemas/lookup.py`** (~25 lines):
- Currently only has `LookupListItem` and `PaginatedLookupListResponse` (from Story 1-12)
- **Add detail-specific schemas here** — `LookupDetailHSCode` and `LookupDetailResponse`

**`api/app/schemas/base.py`** (~59 lines):
- `success_response(data)` — Returns `{"success": True, "data": data, "error": None}`
- `error_response(type_uri, title, status, detail, instance)` — Returns RFC 7807 error envelope
- **Import and use these directly**

**`api/app/api/corrections.py`** (~236 lines) — **Correction Flow Reference:**
- `POST /api/corrections` — Accepts `{lookup_id, correct_hs_code_id, notes}`
- Calls `repo.apply_correction()` which sets `correct_hs_code_id`, `is_verified=True`, `verified_at=now`
- Rate limited: 10/hour per IP via Redis
- Returns updated lookup record
- **The detail page calls this EXISTING endpoint for corrections — do NOT create new correction logic**

**`web/src/app/search/components/CorrectionButton.tsx`** (~25 lines):
- Props: `lookupId`, `matchedHsCode`, `matchedDescription`, `onCorrect` callback
- Renders "Suggest Correction" button, disabled if no lookupId
- Vietnamese text: "Đề xuất sửa đổi"
- **Reuse in detail page** — import directly

**`web/src/app/search/components/CorrectionPanel.tsx`** (~200 lines):
- Props: `isOpen`, `onClose`, `lookupId`, `matchedHsCode`, `matchedDescription`, `onCorrectionSubmitted`
- Full slide-in panel with HS code autocomplete search (debounced 300ms)
- Posts to `POST /api/corrections` with `{lookup_id, correct_hs_code_id, notes}`
- Handles rate limit (429), duplicate (400), already-verified (409) errors
- Vietnamese UI throughout
- **Reuse in detail page** — import directly, pass `lookupId` from route params

**`web/src/app/lookups/page.tsx`** (~150 lines) — **Frontend Pattern Reference:**
- Client component (`"use client"`)
- Local state with useState (no Zustand for lookups)
- Data fetching in useCallback with async/await
- Vietnamese UI text throughout
- **Follow this same pattern** for the detail page

**`web/src/types/hs-code.ts`** — **Existing Types to Know:**
- `ProcessLogEntry`: `{ step: string, status: string, message: string, duration_ms: number, details?: Record<string, unknown> }`
- `Classification`: `{ material: string, function: string }`
- **These types already exist** — use them in the detail page type if helpful, or define lookup-specific types

**`web/src/lib/api.ts`** (~120 lines) — **API Client:**
- `apiClient.get<T>(path)` / `apiClient.post<T>(path, body)` — type-safe HTTP methods
- Uses `NEXT_PUBLIC_API_URL` env variable
- Unwraps envelope: returns `data` from `{success, data, error}`
- `getLookups(limit, offset, verified?)` already exists
- **Add `getLookupDetail(id: number)` following the same pattern**

### New Repository Method (Exact Signature)

**`find_by_id_with_details()` — Based on existing `get_all_with_hs_codes()` pattern:**
```python
async def find_by_id_with_details(self, record_id: int) -> LookupRecord | None:
    """Get a single lookup record with eager-loaded HS code relationships."""
    query = (
        select(LookupRecord)
        .options(
            selectinload(LookupRecord.matched_hs_code),
            selectinload(LookupRecord.correct_hs_code),
        )
        .where(LookupRecord.id == record_id)
    )
    result = await self.session.execute(query)
    return result.scalar_one_or_none()
```

### New Schema Definitions

**Add to `api/app/schemas/lookup.py`:**
```python
class LookupDetailHSCode(BaseModel):
    code: str
    description_vn: str | None
    description_en: str | None
    duty_rate: str | None
    vat_rate: str | None


class LookupDetailResponse(BaseModel):
    id: int
    query_text: str
    query_language: str | None
    matched_hs_code: LookupDetailHSCode | None
    correct_hs_code: LookupDetailHSCode | None
    classification_data: dict | None    # {"material": "...", "function": "..."}
    practical_notes: list | None        # ["note1", "note2"]
    process_logs: list | None           # [{"step": "...", "status": "...", ...}]
    confidence_score: float | None
    search_method: str
    is_verified: bool
    verified_at: str | None             # ISO 8601 or null
    notes: str | None                   # Correction notes
    created_at: str                     # ISO 8601
```

### API Endpoint Implementation

**Add to `api/app/api/lookups.py`:**
```python
@router.get(
    "/{lookup_id}",
    response_model=ApiResponse[LookupDetailResponse],
    summary="Get lookup record details",
)
async def get_lookup_detail(
    lookup_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = LookupRecordRepository(session=db)
    record = await repo.find_by_id_with_details(lookup_id)
    if record is None:
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="Lookup Not Found",
            status=404,
            detail=f"No lookup record with id {lookup_id} exists.",
            instance=f"/api/lookups/{lookup_id}",
        )

    def _build_hs_code(hs) -> dict | None:
        if hs is None:
            return None
        return LookupDetailHSCode(
            code=hs.code,
            description_vn=hs.description_vn,
            description_en=hs.description_en,
            duty_rate=hs.duty_rate,
            vat_rate=hs.vat_rate,
        ).model_dump()

    response = LookupDetailResponse(
        id=record.id,
        query_text=record.query_text,
        query_language=record.query_language,
        matched_hs_code=_build_hs_code(record.matched_hs_code),
        correct_hs_code=_build_hs_code(record.correct_hs_code),
        classification_data=record.classification_data,
        practical_notes=record.practical_notes,
        process_logs=record.process_logs,
        confidence_score=record.confidence_score,
        search_method=record.search_method,
        is_verified=record.is_verified,
        verified_at=record.verified_at.isoformat() if record.verified_at else None,
        notes=record.notes,
        created_at=record.created_at.isoformat(),
    )
    return success_response(response.model_dump())
```

**Note:** `error_response` returns a dict with status 404. Check how the existing codebase handles HTTP status codes — if `error_response` doesn't set the HTTP status, you may need to use `JSONResponse(status_code=404, content=error_response(...))` instead.

### Frontend Implementation Guide

**Type definitions (add to `web/src/types/lookup.ts`):**
```typescript
export interface LookupDetailHSCode {
  code: string;
  description_vn: string | null;
  description_en: string | null;
  duty_rate: string | null;
  vat_rate: string | null;
}

export interface LookupDetail {
  id: number;
  query_text: string;
  query_language: string | null;
  matched_hs_code: LookupDetailHSCode | null;
  correct_hs_code: LookupDetailHSCode | null;
  classification_data: { material: string; function: string } | null;
  practical_notes: string[] | null;
  process_logs: ProcessLogEntry[] | null;  // Reuse from hs-code.ts or define inline
  confidence_score: number | null;
  search_method: string;
  is_verified: boolean;
  verified_at: string | null;
  notes: string | null;
  created_at: string;
}

export interface ProcessLogEntry {
  step: string;
  status: string;
  message: string;
  duration_ms: number;
  details?: Record<string, unknown>;
}
```

**API function (add to `web/src/lib/api.ts`):**
```typescript
export async function getLookupDetail(id: number): Promise<LookupDetail> {
  return apiClient.get<LookupDetail>(`/api/lookups/${id}`);
}
```

**Page structure (`web/src/app/lookups/[id]/page.tsx`):**
- Client component (`"use client"`)
- Use `useParams()` from `next/navigation` to get `id`
- Local state: `lookup: LookupDetail | null`, `isLoading: boolean`, `error: string | null`
- `showCorrectionPanel: boolean` for correction flow
- useEffect: Fetch on mount via `getLookupDetail(Number(params.id))`
- Handle 404: Show "Lookup not found" with link back to `/lookups`
- On correction success: Re-fetch lookup data to show updated verified state

**Page layout sections (top to bottom):**

1. **Breadcrumb**: `Lookups > Lookup #${id}` — "Lookups" links to `/lookups`

2. **Query Section**: Card with query_text in a quoted block, language badge (e.g., "vi", "en", "zh"), created_at date

3. **Matched Result Section**: Card showing:
   - HS code in monospace font (e.g., `7418.20.00`)
   - Description VN and EN
   - Duty rate and VAT rate
   - Confidence badge (color-coded: green >= 80, yellow >= 50, red < 50)
   - Search method badge

4. **Classification Reasoning Section** (only if `classification_data` exists):
   - **Material**: rendered as paragraph
   - **Function**: rendered as paragraph

5. **Practical Notes Section** (only if `practical_notes` exists and has items):
   - Rendered as a numbered/bulleted list

6. **Process Log Section** (only if `process_logs` exists and has items):
   - Collapsible by default (use `<details>/<summary>` or a toggle button)
   - Each log entry: step name, status icon (checkmark/X/skip), message, duration in ms
   - Visual timeline with durations

7. **Correction Section**:
   - If `is_verified`: Show green "Corrected" badge, correct HS code details, verified_at date, correction notes
   - If not verified: Show CorrectionButton that opens CorrectionPanel

**CorrectionButton/CorrectionPanel reuse:**
```typescript
import { CorrectionButton } from '@/app/search/components/CorrectionButton';
import { CorrectionPanel } from '@/app/search/components/CorrectionPanel';
```
Pass props:
- **CorrectionButton:** `lookupId`, `matchedHsCode`, `matchedDescription`, `onCorrect`
- **CorrectionPanel:** `isOpen`, `onClose` (handles both close and success), `lookupId`, `currentHsCode`, `currentDescription`

Note: CorrectionPanel uses `onClose` (not `onCorrectionSubmitted`) and `current*` prefix (not `matched*`) - these are the actual component prop names from Story 1-10.

**Vietnamese UI text:**
- Breadcrumb: "Tra cứu" > "Chi tiết #123"
- Query section header: "Truy vấn tìm kiếm"
- Matched result header: "Kết quả phù hợp"
- Classification header: "Phân tích phân loại"
- Material label: "Chất liệu"
- Function label: "Công dụng"
- Practical notes header: "Ghi chú thực tế"
- Process log header: "Nhật ký xử lý"
- Correction header: "Hiệu chỉnh"
- Corrected badge: "Đã hiệu chỉnh"
- Not found: "Không tìm thấy bản ghi tra cứu"
- Back to list: "Quay lại danh sách"

**Confidence badge colors (consistent with list page):**
- >= 80: green (`bg-green-100 text-green-800`)
- >= 50: yellow (`bg-yellow-100 text-yellow-800`)
- < 50: red (`bg-red-100 text-red-800`)

### Previous Story Intelligence (from Stories 1-8 through 1-12)

**Key learnings from Story 1-12 (direct predecessor):**
- LookupRecordRepository pattern: `select(LookupRecord).options(selectinload(...))` for eager loading
- Route handler: validate → call repo → build schema items → `success_response(response.model_dump())`
- Frontend: Client component, local useState, useCallback for fetching, Vietnamese text
- Navigation: Header has "Lookups" link, rows on list page already call `router.push(/lookups/${id})`
- No service layer needed for simple CRUD reads
- Tests: 218 passed backend, 54 passed frontend, no regressions

**Key learnings from Story 1-11:**
- JSONB columns (classification_data, practical_notes, process_logs) already exist and are populated on every search
- `classification_data` structure: `{"material": "...", "function": "..."}`
- `practical_notes` structure: `["note1", "note2", ...]`
- `process_logs` structure: `[{"step": "...", "status": "...", "message": "...", "duration_ms": 123, "details": {...}}]`

**Key learnings from Story 1-10:**
- CorrectionButton and CorrectionPanel are fully-featured reusable components
- CorrectionPanel handles: autocomplete search, confirmation dialog, rate limit errors, success toast
- All correction logic is in the panel — just import and provide props
- POST /api/corrections endpoint handles all correction logic server-side

**Code review patterns from recent stories:**
- Always use proper type parameters (`dict[str, str]` not just `dict`)
- Verify test count after implementation
- Check that imports reference correct paths

### Git Intelligence (Recent Commits)

| Commit | Description | Relevance |
|--------|-------------|-----------|
| ad58766 | 1-12 done | Direct predecessor — list page complete, rows link to /lookups/[id] |
| 36b114e | 1-11 done | JSONB columns persisted (classification, notes, logs) |
| 6271d95 | feat: Implement lookup history and detail pages | **CHECK**: May contain partial work for detail page |
| a0fb771 | feat: Localize correction UI to Vietnamese | Vietnamese UI pattern established |
| 150c5ea | 1-10 done | Correction components created and working |

**IMPORTANT: Commit 6271d95 may have partial detail page work!** Run `git show --name-only 6271d95` before creating files to check if `/lookups/[id]/page.tsx` already exists. If so, review and extend rather than overwrite.

**Patterns from recent commits:**
- Co-located tests with `_test.py` suffix
- Envelope response on all API responses
- Async/await everywhere (backend)
- Vietnamese UI text (frontend)
- No service layer for simple CRUD endpoints

### Anti-Patterns (NEVER DO)

- **NEVER** create a service layer for this endpoint — it's simple data retrieval, route handler + repository is sufficient
- **NEVER** put business logic in the route handler — validate, call repo, format response only
- **NEVER** use camelCase in API JSON responses — all fields snake_case
- **NEVER** create tests in separate `/tests` directory — co-locate with `_test.py`
- **NEVER** skip the envelope response format
- **NEVER** create new correction logic — reuse existing CorrectionButton/CorrectionPanel and POST /api/corrections endpoint
- **NEVER** fetch via Next.js API routes — fetch FastAPI directly with CORS
- **NEVER** use status enums for loading states — use boolean flags
- **NEVER** modify the LookupRecord model — it already has everything needed
- **NEVER** add Zustand store for lookup detail — use local component state
- **NEVER** duplicate CorrectionPanel — import from `web/src/app/search/components/`

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
web/src/app/lookups/[id]/page.tsx      (new) — Lookup detail page
```

**Files to MODIFY:**
```
api/app/repositories/lookup_record_repository.py      (modify) — Add find_by_id_with_details
api/app/repositories/lookup_record_repository_test.py (modify) — Add tests for new method
api/app/schemas/lookup.py                              (modify) — Add LookupDetailHSCode, LookupDetailResponse
api/app/api/lookups.py                                 (modify) — Add GET /api/lookups/{id}
api/app/api/lookups_test.py                            (modify) — Add tests for detail endpoint
web/src/types/lookup.ts                                (modify) — Add LookupDetail, LookupDetailHSCode types
web/src/lib/api.ts                                     (modify) — Add getLookupDetail function
```

**Files to NOT modify:**
```
api/app/models/lookup_record.py       — Model already complete
api/app/api/corrections.py            — Reuse existing correction endpoint, don't modify
api/app/api/search.py                 — No changes needed
web/src/lib/store.ts                  — No global state for lookup detail
web/src/app/search/components/CorrectionButton.tsx  — Import as-is
web/src/app/search/components/CorrectionPanel.tsx   — Import as-is
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
    classification_data JSONB,      -- {"material": "...", "function": "..."}
    practical_notes JSONB,          -- ["note1", "note2", ...]
    process_logs JSONB,             -- [{"step": "...", "status": "...", "message": "...", "duration_ms": 123}]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Existing HS code table (for eager-loaded relationships):
hs_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    description_vn TEXT,
    description_en TEXT,
    unit VARCHAR(50),
    duty_rate VARCHAR(50),
    vat_rate VARCHAR(50),
    policy_notes TEXT,
    ...
);
```

No migrations needed for this story.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.13]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-10-lookup-history.md]
- [Source: _bmad-output/planning-artifacts/architecture.md#API-Response-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend-Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure-Boundaries]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: _bmad-output/implementation-artifacts/1-12-lookup-history-api-list-page.md]
- [Source: _bmad-output/implementation-artifacts/1-11-persist-full-lookup-details.md]
- [Source: api/app/api/lookups.py — GET /api/lookups (list endpoint, extend with detail)]
- [Source: api/app/api/corrections.py — POST /api/corrections (reuse for corrections)]
- [Source: api/app/repositories/lookup_record_repository.py — find_by_id, get_all_with_hs_codes]
- [Source: api/app/models/lookup_record.py — LookupRecord model with JSONB columns]
- [Source: api/app/schemas/lookup.py — Existing list schemas to extend]
- [Source: api/app/schemas/base.py — ApiResponse, success_response, error_response]
- [Source: web/src/app/search/components/CorrectionButton.tsx — Reusable correction button]
- [Source: web/src/app/search/components/CorrectionPanel.tsx — Reusable correction panel]
- [Source: web/src/app/lookups/page.tsx — Frontend page pattern and list-to-detail navigation]
- [Source: web/src/types/lookup.ts — Existing list types to extend]
- [Source: web/src/lib/api.ts — API client pattern]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. Clean implementation following existing patterns.

### Completion Notes List

- **Task 1**: Added `find_by_id_with_details()` to `LookupRecordRepository` using `selectinload` for both `matched_hs_code` and `correct_hs_code` relationships. 3 unit tests added.
- **Task 2**: Added `LookupDetailHSCode` and `LookupDetailResponse` Pydantic schemas to `api/app/schemas/lookup.py`.
- **Task 3**: Added `GET /api/lookups/{id}` endpoint. Returns full detail with eager-loaded HS codes, or 404 RFC 7807 error for missing records. Follows existing envelope pattern (HTTP 200 always, error status in envelope). 6 endpoint tests added.
- **Task 4**: Added `LookupDetail` and `LookupDetailHSCode` TypeScript interfaces. Added `getLookupDetail()` API function.
- **Task 5**: Built full detail page as client component with: query section with language badge, matched result with confidence badge and duty/VAT rates, classification reasoning (material/function), practical notes list, collapsible process log timeline, correction section with CorrectionButton/CorrectionPanel reuse, breadcrumb navigation. Vietnamese UI throughout. Correction success triggers data re-fetch.
- **Code Review Fixes**: Applied 10 improvements: type safety (proper generics in schemas), nullish coalescing (`??` instead of `||`), type guards (`typeof` check), improved loading UX (separate refetch state), accessibility (ARIA labels), error boundary, and corrected story documentation.

### Change Log

- 2026-02-11: Implemented Story 1-13 — Lookup Detail Page. Added backend detail endpoint with repository, schemas, and route handler. Built frontend detail page with all required sections, CorrectionButton/Panel reuse, and Vietnamese localization. 9 new backend tests (3 repo + 6 endpoint). All 227 backend tests pass, 54 frontend tests pass, no regressions.
- 2026-02-11 (Code Review): Applied 10 fixes from adversarial code review:
  - **Backend:** Added proper type parameters to `LookupDetailResponse` schema (`dict[str, Any]`, `list[str]`, `list[dict[str, Any]]`) for type safety
  - **Frontend:** Changed `||` to `??` for nullish coalescing (4 instances)
  - **Frontend:** Added `typeof` validation for `duration_ms` before rendering
  - **Frontend:** Split loading state into `isLoading` (initial) and `isRefetching` (after correction) with toast indicator instead of full-page spinner
  - **Frontend:** Added ARIA labels (`aria-expanded`, `aria-label`, `aria-hidden`) for accessibility on breadcrumb and process log toggle
  - **Frontend:** Created `error.tsx` error boundary for route-level error handling
  - **Story:** Clarified AC2 (envelope status vs HTTP status)
  - **Story:** Corrected CorrectionPanel prop names in dev notes (`onClose`, `current*` prefix)

### File List

**New files:**
- `web/src/app/lookups/[id]/page.tsx` — Lookup detail page (client component)
- `web/src/app/lookups/[id]/error.tsx` — Error boundary for lookup detail route (added during code review)

**Modified files:**
- `api/app/repositories/lookup_record_repository.py` — Added `find_by_id_with_details()` method
- `api/app/repositories/lookup_record_repository_test.py` — Added 3 tests for new method
- `api/app/schemas/lookup.py` — Added `LookupDetailHSCode` and `LookupDetailResponse` schemas
- `api/app/api/lookups.py` — Added `GET /api/lookups/{id}` detail endpoint
- `api/app/api/lookups_test.py` — Added 6 tests for detail endpoint (+ `_make_mock_detail_record` helper)
- `web/src/types/lookup.ts` — Added `LookupDetail` and `LookupDetailHSCode` interfaces
- `web/src/lib/api.ts` — Added `getLookupDetail()` function
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Updated story status
