# Story 3.2: Integrate NotebookLM into Search Pipeline

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want **my searches to be classified by NotebookLM (Gemini 3) using the official tariff document**,
So that **I get accurate HS code classifications grounded in the actual Vietnam 2026 tariff schedule**.

## Background

Story 3-1 created `NotebookLMService` with `query()`, response parsing (regex HS code extraction), Redis caching, and error handling. This story integrates that service into the existing search pipeline so that NotebookLM becomes the primary AI classification engine for queries not found in the knowledge base.

**Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-15.md`

**Dependencies:** Story 3-1 (NotebookLM service) must be complete (done).

**FRs covered:** FR62 (NotebookLM query), FR63 (auto-store in KB), FR64 (fallback to vector search)

## Acceptance Criteria

1. **AC1: NotebookLM Success — Full Pipeline**
   - **Given** no KB match exists for a query
   - **When** I search for "Thanh treo khăn bằng đồng mạ chrome"
   - **Then** NotebookLM is queried with the tariff notebook
   - **And** the HS code from the response is looked up in the local database for structured rates
   - **And** classification reasoning from NotebookLM is included in the response
   - **And** the result is stored in the knowledge base (`is_verified=false`)
   - **And** the result is cached in Redis (24h TTL) via the NLM service
   - **And** `source="notebooklm"` in the response

2. **AC2: Redis Cache Hit — Cached NLM Response**
   - **Given** a previous NotebookLM query is cached in Redis
   - **When** I search with the same query within 24 hours
   - **Then** the cached response is returned immediately
   - **And** `source="cache"` in the response
   - **And** no NotebookLM API call is made

3. **AC3: Fallback — NotebookLM Unavailable**
   - **Given** NotebookLM is unavailable (rate limit, timeout, service down)
   - **When** I search for a product description
   - **Then** the system falls back to vector/fuzzy search (existing pipeline)
   - **And** `process_logs` include "NotebookLM unavailable, falling back to vector search"
   - **And** `source="ai_suggestion"` (same as current behavior)

4. **AC4: Categorized Guide — No Single HS Code**
   - **Given** NotebookLM returns a categorized guide (no single HS code)
   - **When** the result is processed
   - **Then** the system returns the guidance text as classification reasoning
   - **And** confidence is set to 0 (indicating manual classification needed)
   - **And** the guidance is stored in the lookup record for reference
   - **And** `source="notebooklm"` in the response

5. **AC5: HS Code Not in Database**
   - **Given** NotebookLM returns an HS code that doesn't exist in our local database
   - **When** the result is processed
   - **Then** the system treats it as a guide (no valid match)
   - **And** falls back to vector/fuzzy search
   - **And** `process_logs` include "NLM HS code not found in database, falling back"

6. **AC6: NotebookLM Disabled**
   - **Given** `NOTEBOOKLM_ENABLED=false` in configuration
   - **When** I search for a product description
   - **Then** the NotebookLM step is skipped entirely
   - **And** the system proceeds directly to vector/fuzzy search
   - **And** `process_logs` include "NotebookLM disabled, skipping"

## Tasks / Subtasks

- [x] Task 1: Add `from_cache` flag to `NotebookLMResult` (AC: #2)
  - [x] 1.1 Add `from_cache: bool = False` field to `NotebookLMResult` dataclass in `notebooklm_service.py`
  - [x] 1.2 Set `from_cache=True` when returning cached result from `_get_from_cache()`
  - [x] 1.3 Update existing tests to account for new field (ensure serialization round-trip still works)

- [x] Task 2: Integrate NotebookLM into search route handler (AC: #1, #2, #3, #4, #5, #6)
  - [x] 2.1 In `api/app/api/search.py`, add NotebookLM step between KB lookup and existing AI fallback
  - [x] 2.2 Instantiate `NotebookLMService(redis_client=redis_client)` alongside other services
  - [x] 2.3 After KB miss, call `notebooklm_service.query(body.query)`
  - [x] 2.4 On NLM success with valid HS code:
    - Normalize code format `XXXX.XX.XX` → `XXXXXXXX` (remove dots)
    - Look up HS code in local DB with `selectinload` for fta_rates and hierarchy
    - If found: build response using NLM classification + DB structured data
    - If NOT found: log and fall through to vector/fuzzy search
  - [x] 2.5 On NLM success without HS code (categorized guide):
    - Return guidance as classification with confidence=0
    - Use NLM raw_answer as description, practical_notes from NLM
  - [x] 2.6 On NLM failure (`NotebookLMUnavailableError`):
    - Log the failure reason in process_logs
    - Fall through to existing vector/fuzzy search pipeline
  - [x] 2.7 On NLM disabled (returns `None`):
    - Log "NotebookLM disabled" in process_logs
    - Fall through to existing vector/fuzzy search pipeline
  - [x] 2.8 Set `source="notebooklm"` for fresh NLM results, `source="cache"` for cached NLM results

- [x] Task 3: Auto-store NLM results in knowledge base (AC: #1)
  - [x] 3.1 After successful NLM result, call existing `_record_lookup()` helper with `search_method="notebooklm"`
  - [x] 3.2 Store NLM `classification` and `practical_notes` in the lookup record JSONB fields
  - [x] 3.3 Store NLM process log entries in the lookup record `process_logs` field

- [x] Task 4: Update `SearchResponseData` schema (AC: #1, #2)
  - [x] 4.1 Add `"notebooklm"` and `"cache"` as valid `source` values in the `SearchResponseData` field description

- [x] Task 5: Write tests (AC: #1-#6)
  - [x] 5.1 Create/update `api/app/api/search_test.py` or add NLM integration tests
  - [x] 5.2 Test: NLM success → DB lookup → response with `source="notebooklm"`
  - [x] 5.3 Test: NLM cache hit → response with `source="cache"`
  - [x] 5.4 Test: NLM unavailable → fallback to vector search, process_logs has fallback entry
  - [x] 5.5 Test: NLM returns guide (no HS code) → confidence=0, guidance text
  - [x] 5.6 Test: NLM returns HS code not in DB → falls back to vector search
  - [x] 5.7 Test: NLM disabled → skipped, proceeds to vector search
  - [x] 5.8 Test: `from_cache` flag on `NotebookLMResult` serialization round-trip
  - [x] 5.9 Update any existing search tests that mock the full pipeline to account for the new NLM step

## Dev Notes

### Critical Architecture Patterns (MUST FOLLOW)

**CRITICAL: The search orchestration is in the ROUTE HANDLER, not search_service.py.**

The current pipeline orchestration lives in `api/app/api/search.py` (`search_hs_codes` function), lines 160-668. The `SearchService` in `api/app/services/search_service.py` only handles embedding generation + hybrid DB search. All higher-level orchestration (KB lookup, caching, enhancement, reranking, classification, lookup recording) is in the route handler.

```
CURRENT PIPELINE (in api/app/api/search.py):
1. KB exact hash match          ← KnowledgeBaseService.lookup()
2. KB similar text match        ← (same call, step 2 inside KB service)
   └─ If KB hit → return with source="knowledge_base"
3. Search cache check           ← SearchCacheService.get()
   └─ If cache hit → return with source="ai_suggestion"
4. Query enhancement (optional) ← QueryEnhancementService
5. Vector/fuzzy search          ← SearchService.search()
6. LLM reranking (optional)     ← RerankingService
7. Classification analysis      ← ClassificationAnalyzer
8. Record lookup                ← _record_lookup()

NEW PIPELINE (insert between step 2 and step 3):
1. KB exact/similar match       ← unchanged
   └─ If KB hit → return with source="knowledge_base"
2. *** NotebookLM query ***     ← NEW — NotebookLMService.query()
   └─ If NLM success + HS code in DB → return with source="notebooklm" or "cache"
   └─ If NLM success + no HS code (guide) → return guidance with confidence=0
   └─ If NLM HS code not in DB → fall through
   └─ If NLM unavailable → fall through
   └─ If NLM disabled → fall through
3. Search cache check           ← unchanged (fallback path)
4-8. Rest of pipeline           ← unchanged (fallback path)
```

### Existing Code to Reference (READ THESE FIRST)

**1. `api/app/api/search.py`** — THE main file to modify. The entire search orchestration is here.
- Lines 160-668: `search_hs_codes()` route handler
- Lines 82-138: `_record_lookup()` helper — reuse this for NLM results
- Lines 44-48: `_format_hs_code()` — formats `XXXXXXXX` → `XXXX.XX.XX`
- Lines 242-334: KB lookup block — insert NotebookLM step AFTER this block
- Lines 336-428: Existing search cache check — this becomes the fallback path
- The `add_log()` helper is used for process logging (same pattern for NLM steps)
- The `process_logs` list accumulates all steps for transparency

**2. `api/app/services/notebooklm_service.py`** — NotebookLM service from Story 3-1.
- `NotebookLMService(redis_client)` — constructor takes Redis client
- `query(query_text) → NotebookLMResult | None` — returns None if disabled
- `NotebookLMResult.hs_code` — format is `"7418.20.00"` (with dots), needs `.replace(".", "")` for DB lookup
- `NotebookLMResult.classification` — dict with `reasoning`, `material`, `function` keys
- `NotebookLMResult.practical_notes` — list of strings
- `NotebookLMResult.raw_answer` — full markdown text
- `NotebookLMUnavailableError.reason` — `"timeout"`, `"rate_limit"`, `"auth_error"`, `"service_down"`
- **Redis caching is INTERNAL** — the service handles cache check/store transparently

**3. `api/app/services/knowledge_base_service.py`** — KB lookup pattern.

**4. `api/app/schemas/search.py`** — `SearchResponseData` schema with `source` field.

**5. `api/app/models/lookup_record.py`** — LookupRecord model with JSONB columns.

### Implementation Guide — NotebookLM Integration Block

Insert the following block in `api/app/api/search.py` AFTER the KB lookup try/except block (after line ~334) and BEFORE the existing "AI Fallback" search cache check (line ~336):

```python
# --- NotebookLM AI Search (NEW - primary AI path) ---
from app.services.notebooklm_service import (
    NotebookLMService,
    NotebookLMResult,
    NotebookLMUnavailableError,
)

nlm_service = NotebookLMService(redis_client=redis_client)

try:
    nlm_start = time.time()
    add_log("notebooklm", "started", "Querying NotebookLM for classification...")
    nlm_result = await nlm_service.query(body.query)
    nlm_duration = int((time.time() - nlm_start) * 1000)

    if nlm_result is None:
        # Service is disabled
        add_log("notebooklm", "skipped", "NotebookLM disabled, skipping", duration_ms=nlm_duration)
    elif nlm_result.hs_code:
        # NLM returned an HS code — look up in local DB
        nlm_code_raw = nlm_result.hs_code.replace(".", "")
        add_log("notebooklm", "completed",
                f"NotebookLM returned HS code {nlm_result.hs_code}",
                duration_ms=nlm_duration)

        # DB lookup for structured data
        db_start = time.time()
        add_log("notebooklm_db_lookup", "started", f"Looking up {nlm_code_raw} in database...")
        hs_result = await db.execute(
            select(HSCode)
            .where(HSCode.code == nlm_code_raw)
            .options(
                selectinload(HSCode.fta_rates),
                selectinload(HSCode.subheading)
                .selectinload(HSSubheading.heading)
                .selectinload(HSHeading.chapter),
            )
        )
        hs_code_obj = hs_result.scalar_one_or_none()
        db_duration = int((time.time() - db_start) * 1000)

        if hs_code_obj:
            add_log("notebooklm_db_lookup", "completed",
                    f"HS code {nlm_code_raw} found in database",
                    duration_ms=db_duration)

            # Determine source based on cache hit
            source = "cache" if nlm_result.from_cache else "notebooklm"

            # Build classification from NLM data
            nlm_classification = nlm_result.classification or {}
            classification = ClassificationSchema(
                material=nlm_classification.get("material", ""),
                function=nlm_classification.get("function", ""),
            )

            total_duration = int((time.time() - start_time) * 1000)
            add_log("complete", "completed",
                    f"Search completed (from {source}): {_format_hs_code(hs_code_obj.code)}",
                    duration_ms=total_duration)

            response_data = SearchResponseData(
                hs_code=_format_hs_code(hs_code_obj.code),
                description=hs_code_obj.description_vn,
                duty_rate=_format_rate(float(hs_code_obj.duty_rate)),
                vat_rate=_format_rate(float(hs_code_obj.vat_rate)),
                classification=classification,
                practical_notes=nlm_result.practical_notes,
                confidence=95,  # High confidence for NLM-grounded results
                process_logs=process_logs,
                source=source,
                is_verified=False,
            )

            # Record lookup for knowledge base
            lookup_id = await _record_lookup(
                db=db,
                query=body.query,
                matched_hs_code_id=hs_code_obj.id,
                confidence_score=95,
                search_method="notebooklm",
                classification_data=nlm_classification,
                practical_notes=nlm_result.practical_notes,
                process_logs=[log.model_dump() for log in process_logs],
            )
            response_data.lookup_id = lookup_id

            return success_response(response_data.model_dump())
        else:
            add_log("notebooklm_db_lookup", "failed",
                    f"NLM HS code {nlm_code_raw} not found in database, falling back",
                    duration_ms=db_duration)
    else:
        # NLM returned a categorized guide (no single HS code)
        add_log("notebooklm", "completed",
                "NotebookLM returned categorized guide (no single HS code)",
                duration_ms=nlm_duration)

        source = "cache" if nlm_result.from_cache else "notebooklm"

        classification = ClassificationSchema(
            material=nlm_result.raw_answer[:500],
            function="Categorized guide — manual classification recommended",
        )

        total_duration = int((time.time() - start_time) * 1000)
        add_log("complete", "completed",
                f"Search completed (from {source}): categorized guide",
                duration_ms=total_duration)

        response_data = SearchResponseData(
            hs_code="0000.00.00",
            description=nlm_result.raw_answer[:200],
            duty_rate="N/A",
            vat_rate="N/A",
            classification=classification,
            practical_notes=nlm_result.practical_notes,
            confidence=0,
            process_logs=process_logs,
            source=source,
            is_verified=False,
        )

        # Record the guide in KB for reference
        lookup_id = await _record_lookup(
            db=db,
            query=body.query,
            matched_hs_code_id=None,
            confidence_score=0,
            search_method="notebooklm",
            classification_data={"guide": nlm_result.raw_answer},
            practical_notes=nlm_result.practical_notes,
            process_logs=[log.model_dump() for log in process_logs],
        )
        response_data.lookup_id = lookup_id

        return success_response(response_data.model_dump())

except NotebookLMUnavailableError as e:
    nlm_duration = int((time.time() - nlm_start) * 1000) if 'nlm_start' in locals() else 0
    add_log("notebooklm", "failed",
            f"NotebookLM unavailable ({e.reason}), falling back to vector search",
            duration_ms=nlm_duration,
            details={"reason": e.reason})
    logger.warning("NotebookLM unavailable, falling back", extra={"reason": e.reason})
except Exception as e:
    nlm_duration = int((time.time() - nlm_start) * 1000) if 'nlm_start' in locals() else 0
    add_log("notebooklm", "failed",
            f"NotebookLM error: {str(e)}, falling back to vector search",
            duration_ms=nlm_duration)
    logger.warning("NotebookLM error, falling back", extra={"error": str(e)}, exc_info=True)

# --- Fallback: Existing AI search flow (vector/fuzzy) ---
# (existing code continues unchanged from here)
```

### HS Code Format Conversion (CRITICAL)

**NotebookLM returns:** `"7418.20.00"` (with dots, `XXXX.XX.XX` format)
**Database stores:** `"74182000"` (no dots, 8-digit format)
**API response displays:** `"7418.20.00"` (with dots)

**Conversion:** `nlm_result.hs_code.replace(".", "")` for DB lookup, then `_format_hs_code()` for display.

### `from_cache` Flag Addition (Task 1)

Add to `NotebookLMResult` in `api/app/services/notebooklm_service.py`:

```python
@dataclass
class NotebookLMResult:
    hs_code: str | None
    classification: dict | None
    practical_notes: list[str]
    raw_answer: str
    from_cache: bool = False  # NEW: True when result came from Redis cache
```

In `_get_from_cache()`, set `from_cache=True`:
```python
async def _get_from_cache(self, query_text: str) -> NotebookLMResult | None:
    # ... existing code ...
    if cached:
        data = json.loads(cached)
        result = NotebookLMResult(**data)
        result.from_cache = True  # Mark as cached
        return result
```

**NOTE:** The `from_cache` field must NOT be serialized to Redis (it's a runtime flag, not cached data). The `asdict()` call in `_save_to_cache` will include it, but since it defaults to `False` in `__init__`, deserializing from cache will also default to `False` — then we explicitly set it `True` on cache hit. This is safe because:
1. `_save_to_cache` stores `from_cache=False` (which is the default, harmless)
2. `_get_from_cache` overwrites to `from_cache=True` after deserialization

### Confidence Score Strategy

| Source | Confidence | Rationale |
|--------|-----------|-----------|
| Knowledge base (verified) | 100 or pg_trgm score | Expert-verified, highest trust |
| NotebookLM (fresh or cached) | 95 | AI-grounded in official tariff PDF, very high accuracy |
| NotebookLM guide (no HS code) | 0 | Ambiguous query, manual classification needed |
| Vector/fuzzy search (fallback) | 0-99 (calculated) | Existing weighted scoring |

### Source Field Values

| Value | Meaning |
|-------|---------|
| `"knowledge_base"` | Expert-verified KB match (existing) |
| `"notebooklm"` | Fresh NotebookLM AI classification (NEW) |
| `"cache"` | Cached NotebookLM result from Redis (NEW) |
| `"ai_suggestion"` | Vector/fuzzy search fallback (existing) |

### Import Additions for `api/app/api/search.py`

Add these imports at the top of the file:
```python
from app.services.notebooklm_service import (
    NotebookLMService,
    NotebookLMUnavailableError,
)
```

### Testing Requirements

**Co-locate tests:** Update or create `api/app/api/search_test.py` and `api/app/services/notebooklm_service_test.py`

**Mock the NotebookLM service — do NOT call real NotebookLM:**

```python
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.notebooklm_service import NotebookLMResult, NotebookLMUnavailableError

# Mock for NLM success with HS code
mock_nlm_result = NotebookLMResult(
    hs_code="7418.20.00",
    classification={"reasoning": "...", "material": "copper", "function": "bathroom fitting"},
    practical_notes=["Use EVFTA for 3.7% rate"],
    raw_answer="Full markdown response...",
    from_cache=False,
)

# Mock for NLM cache hit
mock_nlm_cached = NotebookLMResult(
    hs_code="7418.20.00",
    classification={"reasoning": "...", "material": "copper", "function": "bathroom fitting"},
    practical_notes=["Use EVFTA for 3.7% rate"],
    raw_answer="Full markdown response...",
    from_cache=True,
)

# Mock for NLM guide (no HS code)
mock_nlm_guide = NotebookLMResult(
    hs_code=None,
    classification=None,
    practical_notes=[],
    raw_answer="Categorized guide text...",
    from_cache=False,
)
```

**Test scenarios:**

| Test | Scenario | Expected |
|------|----------|----------|
| `test_nlm_success_hs_code_found` | NLM returns HS code in DB | Response with `source="notebooklm"`, confidence=95 |
| `test_nlm_cache_hit` | NLM returns cached result | Response with `source="cache"`, confidence=95 |
| `test_nlm_unavailable_fallback` | NLM raises `NotebookLMUnavailableError` | Falls back to vector search, process_logs has fallback entry |
| `test_nlm_guide_no_hs_code` | NLM returns guide (no HS code) | Response with confidence=0, guidance text |
| `test_nlm_hs_code_not_in_db` | NLM returns code not in DB | Falls back to vector search |
| `test_nlm_disabled` | `NOTEBOOKLM_ENABLED=false` | NLM step skipped, proceeds to vector search |
| `test_nlm_auto_stores_in_kb` | NLM success | `_record_lookup` called with `search_method="notebooklm"` |
| `test_from_cache_flag_serialization` | `NotebookLMResult` with `from_cache` | Serializes/deserializes correctly |

### Anti-Patterns (NEVER DO)

- **NEVER** create a new route handler/endpoint for this — modify the existing `search_hs_codes` function
- **NEVER** move orchestration to `search_service.py` — keep it in the route handler where it currently lives
- **NEVER** skip the DB lookup after NLM returns an HS code — always verify the code exists locally
- **NEVER** cache errors from NotebookLM — only cache successful results (this is handled by NLM service)
- **NEVER** re-implement Redis caching for NLM — the `NotebookLMService` already handles it internally
- **NEVER** generate a new embedding for NLM results — NLM classification is text-based, not vector-based
- **NEVER** call `ClassificationAnalyzer.analyze_async()` for NLM results — NLM already provides classification reasoning
- **NEVER** put tests in a separate `/tests` directory — co-locate at `api/app/api/search_test.py`
- **NEVER** use `source="ai_suggestion"` for NLM results — use `"notebooklm"` or `"cache"`
- **NEVER** skip recording the lookup in the knowledge base — this is how the system self-improves

### Project Structure Notes

**Files to MODIFY:**
```
api/app/api/search.py                                # Add NotebookLM integration block
api/app/services/notebooklm_service.py                # Add from_cache field to NotebookLMResult
api/app/services/notebooklm_service_test.py           # Update tests for from_cache field
api/app/schemas/search.py                             # Update source field description
```

**Files to CREATE:**
```
(none — all changes go into existing files)
```

**Files that MUST NOT be modified:**
```
api/app/services/search_service.py      — NOT the orchestration point
api/app/services/knowledge_base_service.py — Unchanged
api/app/repositories/**                  — No repository changes
api/app/models/**                        — No model changes
web/**                                   — No frontend changes (same API response shape)
```

### Previous Story (3-1) Intelligence

**Learnings from Story 3-1 implementation:**
- `NotebookLMClient` is lazily imported inside `_call_sdk` via `_get_client_class()` — tests must mock `_get_client_class()` not the module-level import
- 24 tests were written covering all edge cases
- Redis caching uses `nlm:{md5(query.lower().strip())}` key pattern with JSON serialization
- `from_cache` field was NOT in the original implementation — this story adds it
- Code review found 1 high + 5 medium issues in story 3-1 and fixed them all

**Git intelligence from recent commits:**
```
da6fdfc feat: implement NotebookLM service and response parser (story 3-1)
3a3ccc0 feat: Add NotebookLM AI Search epic, renumber existing epics
```
Files created in 3-1: `notebooklm_service.py`, `notebooklm_service_test.py`
Files modified in 3-1: `config.py`, `requirements.txt`, `docker-compose.dev.yml`

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Backend | FastAPI | Latest | Python 3.12+ |
| NotebookLM | notebooklm-mcp-cli | >=0.3.0 | Already installed in Story 3-1 |
| Cache | Redis | 7 | NLM caching handled by NLM service internally |
| Database | PostgreSQL 16 | + pgvector | HS code lookup for NLM results |
| Testing | pytest | >=8.0 | asyncio_mode="auto", unittest.mock |
| ORM | SQLAlchemy 2.0 | async | For HS code DB lookup |

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-15.md — Full technical context]
- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.2 — Story requirements and ACs]
- [Source: _bmad-output/planning-artifacts/architecture.md#NotebookLM-Integration — Architecture decisions]
- [Source: _bmad-output/project-context.md — Implementation rules]
- [Source: api/app/api/search.py — Current search pipeline orchestration (lines 160-668)]
- [Source: api/app/services/notebooklm_service.py — NotebookLM service from Story 3-1]
- [Source: api/app/services/knowledge_base_service.py — KB lookup pattern]
- [Source: api/app/schemas/search.py — SearchResponseData schema]
- [Source: api/app/models/lookup_record.py — LookupRecord model with JSONB]
- [Source: api/app/repositories/lookup_record_repository.py — Lookup record data access]
- [Source: _bmad-output/implementation-artifacts/3-1-notebooklm-service-response-parser.md — Previous story learnings]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- No blocking issues encountered during implementation.

### Completion Notes List

- **Task 1:** Added `from_cache: bool = False` field to `NotebookLMResult` dataclass. Set `from_cache=True` in `_get_from_cache()` after deserialization. Updated 3 existing tests and added 1 new test for serialization round-trip. 25 NLM service tests pass (24+1 skipped).
- **Task 2:** Integrated NotebookLM into `search_hs_codes()` route handler between KB lookup and AI fallback. Handles 4 outcomes: NLM success with HS code in DB (source="notebooklm"), NLM cached (source="cache"), NLM guide/no HS code (confidence=0), NLM HS code not in DB (fallback). All errors caught with graceful fallback to vector/fuzzy search.
- **Task 3:** NLM results auto-stored in knowledge base via existing `_record_lookup()` helper with `search_method="notebooklm"`. Classification data, practical notes, and process logs persisted in JSONB fields.
- **Task 4:** Updated `SearchResponseData.source` field description to include `"notebooklm"` and `"cache"` as valid values.
- **Task 5:** Added 7 new integration tests in `TestNotebookLMIntegration` class covering all 6 ACs plus auto-KB-storage. Updated 3 existing NLM service tests for `from_cache` flag. Total: 42 search tests pass, 25 NLM service tests pass. No regressions.

### Change Log

- 2026-02-15: Integrated NotebookLM into search pipeline (Story 3-2). Added `from_cache` flag to `NotebookLMResult`, inserted NLM query step between KB lookup and vector search fallback in `search_hs_codes()`, auto-stores NLM results in knowledge base, updated schema source field, added 8 new tests.

### File List

**Modified:**
- `api/app/services/notebooklm_service.py` — Added `from_cache: bool = False` field to `NotebookLMResult`, set `from_cache=True` in `_get_from_cache()`
- `api/app/services/notebooklm_service_test.py` — Updated cache hit test to assert `from_cache=True`, added `test_from_cache_flag_serialization_round_trip`, updated fresh query test to assert `from_cache=False`
- `api/app/api/search.py` — Added NotebookLM import, inserted ~120 lines of NLM integration block between KB lookup and AI fallback
- `api/app/api/search_test.py` — Added `TestNotebookLMIntegration` class with 7 tests covering AC1-AC6 + auto-KB-storage
- `api/app/schemas/search.py` — Updated `source` field description to include `"notebooklm"` and `"cache"`
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Status: `ready-for-dev` → `in-progress` → `review`
- `_bmad-output/implementation-artifacts/3-2-integrate-notebooklm-into-search-pipeline.md` — Story file updated
