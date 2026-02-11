# Story 1.11: Persist Full Lookup Details

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **every search to persist classification reasoning, practical notes, and process logs alongside the lookup record**,
So that **lookup history and detail pages can display the full search analysis without re-running LLM calls**.

## Background

Stories 1-8 through 1-10 built the knowledge base with lookup records, but only basic metadata is stored (query, matched code, confidence, method). The rich LLM-generated content — classification reasoning (material/function), practical notes, and process logs — is generated at search time and discarded after the response. This story persists that data so Stories 1-12 and 1-13 can display full lookup history without repeating expensive LLM calls.

**Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-10-lookup-history.md`

**Dependencies:** Story 1-8 (done), Story 1-9 (review), Story 1-10 (done)

## Acceptance Criteria

1. **AC1: Migration Adds JSONB Columns**
   - **Given** the `lookup_records` table exists (from Story 1-8)
   - **When** I run the Alembic migration
   - **Then** three new nullable columns are added:
     - `classification_data` (JSONB) — stores `{"material": "...", "function": "..."}`
     - `practical_notes` (JSONB) — stores `["note1", "note2", ...]`
     - `process_logs` (JSONB) — stores `[{"step": "...", "status": "...", "message": "...", "duration_ms": 123, "details": {...}}]`
   - **And** existing data is not affected (columns are nullable)

2. **AC2: Search Persists Classification Data**
   - **Given** a user performs a search via POST /api/search
   - **When** results are returned with classification analysis
   - **Then** the lookup_record is created with `classification_data` containing material and function reasoning from `ClassificationAnalyzer`
   - **And** `practical_notes` contains the list of practical import notes
   - **And** `process_logs` contains the full list of `ProcessLogEntry` objects serialized as JSON

3. **AC3: Dedup Updates Overwrite with Fresh Data**
   - **Given** an existing lookup_record is deduplicated (same query within 24h)
   - **When** the search completes with new LLM output
   - **Then** the existing record's `classification_data`, `practical_notes`, and `process_logs` are updated with the latest values
   - **And** `updated_at` is refreshed

4. **AC4: Data Round-Trips Correctly**
   - **Given** a lookup_record has stored JSONB data
   - **When** I query it from the database
   - **Then** I can retrieve `classification_data` as a Python dict with "material" and "function" keys
   - **And** I can retrieve `practical_notes` as a Python list of strings
   - **And** I can retrieve `process_logs` as a Python list of dicts with step/status/message/duration_ms/details keys

5. **AC5: No-Results Path Handles Missing Data**
   - **Given** a search returns no results
   - **When** the lookup_record is created
   - **Then** `classification_data`, `practical_notes`, and `process_logs` are stored as None (no analysis available)

6. **AC6: KB Path Persists Data**
   - **Given** a search hits the knowledge base (exact or similar match)
   - **When** the lookup_record is created
   - **Then** `classification_data` and `practical_notes` from the ClassificationAnalyzer are persisted
   - **And** `process_logs` containing KB lookup steps are persisted

## Tasks / Subtasks

- [x] Task 1: Create Alembic Migration (AC: #1)
  - [x] 1.1 Create new migration in `api/alembic/versions/` adding 3 JSONB columns to `lookup_records`
  - [x] 1.2 Use `op.add_column('lookup_records', sa.Column('classification_data', JSONB, nullable=True))`
  - [x] 1.3 Same pattern for `practical_notes` and `process_logs`
  - [x] 1.4 Downgrade should `op.drop_column` all three

- [x] Task 2: Update LookupRecord Model (AC: #1, #4)
  - [x] 2.1 Add `classification_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)` to `api/app/models/lookup_record.py`
  - [x] 2.2 Add `practical_notes: Mapped[list | None] = mapped_column(JSONB, nullable=True)`
  - [x] 2.3 Add `process_logs: Mapped[list | None] = mapped_column(JSONB, nullable=True)`
  - [x] 2.4 Import `JSONB` from `sqlalchemy.dialects.postgresql`

- [x] Task 3: Update `_record_lookup()` Signature and Implementation (AC: #2, #3, #5, #6)
  - [x] 3.1 Add parameters: `classification_data: dict | None = None`, `practical_notes: list[str] | None = None`, `process_logs: list[dict] | None = None`
  - [x] 3.2 On new record creation: set these fields on the LookupRecord instance
  - [x] 3.3 On dedup (existing record found): update `classification_data`, `practical_notes`, `process_logs` on the existing record, then flush via `repo.update()`
  - [x] 3.4 Ensure the try/except wrapper doesn't swallow errors silently (log them)

- [x] Task 4: Update All Call Sites of `_record_lookup()` (AC: #2, #5, #6)
  - [x] 4.1 **KB path** (~line 313): Pass `classification_data={"material": analysis.material, "function": analysis.function}`, `practical_notes=analysis.practical_notes`, `process_logs=[log.model_dump() for log in process_logs]`
  - [x] 4.2 **Cache path** (~line 415): Same pattern as KB path
  - [x] 4.3 **AI path** (~line 636): Same pattern as KB path
  - [x] 4.4 **No-results path** (~line 488): Pass `classification_data=None`, `practical_notes=None`, `process_logs=[log.model_dump() for log in process_logs]` (process logs exist even on failure)

- [x] Task 5: Write Tests (AC: #1-6)
  - [x] 5.1 Test: LookupRecord with JSONB fields can be created and read back (round-trip) — `test_create_record_with_jsonb_fields`, `test_create_record_with_none_jsonb_fields`
  - [x] 5.2 Test: `_record_lookup()` stores classification_data, practical_notes, process_logs on new record — `test_stores_classification_data_on_new_record`
  - [x] 5.3 Test: `_record_lookup()` updates JSONB fields on dedup (existing record within 24h) — `test_dedup_updates_jsonb_fields`
  - [x] 5.4 Test: `_record_lookup()` handles None values for no-results path — `test_no_results_stores_none_classification`
  - [x] 5.5 Test: JSONB data preserves structure (nested dicts, lists of strings, lists of dicts) — `test_jsonb_preserves_nested_structure`
  - [x] 5.6 Verify no regressions: 197 tests pass (64/64 in modified files), 14 pre-existing failures unrelated to this story

## Dev Notes

### Critical Architecture Patterns (MUST FOLLOW)

**Backend Layered Architecture:**
```
Request -> api/search.py (thin) -> _record_lookup() helper
                                -> lookup_record_repository.py (data access)
                                -> classification_analyzer.py (analysis generation)
```

**API Response Format - ALL responses MUST use envelope format:**
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

**SQLAlchemy 2.0 Syntax (MANDATORY):**
```python
# Use Mapped + mapped_column syntax (NOT old Column() syntax)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

classification_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
```

**Naming Conventions:**
| Element | Convention | Example |
|---------|------------|---------|
| Columns | snake_case | `classification_data`, `practical_notes`, `process_logs` |
| Python classes | PascalCase | `LookupRecord`, `ProcessLogEntry` |
| Python functions | snake_case | `_record_lookup()` |
| Tests | co-located with `_test.py` suffix | `lookup_record_repository_test.py` |

### Existing Code to Understand (READ THESE FIRST)

**`api/app/models/lookup_record.py`** (~73 lines) - LookupRecord model:
- Uses `Mapped` + `mapped_column()` syntax (SQLAlchemy 2.0)
- Current columns: id, query_text, query_hash, query_language, matched_hs_code_id, correct_hs_code_id, is_verified, verified_by_user_id, verified_at, confidence_score, search_method, notes, created_at, updated_at
- FK relationships to `hs_codes` for both `matched_hs_code_id` and `correct_hs_code_id`
- **ADD 3 new JSONB columns here**

**`api/app/api/search.py`** (~640 lines) - Main search endpoint:
- `_record_lookup()` helper (lines ~82-128): Creates/deduplicates lookup records. Currently takes only basic params: query, matched_hs_code_id, confidence_score, search_method. Returns `int | None` (lookup record ID).
- **4 call sites** for `_record_lookup()`:
  1. KB path (~line 303): Has `analysis` (ClassificationAnalysis) and `process_logs` available
  2. Cache path (~line 402): Has `analysis` and `process_logs` available
  3. No-results path (~line 472): No analysis, but `process_logs` available
  4. AI path (~line 617): Has `analysis` and `process_logs` available
- Process logs tracked via `ProcessLogEntry` Pydantic model, accumulated in `process_logs: list[ProcessLogEntry]` starting at line ~169
- `ClassificationAnalyzer.analyze_async()` returns `ClassificationAnalysis(material, function, practical_notes)`

**`api/app/repositories/lookup_record_repository.py`** (~164 lines) - Existing methods:
- `create(record)` - Insert new record, flush, return
- `find_by_query_hash(query_hash, within_hours=24)` - Dedup check
- `touch_updated_at(record_id)` - Currently called on dedup (just updates timestamp)
- `update(record)` - Flushes session changes
- **On dedup**: Currently `_record_lookup()` calls `touch_updated_at()` only. MUST be changed to update JSONB fields too.

**`api/app/schemas/search.py`** - Defines the data structures being persisted:
- `ProcessLogEntry`: step, status, message, duration_ms (int|None), details (dict|None)
- `ClassificationSchema`: material (str), function (str)
- `SearchResponseData`: classification, practical_notes, process_logs (all returned in response but NOT saved)

**`api/app/services/classification_analyzer.py`** - Generates the data:
- `ClassificationAnalysis` dataclass: material (str), function (str), practical_notes (list[str])
- `analyze_async()` returns this dataclass
- Called at 3 points: KB path, cache path, AI path

### JSONB Data Structures (Exact Shapes to Persist)

**classification_data column:**
```json
{
  "material": "San pham duoc lam bang dong (bao gom ca hop kim dong nhu dong thau - brass)...",
  "function": "Thanh treo khan la mot thiet bi/phu kien dung trong nha tam..."
}
```

**practical_notes column:**
```json
[
  "Hang moi 100%: San pham la hang moi nen du dieu kien nhap khau.",
  "Chinh sach thue: Muc thue nhap khau MFN cho ma nay kha cao (30%)."
]
```

**process_logs column:**
```json
[
  {
    "step": "init",
    "status": "completed",
    "message": "Search initialized",
    "duration_ms": 1,
    "details": {"query_language": "vi"}
  },
  {
    "step": "kb_exact_lookup",
    "status": "completed",
    "message": "Knowledge base exact match found",
    "duration_ms": 12,
    "details": {"match_type": "exact", "confidence": 100}
  }
]
```

### Dedup Update Logic (Critical Detail)

Currently in `_record_lookup()`, when a duplicate is found (same query_hash within 24h):
```python
# CURRENT behavior: just touches updated_at
await repo.touch_updated_at(existing.id)
return existing.id
```

**REQUIRED behavior after this story:**
```python
# NEW behavior: update JSONB fields with fresh data
existing.classification_data = classification_data
existing.practical_notes = practical_notes
existing.process_logs = process_logs
await repo.update(existing)
return existing.id
```

This ensures that when a query is re-searched within 24 hours, the latest LLM analysis replaces any stale data.

### ProcessLogEntry Serialization

`ProcessLogEntry` is a Pydantic model. To store in JSONB:
```python
# Convert list[ProcessLogEntry] -> list[dict] for JSONB storage
process_logs_data = [log.model_dump() for log in process_logs] if process_logs else None
```

### Migration Details

**New migration file:** `api/alembic/versions/YYYYMMDD_add_jsonb_columns_to_lookup_records.py`

```python
# Use JSONB (not JSON) for PostgreSQL indexing support
from sqlalchemy.dialects.postgresql import JSONB

def upgrade():
    op.add_column('lookup_records', sa.Column('classification_data', JSONB, nullable=True))
    op.add_column('lookup_records', sa.Column('practical_notes', JSONB, nullable=True))
    op.add_column('lookup_records', sa.Column('process_logs', JSONB, nullable=True))

def downgrade():
    op.drop_column('lookup_records', 'process_logs')
    op.drop_column('lookup_records', 'practical_notes')
    op.drop_column('lookup_records', 'classification_data')
```

**Note:** Use `JSONB` from `sqlalchemy.dialects.postgresql` in migration, but `JSON` from `sqlalchemy` in the model (SQLAlchemy maps JSON to JSONB on PostgreSQL automatically). Alternatively, use `JSONB` in both for explicitness.

### Database Schema After Migration

```sql
lookup_records (
    -- Existing columns (from Story 1-8):
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    -- NEW columns (this story):
    classification_data JSONB,          -- {"material": "...", "function": "..."}
    practical_notes JSONB,              -- ["note1", "note2", ...]
    process_logs JSONB                  -- [{step, status, message, duration_ms, details}, ...]
);
```

### Previous Story Intelligence (from Stories 1-8, 1-9, 1-10)

**Key learnings from Story 1-8:**
- LookupRecord uses `Mapped` + `mapped_column()` syntax (SQLAlchemy 2.0) — continue this
- Repository uses `AsyncSession` with `await self.session.flush()` for writes
- `compute_query_hash()` is a standalone function in `lookup_record_repository.py`
- `_record_lookup()` in search.py is wrapped in try/except so failures never break search
- `_detect_query_language()` auto-detects vi/en/zh

**Key learnings from Story 1-9:**
- KB lookup is FIRST step in search.py, BEFORE cache check
- KB hit short-circuits entire AI pipeline
- Process logs added for kb_exact_lookup/kb_similar_lookup steps

**Key learnings from Story 1-10:**
- `_record_lookup()` was modified to return `int | None` (lookup_id)
- Added `lookup_id` field to `SearchResponseData` schema
- 164 tests pass as regression baseline
- Redis pipeline mock: `AsyncMock` makes `pipeline()` async when it should be sync — use `MagicMock` for pipeline() returning `MagicMock` context manager with `AsyncMock` __aenter__/__aexit__
- Added `apply_correction()` to LookupRecordRepository — this does NOT need modification for this story

### Git Intelligence (Recent Commits)

| Commit | Description | Relevance |
|--------|-------------|-----------|
| a0fb771 | feat: Localize correction UI to Vietnamese | 1-10 follow-up |
| 7845869 | refactor: update redis client type hint | 1-10 follow-up |
| 150c5ea | 1-10 done | Direct predecessor |
| 8434045 | 1-9 done | KB-enhanced search |
| 19cae5d | feat: Implement knowledge base schema with lookup storage | Story 1-8 |

**Patterns established in recent work:**
- Co-located tests with `_test.py` suffix
- Envelope response format on all responses
- Async/await everywhere
- Services instantiated with session in route handlers
- Process logs for transparency
- Try/except wrapping for non-critical operations (lookup recording)

### Implementation Strategy

**Order of implementation (recommended):**
1. Task 1 (migration) — database schema change first
2. Task 2 (model update) — align SQLAlchemy model with new schema
3. Task 3 (`_record_lookup()` update) — core logic change
4. Task 4 (call site updates) — wire data through to storage
5. Task 5 (tests) — verify everything works, no regressions

**This is a backend-only story.** No frontend changes required. Stories 1-12 and 1-13 will consume this persisted data via new API endpoints.

### Anti-Patterns (NEVER DO)

- **NEVER** use old `Column()` syntax — use `Mapped` + `mapped_column()` (SQLAlchemy 2.0)
- **NEVER** put business logic in route handlers — keep `_record_lookup()` as a helper, repository for data access
- **NEVER** use synchronous SQLAlchemy — must be async with `AsyncSession`
- **NEVER** create tests in a separate `/tests` directory — co-locate with `_test.py`
- **NEVER** skip the envelope response format for any new endpoints
- **NEVER** block search response on JSONB storage failure — keep try/except wrapper
- **NEVER** use `JSON` type without checking it maps to JSONB on PostgreSQL (it does, but verify)
- **NEVER** modify the `apply_correction()` method — it handles different fields (correct_hs_code_id, is_verified, verified_at)
- **NEVER** add indexes on JSONB columns unless specifically needed (not needed for this story — data is read by record ID)

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Backend | FastAPI | Latest | Python 3.12+, async |
| Database | PostgreSQL | 16 | With pgvector + pg_trgm + JSONB |
| ORM | SQLAlchemy | 2.0 | Async mode, Mapped syntax |
| Migrations | Alembic | Latest | Autogenerate or manual |
| Testing | pytest | Latest | With pytest-asyncio, asyncio_mode="auto" |

### Project Structure Notes

- All changes are in `api/` directory only — no frontend changes
- Migration in `api/alembic/versions/`
- Model in `api/app/models/lookup_record.py`
- Search API in `api/app/api/search.py`
- Tests co-located with source files
- No conflicts with current project structure
- Follows existing patterns established in Stories 1-8, 1-9, 1-10

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.11]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-10-lookup-history.md]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns]
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- [Source: _bmad-output/implementation-artifacts/1-10-expert-review-correction-interface.md]
- [Source: api/app/api/search.py - _record_lookup helper, lines 82-128]
- [Source: api/app/api/search.py - KB call site ~line 303, cache ~line 402, no-results ~line 472, AI ~line 617]
- [Source: api/app/models/lookup_record.py - LookupRecord model]
- [Source: api/app/repositories/lookup_record_repository.py - touch_updated_at, update methods]
- [Source: api/app/schemas/search.py - ProcessLogEntry, ClassificationSchema, SearchResponseData]
- [Source: api/app/services/classification_analyzer.py - ClassificationAnalysis dataclass]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Updated existing dedup test `test_deduplicates_within_24h_window` to reflect new behavior (calls `repo.update()` instead of `repo.touch_updated_at()`)

### Completion Notes List

- Task 1: Created migration `20260210_add_jsonb_columns_to_lookup_records.py` adding 3 nullable JSONB columns (classification_data, practical_notes, process_logs) to lookup_records table
- Task 2: Updated LookupRecord model with 3 new `Mapped` + `mapped_column(JSONB)` fields using SQLAlchemy 2.0 syntax
- Task 3: Updated `_record_lookup()` with 3 new optional params; dedup path now calls `repo.update(existing)` to persist fresh JSONB data instead of just `touch_updated_at()`
- Task 4: Updated all 4 call sites (KB, cache, AI, no-results) to pass classification_data, practical_notes, and serialized process_logs
- Task 5: Added 8 new tests (5 in search_test.py, 3 in lookup_record_repository_test.py) — all pass. 197/228 total tests pass; 14 pre-existing failures are unrelated to this story
- **Code Review Fixes:** Fixed type safety violations in model (added proper type parameters: `dict[str, str]`, `list[str]`, `list[dict[str, Any]]`), updated File List to include sprint-status.yaml

### Change Log

- 2026-02-10: Implemented Story 1-11 — Persist full lookup details (classification_data, practical_notes, process_logs as JSONB columns on lookup_records)

### File List

- `api/alembic/versions/20260210_add_jsonb_columns_to_lookup_records.py` (new) — Migration adding 3 JSONB columns
- `api/app/models/lookup_record.py` (modified) — Added classification_data, practical_notes, process_logs fields with proper type hints
- `api/app/api/search.py` (modified) — Updated _record_lookup() signature and all 4 call sites
- `api/app/api/search_test.py` (modified) — Added TestRecordLookupJSONBPersistence (5 tests), updated existing dedup test
- `api/app/repositories/lookup_record_repository_test.py` (modified) — Added 3 JSONB round-trip tests
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified) — Updated story status to 'review'
