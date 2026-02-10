# Story 1.9: Knowledge-Enhanced Search

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want **my searches to return expert-verified results when available**,
So that **I get accurate HS codes based on real expert knowledge, not just AI guesses**.

## Background

Three attempts at AI-based search (vector embeddings, category context enrichment, LLM query enhancement + reranking) all failed at ~0% accuracy. Story 1-8 created the `lookup_records` table that stores every search query with fields for expert correction. This story makes the knowledge base the **primary search mechanism**: verified KB results are returned first, and the existing AI pipeline serves as fallback only when no KB match exists.

**Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-10.md`

**Dependency:** Story 1-8 (Knowledge Base Schema & Lookup Storage) - DONE

## Acceptance Criteria

1. **AC1: Exact KB Match Returns Verified Result**
   - **Given** an expert has previously verified a query -> HS code mapping in `lookup_records`
   - **When** another user searches with the same query text (normalized: stripped, lowercased)
   - **Then** the verified HS code is returned with `source: "knowledge_base"` and `confidence: 100`
   - **And** response time is <50ms for the KB lookup portion

2. **AC2: Similar KB Match Returns Verified Result**
   - **Given** an expert has verified a similar (but not exact) query
   - **When** a user searches with similar text (pg_trgm `similarity()` >= 0.85)
   - **Then** the system returns the verified HS code with high confidence (scaled by similarity score)
   - **And** response time is <100ms for the KB similarity lookup portion
   - **And** `source: "knowledge_base"` is set on the response

3. **AC3: AI Fallback When No KB Match**
   - **Given** no verified match exists in the knowledge base
   - **When** a user searches for a product description
   - **Then** the system falls back to the existing vector/fuzzy/LLM search pipeline
   - **And** results are marked with `source: "ai_suggestion"`

4. **AC4: Search Priority Order**
   - **Given** the search flow processes a query
   - **Then** the system checks in this order:
     1. Exact match in verified KB (by `query_hash`, <50ms)
     2. Similar match in verified KB (pg_trgm >= 0.85, <100ms)
     3. Fallback to existing search pipeline (vector + fuzzy + LLM, ~2-3s)
   - **And** the flow short-circuits on the first hit (no unnecessary downstream calls)

5. **AC5: Response Includes Source and Verification Metadata**
   - **Given** any search result is returned
   - **Then** the response includes fields: `source` ("knowledge_base" | "ai_suggestion"), `is_verified` (boolean), `verified_by` (string | null), `verified_at` (ISO datetime | null)
   - **And** these fields are present on ALL search responses (KB hits AND AI fallback)

6. **AC6: Lookup Records Still Created**
   - **Given** a search returns a KB hit
   - **When** the lookup record is created
   - **Then** `search_method` is set to `"knowledge_base"`
   - **And** KB hits are still deduplicated within the 24hr window (same as AI searches)

## Tasks / Subtasks

- [x] Task 1: Add KB Lookup Methods to LookupRecordRepository (AC: #1, #2)
  - [x] 1.1 Add `find_verified_exact(query_hash: str) -> LookupRecord | None` - finds verified record by exact query_hash match (is_verified=True, correct_hs_code_id IS NOT NULL)
  - [x] 1.2 Add `find_verified_similar(query_text: str, threshold: float = 0.85, limit: int = 1) -> list[LookupRecord]` - finds verified records by pg_trgm similarity on query_text, ordered by similarity DESC, filtered by threshold
  - [x] 1.3 Add tests for both methods in `lookup_record_repository_test.py`

- [x] Task 2: Create KnowledgeBaseService (AC: #1, #2, #4)
  - [x] 2.1 Create `api/app/services/knowledge_base_service.py` with class `KnowledgeBaseService`
  - [x] 2.2 Constructor takes `session: AsyncSession`
  - [x] 2.3 Implement `lookup(query: str) -> KBLookupResult | None` method:
    - Compute query_hash via `compute_query_hash(query)`
    - Step 1: Try `repo.find_verified_exact(query_hash)` - if found, return with confidence=100
    - Step 2: Try `repo.find_verified_similar(query, threshold=0.85)` - if found, return with confidence scaled by similarity
    - Step 3: Return None (triggers AI fallback in caller)
  - [x] 2.4 Define `KBLookupResult` dataclass: hs_code_id, confidence, similarity_score, lookup_record_id, verified_by_user_id, verified_at
  - [x] 2.5 Create co-located test file `knowledge_base_service_test.py`

- [x] Task 3: Add Source/Verification Fields to Search Response Schema (AC: #5)
  - [x] 3.1 Add `source: str` field to `SearchResponseData` schema (default: "ai_suggestion")
  - [x] 3.2 Add `is_verified: bool` field (default: False)
  - [x] 3.3 Add `verified_by: str | None` field (default: None)
  - [x] 3.4 Add `verified_at: str | None` field (default: None)

- [x] Task 4: Integrate KB Lookup into Search API (AC: #1, #2, #3, #4, #6)
  - [x] 4.1 In `api/app/api/search.py`, import and instantiate `KnowledgeBaseService`
  - [x] 4.2 Add KB lookup as FIRST step after request validation, BEFORE cache check
  - [x] 4.3 If KB hit: load full HS code object, generate classification via LLM (same as existing flow), set source="knowledge_base", set verification metadata, record lookup with search_method="knowledge_base", return response (short-circuit)
  - [x] 4.4 If KB miss: continue existing flow unchanged (cache check -> hybrid search -> etc.), set source="ai_suggestion" on response
  - [x] 4.5 Add process_log entries for KB lookup steps: "kb_exact_lookup" and "kb_similar_lookup" with timing
  - [x] 4.6 Update existing `_record_lookup()` calls to pass search_method="knowledge_base" for KB hits

- [x] Task 5: Write Integration Tests (AC: #1-6)
  - [x] 5.1 Test: KB exact match returns verified result with source="knowledge_base", confidence=100
  - [x] 5.2 Test: KB similar match returns verified result with scaled confidence
  - [x] 5.3 Test: No KB match falls back to AI search with source="ai_suggestion"
  - [x] 5.4 Test: Search priority order (exact KB > similar KB > AI fallback)
  - [x] 5.5 Test: Response always includes source and verification metadata fields
  - [x] 5.6 Test: KB hit still creates/deduplicates lookup_record with search_method="knowledge_base"

## Dev Notes

### Critical Architecture Patterns (MUST FOLLOW)

**Backend Layered Architecture:**
```
Request -> api/search.py (thin) -> knowledge_base_service.py (NEW - KB logic)
                                -> search_service.py (existing - AI fallback)
                                -> lookup_record_repository.py (data access)
                                -> search_repository.py (data access)
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
| Columns | snake_case | `query_hash`, `is_verified` |
| Python classes | PascalCase | `KnowledgeBaseService` |
| Python functions | snake_case | `find_verified_exact()` |
| Files | snake_case | `knowledge_base_service.py` |
| Tests | co-located with `_test.py` suffix | `knowledge_base_service_test.py` |

### Existing Code to Understand (READ THESE FIRST)

**`api/app/api/search.py`** - The main search endpoint. Current flow:
1. Validate request
2. Initialize services (SearchService, SearchCacheService, LLMReasoningService, QueryEnhancementService, RerankingService)
3. Check Redis cache → if hit, load HS code, generate LLM classification, record lookup, return
4. If cache miss → query enhancement → hybrid search → reranking → cache result → LLM classification → record lookup → return
5. Three integration points for `_record_lookup()`: cache hit path (~line 303), no results path (~line 371), found results path (~line 515)

**KB integration point:** Insert KB lookup AFTER request validation but BEFORE cache check. If KB hits, short-circuit the entire downstream flow.

**`api/app/repositories/lookup_record_repository.py`** - Existing methods:
- `create(record)` - Insert new record
- `find_by_query_hash(query_hash, within_hours=24)` - Dedup check (does NOT filter by is_verified)
- `get_unverified(limit, offset)` - List unverified records
- `count_unverified()` - Count unverified
- `update(record)` - Update record
- `touch_updated_at(record_id)` - Touch timestamp for dedup
- `compute_query_hash(query_text)` - SHA-256 of normalized text (standalone function)

**`api/app/services/search_service.py`** - SearchService class:
- `search(query, limit)` → calls `SearchRepository.hybrid_search()`
- `search_single(query)` → convenience wrapper
- `_calculate_confidence(result)` → 0-100 confidence from vector/fuzzy scores

**`api/app/repositories/search_repository.py`** - SearchRepository class:
- `hybrid_search(query, embedding, limit)` → exact match → vector search → fuzzy search → merge
- `search_exact_match(code)` → 8-digit code lookup
- `search_by_vector(embedding, limit)` → pgvector cosine similarity
- `search_by_fuzzy(query, limit)` → pg_trgm similarity on description_vn and description_en

**`api/app/schemas/search.py`** - Current response schema:
```python
class SearchResponseData(BaseModel):
    hs_code: str                          # Formatted "7418.20.00"
    description: str                      # Vietnamese description
    duty_rate: str                        # "5%"
    vat_rate: str                         # "10%"
    classification: ClassificationSchema  # Material + function analysis
    practical_notes: list[str]            # Import advice
    confidence: int                       # 0-100
    process_logs: list[ProcessLogEntry]   # Step-by-step logs
```
**ADD** to this schema: `source`, `is_verified`, `verified_by`, `verified_at`

### Database Schema (lookup_records - Already Exists)

```sql
lookup_records (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,              -- SHA-256 of normalized query
    query_language VARCHAR(5),                     -- 'vi', 'en', 'zh', NULL
    matched_hs_code_id INTEGER REFERENCES hs_codes(id),
    correct_hs_code_id INTEGER REFERENCES hs_codes(id),  -- Expert correction
    is_verified BOOLEAN DEFAULT false NOT NULL,
    verified_by_user_id INTEGER,                  -- No FK (users table doesn't exist yet)
    verified_at TIMESTAMP WITH TIME ZONE,
    confidence_score FLOAT,
    search_method VARCHAR(20) NOT NULL,            -- 'vector', 'exact', 'knowledge_base'
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

**Key KB query for exact match:**
```sql
SELECT * FROM lookup_records
WHERE query_hash = :hash AND is_verified = true AND correct_hs_code_id IS NOT NULL
LIMIT 1;
```

**Key KB query for similar match:**
```sql
SELECT *, similarity(query_text, :query) AS sim
FROM lookup_records
WHERE is_verified = true AND correct_hs_code_id IS NOT NULL
  AND similarity(query_text, :query) >= 0.85
ORDER BY sim DESC
LIMIT 1;
```

Both queries use existing indexes (`idx_lookup_records_query_hash` for exact, `idx_lookup_records_query_trgm` + `idx_lookup_records_verified` for similar).

### Implementation Strategy

**KnowledgeBaseService Pattern:**
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class KBLookupResult:
    hs_code_id: int
    confidence: int              # 0-100
    similarity_score: float      # 1.0 for exact, 0.85-1.0 for similar
    lookup_record_id: int
    verified_by_user_id: int | None
    verified_at: datetime | None
    match_type: str              # "exact" or "similar"

class KnowledgeBaseService:
    def __init__(self, session: AsyncSession):
        self.repo = LookupRecordRepository(session)

    async def lookup(self, query: str) -> KBLookupResult | None:
        query_hash = compute_query_hash(query)

        # Step 1: Exact hash match
        exact = await self.repo.find_verified_exact(query_hash)
        if exact:
            return KBLookupResult(
                hs_code_id=exact.correct_hs_code_id,
                confidence=100,
                similarity_score=1.0,
                lookup_record_id=exact.id,
                verified_by_user_id=exact.verified_by_user_id,
                verified_at=exact.verified_at,
                match_type="exact",
            )

        # Step 2: Similar text match
        similar = await self.repo.find_verified_similar(query, threshold=0.85)
        if similar:
            record, sim_score = similar[0]
            return KBLookupResult(
                hs_code_id=record.correct_hs_code_id,
                confidence=int(sim_score * 100),
                similarity_score=sim_score,
                lookup_record_id=record.id,
                verified_by_user_id=record.verified_by_user_id,
                verified_at=record.verified_at,
                match_type="similar",
            )

        return None
```

**Search API Integration Point (in search.py):**
```python
# AFTER: request validation
# BEFORE: cache check

# --- KB Lookup (NEW) ---
kb_service = KnowledgeBaseService(db)
kb_result = await kb_service.lookup(request.query)

if kb_result:
    # Short-circuit: load HS code, generate classification, return
    # Set source="knowledge_base", is_verified=True
    # Record lookup with search_method="knowledge_base"
    ...
    return success_response(data=response_data)

# --- Existing flow continues (cache check, hybrid search, etc.) ---
# Set source="ai_suggestion", is_verified=False on all responses
```

### Performance Considerations

- **Exact KB match:** Single btree index lookup on `query_hash` + filter `is_verified=true` → <5ms
- **Similar KB match:** GIN trigram index scan on `query_text` + filter `is_verified=true` → <50ms for typical table sizes
- **Short-circuit:** When KB hits, skip embedding generation (~500ms), vector search (~200ms), LLM calls (~2s) = massive latency savings
- **No new migrations needed:** All indexes already exist from Story 1-8

### Files to Create

| File | Purpose |
|------|---------|
| `api/app/services/knowledge_base_service.py` | KB lookup service with exact + similar match |
| `api/app/services/knowledge_base_service_test.py` | Co-located tests for KB service |

### Files to Modify

| File | Change |
|------|--------|
| `api/app/repositories/lookup_record_repository.py` | Add `find_verified_exact()` and `find_verified_similar()` methods |
| `api/app/repositories/lookup_record_repository_test.py` | Add tests for new repository methods |
| `api/app/schemas/search.py` | Add `source`, `is_verified`, `verified_by`, `verified_at` fields to SearchResponseData |
| `api/app/api/search.py` | Add KB lookup as first step before cache check, set source/verification fields on all responses |
| `api/app/api/search_test.py` | Add integration tests for KB hit/miss/fallback scenarios |

### Previous Story Intelligence (from Story 1-8)

**Key learnings from Story 1-8 implementation:**
- LookupRecord model uses `Mapped` + `mapped_column()` syntax (SQLAlchemy 2.0 style) - MUST continue this pattern
- Repository uses `AsyncSession` with `await self.session.flush()` for writes
- `compute_query_hash()` is a standalone function (not a method) - import from `lookup_record_repository`
- `_record_lookup()` in `search.py` is wrapped in try/except so failures never break search - maintain this pattern
- `_detect_query_language()` auto-detects vi/en/zh - already integrated
- Tests use `pytest` with `pytest-asyncio` for async tests
- Full test suite has some pre-existing failures (9 failed, 13 errors from DB connection issues) - do NOT count these as regressions
- The `verified_by_user_id` column has NO FK constraint (users table doesn't exist yet from Epic 2)

**Code review feedback from 1-8:** Added query_language detection, removed redundant index declarations, improved logging. Follow these standards.

### Git Intelligence (Recent Commits)

| Commit | Description | Relevance |
|--------|-------------|-----------|
| 19cae5d | feat: Implement knowledge base schema with lookup storage and query language detection | **Direct predecessor** - Story 1-8 |
| d803744 | feat: Implement model selection UI and LLM/query enhancement/reranking services | Search pipeline with LLM services |
| b68b958 | 1-4 done | Search UI with SearchBar component |
| 3d18b72 | 1-3 done | Search API with hybrid search |
| 471fa2d | 1-2 done | Database schema and data import |

**Patterns established:**
- Co-located tests with `_test.py` suffix
- Envelope response format consistent
- Async/await everywhere
- Services instantiated with session in route handlers
- Process logs tracked for transparency

### Anti-Patterns (NEVER DO)

- **NEVER** use synchronous SQLAlchemy (must be async with `AsyncSession`)
- **NEVER** put business logic in route handlers (use KnowledgeBaseService)
- **NEVER** create tests in a separate `/tests` directory (co-locate with `_test.py`)
- **NEVER** use the old `Column()` syntax (use `Mapped` + `mapped_column()`)
- **NEVER** skip the envelope response format
- **NEVER** block on KB lookup failure - wrap in try/except, fall back to AI search
- **NEVER** remove or modify existing `_record_lookup()` behavior - only ADD KB-specific path
- **NEVER** create new migrations for this story - all needed indexes exist from Story 1-8
- **NEVER** change the existing SearchService or SearchRepository - KB is a NEW layer on top
- **NEVER** return KB results without loading the full HS code object (need description, duty_rate, etc.)

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Backend | FastAPI | Latest | Python 3.12+, async |
| Database | PostgreSQL | 16 | With pgvector + pg_trgm |
| ORM | SQLAlchemy | 2.0 | Async mode, Mapped syntax |
| Cache | Redis | 7 | Sessions, search cache |
| Testing | pytest | Latest | With pytest-asyncio |
| Embeddings | OpenRouter API | text-embedding-3-large | 3072 dimensions (NOT needed for KB hits) |

### Project Structure Notes

- All new files follow existing patterns exactly
- No conflicts with current project structure
- KnowledgeBaseService sits alongside existing services in `api/app/services/`
- No new routes needed - modifying existing `POST /api/search` endpoint only
- No new Alembic migrations needed - all DB schema in place from Story 1-8

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.9]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-10.md]
- [Source: _bmad-output/planning-artifacts/architecture.md#Search-Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: _bmad-output/implementation-artifacts/1-8-knowledge-base-schema-lookup-storage.md]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- No blocking issues encountered during implementation.

### Completion Notes List

- **Task 1:** Added `find_verified_exact()` and `find_verified_similar()` to LookupRecordRepository. Exact match uses btree index on query_hash with is_verified and correct_hs_code_id filters. Similar match uses pg_trgm `similarity()` with GIN index. 7 new tests added. (20/20 pass)
- **Task 2:** Created KnowledgeBaseService with `lookup()` method implementing the 2-step priority: exact hash match (confidence=100) -> similar text match (confidence scaled by similarity). Returns KBLookupResult dataclass with verification metadata. 9 tests added. (9/9 pass)
- **Task 3:** Added `source`, `is_verified`, `verified_by`, `verified_at` fields to SearchResponseData schema. All have sensible defaults (ai_suggestion, False, None, None) so existing responses remain backward-compatible.
- **Task 4:** Integrated KB lookup as FIRST step in search.py, BEFORE cache check. KB hit short-circuits entire AI pipeline (skips embedding, vector search, LLM calls). KB miss falls back to existing flow unchanged. All responses now include source/verification metadata. KB failures wrapped in try/except to never break search. Process logs added for kb_exact_lookup/kb_similar_lookup steps.
- **Task 5:** 6 integration tests covering all ACs: exact KB match, similar KB match, AI fallback, priority order verification, response field presence, and lookup record creation with search_method="knowledge_base". (30/30 pass)
- **Full regression:** 59/59 tests pass across all test files.

### File List

**New files:**
- `api/app/services/knowledge_base_service.py` - KnowledgeBaseService with KB lookup logic
- `api/app/services/knowledge_base_service_test.py` - Co-located tests for KB service (9 tests)

**Modified files:**
- `api/app/repositories/lookup_record_repository.py` - Added find_verified_exact() and find_verified_similar() methods
- `api/app/repositories/lookup_record_repository_test.py` - Added 7 tests for new repository methods
- `api/app/schemas/search.py` - Added source, is_verified, verified_by, verified_at fields to SearchResponseData
- `api/app/api/search.py` - Integrated KB lookup as first step, clean up imports
- `api/app/api/search_test.py` - Added 6 integration tests for KB search flow (TestKBSearchIntegration)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Updated sprint tracking

### Change Log

- 2026-02-10: Implemented Story 1-9 Knowledge-Enhanced Search. KB becomes primary search mechanism with expert-verified results returned first (exact hash match -> pg_trgm similar match). AI pipeline serves as fallback only. All responses now include source and verification metadata.
- 2026-02-10: Fixed inconsistent imports in search.py and updated documentation file lists.
