# Story 9.1: Customs Report Parser & Import Service

Status: done

## Story

As an **admin**,
I want **a service that parses customs import/export report files and extracts verified product-to-HS code mappings into the knowledge base**,
So that **search accuracy is dramatically improved with ground-truth data from thousands of real customs declarations**.

## Acceptance Criteria

1. **Given** a customs import/export report file (XLS or XLSX format)
   **When** the parser processes the file
   **Then** it extracts all rows containing a product description and 8-digit HS code
   **And** normalizes product descriptions (trim whitespace, normalize Unicode)
   **And** matches each HS code against the `hs_codes` table

2. **Given** extracted product-to-HS code pairs
   **When** the import service runs
   **Then** each pair is inserted into `lookup_records` with:
   - `query_text` = product description from report
   - `query_hash` = SHA-256 of normalized product description (use existing `compute_query_hash` from `app.repositories.lookup_record_repository`)
   - `matched_hs_code_id` = `correct_hs_code_id` = matched HS code ID (from `hs_codes.id` lookup by `hs_codes.code`)
   - `is_verified` = true
   - `search_method` = "customs_import"
   - `confidence_score` = 100
   - `notes` = source file name and company name

3. **Given** a product description that already exists in the knowledge base (same `query_hash`)
   **When** the import runs
   **Then** the duplicate is skipped (not inserted)
   **And** the skip count is tracked in the import summary

4. **Given** an HS code in the report that does not match any code in the `hs_codes` table
   **When** the import runs
   **Then** the row is logged as an error (unmatched HS code)
   **And** the error count and details are tracked in the import summary

5. **Given** all 3 initial report files are processed
   **When** import completes
   **Then** a summary is produced: total rows processed, records imported, duplicates skipped, unmatched codes, errors
   **And** imported records are immediately available via KB search (`find_verified_exact` and `find_verified_similar`)

## Tasks / Subtasks

- [x] Task 1: Analyze report file formats (AC: #1)
  - [x] 1.1 Examine `docs/baocaohangchitiet/bchangchitiet-1-dothanh.xls` — identify sheet structure, column positions for product name and HS code, header rows, data start row
  - [x] 1.2 Examine `docs/baocaohangchitiet/bchangchitiet-2-growatt.xls` — same analysis (~19,898 rows, largest file)
  - [x] 1.3 Examine `docs/baocaohangchitiet/bchangchitiet-3-kde.xlsx` — same analysis (XLSX format)
  - [x] 1.4 Document column mappings per file format (product description column, HS code column, header row, data start row)
- [x] Task 2: Create `CustomsReportParser` class (AC: #1)
  - [x] 2.1 Create `api/app/services/customs_import_service.py`
  - [x] 2.2 Implement XLS parsing using `xlrd` library (for `.xls` files — Do Thanh and Growatt)
  - [x] 2.3 Implement XLSX parsing using `openpyxl` (for `.xlsx` files — KDE). NOTE: `openpyxl` is already in requirements.txt
  - [x] 2.4 Auto-detect format by file extension (`.xls` vs `.xlsx`)
  - [x] 2.5 Extract `(product_name, hs_code_str)` tuples, normalize product descriptions (strip, normalize Unicode via `unicodedata.normalize("NFC", ...)`)
  - [x] 2.6 Validate HS codes: must be 8-digit numeric strings. Strip any dots/spaces from raw code strings.
  - [x] 2.7 Return `list[ParsedRow]` dataclass with product_name, hs_code, row_number for traceability
- [x] Task 3: Create `CustomsImportService` class (AC: #2, #3, #4, #5)
  - [x] 3.1 Accept parsed rows + AsyncSession
  - [x] 3.2 Build a set of all HS codes in the parsed data, batch-query `hs_codes` table to get `{code: id}` mapping
  - [x] 3.3 For each row: compute `query_hash` using existing `compute_query_hash()` from `app.repositories.lookup_record_repository`
  - [x] 3.4 Deduplicate: check if `query_hash` already exists in `lookup_records` (single bulk query for all hashes at once for efficiency)
  - [x] 3.5 Track unmatched HS codes (code not found in `hs_codes` table)
  - [x] 3.6 Bulk insert new `LookupRecord` objects with the fields specified in AC #2
  - [x] 3.7 Return `ImportResult` dataclass: total_rows, records_imported, duplicates_skipped, unmatched_codes (list of code+row), errors (list of error details)
- [x] Task 4: Create CLI import script (AC: #5)
  - [x] 4.1 Create `api/app/scripts/import_customs_data.py`
  - [x] 4.2 Accept directory path as argument, process all `.xls`/`.xlsx` files found
  - [x] 4.3 For each file: parse, import, print summary
  - [x] 4.4 Print grand total summary at the end
  - [x] 4.5 Usage: `python -m app.scripts.import_customs_data docs/baocaohangchitiet/`
- [x] Task 5: Add `xlrd` to requirements.txt (AC: #1)
  - [x] 5.1 Add `xlrd>=2.0.0` to `api/requirements.txt` — needed for `.xls` format parsing (openpyxl only handles `.xlsx`)
- [x] Task 6: Write tests (AC: all)
  - [x] 6.1 Create `api/app/services/customs_import_service_test.py` (co-located)
  - [x] 6.2 Test parser: valid XLS data extraction, valid XLSX data extraction, empty file handling, missing columns, malformed HS codes
  - [x] 6.3 Test import service: successful import, duplicate skipping, unmatched HS code tracking, summary accuracy
  - [x] 6.4 Test `compute_query_hash` integration (reuse existing function, not re-implement)

## Dev Notes

### Critical Architecture Compliance

- **Layering:** This story is backend-only (service + script). No route handlers needed — Story 9-2 adds the API endpoints.
- **Service layer:** ALL business logic goes in `CustomsReportParser` and `CustomsImportService` in `api/app/services/customs_import_service.py`
- **Repository reuse:** Use existing `LookupRecordRepository` for database operations where possible. For bulk operations, direct SQLAlchemy in the service is acceptable (bulk insert performance).
- **Hash function:** MUST reuse `compute_query_hash()` from `api/app/repositories/lookup_record_repository.py`. Do NOT re-implement SHA-256 hashing. Import it: `from app.repositories.lookup_record_repository import compute_query_hash`

### Existing Code to Reuse (DO NOT Reinvent)

| What | Where | How to Use |
|------|-------|------------|
| `compute_query_hash(query_text)` | `api/app/repositories/lookup_record_repository.py` | Import and call for deduplication hash |
| `LookupRecord` model | `api/app/models/lookup_record.py` | Create instances for bulk insert |
| `HSCode` model | `api/app/models/hs_code.py` | Query by `code` field to get `id` for FK |
| `get_settings()` | `api/app/core/config.py` | Get `database_url` for engine creation in CLI script |
| Import script pattern | `api/app/scripts/import_tariff_data.py` | Follow same pattern: argparse, asyncio.run, create_async_engine, async_sessionmaker |

### LookupRecord Field Mapping for Customs Import

```python
LookupRecord(
    query_text=product_name,                  # from report row
    query_hash=compute_query_hash(product_name),  # SHA-256 of normalized text
    matched_hs_code_id=hs_code_id,            # from hs_codes table lookup
    correct_hs_code_id=hs_code_id,            # same as matched (customs-verified)
    is_verified=True,                         # customs data = ground truth
    search_method="customs_import",           # new search method type
    confidence_score=100,                     # maximum confidence
    notes=f"Source: {file_name} ({company_name})",  # traceability
    # Leave null: query_language, verified_by_user_id, verified_at,
    #   submitted_by_user_id, correction_status, rejection_reason,
    #   classification_data, practical_notes, process_logs, nlm_raw_response
)
```

### Data Source Files

| # | File | Company | Format | Estimated Rows |
|---|------|---------|--------|----------------|
| 1 | `bchangchitiet-1-dothanh.xls` | Do Thanh | XLS | ~1,500 |
| 2 | `bchangchitiet-2-growatt.xls` | Growatt Vietnam | XLS | ~19,898 |
| 3 | `bchangchitiet-3-kde.xlsx` | KDE | XLSX | ~3,500 |

**File analysis notes:**
- These are Vietnamese customs-approved "bao cao hang chi tiet" (detailed goods reports)
- Vietnamese customs report formats: expect columns for "Ten hang" / "Mo ta hang hoa" (product description) and "Ma so" / "Ma HS" (HS code)
- HS codes in reports may have dots (e.g., "8507.60.00") — strip dots to get 8-digit code ("85076000")
- Some rows may be subtotals, headers, or empty — skip non-data rows
- Product descriptions are in Vietnamese

### Library Requirements

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| `openpyxl` | >= 3.1.0 | Parse XLSX files | Already in requirements.txt |
| `xlrd` | >= 2.0.0 | Parse XLS files | MUST ADD to requirements.txt |

**IMPORTANT about xlrd:** Version 2.0+ only supports `.xls` format (removed xlsx support). This is correct — we use openpyxl for xlsx and xlrd for xls.

### Performance Considerations

- Growatt file is 31 MB with ~20K rows — use batch processing
- Bulk insert with `session.add_all()` + `session.flush()` in batches of 500-1000 records
- Bulk dedup check: query all existing `query_hash` values in one SELECT before inserting (not one-by-one)
- Bulk HS code lookup: query all distinct codes in one SELECT (not one-by-one)

### Testing Approach

- Tests go in `api/app/services/customs_import_service_test.py` (co-located with source)
- Use pytest with `asyncio_mode = "auto"`
- Mock database session for import service tests
- For parser tests: create small test XLS/XLSX files in memory using openpyxl/xlrd, or use fixture data
- Do NOT test with the actual 31MB data files in unit tests

### Project Structure Notes

```
api/app/
├── services/
│   ├── customs_import_service.py      # NEW: CustomsReportParser + CustomsImportService
│   └── customs_import_service_test.py # NEW: Tests (co-located)
├── scripts/
│   └── import_customs_data.py         # NEW: CLI script
└── requirements.txt                   # MODIFY: add xlrd>=2.0.0
```

No new API routes, no frontend changes, no migrations needed in this story.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 9, Story 9-1]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-24.md#Section 4.5]
- [Source: api/app/repositories/lookup_record_repository.py#compute_query_hash]
- [Source: api/app/models/lookup_record.py#LookupRecord]
- [Source: api/app/models/hs_code.py#HSCode]
- [Source: api/app/scripts/import_tariff_data.py] (pattern reference for CLI script)
- [Source: api/app/core/config.py#get_settings]

### Previous Stories Intelligence

This is the first story in Epic 9, so no previous story in this epic. However, relevant patterns from previous epics:

- **Import script pattern** (Story 1-2): `import_tariff_data.py` uses argparse, creates async engine from `get_settings().database_url`, uses `async_sessionmaker`. Follow the same pattern.
- **Knowledge base service** (Story 1-8, 1-9): The KB service uses `find_verified_exact` (hash match) and `find_verified_similar` (pg_trgm). Imported customs records will automatically be returned by these queries — no changes needed.
- **search_method field values in use:** "hybrid", "notebooklm", "expert_correction". This story adds "customs_import" — the `search_method` column is `String(20)`, which is sufficient.

### Git Intelligence

Recent commits show:
- `c1d492d` — Sprint change proposal for Epic 9 was already committed with data files
- Codebase follows pattern: services contain all business logic, co-located tests, no trailing slashes on API routes
- All previous stories have had code review with auto-fixes (common issues: type hints, error handling, edge cases)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Debug Log References
- Analyzed all 3 customs report files using xlrd/openpyxl to determine column mappings
- File 1 (Do Thanh): 58 cols, header row 3, HS col 23, name col 25, 1488 data rows. Company: DKE Vietnam
- File 2 (Growatt XLS): 54 cols, header row 9, HS col 21, name col 22, 313 data rows. Company: Nhom Do Thanh
- File 3 (KDE XLSX): same 54-col format, header row 10 (1-indexed), HS col 21, name col 22, 19898 data rows. Company: Growatt Vietnam
- Key finding: Do Thanh file has 2 extra columns (STK 11 SO) shifting HS/name columns by +2
- Implemented auto-detection of header row by scanning for "Ma HS" and "Ten hang" column headers
- Product names contain "#&" separator (e.g., "CODE#&Description") -- parser strips the prefix
- HS codes may appear as floats (e.g., "39269099.0") or with dots -- parser normalizes both formats

### Completion Notes List
- All 6 tasks completed with 37 tests passing (0 failures)
- CustomsReportParser auto-detects file format (XLS/XLSX) and column positions dynamically
- CustomsImportService performs bulk HS code lookup, bulk dedup check, and batch insert (500 records/batch)
- Reuses existing compute_query_hash() from lookup_record_repository (no re-implementation)
- CLI script follows same pattern as import_tariff_data.py (argparse, asyncio.run, async engine)
- All ruff lint checks pass (0 errors)
- No regressions introduced (pre-existing failures in excel_parser_service_test.py and auth_integration_test.py unrelated)

### File List
- `api/app/services/customs_import_service.py` — NEW: CustomsReportParser + CustomsImportService classes
- `api/app/services/customs_import_service_test.py` — NEW: 48 unit tests (co-located, increased from 37 after code review)
- `api/app/scripts/import_customs_data.py` — NEW: CLI script for batch import
- `api/requirements.txt` — MODIFIED: added xlrd>=2.0.0

### Change Log
- 2026-02-24: Implemented customs report parser and import service (Story 9-1). Added CustomsReportParser (XLS/XLSX auto-detect, header scanning, HS code normalization, product name cleanup), CustomsImportService (bulk HS lookup, dedup, batch insert into lookup_records), CLI import script, and 37 co-located tests. Added xlrd dependency.
- 2026-02-24: Code review (Story 9-1) — 1 critical + 2 high + 3 medium + 1 low issues fixed. Fixes: (1) Cleaned up double-await pattern in import_customs_data.py (C1); (2) Added 6 XLS mock tests in TestCustomsReportParserXls class covering _parse_xls code path with full logic coverage (C2); (3) Fixed AsyncMock unawaited coroutine warnings by overriding session.add_all/flush to be sync/async respectively in 4 import service tests (M1); (4) Added TestDetectCompanyName class with 5 tests for the CLI's detect_company_name function (M4); (5) Optimized _parse_xlsx to use min_row=data_start_row+1 instead of iterating from row 1 (M5); (6) Wrapped wb.close() in try/finally block in _parse_xlsx for safe cleanup on error paths (L1). All 48 tests pass, 0 ruff errors, 0 warnings.
