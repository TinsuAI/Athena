# Sprint Change Proposal — Customs Data Ingestion

**Date:** 2026-02-24
**Author:** tinsu
**Status:** Approved
**Change Scope:** Minor-Moderate (New Epic, no rework)

---

## Section 1: Issue Summary

### Problem Statement

Athena's knowledge base currently grows through two slow, one-at-a-time channels:

1. **NotebookLM auto-storage** — each novel search query triggers a NotebookLM call, and the result is stored in the KB. Rate-limited to ~50 queries/day on free tier.
2. **Expert corrections** — individual corrections submitted by users and approved by experts.

The user has acquired **3 customs-approved import/export reports** from Vietnamese companies containing thousands of official product-to-HS code mappings verified by Vietnamese Customs in 2025. There is no mechanism to ingest this bulk data into the knowledge base, nor to support ongoing ingestion of similar reports from additional companies.

### Context

- **Discovery:** User obtained real-world customs data files from 3 companies
- **Data location:** `docs/baocaohangchitiet/`
- **Files:**
  | # | File | Company | Size | Format |
  |---|------|---------|------|--------|
  | 1 | `bchangchitiet-1-dothanh.xls` | Do Thanh | 1.6 MB | XLS |
  | 2 | `bchangchitiet-2-growatt.xls` | Growatt Vietnam | 31 MB | XLS |
  | 3 | `bchangchitiet-3-kde.xlsx` | KDE | 4.1 MB | XLSX |
- **Data volume:** ~25,000+ product lines across all 3 files (Growatt alone has ~19,898)
- **Data quality:** Customs-approved = ground-truth classifications, highest possible confidence

### Evidence

- The knowledge base likely has dozens to low hundreds of records from organic searches
- Bulk import would represent a **100x+ increase** in verified KB content
- KB lookup is the #1 priority in the search pipeline (checked before NotebookLM)
- More KB entries = fewer NotebookLM calls = lower rate limit pressure
- More KB entries = faster searches (<50ms KB lookup vs 5-15s NotebookLM)

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Impact | Details |
|------|--------|---------|
| Epic 1 (Core Search) | **Positive** | KB service automatically serves better results — no changes needed |
| Epic 2 (Tariff Browser) | None | Different data domain |
| Epic 3 (NotebookLM) | **Positive** | Fewer novel queries hit NotebookLM — no changes needed |
| Epic 4 (Auth) | None | Complete |
| Epic 5 (RBAC) | **Minor** | Bulk import requires admin role — uses existing permission model |
| Epic 6 (Favorites/History) | None | Complete |
| Epic 7 (Advanced Search) | **Positive** | Fewer low-confidence results — no changes needed |
| Epic 8 (Admin Data Mgmt) | None | Different data domain (tariff rates vs product mappings) |

**No existing epics are blocked, invalidated, or require modification.**

### Story Impact

- No existing stories need changes
- 3 new stories added in new Epic 9

### Artifact Conflicts

| Artifact | Change Needed |
|----------|--------------|
| **PRD** | Add FR74-FR78 (customs data ingestion capability) |
| **Architecture** | Add new endpoints, service documentation, `customs_import_batches` table |
| **Epics** | Add Epic 9 with 3 stories, update frontmatter counts |
| **Sprint Status** | Add Epic 9 entries |
| **UI/UX** | New admin page for bulk import |
| **Database** | `customs_import_batches` table (new); `lookup_records` unchanged |

### Technical Impact

- **No schema migration needed for core data** — `lookup_records` already has all fields needed for bulk import
- **One small migration** — new `customs_import_batches` table for batch tracking
- **No changes to search pipeline** — existing `find_verified_exact` and `find_verified_similar` automatically pick up imported records
- **No new external dependencies** — XLS/XLSX parsing uses existing libraries (openpyxl, xlrd)

---

## Section 3: Recommended Approach

### Selected Path: New Epic 9 — Customs Data Ingestion

**Type:** Direct Adjustment (new epic with new stories, no rework)

Create a new Epic 9 with 3 focused stories, prioritized immediately before Epic 7 and Epic 8.

### Rationale

| Factor | Assessment |
|--------|------------|
| **Implementation effort** | Low-Medium — 2-3 stories, no rework |
| **Timeline impact** | Minimal — no blockers on other epics |
| **Technical risk** | Low — existing schema fits, straightforward parsing |
| **Search accuracy impact** | Massive — thousands of verified mappings |
| **API cost reduction** | Significant — fewer NotebookLM calls |
| **Business value** | Very high — directly addresses PRD success metrics |
| **Long-term sustainability** | High — reusable pipeline for ongoing ingestion |

### Alternatives Considered

| Alternative | Verdict | Reason |
|-------------|---------|--------|
| Extend Epic 8 | Rejected | Different data domain — tariff rates vs product mappings |
| One-time script only | Rejected | User confirmed ongoing ingestion need |
| Defer to post-MVP | Rejected | Data available now, low effort, high impact on search quality |

### Effort & Risk

- **Effort:** Medium (3 stories, estimated 3-5 days total)
- **Risk:** Low — no new external dependencies, no schema changes to existing tables, no rework
- **Timeline impact:** None on existing epics — purely additive

---

## Section 4: Detailed Change Proposals

### 4.1 PRD Changes

**Add to Section 9 (Functional Requirements), after FR71-FR73:**

**Customs Data Ingestion (FR74-FR78):** _(added via sprint change 2026-02-24)_
- **FR74:** Admins can upload customs-approved import/export report files (XLS/XLSX) to bulk-import verified product-to-HS code mappings into the knowledge base
- **FR75:** The system parses uploaded reports to extract product descriptions and their associated 8-digit HS codes, matching them against the existing hs_codes table
- **FR76:** Admins can preview import results before confirming (total records, unique products, duplicates detected, unmatched HS codes)
- **FR77:** Imported records are stored as verified knowledge base entries (is_verified=true, search_method="customs_import") and are immediately available for search
- **FR78:** Admins can view import history showing past imports with source file, date, record counts, and error summary

**Add to FR Coverage Validation table:**

| Customs data ingestion (from sprint change 2026-02-24) | FR74-FR78 |

### 4.2 Epic Changes

**Update frontmatter:**
- totalEpics: 8 → 9
- totalStories: 44 → 47
- frCoverage: '70/70 (100%)' → '75/75 (100%)'

**Add FR Coverage Map rows:**

| FR | Epic | Description |
|----|------|-------------|
| FR74 | Epic 9 | Admin upload customs reports for bulk KB import |
| FR75 | Epic 9 | Parse reports, extract product + HS code pairs |
| FR76 | Epic 9 | Preview import results before confirming |
| FR77 | Epic 9 | Store as verified KB entries, immediately searchable |
| FR78 | Epic 9 | View import history with stats |

**Add Epic 9 summary and 3 stories** (see full story details in Section 4.5 below).

### 4.3 Architecture Changes

**Add API endpoints:**

```
POST /api/admin/customs-import/upload   # Upload customs report, return preview
POST /api/admin/customs-import/execute  # Confirm and run bulk import
GET  /api/admin/customs-import/history  # Past import batches (paginated)
GET  /api/admin/customs-import/stats    # KB quality stats by source
```

**Add table:**

```sql
customs_import_batches (id, file_name, company_name, imported_by_user_id,
    total_rows, records_imported, duplicates_skipped, unmatched_codes, errors,
    started_at, completed_at)
```

**Add "Customs Data Ingestion" architecture section** documenting:
- Data target: `lookup_records` (no migration)
- File formats: XLS (xlrd) + XLSX (openpyxl)
- Deduplication: SHA-256 query_hash
- Verification level: is_verified=true, confidence=100
- New services: `CustomsReportParser`, `CustomsImportService`
- Import flow (8 steps)
- Data flow into existing search pipeline (no changes needed)

### 4.4 Sprint Status Changes

**Add Epic 9 block:**

```yaml
# Epic 9: Customs Data Ingestion (NEW - Sprint Change 2026-02-24, 3 stories)
epic-9: backlog
9-1-customs-report-parser-import-service: backlog
9-2-admin-bulk-import-api-ui: backlog
9-3-import-history-quality-dashboard: backlog
epic-9-retrospective: optional
```

### 4.5 Story Details

#### Story 9-1: Customs Report Parser & Import Service

As an **admin**,
I want **a service that parses customs import/export report files and extracts verified product-to-HS code mappings into the knowledge base**,
So that **search accuracy is dramatically improved with ground-truth data from thousands of real customs declarations**.

**Data Source:** `docs/baocaohangchitiet/` (3 XLS/XLSX files from Do Thanh, Growatt Vietnam, KDE)

**Acceptance Criteria:**

**Given** a customs import/export report file (XLS or XLSX format)
**When** the parser processes the file
**Then** it extracts all rows containing a product description and 8-digit HS code
**And** normalizes product descriptions (trim whitespace, normalize Unicode)
**And** matches each HS code against the `hs_codes` table

**Given** extracted product-to-HS code pairs
**When** the import service runs
**Then** each pair is inserted into `lookup_records` with:
  - `query_text` = product description from report
  - `query_hash` = SHA-256 of normalized product description
  - `matched_hs_code_id` = `correct_hs_code_id` = matched HS code ID
  - `is_verified` = true
  - `search_method` = "customs_import"
  - `confidence_score` = 100
  - `notes` = source file name and company name

**Given** a product description that already exists in the knowledge base (same query_hash)
**When** the import runs
**Then** the duplicate is skipped (not inserted)
**And** the skip count is tracked in the import summary

**Given** an HS code in the report that does not match any code in the `hs_codes` table
**When** the import runs
**Then** the row is logged as an error (unmatched HS code)
**And** the error count and details are tracked in the import summary

**Given** all 3 initial report files are processed
**When** import completes
**Then** a summary is produced: total rows processed, records imported, duplicates skipped, unmatched codes, errors
**And** imported records are immediately available via KB search (find_verified_exact and find_verified_similar)

**Technical Tasks:**

1. Analyze the 3 report file formats — identify column positions for product name and HS code across Do Thanh (XLS), Growatt (XLS), KDE (XLSX)
2. Create `api/app/services/customs_import_service.py`:
   - `CustomsReportParser` class — parse XLS/XLSX, extract (product_name, hs_code) pairs
   - `CustomsImportService` class — match HS codes, deduplicate, bulk insert
   - Return `ImportResult` dataclass with counts and error details
3. Create `api/app/scripts/import_customs_data.py`:
   - CLI script for initial bulk import
   - Usage: `python -m app.scripts.import_customs_data docs/baocaohangchitiet/`
4. Tests: parser tests with sample data, import service tests with mocked DB

---

#### Story 9-2: Admin Bulk Import API & UI

As an **admin**,
I want **a web interface to upload customs report files, preview the import, and confirm execution**,
So that **I can import new company data files as they become available without needing CLI access**.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I navigate to the admin section
**Then** I see a "Nhap du lieu hai quan" (Customs Data Import) menu item

**Given** I am on the customs data import page
**When** I upload an XLS/XLSX file
**Then** the system parses the file and shows a preview:
  - Total rows found
  - Sample rows (first 10 product-to-HS code pairs)
  - Duplicate count (already in KB)
  - Unmatched HS code count
  - Ready-to-import count

**Given** I have reviewed the preview
**When** I click "Xac nhan nhap" (Confirm Import)
**Then** the import executes and I see a results summary:
  - Records imported
  - Duplicates skipped
  - Errors encountered
  - Time elapsed

**Given** I upload a file that is not XLS/XLSX or has no parseable data
**When** the system processes the file
**Then** I see a clear error message explaining the issue

**Technical Tasks:**

1. Backend endpoints:
   - `POST /api/admin/customs-import/upload` — parse file, return preview
   - `POST /api/admin/customs-import/execute` — run import, return results
   - Both require admin role
2. Frontend page: `web/src/app/admin/customs-import/page.tsx`
   - File upload dropzone
   - Preview table with stats
   - Confirm/cancel buttons
   - Results summary display
3. Tests: API endpoint tests, parser edge cases

---

#### Story 9-3: Import History & Quality Dashboard

As an **admin**,
I want **to see a history of customs data imports and knowledge base quality stats**,
So that **I can track what has been imported, monitor KB growth, and identify data quality issues**.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I navigate to the customs data import page
**Then** I see a history section showing past imports:
  - Source file name
  - Import date
  - Records imported / duplicates / errors
  - Imported by (admin user)

**Given** imports have been completed
**When** I view the quality dashboard section
**Then** I see:
  - Total verified KB records (breakdown by search_method: customs_import, notebooklm, expert_correction)
  - Top HS chapters by KB coverage
  - Recent import activity

**Technical Tasks:**

1. New table: `customs_import_batches` (id, file_name, company_name, imported_by_user_id, total_rows, records_imported, duplicates_skipped, unmatched_codes, errors, started_at, completed_at)
2. Alembic migration for new table
3. Backend endpoints:
   - `GET /api/admin/customs-import/history` — paginated import history
   - `GET /api/admin/customs-import/stats` — KB quality stats
4. Frontend: history table + stats cards on the customs import admin page
5. Tests: history retrieval, stats aggregation

---

## Section 5: Implementation Handoff

### Change Scope Classification: Minor-Moderate

- **Minor aspects:** No rework, no schema changes to existing tables, no pipeline changes
- **Moderate aspects:** New epic with 3 stories, new admin UI page, new database table

### Handoff

| Recipient | Responsibility |
|-----------|---------------|
| **Development team** | Implement Stories 9-1, 9-2, 9-3 via standard dev-story workflow |
| **tinsu (PO)** | Provide additional customs report files as available; validate import results |

### Implementation Sequence

1. **Story 9-1** (independent — can start immediately): Parser + import service + CLI script. Run initial import of all 3 files.
2. **Story 9-2** (depends on 9-1): Admin API endpoints + frontend upload/preview UI
3. **Story 9-3** (depends on 9-2): Batch tracking table + history/stats UI

### Success Criteria

- [ ] All 3 initial report files successfully imported
- [ ] Imported records appear in KB search results (verified via test queries)
- [ ] Admin can upload new files via web UI and see preview before confirming
- [ ] Import history shows all past imports with accurate counts
- [ ] No regressions in existing search pipeline, auth, or admin features

### Priority

Epic 9 is prioritized **before Epic 7 (Advanced Search) and Epic 8 (Admin Data Mgmt)** due to:
- Highest ROI for search accuracy improvement
- Data available immediately
- Low technical risk
- Reduces NotebookLM API pressure
