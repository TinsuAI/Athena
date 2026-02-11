# Sprint Change Proposal — Tariff Schedule Browser & Data Import Expansion

**Date:** 2026-02-11
**Author:** tinsu (with AI assistance)
**Status:** Approved
**Scope:** Moderate
**Workflow:** correct-course

---

## Section 1: Issue Summary

### Problem Statement

The current Vietnamese tariff schedule lives in a 32MB Excel file (`BIEU-THUE-XNK-2026.xlsx`) with 38 sheets and 19,901 rows × 106 columns. Every customs professional opens this file daily to find HS codes, browse the hierarchy, and check FTA rates. This is slow, difficult to navigate, and error-prone.

Athena already has AI-powered search (Epic 1, Stories 1-1 through 1-13) and 11,871 HS codes with 211,391 FTA rates imported into the database. However, there is **no browsable tariff schedule page** — users cannot navigate the hierarchy visually or see FTA rates inline the way they do in Excel.

### Context

- **Discovered:** Stakeholder request during sprint execution (2026-02-11)
- **Trigger:** User need to replace the Excel browsing workflow with a web-based experience
- **Evidence:** The Excel file is 32MB, has 38 sheets of FTA rate data, and is the primary daily tool for customs teams. Data gaps exist in the current import (no export rates, environmental tax, special consumption tax, RCEP yearly rates, FTA conditions).

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Impact Level | Details |
|------|-------------|---------|
| **Epic 1** (Core Search) | None | No changes to existing done/review stories. |
| **Epic 2** (Tariff Browser, NEW) | **Major** | New epic with 3 stories: 2.1 (data import expansion), 2.2 (browse API), 2.3 (browse page). Covers FR8, FR54-FR61. |
| **Epic 3** (Auth, was Epic 2) | None | Renumbered only |
| **Epic 4** (Favorites/History, was Epic 3) | None | Renumbered only |
| **Epic 5** (Advanced Search, was Epic 4) | Minor | Old Story 4.1 moved to Epic 2. Remaining: 3 stories covering FR9, FR44, FR45. |
| **Epic 6** (Admin Data, was Epic 5) | Minor | Renumbered. Future admin uploads must use expanded parser. |

### Story Impact

| Story | Change Type | Details |
|-------|------------|---------|
| **2.1 (NEW)** | Add | Expand tariff import: export rates, TTDB, BVMT, RCEP yearly, FTA conditions, export FTAs, VAT reduction |
| **2.2 (NEW)** | Add | Browse API endpoints: sections, chapters, chapter detail with inline rates, browse search |
| **2.3 (NEW)** | Add | Full tariff schedule browser page with inline rates, search, FTA display |

### Artifact Conflicts

| Artifact | Status | Changes Needed |
|----------|--------|----------------|
| **PRD** | Action needed | Add FR54-FR61, modify FR16 for export FTAs + RCEP yearly |
| **Architecture** | Action needed | Schema migration: 4 new columns on hs_codes, 4 new columns on fta_rates, 3 new export FTA agreements |
| **Epics** | Action needed | Update Epic 4 description and FR coverage map |
| **UX Design** | Action needed | Browse page UI design (tree view, inline rates, search) |
| **Import Scripts** | Action needed | Parser expansion for 15+ new Excel columns |

### Technical Impact

- **Database:** Alembic migration adding columns to `hs_codes` and `fta_rates`
- **Parser:** `tariff_hierarchy_parser.py` expanded to read columns CD, CG, CJ-CR, CS, CW + FTA conditions + RCEP yearly rates
- **API:** New `/api/browse/*` endpoints with optimized hierarchy queries
- **Frontend:** New `/browse` page with collapsible tree, inline rates, search
- **Re-import:** Full data re-import required after schema + parser changes

---

## Section 3: Recommended Approach

### Selected Path: Direct Adjustment

Modify existing stories and add new ones within the current epic structure. No rollback or MVP scope reduction needed.

### Rationale

1. **Data foundation exists:** 11,871 HS codes and full hierarchy already in DB
2. **Planned work:** Story 4.1 (Hierarchical Browser) was already in the backlog
3. **Additive changes:** New DB columns and FTA entries don't break existing functionality
4. **Low risk:** All data is in the Excel file, schema is extensible
5. **High value:** Directly addresses the #1 daily workflow pain point

### Effort & Risk

| Dimension | Assessment |
|-----------|-----------|
| **Effort** | Medium — ~3 stories, schema migration, parser update, new page |
| **Risk** | Low — data is well-understood, architecture supports expansion |
| **Timeline** | Minimal impact — can start immediately, parallel with Epic 1 review items |

---

## Section 4: Detailed Change Proposals

### 4.1 PRD Changes

**Add new Functional Requirements:**

| FR | Description |
|----|-------------|
| FR54 | Users can browse the full tariff schedule as a collapsible tree (Section → Chapter → Heading → Subheading → 8-digit code) with inline rate data per row |
| FR55 | Users can view export duty rates for any HS code |
| FR56 | Users can view special consumption tax (TTDB) for applicable HS codes |
| FR57 | Users can view environmental protection tax (BVMT) for applicable HS codes |
| FR58 | Users can view VAT reduction eligibility for applicable HS codes |
| FR59 | Users can search/filter within the tariff browser by code number or description text |
| FR60 | Users can jump to a specific chapter via quick selector in the browser |
| FR61 | Users can view section and chapter classification notes in the browser |

**Modify FR16:**

- **OLD:** "Users can view FTA preferential rates for applicable trade agreements (CPTPP, EVFTA, RCEP, ACFTA, AKFTA, AJCEP, VKFTA, and others)"
- **NEW:** "Users can view FTA preferential rates for all active import AND export trade agreements, including RCEP year-by-year rates (2022-2027) and export FTA rates (CPTPP-XK, EV-XK, UKV-XK)"

### 4.2 Architecture — Schema Changes

**hs_codes table — new columns:**

| Column | Type | Source (Excel) | Description |
|--------|------|----------------|-------------|
| `export_duty_rate` | NUMERIC, nullable | Col CG (85) | Export duty rate |
| `special_consumption_tax` | VARCHAR, nullable | Col CD (82) | Can be % or conditional text |
| `environmental_tax` | VARCHAR, nullable | Col CS (97) | Can be per-unit amounts |
| `vat_reduction` | VARCHAR, nullable | Col CW (101) | VAT reduction indicator |

**fta_rates table — new columns:**

| Column | Type | Description |
|--------|------|-------------|
| `rate_year` | INTEGER, nullable | For RCEP yearly rates (2022-2027) |
| `is_export` | BOOLEAN, default false | Distinguish import vs export FTA |
| `legal_document` | VARCHAR, nullable | Legal document reference |
| `effective_date` | VARCHAR, nullable | Effective date of the rate |

**New FTA agreements to import:**

| Agreement | Type | Excel Sheet |
|-----------|------|-------------|
| CPTPP-XK | Export | CPTPP-XK (769 rows) |
| EV-XK | Export | EV-XK (1,271 rows) |
| UKV-XK | Export | UKV-XK (1,275 rows) |

### 4.3 Epics — Reordering (Approved 2026-02-11)

**Epic reorder applied:**
- **Epic 2 (NEW):** Tariff Schedule Browser — FR8, FR54, FR55, FR56, FR57, FR58, FR59, FR60, FR61
- **Epic 3 (was 2):** User Authentication & Sessions — FR30-FR35
- **Epic 4 (was 3):** Personalization - Favorites & History — FR19-FR29
- **Epic 5 (was 4):** Advanced Search & Discovery — FR9, FR44, FR45 (old 4.1 moved to Epic 2)
- **Epic 6 (was 5):** Admin Data Management — FR36-FR42

### 4.4 New Stories (Epic 2)

#### Story 2.1: Expand Tariff Import with Export Rates, Taxes, and FTA Conditions

**Epic:** Epic 2
**Dependencies:** None (can start immediately)

**Acceptance Criteria:**
- Migration adds 4 new columns to `hs_codes` and 4 new columns to `fta_rates`
- Parser reads Excel columns CD, CG, CJ-CR, CS, CW for tax/rate data
- Parser populates FTA `conditions` field (currently always NULL)
- RCEP yearly rates stored with `rate_year` (2022-2027)
- Export FTA rates imported from CPTPP-XK, EV-XK, UKV-XK sheets with `is_export=true`
- Legal document and effective date captured per FTA rate
- Full re-import completes successfully
- All existing functionality unchanged

#### Story 2.2: Tariff Browse API Endpoints

**Epic:** Epic 2
**Dependencies:** Story 2.1

**Endpoints:**
- `GET /api/browse/sections` — All sections with chapter counts
- `GET /api/browse/chapters?section_id={id}` — Chapters in section with counts
- `GET /api/browse/chapters/{chapter_code}` — Full chapter data: headings → subheadings → codes with inline rates (paginated)
- `GET /api/browse/search?q={text}&chapter={code}` — Text search within browse (pg_trgm + exact code match)

**Backend layering:**
- Route: `api/app/api/browse.py`
- Service: `api/app/services/browse_service.py`
- Repository: `api/app/repositories/browse_repository.py`

#### Story 2.3: Tariff Schedule Browser Page

**Epic:** Epic 2
**Dependencies:** Story 2.2

**Acceptance Criteria:**
- Collapsible tree view at `/browse`: Sections → Chapters → Headings → Subheadings → 8-digit codes
- Inline data per HS code row: code, description (VN/EN), import duty, VAT, export duty
- Expandable FTA rates panel per code (all 18+ agreements)
- Show special consumption tax, environmental tax where applicable
- Section/chapter notes displayed as expandable info panels
- "Jump to chapter" quick selector dropdown
- Total count indicators per chapter
- Responsive table layout (desktop-optimized, tablet-functional)
- Keyboard navigation (arrow keys expand/collapse)

---

## Section 5: Implementation Handoff

### Scope Classification: Moderate

Requires backlog reorganization and new story creation, but no fundamental replan.

### Handoff Plan

| Role | Responsibility |
|------|---------------|
| **Development Team** | Implement stories 2.1, 2.2, 2.3 |
| **SM/PO** | Update sprint status, create story files, prioritize relative to remaining Epic 1 review items |

### Implementation Order

1. **Story 2.1** — Data import expansion (schema + parser + re-import)
2. **Story 2.2** — Browse API endpoints
3. **Story 2.3** — Browse page frontend

Stories 2.2 and 2.3 can be developed in parallel once Story 2.1 is complete.

### Success Criteria

- [ ] All data from BT2026 Excel sheet captured in database (import/export rates, taxes, FTA conditions)
- [ ] Export FTA rates from 3 additional sheets imported
- [ ] Browse page displays full tariff hierarchy with inline rates
- [ ] Users can search/filter within the tariff browser
- [ ] FTA rates viewable per HS code without clicking into separate detail view
- [ ] Page performs well with 11,871+ codes (lazy loading per chapter)
