# Sprint Change Proposal - Lookup History & Detail Pages

**Date:** 2026-02-10
**Author:** tinsu
**Status:** Approved
**Change Scope:** Minor
**Triggered By:** Stories 1-8, 1-9, 1-10 (Knowledge Base implementation)

---

## Section 1: Issue Summary

### Problem Statement

After implementing the knowledge base system (Stories 1-8, 1-9, 1-10), the search pipeline generates rich lookup data per search — classification reasoning (material/function analysis), practical import notes, and detailed process logs — but this data is **not persisted**. The `lookup_records` table only stores basic metadata (query, matched code, confidence, method).

Additionally, there is **no UI to browse past lookups** or review individual lookup details. Users can only see results at search time, with no way to revisit past analyses or review the growing knowledge base.

### Context

- Discovered during implementation of Stories 1-8 through 1-10 (2026-02-10)
- The `LookupRecord` model stores: query_text, query_hash, query_language, matched/correct HS code IDs, confidence, search_method, verification status
- The `SearchResponseData` returns (but doesn't persist): classification (material + function), practical_notes, process_logs
- The only lookup API is `GET /api/corrections/lookups` which returns **only unverified** records
- No frontend pages exist for lookup browsing or detail viewing

### Evidence

- `api/app/models/lookup_record.py`: No columns for classification_data, practical_notes, or process_logs
- `api/app/api/search.py`: `_record_lookup()` only stores query, matched_hs_code_id, confidence_score, search_method — discards LLM output
- `api/app/schemas/search.py`: `SearchResponseData` includes classification, practical_notes, process_logs but these are ephemeral

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Impact | Details |
|------|--------|---------|
| **Epic 1: Core HS Code Search** | Direct | Add 3 new stories (1-11, 1-12, 1-13). Total stories: 14. Epic remains in-progress. |
| **Epic 2: Auth & Sessions** | None | No impact |
| **Epic 3: Favorites & History** | Indirect | FR25-29 (search_history) is user-scoped and simple. Lookup history is system-wide and richer. No conflict — they serve different purposes. |
| **Epic 4: Advanced Search** | None | No impact |
| **Epic 5: Admin Data Management** | None | No impact |

### Story Impact

**New stories required:**

| Story | Description | Effort |
|-------|-------------|--------|
| **1-11: Persist Full Lookup Details** | Migration + update search API to store classification_data, practical_notes, process_logs as JSONB | Low |
| **1-12: Lookup History API & List Page** | GET /api/lookups endpoint + /lookups frontend page | Medium |
| **1-13: Lookup Detail Page** | GET /api/lookups/{id} + /lookups/[id] frontend page with correction | Medium |

**Existing stories requiring updates:** None — existing stories are unaffected. The new stories build on existing infrastructure.

### Artifact Conflicts

| Artifact | Conflict | Action Needed |
|----------|----------|---------------|
| **PRD** | No conflict | Add FR51-FR53 for lookup persistence and history |
| **Architecture** | No conflict | Add API endpoints, DB columns, frontend pages |
| **UX Design** | No conflict | New pages follow existing "Professional Efficiency" design |
| **Epics** | No conflict | Add 3 stories to Epic 1, update description |
| **Sprint Status** | No conflict | Add 3 new story entries, update totalStories |

### Technical Impact

- **Database:** Alembic migration to add 3 JSONB columns to `lookup_records`
- **Backend:** Update `_record_lookup()` signature and call sites. New `GET /api/lookups` and `GET /api/lookups/{id}` endpoints.
- **Frontend:** 2 new pages (`/lookups`, `/lookups/[id]`). Reuse existing CorrectionButton/CorrectionPanel components.
- **Infrastructure:** No changes needed
- **Deployment:** Standard migration + deploy cycle

---

## Section 3: Recommended Approach

### Selected Path: Direct Adjustment

Add 3 new stories to Epic 1 within the existing plan. No rollback, no MVP scope change.

### Rationale

- The data layer (`lookup_records` table) already exists — just needs 3 new columns
- The search API already generates the data — just needs to pass it to `_record_lookup()`
- Frontend correction components (CorrectionButton, CorrectionPanel) already exist — reusable on the detail page
- All changes follow existing architectural patterns (layered backend, envelope responses, co-located tests)
- Low risk, low effort, high value for knowledge base visibility

### Effort Estimate

| Story | Backend | Frontend | Total |
|-------|---------|----------|-------|
| 1-11 | Low | None | Low |
| 1-12 | Low | Medium | Medium |
| 1-13 | Low | Medium | Medium |

### Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| JSONB columns increase row size | Low | Classification + notes are small (<5KB per record) |
| Process logs contain verbose data | Low | Optional column, can be pruned or TTL'd later |
| New pages need responsive design | Low | Follow existing patterns from search page |

### Timeline Impact

Minimal. These stories can run in sequence after 1-10 and should take 2-3 story cycles total.

---

## Section 4: Detailed Change Proposals

### 4.1 Story Changes

#### Story 1-11: Persist Full Lookup Details (NEW)

As a **developer**,
I want **every search to persist classification reasoning, practical notes, and process logs alongside the lookup record**,
So that **lookup history and detail pages can display the full search analysis without re-running LLM calls**.

**Background:**
Stories 1-8 through 1-10 built the knowledge base with lookup records, but only basic metadata is stored (query, matched code, confidence, method). The rich LLM-generated content — classification reasoning (material/function), practical notes, and process logs — is generated at search time and discarded after the response. This story persists that data for later retrieval.

**Acceptance Criteria:**

**Given** the `lookup_records` table
**When** I run the migration
**Then** three new columns are added:
- `classification_data` (JSONB, nullable) — stores `{"material": "...", "function": "..."}`
- `practical_notes` (JSONB, nullable) — stores `["note1", "note2", ...]`
- `process_logs` (JSONB, nullable) — stores `[{"step": "...", "status": "...", "message": "...", "duration_ms": 123, "details": {...}}]`

**Given** a user performs a search via POST /api/search
**When** results are returned with classification analysis
**Then** the lookup_record is created/updated with classification_data, practical_notes, and process_logs

**Given** an existing lookup_record is deduplicated (same query within 24h)
**When** the search completes
**Then** the existing record's classification_data, practical_notes, and process_logs are updated with the latest values

**Given** a lookup_record has stored data
**When** I query it from the database
**Then** I can retrieve the full classification reasoning, practical notes, and process logs as structured JSON

**Technical Tasks:**
1. Add JSONB columns to `lookup_records` via Alembic migration
2. Update `LookupRecord` SQLAlchemy model with new mapped columns (JSON type)
3. Update `_record_lookup()` in `api/app/api/search.py` to accept and store classification_data, practical_notes, process_logs
4. Update all call sites of `_record_lookup()` (KB path, cache path, AI path, no-results path) to pass the new data
5. Write tests for data persistence and dedup update

**Definition of Done:**
- [ ] Migration adds 3 JSONB columns to lookup_records
- [ ] Every search persists classification_data, practical_notes, process_logs
- [ ] Dedup updates overwrite previous LLM output with fresh data
- [ ] Tests verify data round-trips correctly

**Dependency:** Stories 1-8, 1-9, 1-10 must be complete.

---

#### Story 1-12: Lookup History API & List Page (NEW)

As a **user**,
I want **to view a paginated list of all past lookups**,
So that **I can browse search history, see which queries have been verified, and navigate to individual lookup details**.

**Acceptance Criteria:**

**Given** lookup records exist in the database
**When** I call GET /api/lookups?limit=20&offset=0
**Then** I receive a paginated list of lookup records ordered by created_at DESC
**And** each item includes: id, query_text, query_language, matched_hs_code (code + description_vn), confidence_score, search_method, is_verified, created_at
**And** response follows envelope format `{success, data, error}`

**Given** I want to filter lookups
**When** I call GET /api/lookups?verified=true
**Then** only verified (corrected) lookups are returned
**When** I call GET /api/lookups?verified=false
**Then** only unverified lookups are returned

**Given** I navigate to /lookups in the frontend
**When** the page loads
**Then** I see a table/list of lookup records with columns: Query, Matched Code, Confidence, Status (verified/unverified badge), Date
**And** each row is clickable to navigate to /lookups/[id]
**And** I see pagination controls
**And** I see a filter toggle for verified/unverified/all

**Given** there are no lookup records
**When** I view the /lookups page
**Then** I see an empty state: "No lookups yet. Search for HS codes to start building history."

**Technical Tasks:**
1. Add `get_all_with_hs_codes(limit, offset, verified_filter)` method to `LookupRecordRepository`
2. Add `count_all(verified_filter)` method to `LookupRecordRepository`
3. Create API router: `api/app/api/lookups.py` with GET /api/lookups endpoint
4. Create response schema in `api/app/schemas/lookup.py`
5. Register router in `api/app/main.py`
6. Build frontend page: `web/src/app/lookups/page.tsx`
7. Build LookupList component: `web/src/app/lookups/components/LookupList.tsx`
8. Add /lookups to sidebar/header navigation

**Definition of Done:**
- [ ] GET /api/lookups returns paginated results with HS code details
- [ ] Filtering by verified status works
- [ ] Frontend /lookups page displays lookup list with all columns
- [ ] Pagination works correctly
- [ ] Rows navigate to /lookups/[id] on click
- [ ] Empty state displays correctly
- [ ] Navigation link added to sidebar/header

**Dependency:** Story 1-11 must be complete.

---

#### Story 1-13: Lookup Detail Page (NEW)

As a **user**,
I want **to view the full details of a past lookup including classification reasoning, practical notes, and process logs**,
So that **I can review the search analysis and submit corrections if the result was wrong**.

**Acceptance Criteria:**

**Given** a lookup record exists with persisted data
**When** I call GET /api/lookups/{id}
**Then** I receive the full lookup record including:
- query_text, query_language, created_at
- matched HS code with code, description_vn, description_en, duty_rate, vat_rate
- correct HS code (if corrected) with same fields
- classification_data (material + function reasoning)
- practical_notes (list of strings)
- process_logs (list of step objects)
- is_verified, verified_at, notes
- confidence_score, search_method

**Given** I navigate to /lookups/[id] in the frontend
**When** the page loads
**Then** I see the full lookup detail with sections:
- **Query**: original search text with language badge
- **Matched Result**: HS code, description, duty/VAT rates, confidence badge
- **Classification Reasoning**: material and function analysis (rendered as readable text)
- **Practical Notes**: list of import notes
- **Process Log**: collapsible timeline of search steps with durations
- **Correction**: status badge (verified/unverified) and correction button

**Given** I am viewing an unverified lookup
**When** I click "Suggest Correction"
**Then** the CorrectionPanel opens (reuse existing component from search page)
**And** I can submit a correction that immediately verifies the lookup

**Given** I am viewing a verified (corrected) lookup
**When** I see the correction section
**Then** I see the correct HS code with description, verification date, and correction notes
**And** the "Suggest Correction" button is disabled with tooltip "Already corrected"

**Given** a lookup record does not exist
**When** I call GET /api/lookups/99999
**Then** I receive a 404 error following RFC 7807 format

**Technical Tasks:**
1. Add `find_by_id_with_details()` to `LookupRecordRepository` (eager load matched + correct HS codes with fta_rates)
2. Add GET /api/lookups/{id} endpoint to `api/app/api/lookups.py`
3. Create detail response schema with all fields including classification, notes, logs
4. Build frontend page: `web/src/app/lookups/[id]/page.tsx`
5. Build LookupDetail component with tabbed/sectioned layout
6. Build ProcessLogTimeline component for visualizing search steps with durations
7. Reuse CorrectionButton and CorrectionPanel from `web/src/app/search/components/`
8. Add breadcrumb navigation (Lookups > Lookup #123)

**Definition of Done:**
- [ ] GET /api/lookups/{id} returns full detail with classification, notes, logs
- [ ] 404 returned for missing lookup (RFC 7807)
- [ ] Frontend /lookups/[id] displays all sections
- [ ] Classification reasoning renders material + function analysis
- [ ] Practical notes render as formatted list
- [ ] Process logs render as collapsible timeline with durations
- [ ] Correction flow works for unverified lookups (reuses existing components)
- [ ] Verified lookups show correction details
- [ ] Navigation from /lookups list to detail works
- [ ] Breadcrumb navigation works

**Dependency:** Stories 1-11, 1-12 must be complete.

---

### 4.2 PRD Changes

**Section:** 9. Functional Requirements (after FR50)

**Add:**

#### Lookup History & Details

- **FR51:** The system persists classification reasoning, practical notes, and process logs for every search lookup
- **FR52:** Users can view a paginated list of all past lookups with matched HS code, confidence, and verification status
- **FR53:** Users can view full details of any past lookup including classification reasoning, practical notes, process logs, and submit corrections

**FR Coverage Map additions:**

| FR | Epic | Description |
|----|------|-------------|
| FR51 | Epic 1 | Persist full lookup details |
| FR52 | Epic 1 | View lookup history list |
| FR53 | Epic 1 | View lookup details and correct |

---

### 4.3 Architecture Changes

**API Endpoints — add:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/lookups` | GET | List all lookups (paginated, filterable by verified) |
| `/api/lookups/{id}` | GET | Full lookup detail with classification, notes, logs |

**Database Schema — update `lookup_records`:**

```sql
-- Add to existing lookup_records table
classification_data JSONB,   -- {"material": "...", "function": "..."}
practical_notes JSONB,       -- ["note1", "note2", ...]
process_logs JSONB           -- [{step, status, message, duration_ms, details}, ...]
```

**Frontend Structure — add:**

```
web/src/app/
├── lookups/
│   ├── page.tsx                    # Lookup history list
│   ├── components/
│   │   └── LookupList.tsx
│   └── [id]/
│       ├── page.tsx                # Lookup detail view
│       └── components/
│           ├── LookupDetail.tsx
│           └── ProcessLogTimeline.tsx
```

**Backend Structure — add:**

```
api/app/
├── api/
│   └── lookups.py                  # Lookup endpoints
├── schemas/
│   └── lookup.py                   # Lookup response schemas
```

---

### 4.4 Sprint Status Changes

**Update `sprint-status.yaml`:**

- `totalStories: 31` → `totalStories: 34`
- Add under epic-1:
  - `1-11-persist-full-lookup-details: backlog`
  - `1-12-lookup-history-api-list-page: backlog`
  - `1-13-lookup-detail-page: backlog`

**Update Epic 1 FRs covered:** Add FR51, FR52, FR53

---

## Section 5: Implementation Handoff

### Change Scope Classification: Minor

This change can be implemented directly by the development team. No backlog reorganization or strategic replan needed.

### Handoff

| Recipient | Responsibility |
|-----------|---------------|
| **Development team** | Implement stories 1-11 → 1-12 → 1-13 in sequence |

### Implementation Sequence

1. **Story 1-11** (backend only): Migration + update search API to persist data
2. **Story 1-12** (full-stack): New API endpoint + frontend list page
3. **Story 1-13** (full-stack): New API endpoint + frontend detail page with correction

### Success Criteria

- [ ] All past lookups browsable via /lookups page
- [ ] Individual lookup details viewable with full classification reasoning
- [ ] Corrections submittable from the detail page
- [ ] Process logs visible as timeline for debugging/transparency
- [ ] All new endpoints follow envelope response format and RFC 7807 errors
- [ ] Tests written for all new backend code
