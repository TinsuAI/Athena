# Story 1.10: Anonymous Correction Interface

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As **anyone using the search**,
I want **to submit corrections when the system suggests the wrong HS code**,
So that **the knowledge base improves with real-world feedback**.

## Background

Stories 1-8 and 1-9 established the knowledge base infrastructure: every search is recorded in `lookup_records`, and verified corrections become the primary search mechanism (exact hash match -> pg_trgm similar match -> AI fallback). However, there is currently NO way for anyone to submit corrections. This story creates the anonymous correction interface - a public, rate-limited API and inline UI that allows anyone to suggest corrections without logging in. Corrections are auto-verified for MVP and immediately improve future search results.

**Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-10-story-1-10-anonymous-corrections.md`

**Dependencies:** Story 1-8 (done), Story 1-9 (review)

## Acceptance Criteria

1. **AC1: Suggest Correction Without Login**
   - **Given** I am on the search results page
   - **When** I see an incorrect HS code suggestion
   - **Then** I can click "Suggest Correction" without logging in
   - **And** no authentication prompt appears

2. **AC2: Correction Panel UI**
   - **Given** I click "Suggest Correction"
   - **When** the correction panel opens
   - **Then** I can search for the correct HS code via autocomplete
   - **And** I can add optional notes (max 200 characters)
   - **And** I can submit the correction

3. **AC3: Successful Correction Submission**
   - **Given** I submit a correction
   - **When** the submission succeeds
   - **Then** I see a success toast: "Thanks! Your correction will help improve search quality"
   - **And** the correction is immediately available in the knowledge base (auto-verified)
   - **And** the correction panel closes

4. **AC4: Rate Limiting**
   - **Given** I try to submit multiple corrections quickly
   - **When** I exceed 10 corrections per hour from the same IP
   - **Then** I see "Rate limit reached - please try again later"
   - **And** the submission is blocked

5. **AC5: GET Unverified Lookups API**
   - **Given** the lookup_records table has data
   - **When** I call `GET /api/corrections/lookups`
   - **Then** I receive a paginated list of unverified lookup records with their matched HS code details
   - **And** results are ordered by created_at descending

6. **AC6: POST Correction API**
   - **Given** I submit a correction via `POST /api/corrections`
   - **When** the request body contains `{ lookup_id, correct_hs_code_id, notes? }`
   - **Then** the lookup_record is updated: `correct_hs_code_id` is set, `is_verified = true`, `verified_at = now()`, `notes` is stored
   - **And** the response returns the updated record

7. **AC7: No Expert Role**
   - **Given** the user model (when it exists in Epic 2)
   - **Then** only "user" and "admin" roles exist
   - **And** no "expert" role exists in the database or auth system
   - **And** no `/expert/review` page exists in the frontend

## Tasks / Subtasks

- [x] Task 1: Create Corrections API Router (AC: #4, #5, #6)
  - [x] 1.1 Create `api/app/api/corrections.py` with `APIRouter(prefix="/api/corrections", tags=["corrections"])`
  - [x] 1.2 Implement `GET /api/corrections/lookups` endpoint - returns paginated unverified lookup records with matched HS code details (query params: limit, offset)
  - [x] 1.3 Implement `POST /api/corrections` endpoint - accepts `{ lookup_id: int, correct_hs_code_id: int, notes?: str }`, validates both IDs exist, updates lookup_record with correction, sets is_verified=true, verified_at=now()
  - [x] 1.4 Add IP-based rate limiting: 10 corrections per hour per IP using Redis sliding window (separate from existing 100 req/min search rate limit)
  - [x] 1.5 Register corrections router in `api/app/main.py`
  - [x] 1.6 Create Pydantic request/response schemas in `api/app/schemas/correction.py`
  - [x] 1.7 Create co-located tests `api/app/api/corrections_test.py`

- [x] Task 2: Add Repository Methods for Corrections (AC: #5, #6)
  - [x] 2.1 Add `get_unverified_with_hs_codes(limit, offset)` method to LookupRecordRepository - returns unverified records joined with HS code data (code, description_vn, description_en)
  - [x] 2.2 Add `find_by_id(id)` method to LookupRecordRepository
  - [x] 2.3 Add `apply_correction(record_id, correct_hs_code_id, notes)` method - sets correct_hs_code_id, is_verified=true, verified_at=now(), notes
  - [x] 2.4 Add tests for new repository methods

- [x] Task 3: Add HS Code Autocomplete API (AC: #2)
  - [x] 3.1 Add `GET /api/hs-codes/autocomplete?q=<query>&limit=10` endpoint to existing hs_codes router
  - [x] 3.2 Search HS codes by code prefix OR description substring (Vietnamese and English)
  - [x] 3.3 Return lightweight results: `{ id, code, description_vn, description_en }`
  - [x] 3.4 Add tests for autocomplete endpoint

- [x] Task 4: Build CorrectionButton Component (AC: #1)
  - [x] 4.1 Create `web/src/app/search/components/CorrectionButton.tsx`
  - [x] 4.2 Ghost button style with "Suggest Correction" text
  - [x] 4.3 No auth check - available to all visitors
  - [x] 4.4 OnClick opens CorrectionPanel (passes current lookup context)

- [x] Task 5: Build CorrectionPanel Component (AC: #2, #3, #4)
  - [x] 5.1 Create `web/src/app/search/components/CorrectionPanel.tsx`
  - [x] 5.2 Slide-in panel from right side (similar pattern to detail panels)
  - [x] 5.3 Show current suggestion as read-only (HS code + description, highlighted)
  - [x] 5.4 HS code autocomplete search field (calls `GET /api/hs-codes/autocomplete`)
  - [x] 5.5 Optional notes textarea (max 200 chars with counter)
  - [x] 5.6 Submit button calling `POST /api/corrections`
  - [x] 5.7 Handle rate limit error (429) with user-friendly message
  - [x] 5.8 Success toast notification on submission
  - [x] 5.9 Close panel after successful submission

- [x] Task 6: Integrate CorrectionButton into Search Page (AC: #1)
  - [x] 6.1 Add CorrectionButton to search results display in `web/src/app/search/page.tsx`
  - [x] 6.2 Pass lookup context (lookup_id from search response, matched HS code info) to CorrectionButton
  - [x] 6.3 Manage CorrectionPanel open/close state

- [x] Task 7: Update Search Response to Include lookup_id (AC: #6)
  - [x] 7.1 Add `lookup_id: int | None` field to `SearchResponseData` schema in `api/app/schemas/search.py`
  - [x] 7.2 Return the created/found lookup_record.id in search response so frontend can reference it for corrections
  - [x] 7.3 Update `_record_lookup()` to return the record ID to the caller
  - [x] 7.4 Update search endpoint to include lookup_id in response

- [x] Task 8: Write Integration Tests (AC: #1-7)
  - [x] 8.1 Test: GET /api/corrections/lookups returns paginated unverified records
  - [x] 8.2 Test: POST /api/corrections updates record with correction and auto-verifies
  - [x] 8.3 Test: POST /api/corrections with invalid lookup_id returns 404
  - [x] 8.4 Test: POST /api/corrections with invalid hs_code_id returns 400
  - [x] 8.5 Test: Rate limiting blocks after 10 corrections per hour per IP
  - [x] 8.6 Test: Corrected records appear in KB search (verify integration with KnowledgeBaseService)
  - [x] 8.7 Test: No authentication required for correction endpoints

## Dev Notes

### Critical Architecture Patterns (MUST FOLLOW)

**Backend Layered Architecture:**
```
Request -> api/corrections.py (thin) -> lookup_record_repository.py (data access)
                                     -> hs_code_service.py (autocomplete)
```

**API Response Format - ALL responses MUST use envelope format:**
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

**Naming Conventions:**
| Element | Convention | Example |
|---------|------------|---------|
| Table | snake_case, plural | `lookup_records` |
| Columns | snake_case | `correct_hs_code_id`, `is_verified` |
| Python classes | PascalCase | `CorrectionRequest`, `LookupRecordRepository` |
| Python functions | snake_case | `apply_correction()` |
| Files | snake_case | `corrections.py`, `correction.py` |
| Tests | co-located with `_test.py` suffix | `corrections_test.py` |
| React components | PascalCase files | `CorrectionButton.tsx`, `CorrectionPanel.tsx` |
| TypeScript functions | camelCase | `submitCorrection()` |

### Existing Code to Understand (READ THESE FIRST)

**`api/app/api/search.py`** (636 lines) - Main search endpoint:
- Flow: KB lookup (primary) -> cache check -> query enhancement -> vector search -> reranking -> classification -> response
- `_record_lookup()` helper (lines 82-122): Creates lookup records with dedup logic. Currently returns None. **MUST be modified** to return the record ID so the frontend can reference it for corrections.
- Three `_record_lookup()` call sites: cache hit (~line 303), no results (~line 371), found results (~line 515)
- Process logs tracked via `ProcessLogEntry` objects
- Uses `Depends(get_db)`, `Depends(get_redis)` for DI

**`api/app/repositories/lookup_record_repository.py`** (120 lines) - Existing methods:
- `create(record)` - Insert new record
- `find_by_query_hash(query_hash, within_hours=24)` - Dedup check
- `get_unverified(limit, offset)` - List unverified records (exists but only returns LookupRecord, no HS code join)
- `count_unverified()` - Count unverified
- `update(record)` - Update record
- `touch_updated_at(record_id)` - Touch timestamp
- `find_verified_exact(query_hash)` - KB exact match
- `find_verified_similar(query_text, threshold)` - KB similar match
- `compute_query_hash(query_text)` - SHA-256 of normalized text (standalone function)

**`api/app/models/lookup_record.py`** (73 lines) - LookupRecord model:
- Uses `Mapped` + `mapped_column()` syntax (SQLAlchemy 2.0)
- Key columns: `query_text`, `query_hash`, `matched_hs_code_id`, `correct_hs_code_id`, `is_verified`, `verified_by_user_id`, `verified_at`, `notes`
- FK relationships to `hs_codes` for both `matched_hs_code_id` and `correct_hs_code_id`
- `verified_by_user_id` is plain INTEGER (no FK, users table doesn't exist yet)

**`api/app/api/hs_codes.py`** - Existing HS code router:
- Pattern: `router = APIRouter(prefix="/api/hs-codes", tags=["hs-codes"])`
- Uses `HSCodeService(db)` for business logic
- Returns `ApiResponse[HSCodeSchema]` envelope
- **Add autocomplete endpoint HERE** (same router, new endpoint)

**`api/app/main.py`** (76 lines) - Router registration:
```python
from app.api.hs_codes import router as hs_codes_router
from app.api.search import router as search_router
app.include_router(hs_codes_router)
app.include_router(search_router)
# ADD: from app.api.corrections import router as corrections_router
# ADD: app.include_router(corrections_router)
```

**`api/app/core/rate_limiter.py`** (216 lines) - Existing rate limiter:
- Redis-based sliding window counter
- Currently: 100 req/min per IP on `/api/search`
- Uses `X-Forwarded-For` header for proxied clients
- **For corrections:** Create a SEPARATE rate limit key prefix with 10/hour window, NOT reuse the existing 100/min limiter

**`web/src/app/search/page.tsx`** (311 lines) - Search page:
- Client component with Zustand store hooks
- Renders single best match result (not result list)
- Shows classification reasoning, practical notes, process logs
- **Add CorrectionButton** below the search result display
- No correction UI components exist yet

**`web/src/lib/api.ts`** (113 lines) - API client:
- Generic `ApiClient` class with `.get()`, `.post()`, `.put()`, `.delete()` methods
- All responses typed as `ApiResponse<T>`
- Credentials included for auth cookies
- **Use apiClient.post()** for correction submission
- **Use apiClient.get()** for autocomplete

**`api/app/schemas/search.py`** - Current SearchResponseData:
```python
class SearchResponseData(BaseModel):
    hs_code: str
    description: str
    duty_rate: str
    vat_rate: str
    classification: ClassificationSchema
    practical_notes: list[str]
    confidence: int
    process_logs: list[ProcessLogEntry]
    source: str = "ai_suggestion"           # Added in 1-9
    is_verified: bool = False                # Added in 1-9
    verified_by: str | None = None           # Added in 1-9
    verified_at: str | None = None           # Added in 1-9
    # ADD: lookup_id: int | None = None      # NEW for 1-10
```

### Database Schema (lookup_records - Already Exists from 1-8)

```sql
lookup_records (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    query_language VARCHAR(5),
    matched_hs_code_id INTEGER REFERENCES hs_codes(id),
    correct_hs_code_id INTEGER REFERENCES hs_codes(id),
    is_verified BOOLEAN DEFAULT false NOT NULL,
    verified_by_user_id INTEGER,                  -- No FK (users table in Epic 2)
    verified_at TIMESTAMP WITH TIME ZONE,
    confidence_score FLOAT,
    search_method VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Existing indexes:
idx_lookup_records_query_hash (btree on query_hash)
idx_lookup_records_verified (btree on is_verified)
idx_lookup_records_query_trgm (GIN on query_text gin_trgm_ops)
idx_lookup_records_created_at (btree on created_at DESC)
```

**No new migrations needed.** All required columns and indexes already exist from Story 1-8. The `correct_hs_code_id`, `is_verified`, `verified_at`, and `notes` fields are already in the table - they just need to be populated by the correction API.

### Correction Flow (End-to-End)

```
1. User searches → search.py creates lookup_record → returns lookup_id in response
2. User sees incorrect result → clicks "Suggest Correction" (no login)
3. CorrectionPanel opens → user searches for correct HS code (autocomplete)
4. User submits → POST /api/corrections { lookup_id, correct_hs_code_id, notes? }
5. Backend: validates IDs, updates lookup_record (correct_hs_code_id, is_verified=true, verified_at=now(), notes)
6. Next search for same/similar query → KnowledgeBaseService finds verified record → returns instantly
```

### Rate Limiting Strategy for Corrections

Create a SEPARATE rate limiting mechanism for corrections (do NOT reuse the existing 100 req/min limiter):

```python
# In api/app/api/corrections.py
CORRECTION_RATE_LIMIT = 10       # max corrections
CORRECTION_RATE_WINDOW = 3600    # per hour (seconds)
CORRECTION_RATE_PREFIX = "correction_rate:"  # separate Redis key prefix

async def check_correction_rate_limit(redis, client_ip: str) -> tuple[bool, int, int]:
    """Check IP-based rate limit for corrections (10/hour)."""
    key = f"{CORRECTION_RATE_PREFIX}{client_ip}"
    # Use Redis INCR + EXPIRE sliding window pattern
    # Return (allowed, remaining, reset_seconds)
```

The existing `RateLimitMiddleware` in `rate_limiter.py` runs on ALL `/api/*` requests (100/min). Corrections will also be subject to this global limit PLUS the stricter 10/hour correction-specific limit.

### Frontend Component Architecture

```
web/src/app/search/
├── page.tsx                    # MODIFY: add CorrectionButton, manage panel state
├── components/
│   ├── SearchBar.tsx           # Existing - no changes
│   ├── CorrectionButton.tsx    # NEW: ghost button "Suggest Correction"
│   └── CorrectionPanel.tsx     # NEW: slide-in panel with autocomplete
```

**CorrectionButton Pattern:**
```tsx
interface CorrectionButtonProps {
  lookupId: number | null;
  matchedHsCode: string;
  matchedDescription: string;
  onCorrect: () => void;          // Opens CorrectionPanel
}
```

**CorrectionPanel Pattern:**
```tsx
interface CorrectionPanelProps {
  isOpen: boolean;
  onClose: () => void;
  lookupId: number;
  currentHsCode: string;          // Current (possibly wrong) suggestion
  currentDescription: string;
}
// Uses apiClient.get('/api/hs-codes/autocomplete?q=...') for search
// Uses apiClient.post('/api/corrections', { lookup_id, correct_hs_code_id, notes })
```

### Implementation Strategy

**Order of implementation:**
1. Task 7 first (add lookup_id to search response) - enables frontend to reference lookups
2. Task 2 (repository methods) - data access layer
3. Task 1 (corrections API) - backend endpoints with rate limiting
4. Task 3 (autocomplete API) - needed for frontend search
5. Task 4 (CorrectionButton) - simple UI component
6. Task 5 (CorrectionPanel) - main correction UI
7. Task 6 (integration) - wire everything together
8. Task 8 (integration tests) - verify end-to-end flow

### Previous Story Intelligence (from Stories 1-8, 1-9)

**Key learnings from Story 1-8 implementation:**
- LookupRecord model uses `Mapped` + `mapped_column()` syntax (SQLAlchemy 2.0) - MUST continue
- Repository uses `AsyncSession` with `await self.session.flush()` for writes
- `compute_query_hash()` is a standalone function - import from `lookup_record_repository`
- `_record_lookup()` in search.py is wrapped in try/except so failures never break search
- `_detect_query_language()` auto-detects vi/en/zh
- Code review feedback: Added query_language detection, removed redundant index declarations, improved logging

**Key learnings from Story 1-9 implementation:**
- KnowledgeBaseService sits in `api/app/services/knowledge_base_service.py`
- KB lookup is FIRST step in search.py, BEFORE cache check
- KB hit short-circuits entire AI pipeline (skips embedding, vector search, LLM calls)
- Response includes `source`, `is_verified`, `verified_by`, `verified_at` fields
- 59/59 tests pass across all test files - this is the regression baseline
- Process logs added for kb_exact_lookup/kb_similar_lookup steps

**Full regression baseline:** 59/59 tests pass. Do NOT introduce regressions.

### Git Intelligence (Recent Commits)

| Commit | Description | Relevance |
|--------|-------------|-----------|
| 8434045 | 1-9 done | Direct predecessor - KB-enhanced search |
| 19cae5d | feat: Implement knowledge base schema with lookup storage | Story 1-8 - foundation |
| d803744 | feat: Implement model selection UI and LLM services | Search pipeline with LLM |
| b68b958 | 1-4 done | Search UI with SearchBar component |
| 3d18b72 | 1-3 done | Search API with hybrid search |

**Files changed in most recent commit (1-9 done):**
- `api/app/api/search.py` - KB lookup integration
- `api/app/api/search_test.py` - KB search tests
- `api/app/repositories/lookup_record_repository.py` - find_verified_exact/similar
- `api/app/repositories/lookup_record_repository_test.py` - KB repo tests
- `api/app/schemas/search.py` - source/verification fields
- `api/app/services/knowledge_base_service.py` - KB service (new)
- `api/app/services/knowledge_base_service_test.py` - KB tests (new)

**Patterns established:**
- Co-located tests with `_test.py` suffix
- Envelope response format on all responses
- Async/await everywhere
- Services instantiated with session in route handlers
- Process logs for transparency
- Try/except wrapping for non-critical operations

### Anti-Patterns (NEVER DO)

- **NEVER** require login for correction submission (this is anonymous/public)
- **NEVER** use synchronous SQLAlchemy (must be async with `AsyncSession`)
- **NEVER** put business logic in route handlers (use repository layer)
- **NEVER** create tests in a separate `/tests` directory (co-locate with `_test.py`)
- **NEVER** use the old `Column()` syntax (use `Mapped` + `mapped_column()`)
- **NEVER** skip the envelope response format
- **NEVER** create new database migrations (all schema exists from 1-8)
- **NEVER** add an "expert" role to the user model
- **NEVER** create an `/expert/review` page
- **NEVER** reuse the existing 100 req/min rate limiter for corrections (create separate 10/hour limiter)
- **NEVER** block the search response for lookup_id retrieval (keep it lightweight)
- **NEVER** allow corrections without validating that lookup_id and correct_hs_code_id exist
- **NEVER** bypass rate limiting - corrections from same IP exceeding 10/hour MUST be rejected

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Backend | FastAPI | Latest | Python 3.12+, async |
| Database | PostgreSQL | 16 | With pgvector + pg_trgm |
| ORM | SQLAlchemy | 2.0 | Async mode, Mapped syntax |
| Cache/Rate Limit | Redis | 7 | Sessions, search cache, rate limiting |
| Testing | pytest | Latest | With pytest-asyncio |
| Frontend | Next.js | 15+ | App Router, TypeScript |
| Styling | Tailwind CSS | Latest | Utility-first |
| State | Zustand | Latest | Single store with slices |
| API Client | fetch | Native | Via apiClient in web/src/lib/api.ts |

### Project Structure Notes

- All new backend files follow existing patterns in `api/app/api/`, `api/app/schemas/`
- All new frontend files go in `web/src/app/search/components/`
- No new database tables or migrations needed
- No conflicts with current project structure
- Corrections router follows same pattern as hs_codes router and search router

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.10]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-10-story-1-10-anonymous-corrections.md]
- [Source: _bmad-output/planning-artifacts/architecture.md#API-Endpoints]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: _bmad-output/implementation-artifacts/1-8-knowledge-base-schema-lookup-storage.md]
- [Source: _bmad-output/implementation-artifacts/1-9-knowledge-enhanced-search.md]
- [Source: api/app/api/search.py - _record_lookup helper]
- [Source: api/app/repositories/lookup_record_repository.py - existing methods]
- [Source: api/app/models/lookup_record.py - LookupRecord schema]
- [Source: api/app/main.py - router registration pattern]
- [Source: api/app/core/rate_limiter.py - rate limiting implementation]
- [Source: web/src/app/search/page.tsx - search UI]
- [Source: web/src/lib/api.ts - API client pattern]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- Redis pipeline mock: `AsyncMock` makes `pipeline()` async when it should be sync returning an async context manager. Fix: Use `MagicMock` for pipeline() returning `MagicMock` context manager with `AsyncMock` __aenter__/__aexit__.
- Pydantic serialization warning: `_record_lookup` mock returns AsyncMock default instead of int for `lookup_id` field. Fix: Set `return_value=1` on all `_record_lookup` patches in KB integration tests.

### Completion Notes List

- Task 1: Created corrections API router (`api/app/api/corrections.py`) with GET /lookups and POST / endpoints, Redis sliding window rate limiting (10/hour per IP), registered in main.py. 19 unit tests all passing.
- Task 2: Added `get_unverified_with_hs_codes()`, `find_by_id()`, `apply_correction()` to LookupRecordRepository. 6 new tests, 26 total repo tests passing.
- Task 3: Added HS code autocomplete API (`GET /api/hs-codes/autocomplete`) with search by code prefix + description. Added HSCodeAutocompleteItem schema. 6 tests passing. Route placed BEFORE `/{code}` to prevent path conflict.
- Task 4: Created CorrectionButton component - ghost-style button, no auth, disabled when no lookup_id.
- Task 5: Created CorrectionPanel component - slide-in panel with autocomplete search (debounced 300ms), notes textarea (200 char), submit, 429 handling, success toast, auto-close.
- Task 6: Integrated CorrectionButton and CorrectionPanel into search page. Added correctionPanelOpen state. Updated SearchResult type with lookup_id field.
- Task 7: Added `lookup_id` field to SearchResponseData schema. Modified `_record_lookup()` to return int|None. Updated all 4 call sites in search.py. Fixed Pydantic serialization warnings in 6 KB integration tests.
- Task 8: Added 3 KB integration tests (TestCorrectionKBIntegration) verifying correction → KB search flow: exact hash match, similar text match, auto-verification. All 22 corrections tests passing.

### File List

**New files:**
- `api/app/schemas/correction.py` - Pydantic schemas for corrections API
- `api/app/api/corrections.py` - Corrections API router with rate limiting
- `api/app/api/corrections_test.py` - 22 tests for corrections endpoint
- `web/src/app/search/components/CorrectionButton.tsx` - Suggest correction button component
- `web/src/app/search/components/CorrectionPanel.tsx` - Slide-in correction panel with autocomplete

**Modified files:**
- `api/app/main.py` - Register corrections router, add AC7 comment about role reservation
- `api/app/repositories/lookup_record_repository.py` - Added get_unverified_with_hs_codes, find_by_id, apply_correction methods
- `api/app/repositories/lookup_record_repository_test.py` - Added 6 new tests (26 total)
- `api/app/schemas/hs_code.py` - Added HSCodeAutocompleteItem schema
- `api/app/repositories/hs_code_repository.py` - Added autocomplete method
- `api/app/services/hs_code_service.py` - Added autocomplete method
- `api/app/api/hs_codes.py` - Added GET /autocomplete endpoint
- `api/app/api/hs_codes_test.py` - Added 6 autocomplete tests
- `api/app/schemas/search.py` - Added lookup_id field to SearchResponseData
- `api/app/api/search.py` - _record_lookup returns int|None, lookup_id assigned in response
- `api/app/api/search_test.py` - Fixed _record_lookup mock return values for KB integration tests
- `web/src/types/hs-code.ts` - Added source, is_verified, verified_by, verified_at, lookup_id fields
- `web/src/app/search/page.tsx` - Integrated CorrectionButton and CorrectionPanel
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Updated story 1-10 status
- `_bmad-output/planning-artifacts/epics.md` - Updated Epic 1 story list

## Change Log

- 2026-02-10: Implemented Story 1.10 - Anonymous Correction Interface. All 8 tasks complete. 164 tests pass (no regressions).
- 2026-02-10: Code review fixes applied:
  - Added duplicate correction validation (rejects if correct_hs_code_id == matched_hs_code_id)
  - Added already-corrected check (409 Conflict if record already verified)
  - Added confirmation dialog before submitting corrections
  - Added console.error for autocomplete failures (debugging)
  - Fixed type annotation (redis.Redis[bytes] | None)
  - Added AC7 comment in main.py reserving role names for Epic 2
  - Updated File List to include sprint-status.yaml and epics.md
  - Added 2 new tests for validation rules (total: 24 corrections tests)
