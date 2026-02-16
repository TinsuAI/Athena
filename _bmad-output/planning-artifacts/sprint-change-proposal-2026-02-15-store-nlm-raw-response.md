# Sprint Change Proposal — Store Full NotebookLM Response

**Date:** 2026-02-15
**Author:** tinsu (facilitated by PM agent)
**Triggered by:** Epic 3 (NotebookLM AI Search) — post-implementation review
**Scope:** Minor — 1 new story, backend + frontend
**Status:** Approved (2026-02-15)

---

## Section 1: Issue Summary

After completing Epic 3 (Stories 3-1 and 3-2), the full NotebookLM response text (`raw_answer`) is not persisted to the database. The service correctly queries NotebookLM and parses the response to extract HS codes, classification reasoning, and practical notes — but the original markdown response from Gemini 3 is discarded after the search completes.

**Problem:** Users cannot review exactly what NotebookLM responded to each query. Only parsed/extracted snippets are stored in `classification_data` and `practical_notes` JSONB columns. The full response context is lost.

**Discovery:** Post-implementation review of Epic 3 data persistence.

**Evidence:**
- `api/app/api/search.py:422` — stores `nlm_classification` (parsed dict), not `raw_answer`
- `api/app/models/lookup_record.py` — no column for raw response storage
- `web/src/app/lookups/[id]/page.tsx` — only shows `classification_data.material` and `.function`, no way to see full NLM response
- `NotebookLMResult.raw_answer` is available at query time but never persisted

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Impact | Details |
|------|--------|---------|
| Epic 3: NotebookLM AI Search | **Add Story 3-3** | New story for raw response persistence + UI display |
| All other epics | None | No cross-epic impact |

### Story Impact

- **New Story 3-3:** Store and display full NotebookLM response
- Stories 3-1 and 3-2 remain done — no modifications to existing logic needed

### Artifact Conflicts

- **PRD:** No conflict — aligns with FR63 (auto-store in KB)
- **Architecture:** No conflict — follows JSONB/TEXT column pattern from Story 1-11
- **UI/UX:** Minor addition — new collapsible section on lookup detail page

### Technical Impact

| File | Change Type | Description |
|------|-------------|-------------|
| `api/alembic/versions/` | New | Migration adding `nlm_raw_response` TEXT column |
| `api/app/models/lookup_record.py` | Modified | Add `nlm_raw_response` field |
| `api/app/api/search.py` | Modified | Update `_record_lookup()` + 2 NLM call sites |
| `api/app/schemas/lookup.py` or `lookup_record.py` | Modified | Add field to response schema |
| `web/src/types/lookup.ts` | Modified | Add `nlm_raw_response` to type |
| `web/src/app/lookups/[id]/page.tsx` | Modified | Add collapsible raw response section |

---

## Section 3: Recommended Approach

**Path:** Direct Adjustment — add Story 3-3 within Epic 3.

**Rationale:**
- Low effort (single story, ~7 tasks)
- Zero risk (nullable column, backward-compatible)
- No timeline impact
- Follows established patterns from Story 1-11 (column addition to `lookup_records`)

| Metric | Assessment |
|--------|-----------|
| Effort | Low |
| Risk | Low |
| Timeline impact | None |

---

## Section 4: Detailed Change Proposals

### 4.1 Database Migration

**File:** `api/alembic/versions/YYYYMMDD_add_nlm_raw_response_to_lookup_records.py`

```sql
ALTER TABLE lookup_records ADD COLUMN nlm_raw_response TEXT;
```

Nullable TEXT column — existing rows unaffected.

### 4.2 SQLAlchemy Model Update

**File:** `api/app/models/lookup_record.py`

```python
# NEW field:
nlm_raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### 4.3 Search Pipeline — Persist Raw Response

**File:** `api/app/api/search.py`

Update `_record_lookup()` signature:
```
OLD: _record_lookup(db, query, matched_hs_code_id, confidence_score, search_method,
                    classification_data, practical_notes, process_logs)
NEW: _record_lookup(db, query, matched_hs_code_id, confidence_score, search_method,
                    classification_data, practical_notes, process_logs, nlm_raw_response)
```

Update 2 NLM call sites to pass `nlm_raw_response=nlm_result.raw_answer`:
1. **NLM success path** (~line 416): Pass `nlm_raw_response=nlm_result.raw_answer`
2. **NLM guide path** (~line 468): Pass `nlm_raw_response=nlm_result.raw_answer`

Non-NLM call sites pass `nlm_raw_response=None` (default).

### 4.4 Lookup API Response Schema

**File:** `api/app/schemas/lookup.py` (or `lookup_record.py`)

```python
# NEW field:
nlm_raw_response: str | None = None
```

### 4.5 Lookup API Endpoint

**File:** `api/app/api/lookups.py`

Ensure `nlm_raw_response` is included in the detail response. Should work automatically if schema and model are updated.

### 4.6 Frontend Type Definition

**File:** `web/src/types/lookup.ts`

```typescript
// NEW field:
nlm_raw_response: string | null;
```

### 4.7 Frontend Lookup Detail Page

**File:** `web/src/app/lookups/[id]/page.tsx`

Add collapsible "Phản hồi NotebookLM" section after "Phân tích phân loại" (Classification Reasoning), visible when `lookup.nlm_raw_response` is present. Renders the full markdown response as preformatted text with proper whitespace handling.

---

## Section 5: Implementation Handoff

### Scope Classification: Minor

Direct implementation by development team. No backlog reorganization or architectural changes needed.

### New Story: 3-3 — Store and Display Full NotebookLM Response

**Tasks:**
1. Create Alembic migration adding `nlm_raw_response` TEXT column to `lookup_records`
2. Update `LookupRecord` SQLAlchemy model with new field
3. Update `_record_lookup()` helper to accept and store `nlm_raw_response`
4. Update 2 NLM call sites in `search.py` to pass `nlm_result.raw_answer`
5. Update lookup response schema to include `nlm_raw_response`
6. Update frontend `LookupDetail` type with new field
7. Add collapsible "Phản hồi NotebookLM" section to lookup detail page
8. Write backend tests (migration, persistence, round-trip)

### Success Criteria

- Every NotebookLM-sourced lookup stores the full `raw_answer` in `nlm_raw_response`
- Lookup detail page displays the full NLM response in a readable, collapsible section
- Existing lookups unaffected (column is nullable)
- Non-NLM lookups show no raw response section (field is null)
- All existing tests pass without regression

### Handoff

| Role | Responsibility |
|------|---------------|
| Developer | Implement Story 3-3 (all tasks) |
| Developer | Run migration on dev environment |

---

## Approval

- [x] User approves Sprint Change Proposal (2026-02-15)
- [x] Story 3-3 created and added to sprint status
- [x] Epic 3 sprint-status updated with new story
