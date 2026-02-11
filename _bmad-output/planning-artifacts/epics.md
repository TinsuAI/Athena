---
stepsCompleted: [1, 2, 3, 4]
status: complete
completedAt: '2026-01-26'
totalEpics: 6  # Reordered 2026-02-11: New Epic 2 (Tariff Browser), old 2→3, 3→4, 4→5, 5→6
totalStories: 37  # Added Stories 2-1, 2-2, 2-3 (Tariff Browser, Sprint Change 2026-02-11). Removed old 4.1 (moved to Epic 2).
frCoverage: '61/61 (100%)'  # Added FR54-FR61 (2026-02-11)
inputDocuments:
  - path: _bmad-output/planning-artifacts/prd.md
    type: prd
    description: Complete PRD with 50 functional requirements
  - path: _bmad-output/planning-artifacts/architecture.md
    type: architecture
    description: Full architecture with Next.js + FastAPI + PostgreSQL stack
  - path: _bmad-output/planning-artifacts/ux-design-specification.md
    type: ux-design
    description: UX Design with Tailwind + shadcn/ui components
workflowType: 'epics-and-stories'
project_name: 'athena'
user_name: 'tinsu'
date: '2026-01-26'
---

# Athena - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Athena, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

**HS Code Search (FR1-FR9):**
- FR1: Users can search for HS codes by entering product descriptions in Vietnamese
- FR2: Users can search for HS codes by entering product descriptions in English
- FR3: Users can search for HS codes by entering product descriptions in Chinese
- FR4: Users can search for HS codes by entering the exact HS code number
- FR5: Users can view search results ranked by confidence/relevance score
- FR6: Users can see confidence indicators (high/medium/low) for each search result
- FR7: Users can view full tariff details for any HS code in search results
- FR8: Users can browse HS codes hierarchically by Section, Chapter, and Heading
- FR9: Users can filter search results by HS code chapter

**Tariff Data Display (FR10-FR18):**
- FR10: Users can view the 8-digit Vietnam HS code for any tariff entry
- FR11: Users can view the Vietnamese description for any HS code
- FR12: Users can view the English description for any HS code
- FR13: Users can view the unit of measure for any HS code
- FR14: Users can view the standard import duty rate for any HS code
- FR15: Users can view the VAT rate for any HS code
- FR16: Users can view FTA preferential rates for applicable trade agreements (CPTPP, EVFTA, RCEP, ACFTA, AKFTA, AJCEP, VKFTA, and others)
- FR17: Users can view policy notes and restrictions for any HS code
- FR18: Users can view the current tariff data version and effective date

**User Favorites (FR19-FR24):**
- FR19: Users can save any HS code to their personal favorites
- FR20: Users can add personal notes to saved favorites
- FR21: Users can view their complete favorites list
- FR22: Users can remove HS codes from their favorites
- FR23: Users can search within their favorites
- FR24: Users can access favorites for quick re-lookup during search workflow

**Search History (FR25-FR29):**
- FR25: The system records all user searches automatically
- FR26: Users can view their recent search history
- FR27: Users can re-execute a previous search from history
- FR28: Users can see which HS code they selected for each historical search
- FR29: Users can clear their search history

**User Authentication (FR30-FR35):**
- FR30: Users can create an account with email and password
- FR31: Users can log in to the system with their credentials
- FR32: Users can log out of the system
- FR33: Users can reset their password if forgotten
- FR34: The system maintains user sessions across browser sessions
- FR35: Admins can assign user roles (standard user, admin)

**Admin Data Management (FR36-FR42):**
- FR36: Admins can upload new tariff data files (Excel format)
- FR37: Admins can preview uploaded data before activation (row count, change summary)
- FR38: Admins can see a comparison of changes between current and uploaded data
- FR39: Admins can activate uploaded tariff data to make it live
- FR40: Admins can roll back to the previous tariff data version
- FR41: Admins can view the history of data uploads and activations
- FR42: The system validates uploaded Excel files for correct format before processing

**System Feedback & Error Handling (FR43-FR47):**
- FR43: Users receive clear feedback when search returns no results
- FR44: Users receive suggestions for alternative search terms when results are low-confidence
- FR45: Users can report incorrect or missing HS code data (feedback mechanism)
- FR46: The system displays appropriate error messages for system failures
- FR47: Users can see a loading indicator during search operations

**Data Integrity (FR48-FR50):**
- FR48: The system preserves exact HS code formats as published (no truncation)
- FR49: The system preserves duty rate decimal precision from source data
- FR50: The system displays policy notes verbatim from source data

### Non-Functional Requirements

**Performance:**
- NFR-P1: Search query response time <3 seconds (95th percentile)
- NFR-P2: Page initial load time <4 seconds
- NFR-P3: HS code detail retrieval <1 second
- NFR-P4: Favorites/History load <2 seconds
- NFR-P5: Admin data upload processing <5 minutes for full dataset (~20,000 records)

**Reliability:**
- NFR-R1: System availability 99.5% during business hours (Mon-Sat 7am-7pm ICT)
- NFR-R2: Planned maintenance window off-hours only (after 8pm ICT)
- NFR-R3: Zero tolerance for user favorites/history loss
- NFR-R4: Graceful degradation - search returns partial results rather than failing completely
- NFR-R5: Recovery time objective (RTO) <2 hours for full system recovery

**Scalability:**
- NFR-S1: Support 50-100 concurrent users
- NFR-S2: Support 500+ searches per minute system-wide
- NFR-S3: Support 5 years of search history database growth
- NFR-S4: Support up to 50,000 HS codes data scale

**Security:**
- NFR-SEC1: HTTPS/TLS 1.2+ for all data in transit
- NFR-SEC2: Bcrypt with cost factor >=10 for password storage
- NFR-SEC3: JWT with 24-hour expiry, refresh tokens for session management
- NFR-SEC4: Server-side validation on all user inputs
- NFR-SEC5: Role-based access control; admin actions logged
- NFR-SEC6: Rate limiting 100 requests/minute per user

**Usability:**
- NFR-U1: Single text field search input, no mode selection required
- NFR-U2: View 10+ results without scrolling
- NFR-U3: Tab/Enter keyboard navigation for power users
- NFR-U4: Bilingual (VN + EN) descriptions shown together
- NFR-U5: Functional on tablet (1024px+)

**Accessibility:**
- NFR-A1: WCAG 2.1 Level AA for core workflows
- NFR-A2: All interactive elements labeled for screen readers
- NFR-A3: 4.5:1 minimum color contrast for text
- NFR-A4: All functions accessible via keyboard

**Internationalization:**
- NFR-I1: UTF-8 character encoding throughout
- NFR-I2: Accept Vietnamese diacritics, Chinese characters in input
- NFR-I3: English interface (Vietnamese data displayed)
- NFR-I4: Support both comma and period decimal separators

**Monitoring & Observability:**
- NFR-M1: External health check every 5 minutes
- NFR-M2: Admin notification within 5 minutes of critical errors
- NFR-M3: Log all searches (anonymized for analysis)
- NFR-M4: Response time monitoring for performance tracking

### Additional Requirements

**From Architecture - Starter Template:**
- Initialize project with Next.js 15+ App Router, TypeScript, Tailwind CSS for frontend
- Initialize backend with FastAPI (Python 3.12+), async SQLAlchemy 2.0
- Set up PostgreSQL 16 with pgvector extension for database
- Configure Redis 7 for sessions, caching, and rate limiting
- Implement NextAuth.js v5 with fastapi-nextauth-jwt for authentication flow
- Use Docker Compose with nginx reverse proxy for deployment

**From Architecture - Search Implementation:**
- Implement hybrid search: vector similarity (pgvector) + fuzzy text (pg_trgm) + exact match
- Use OpenRouter API for embedding generation (configurable models)
- Normalize confidence scores to 0-100% from cosine similarity

**From Architecture - Code Patterns:**
- Follow layered architecture: API routes → Services → Repositories
- Use envelope response format: `{success, data, error}` for all API responses
- Use RFC 7807 error structure for error responses
- Co-locate tests with source files
- Follow naming conventions: snake_case (Python/DB/API), camelCase/PascalCase (TypeScript)

**From UX Design - Component Requirements:**
- Build custom SearchBar component with language detection indicator
- Build ResultCard component with confidence visualization
- Build ConfidenceBadge component (green/yellow/red color-coded)
- Build TariffDetailPanel with tabbed content (Overview/FTA Rates/Policy Notes)
- Build FavoriteCard with personal notes field
- Build HistoryItem with one-click re-execute

**From UX Design - Interaction Patterns:**
- Implement instant search with 150ms debounce
- Support keyboard shortcuts (/, Cmd+K for search, arrow keys, Enter)
- Use toast notifications (green success 3s, red error 5s)
- Show skeleton loaders during search operations
- Auto-focus search bar on page load

**From UX Design - Responsive Design:**
- Desktop (1024px+): Full sidebar navigation, detail panel as right drawer
- Tablet (768px-1023px): Collapsible sidebar, detail panel as modal overlay
- Mobile (320px-767px): Bottom navigation bar, full-screen detail view

**From UX Design - Accessibility:**
- Implement focus indicators (2px solid primary with offset)
- Ensure 44x44px minimum touch targets
- Add skip link to main content
- Respect `prefers-reduced-motion` for animations

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | Epic 1 | Search by Vietnamese descriptions |
| FR2 | Epic 1 | Search by English descriptions |
| FR3 | Epic 1 | Search by Chinese descriptions |
| FR4 | Epic 1 | Search by exact HS code |
| FR5 | Epic 1 | View confidence-ranked results |
| FR6 | Epic 1 | See confidence indicators |
| FR7 | Epic 1 | View full tariff details from results |
| FR8 | Epic 2 | Browse HS codes hierarchically |
| FR9 | Epic 5 | Filter by HS code chapter |
| FR10 | Epic 1 | View 8-digit HS code |
| FR11 | Epic 1 | View Vietnamese description |
| FR12 | Epic 1 | View English description |
| FR13 | Epic 1 | View unit of measure |
| FR14 | Epic 1 | View import duty rate |
| FR15 | Epic 1 | View VAT rate |
| FR16 | Epic 1 | View FTA preferential rates |
| FR17 | Epic 1 | View policy notes |
| FR18 | Epic 1 | View data version and date |
| FR19 | Epic 4 | Save to favorites |
| FR20 | Epic 4 | Add notes to favorites |
| FR21 | Epic 4 | View favorites list |
| FR22 | Epic 4 | Remove from favorites |
| FR23 | Epic 4 | Search within favorites |
| FR24 | Epic 4 | Quick access during search |
| FR25 | Epic 4 | Auto-record searches |
| FR26 | Epic 4 | View search history |
| FR27 | Epic 4 | Re-execute from history |
| FR28 | Epic 4 | See selected code in history |
| FR29 | Epic 4 | Clear search history |
| FR30 | Epic 3 | Create account |
| FR31 | Epic 3 | Login |
| FR32 | Epic 3 | Logout |
| FR33 | Epic 3 | Password reset |
| FR34 | Epic 3 | Persistent sessions |
| FR35 | Epic 3 | Role assignment |
| FR36 | Epic 6 | Upload tariff Excel |
| FR37 | Epic 6 | Preview uploaded data |
| FR38 | Epic 6 | Compare changes |
| FR39 | Epic 6 | Activate new data |
| FR40 | Epic 6 | Rollback to previous |
| FR41 | Epic 6 | View upload history |
| FR42 | Epic 6 | Validate Excel format |
| FR43 | Epic 1 | No results feedback |
| FR44 | Epic 5 | Low-confidence suggestions |
| FR45 | Epic 5 | Report data issues |
| FR46 | Epic 1 | System error messages |
| FR47 | Epic 1 | Loading indicators |
| FR48 | Epic 1 | Preserve HS code format |
| FR49 | Epic 1 | Preserve duty rate precision |
| FR50 | Epic 1 | Display policy notes verbatim |
| FR51 | Epic 1 | Persist full lookup details |
| FR52 | Epic 1 | View lookup history list |
| FR53 | Epic 1 | View lookup details and correct |
| FR54 | Epic 2 | Collapsible tariff tree with inline rates |
| FR55 | Epic 2 | View export duty rates |
| FR56 | Epic 2 | View special consumption tax |
| FR57 | Epic 2 | View environmental tax |
| FR58 | Epic 2 | View VAT reduction eligibility |
| FR59 | Epic 2 | Search/filter within tariff browser |
| FR60 | Epic 2 | Jump to chapter quick selector |
| FR61 | Epic 2 | View section/chapter notes |

## Epic List

### Epic 1: Core HS Code Search Experience
Users can search for HS codes in Vietnamese, English, or Chinese and view complete tariff details including duty rates, VAT, and FTA preferential rates. Search is powered by an expert-verified knowledge base with AI fallback for novel queries. This is the MVP - the fundamental value proposition of Athena.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR43, FR46, FR47, FR48, FR49, FR50, FR51, FR52, FR53

**Implementation Notes:**
- Includes project scaffolding from Architecture starter template
- Sets up PostgreSQL + pgvector, hybrid search, FastAPI backend, Next.js frontend
- Builds core UI components: SearchBar, ResultCard, ConfidenceBadge, TariffDetailPanel
- Implements 150ms debounced search with loading skeletons
- **Story 1-2.1 added (2026-02-02):** Fix category context import (deprioritized, no longer blocking)
- **Stories 1-8, 1-9, 1-10 added (2026-02-10):** Knowledge base with human-in-the-loop correction system. Primary search via expert-verified KB, AI search as fallback. Expert correction interface for continuous improvement.
- **Stories 1-11, 1-12, 1-13 added (2026-02-10):** Persist full lookup details (classification, notes, logs) and add lookup history list page + detail page with correction.

### Epic 2: Tariff Schedule Browser (ADDED 2026-02-11)
Users can browse the full tariff schedule as a web-based replacement for the Excel file, with collapsible hierarchy, inline rates (import/export/FTA/taxes), search within browse, and section/chapter notes. Data import is expanded to capture all rate data from the Excel.

**FRs covered:** FR8, FR54, FR55, FR56, FR57, FR58, FR59, FR60, FR61

**Implementation Notes:**
- **Sprint Change Proposal:** `sprint-change-proposal-2026-02-11.md`
- Story 2-1: Expand tariff import (export rates, TTDB, BVMT, RCEP yearly, FTA conditions, export FTAs)
- Story 2-2: Browse API endpoints (sections, chapters, chapter detail with rates, browse search)
- Story 2-3: Tariff Schedule Browser page (collapsible tree, inline rates, search/filter, jump-to-chapter)
- Schema migration: 4 new columns on hs_codes, 4 new columns on fta_rates
- 3 new export FTA agreements imported (CPTPP-XK, EV-XK, UKV-XK)

### Epic 3: User Authentication & Sessions (was Epic 2)
Users can create accounts, log in securely, and maintain persistent sessions across browser sessions. Enables personalization features in subsequent epics.

**FRs covered:** FR30, FR31, FR32, FR33, FR34, FR35

**Implementation Notes:**
- NextAuth.js v5 with credentials provider
- FastAPI JWT validation with fastapi-nextauth-jwt
- Role-based access (user/admin)
- Password reset flow

### Epic 4: Personalization - Favorites & History (was Epic 3)
Users can save frequently-used HS codes to favorites with personal notes, and access their complete search history for quick re-lookups. Completes the daily workflow optimization.

**FRs covered:** FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27, FR28, FR29

**Implementation Notes:**
- FavoriteCard and HistoryItem components from UX spec
- Optimistic UI updates
- Search within favorites
- One-click history re-execution

### Epic 5: Advanced Search & Discovery (was Epic 4, remaining stories)
Users can filter search results by chapter, receive guidance when search results have low confidence, and report data issues. Handles edge cases and ambiguous queries.

**FRs covered:** FR9, FR44, FR45

**Implementation Notes:**
- Chapter filter on search results
- Low-confidence guidance with alternative term suggestions
- Feedback mechanism for reporting data issues
- Note: Hierarchical browsing (FR8) moved to Epic 2

### Epic 6: Admin Data Management (was Epic 5)
Admins can upload new tariff data (Excel), preview changes, activate updates, and rollback if needed. Enables annual tariff updates.

**FRs covered:** FR36, FR37, FR38, FR39, FR40, FR41, FR42

**Implementation Notes:**
- Excel parser service for Vietnam Customs format
- Change detection and preview
- Version management with activation/rollback
- Admin-only access with audit logging

---

## Epic 1: Core HS Code Search Experience

Users can search for HS codes in Vietnamese, English, or Chinese and view complete tariff details including duty rates, VAT, and FTA preferential rates.

### Story 1.1: Project Scaffolding & Infrastructure Setup

As a **developer**,
I want **a fully configured development environment with the project structure and infrastructure ready**,
So that **I can begin building features immediately without setup delays**.

**Acceptance Criteria:**

**Given** a fresh clone of the repository
**When** I run `docker-compose -f docker-compose.dev.yml up -d`
**Then** PostgreSQL (with pgvector extension) and Redis containers start successfully
**And** I can connect to PostgreSQL on port 5432

**Given** the backend setup instructions
**When** I run `cd api && pip install -r requirements.txt && uvicorn app.main:app --reload`
**Then** FastAPI server starts on port 8000
**And** I can access `/health` endpoint returning `{"status": "healthy"}`

**Given** the frontend setup instructions
**When** I run `cd web && npm install && npm run dev`
**Then** Next.js server starts on port 3000
**And** I can see a basic landing page with "Athena" title

**Given** the complete project
**When** I review the folder structure
**Then** it matches the Architecture document structure (web/, api/, nginx/, docker-compose.yml)
**And** Tailwind CSS and shadcn/ui are configured in the frontend
**And** SQLAlchemy with async support is configured in the backend

---

### Story 1.2: HS Code Database Schema & Data Import

As a **developer**,
I want **the database schema for HS codes and tariff data with the full Vietnam Customs 2026 dataset loaded**,
So that **I can develop and test search functionality against the complete production data**.

**Data Source:** `docs/BIEU-THUE-XNK-2026.xlsx` (Vietnam Customs Tariff Schedule 2026)

**Acceptance Criteria:**

**Given** the database is running
**When** I run `alembic upgrade head`
**Then** the following tables are created:
- `hs_codes` (id, code, description_vn, description_en, unit, duty_rate, vat_rate, policy_notes, embedding, data_version_id, created_at)
- `fta_rates` (id, hs_code_id, agreement_code, preferential_rate, conditions)
- `data_versions` (id, name, source_file, uploaded_at, activated_at, is_active)

**Given** the tariff file `docs/BIEU-THUE-XNK-2026.xlsx`
**When** I run the data import script
**Then** all HS codes from the 2026 tariff schedule are imported with their FTA rates
**And** import completes in <5 minutes (NFR-P5)
**And** the data_version is marked as active with name "2026 Tariff Schedule"
**And** HS code formats are preserved exactly (no truncation per FR48)
**And** duty rate decimal precision is preserved (per FR49)
**And** all 20+ FTA agreement rates are imported per code

**Given** HS codes exist in the database
**When** I query for a specific HS code (e.g., "85094010")
**Then** I receive the complete record including VN/EN descriptions, duty rate, VAT, and all FTA rates

---

### Story 1.2.1: Fix Category Context Import (ADDED 2026-02-02)

**Sprint Change Proposal:** `sprint-change-proposal-2026-02-02.md`

As a **developer**,
I want **the tariff import to capture category indicator rows and append context to HS codes**,
So that **search can distinguish between codes like "Other bamboo" vs "Other wood"**.

**Background:**
The Vietnam Customs Excel file contains category indicator rows (e.g., "- Từ tre:" meaning "From bamboo") that group HS codes. The current parser skips these rows because they lack 8-digit codes, causing child HS codes to lose crucial classification context. This results in 0% search accuracy.

**Acceptance Criteria:**

**Given** the Excel row "- Từ tre:" (indent level 1, no 8-digit code)
**When** the parser processes subsequent 8-digit codes at deeper indent levels
**Then** those codes include category context in their description_vn field

**Given** HS code 4419.19.00 (currently "- - Loại khác")
**When** re-import completes
**Then** description becomes "- - Loại khác [Từ tre / Of bamboo]"

**Given** HS code 4419.90.00 (currently "- Loại khác")
**When** re-import completes
**Then** description becomes "- Loại khác [không thuộc tre hoặc gỗ nhiệt đới]"

**Given** the data is re-imported with category context
**When** I search for "Khay chia bát đĩa, gỗ MDF phủ Veneer"
**Then** the search returns 4419.90.00 (not 4419.19.00)

**Given** the data is re-imported with category context
**When** I search for "Bộ trộn nước nóng lạnh cho vòi sen, bằng đồng"
**Then** the search returns 7418.20.00 (not 8481.80.98)

**Given** embeddings are regenerated
**When** I run `python -m app.scripts.generate_embeddings --force-regenerate`
**Then** all 11,871 HS codes have embeddings that include category context

**Technical Tasks:**

1. Modify `api/app/services/tariff_hierarchy_parser.py`:
   - Add `category_stack: list[tuple[int, str]]` to track (indent_level, category_name)
   - When encountering a row with description but no 8-digit code and starts with "- ": push to stack
   - When indent level decreases: pop categories at higher indent levels
   - When creating HSCodeData: append category context from stack to description_vn

2. Re-import tariff data:
   ```bash
   docker exec athena-api python -m app.scripts.import_tariff_hierarchy
   ```

3. Regenerate all embeddings:
   ```bash
   docker exec athena-api python -m app.scripts.generate_embeddings --force-regenerate
   ```

4. Clear all caches:
   ```bash
   docker exec athena-redis redis-cli FLUSHALL
   ```

5. Validate with test queries (target: >50% improvement from 0% baseline)

**Definition of Done:**
- [ ] Parser captures category indicator rows
- [ ] Category context appended to child HS code descriptions
- [ ] Data re-imported successfully
- [ ] Embeddings regenerated (11,871 codes)
- [ ] Caches cleared
- [ ] MDF kitchenware query returns 4419.90.00
- [ ] Copper mixer query returns 7418.20.00
- [ ] At least 10 test queries validated

---

### Story 1.3: Search API with Hybrid Search & Customs Classification Analysis

As a **user**,
I want **to search for HS codes using detailed product descriptions in any language and receive comprehensive customs classification analysis**,
So that **I can understand not just the HS code, but the reasoning behind the classification**.

**Acceptance Criteria:**

**Given** I am a user with a detailed Vietnamese product description
**When** I send POST `/api/search` with `{"query": "Thanh treo khăn MITO, mã A2018ANE, bằng đồng mạ chrome, kích thước 33,5x8cm, nhà sản xuất INDA S.p.a, hàng mới 100%"}`
**Then** I receive a customs classification analysis response
**And** response time is <3 seconds (NFR-P1)
**And** response format includes:
```json
{
  "success": true,
  "data": {
    "hsCode": "7418.20.00",
    "description": "Đồ trang bị trong nhà vệ sinh và các bộ phận của chúng (bằng đồng)",
    "dutyRate": "30%",
    "vatRate": "8% hoặc 10%",
    "classification": {
      "material": "Sản phẩm được làm bằng đồng (bao gồm cả hợp kim đồng như đồng thau - brass), dù có mạ chrome thì vẫn được phân loại theo kim loại cơ bản là đồng thuộc Chương 74 (\"Đồng và các sản phẩm bằng đồng\").",
      "function": "Thanh treo khăn là một thiết bị/phụ kiện dùng trong nhà tắm. Theo Danh mục thuế, Nhóm 74.18 bao gồm: \"Bộ đồ ăn, đồ nhà bếp... và đồ trang bị trong nhà vệ sinh và các bộ phận của chúng, bằng đồng\". Trong nhóm này, mã 7418.20.00 được dành riêng cho \"Đồ trang bị trong nhà vệ sinh và các bộ phận của chúng\"."
    },
    "practicalNotes": [
      "Hàng mới 100%: Sản phẩm là hàng mới nên đủ điều kiện nhập khẩu. Trong biểu thuế có ghi chú chính sách quản lý đối với hàng tiêu dùng đã qua sử dụng (cấm nhập khẩu), nhưng không áp dụng với hàng của bạn.",
      "Chính sách thuế: Mức thuế nhập khẩu MFN cho mã này khá cao (30%). Nếu hàng hóa có C/O (Chứng nhận xuất xứ) từ các nước có hiệp định thương mại tự do với Việt Nam (như Châu Âu - EVFTA, hoặc các nước ASEAN, v.v.), bạn nên xuất trình để được hưởng mức thuế ưu đãi đặc biệt thấp hơn."
    ],
    "confidence": 95
  }
}
```

**Given** I search with a simple Vietnamese description
**When** I send POST `/api/search` with `{"query": "máy xay sinh tố"}`
**Then** I receive customs classification analysis with material analysis and function explanation
**And** the system extracts key features from the query to determine material and function

**Given** I search with an English description
**When** I send POST `/api/search` with `{"query": "copper bathroom towel rack, chrome plated, 33.5x8cm"}`
**Then** I receive relevant classification analysis with reasoning in Vietnamese (per NFR-I3)
**And** the analysis includes material classification and functional categorization

**Given** I search with a Chinese description
**When** I send POST `/api/search` with `{"query": "铜制浴室毛巾架，镀铬"}`
**Then** I receive relevant classification analysis (best effort per Architecture)

**Given** I search with an exact HS code
**When** I send POST `/api/search` with `{"query": "7418.20.00"}`
**Then** I receive that exact HS code with 100% confidence (FR4)
**And** the response includes full classification reasoning and practical notes

**Given** I search with a query that has no matches
**When** I send POST `/api/search` with `{"query": "xyznonexistent123"}`
**Then** I receive error response with guidance
**And** the response includes `{"success": false, "error": {"message": "No matching HS code found. Try using more specific product details (material, function, industry)"}}`

**Technical Implementation Notes:**
- The API must analyze the input query to extract: material, dimensions, manufacturer details, condition (new/used)
- Classification reasoning must reference the Vietnam Customs tariff structure (Chương/Nhóm)
- Practical notes should include: import eligibility based on condition, FTA optimization opportunities
- Material-based classification takes precedence over surface treatment (e.g., copper base vs chrome plating)

---

### Story 1.4: Search Page UI - SearchBar Component

As a **user**,
I want **a prominent search bar that accepts my input in any language**,
So that **I can quickly enter product descriptions without switching modes**.

**Acceptance Criteria:**

**Given** I navigate to the search page (`/search`)
**When** the page loads
**Then** the search bar is auto-focused and ready for input
**And** page loads in <4 seconds (NFR-P2)

**Given** I am on the search page
**When** I type a product description
**Then** search is triggered after 150ms debounce (UX spec)
**And** a loading indicator appears during search (FR47)

**Given** I type Vietnamese text with diacritics (e.g., "máy xay")
**When** I submit the search
**Then** the characters are handled correctly (NFR-I2)

**Given** I want to clear my search
**When** I click the clear button or press Escape
**Then** the search input is cleared
**And** previous results are removed

**Given** I am a power user
**When** I press "/" or Cmd+K anywhere on the page
**Then** the search bar receives focus (UX keyboard shortcuts)

---

### Story 1.5: Search Results Display

As a **user**,
I want **to see search results with clear confidence indicators**,
So that **I can quickly identify the most likely correct HS code**.

**Acceptance Criteria:**

**Given** I have searched for a product description
**When** results are returned
**Then** I see ResultCard components for each result
**And** results are ordered by confidence score (highest first) (FR5)
**And** I can view 10+ results without scrolling (NFR-U2)

**Given** a search result with 80-100% confidence
**When** it is displayed
**Then** I see a green ConfidenceBadge labeled "High Match" (FR6)

**Given** a search result with 50-79% confidence
**When** it is displayed
**Then** I see a yellow ConfidenceBadge labeled "Possible Match"

**Given** a search result with <50% confidence
**When** it is displayed
**Then** I see a red ConfidenceBadge labeled "Low Match - Verify"

**Given** each ResultCard
**When** I view it
**Then** I see the HS code (monospace font), Vietnamese description, English description, and confidence badge
**And** descriptions are truncated with expand option if too long

**Given** I search and no results are found
**When** results are displayed
**Then** I see a friendly "No HS codes match your search" message (FR43)
**And** I see suggestions to refine my search terms

---

### Story 1.6: HS Code Detail View

As a **user**,
I want **to view complete tariff details for any HS code**,
So that **I can see duty rates, FTA rates, and policy notes for customs declarations**.

**Acceptance Criteria:**

**Given** I see search results
**When** I click on a ResultCard (or press Enter on focused result)
**Then** TariffDetailPanel opens showing full details
**And** detail retrieval is <1 second (NFR-P3)

**Given** I am viewing TariffDetailPanel
**When** I look at the Overview tab
**Then** I see:
- 8-digit HS code in monospace font (FR10)
- Vietnamese description (FR11)
- English description (FR12)
- Unit of measure (FR13)
- Standard import duty rate with decimal precision (FR14, FR49)
- VAT rate (FR15)
- Data version and effective date (FR18)

**Given** I am viewing TariffDetailPanel
**When** I click the "FTA Rates" tab
**Then** I see an accordion with all FTA preferential rates (FR16)
**And** agreements include CPTPP, EVFTA, RCEP, ACFTA, AKFTA, AJCEP, VKFTA, and others

**Given** I am viewing TariffDetailPanel
**When** I click the "Policy Notes" tab
**Then** I see policy notes and restrictions displayed verbatim (FR17, FR50)

**Given** I am viewing TariffDetailPanel
**When** I want to copy the HS code
**Then** I can click a copy button to copy the formatted code to clipboard

---

### Story 1.7: Error Handling & System Feedback

As a **user**,
I want **clear feedback when things go wrong or are loading**,
So that **I understand the system state and can take appropriate action**.

**Acceptance Criteria:**

**Given** the search API is unavailable
**When** I attempt to search
**Then** I see a user-friendly error message (FR46)
**And** the error follows RFC 7807 format with actionable guidance
**And** I can retry the search

**Given** the page is loading
**When** I wait for content
**Then** I see skeleton loaders for the search results area (UX spec)
**And** the skeleton provides visual feedback without blocking

**Given** I trigger multiple rapid searches
**When** responses arrive out of order
**Then** only the most recent search results are displayed
**And** stale results are discarded

**Given** there is a network timeout
**When** the search fails
**Then** I see "Search timed out. Please try again."
**And** I can retry without refreshing the page

---

### Story 1.8: Knowledge Base Schema & Lookup Storage (ADDED 2026-02-10)

**Sprint Change Proposal:** `sprint-change-proposal-2026-02-10.md`

As a **developer**,
I want **a knowledge base that stores every user lookup with a field for expert correction**,
So that **verified human classifications can enhance future search results**.

**Background:**
Three attempts at AI-based search (vector embeddings, category context enrichment, LLM query enhancement + reranking) all failed at 0% accuracy. HS code classification requires specialized domain expertise that general-purpose AI cannot replicate. This story creates the foundation for a knowledge base where expert-verified classifications become the primary search mechanism.

**Acceptance Criteria:**

**Given** the database is running
**When** I run the migration
**Then** the `lookup_records` table is created with columns: id, query_text, query_hash, query_language, matched_hs_code_id, correct_hs_code_id, is_verified, verified_by_user_id, verified_at, confidence_score, search_method, notes, created_at, updated_at

**Given** a user performs a search via POST /api/search
**When** results are returned
**Then** a lookup_record is automatically created with query_text, matched_hs_code_id, is_verified=false

**Given** duplicate queries within 24 hours
**When** the same query text is searched again
**Then** no duplicate lookup_record is created (deduplicate by query_hash)

**Given** the lookup_records table has data
**When** I query for unverified records
**Then** I can retrieve all records where is_verified = false, ordered by created_at descending

**Technical Tasks:**
1. Create SQLAlchemy model: `api/app/models/lookup_record.py`
2. Create Alembic migration for `lookup_records` table with indexes (query_hash, is_verified, query_text pg_trgm)
3. Create repository: `api/app/repositories/lookup_record_repository.py`
4. Integrate lookup storage into search API endpoint
5. Add deduplication logic by query_hash (24hr window)

**Definition of Done:**
- [ ] lookup_records table created with all columns and indexes
- [ ] Every search auto-creates a lookup_record
- [ ] Duplicate queries within 24hrs are deduplicated
- [ ] Unverified records retrievable and sortable

---

### Story 1.9: Knowledge-Enhanced Search (ADDED 2026-02-10)

**Sprint Change Proposal:** `sprint-change-proposal-2026-02-10.md`

As a **user**,
I want **my searches to return expert-verified results when available**,
So that **I get accurate HS codes based on real expert knowledge, not just AI guesses**.

**Acceptance Criteria:**

**Given** an expert has previously verified a query -> HS code mapping
**When** another user searches with the same query text
**Then** the verified HS code is returned with source: "knowledge_base" and confidence: 100

**Given** an expert has verified a similar (but not exact) query
**When** a user searches with similar text (pg_trgm similarity >= 0.85)
**Then** the system returns the verified HS code with high confidence

**Given** no verified match exists in the knowledge base
**When** a user searches for a product description
**Then** the system falls back to vector/fuzzy/LLM search
**And** results are marked with source: "ai_suggestion"

**Given** the search flow processes a query
**Then** the system checks in this order:
1. Exact match in verified KB (query_hash, <50ms)
2. Similar match in verified KB (pg_trgm >= 0.85, <100ms)
3. Fallback to vector search + LLM (existing pipeline, ~2-3s)

**Technical Tasks:**
1. Create service: `api/app/services/knowledge_base_service.py`
2. Implement exact match lookup by query_hash
3. Implement similarity match using pg_trgm on query_text
4. Integrate KB lookup as first step in search API (before vector search)
5. Add `source`, `isVerified`, `verifiedBy`, `verifiedAt` fields to search response schema
6. Write tests for KB hit and miss scenarios

**Definition of Done:**
- [ ] KB exact match returns verified results in <50ms
- [ ] KB similar match returns verified results in <100ms
- [ ] AI fallback works when no KB match exists
- [ ] Response includes source and verification metadata
- [ ] All searches still create lookup_records

**Dependency:** Story 1-8 must be complete

---

### Story 1.10: Anonymous Correction Interface (ADDED 2026-02-10, MODIFIED 2026-02-10)

**Sprint Change Proposal:** `sprint-change-proposal-2026-02-10-story-1-10-anonymous-corrections.md`

As **anyone using the search**,
I want **to submit corrections when the system suggests the wrong HS code**,
So that **the knowledge base improves with real-world feedback**.

**Acceptance Criteria:**

**Given** I am on the search results page
**When** I see an incorrect HS code suggestion
**Then** I can click "Suggest Correction" without logging in

**Given** I click "Suggest Correction"
**When** the correction panel opens
**Then** I can search for the correct HS code and submit with optional notes

**Given** I submit a correction
**When** the submission succeeds
**Then** I see "Thanks! Your correction will help improve search quality"
**And** the correction is immediately available in the knowledge base

**Given** I try to submit multiple corrections quickly
**When** I exceed 10 corrections per hour
**Then** I see "Rate limit reached - please try again later"

**API Endpoints:**
- GET /api/corrections/lookups         # Public, rate-limited
- POST /api/corrections                 # Public, rate-limited
  Body: { lookup_id, correct_hs_code_id, notes? }

**Technical Tasks:**
1. Create API router: `api/app/api/corrections.py` (public endpoints)
2. Add rate limiting: 10 corrections per IP per hour
3. Remove expert role from user model (keep user/admin only)
4. Build CorrectionButton component (inline on ResultCard)
5. Build CorrectionPanel component (slide-in from search page)
6. Auto-verify corrections for MVP (is_verified = true)
7. Delete `/expert/review` page and components

**Frontend Integration:**
- Add "Suggest Correction" to each ResultCard
- CorrectionPanel with HS code autocomplete
- Success toast notification

**Definition of Done:**
- [ ] Anyone can submit corrections without login
- [ ] Corrections rate-limited (10/hour per IP)
- [ ] Corrections immediately improve search
- [ ] No expert role in database or auth system
- [ ] No /expert/review page exists

**Dependency:** Story 1-8, 1-9 must be complete.

---

### Story 1.11: Persist Full Lookup Details (ADDED 2026-02-10)

**Sprint Change Proposal:** `sprint-change-proposal-2026-02-10-lookup-history.md`

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

### Story 1.12: Lookup History API & List Page (ADDED 2026-02-10)

**Sprint Change Proposal:** `sprint-change-proposal-2026-02-10-lookup-history.md`

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

### Story 1.13: Lookup Detail Page (ADDED 2026-02-10)

**Sprint Change Proposal:** `sprint-change-proposal-2026-02-10-lookup-history.md`

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

## Epic 2: Tariff Schedule Browser (ADDED 2026-02-11)

Users can browse the full tariff schedule as a web-based replacement for the Excel file, with collapsible hierarchy, inline rates, and search within browse.

### Story 2.1: Expand Tariff Import with Export Rates, Taxes, and FTA Conditions

**Sprint Change Proposal:** `sprint-change-proposal-2026-02-11.md`

As a **developer**,
I want **the tariff import to capture all rate data from the Excel including export rates, taxes, and FTA conditions**,
So that **the tariff browser can display complete data and fully replace the Excel file**.

**Background:**
The current import captures import duty, VAT, 18 FTA import rates, and policy notes. Missing data includes: export duty rates, special consumption tax (TTDB), environmental protection tax (BVMT), VAT reduction indicators, RCEP year-by-year rates, FTA conditions, and export FTA rates (CPTPP-XK, EV-XK, UKV-XK).

**Acceptance Criteria:**

**Given** the database is running
**When** I run the new migration
**Then** the `hs_codes` table gains 4 new columns:
- `export_duty_rate` (NUMERIC, nullable) — from Excel col CG (85)
- `special_consumption_tax` (VARCHAR, nullable) — from Excel col CD (82)
- `environmental_tax` (VARCHAR, nullable) — from Excel col CS (97)
- `vat_reduction` (VARCHAR, nullable) — from Excel col CW (101)

**Given** the database is running
**When** I run the new migration
**Then** the `fta_rates` table gains 4 new columns:
- `rate_year` (INTEGER, nullable) — for RCEP yearly rates (2022-2027)
- `is_export` (BOOLEAN, default false) — distinguish import vs export FTA
- `legal_document` (VARCHAR, nullable) — e.g., "118/2022/NĐ-CP"
- `effective_date` (VARCHAR, nullable) — e.g., "30/12/2022"

**Given** the updated parser and Excel file
**When** I run the data import script
**Then** all HS codes include export_duty_rate, special_consumption_tax, environmental_tax, vat_reduction where present in Excel
**And** FTA conditions field is populated (no longer always NULL)
**And** RCEP yearly rates are stored with rate_year values (2022-2027)
**And** Export FTA rates from CPTPP-XK, EV-XK, UKV-XK sheets are imported with is_export=true
**And** Legal document and effective date are captured per FTA rate
**And** All existing functionality is unchanged

**Technical Tasks:**
1. Create Alembic migration adding columns to `hs_codes` and `fta_rates`
2. Update SQLAlchemy models with new columns
3. Update `tariff_hierarchy_parser.py` to read Excel columns CD, CG, CJ-CR, CS, CW
4. Update parser to populate FTA `conditions` field
5. Add RCEP yearly rate parsing (columns BT-BX with year headers from row 7)
6. Add export FTA sheet parsing (CPTPP-XK, EV-XK, UKV-XK sheets)
7. Capture legal_document and effective_date per FTA rate
8. Re-import all data
9. Write tests for new columns and rate types

**Definition of Done:**
- [ ] Migration adds 4 columns to hs_codes and 4 columns to fta_rates
- [ ] Parser reads all new Excel columns
- [ ] FTA conditions populated where present
- [ ] RCEP yearly rates stored with rate_year
- [ ] Export FTA rates imported with is_export=true
- [ ] Legal documents and effective dates captured
- [ ] Full re-import completes successfully
- [ ] Existing search and lookup features unchanged

---

### Story 2.2: Tariff Browse API Endpoints

**Sprint Change Proposal:** `sprint-change-proposal-2026-02-11.md`

As a **developer**,
I want **dedicated API endpoints for browsing the tariff hierarchy with inline rate data**,
So that **the frontend tariff browser page can efficiently load and display the schedule**.

**Acceptance Criteria:**

**Given** the API is running
**When** I call GET /api/browse/sections
**Then** I receive all 20 sections with section_number, section_roman, name_vn, name_en, and chapter_count
**And** response follows envelope format `{success, data, error}`

**Given** a section exists
**When** I call GET /api/browse/chapters?section_id={id}
**Then** I receive all chapters in that section with chapter_code, name_vn, name_en, heading_count, hs_code_count
**And** section notes_vn and notes_en are included

**Given** a chapter exists
**When** I call GET /api/browse/chapters/{chapter_code}
**Then** I receive the full chapter hierarchy: headings → subheadings → HS codes
**And** each HS code includes: code, description_vn, description_en, unit, duty_rate, vat_rate, export_duty_rate, special_consumption_tax, environmental_tax, vat_reduction, policy_notes
**And** each HS code includes nested FTA rates (all agreements with preferential_rate, conditions, rate_year, is_export)
**And** chapter notes_vn and notes_en are included
**And** response is paginated if chapter has >500 codes

**Given** I want to search within the tariff browser
**When** I call GET /api/browse/search?q={text}&chapter={code}
**Then** I receive matching HS codes via pg_trgm text search on description_vn/description_en + exact code match
**And** optional chapter filter narrows results
**And** each result includes hierarchy path (section → chapter → heading) + inline rates

**Technical Tasks:**
1. Create route handler: `api/app/api/browse.py`
2. Create service: `api/app/services/browse_service.py`
3. Create repository: `api/app/repositories/browse_repository.py`
4. Create response schemas in `api/app/schemas/browse.py`
5. Register router in `api/app/main.py`
6. Optimize queries with appropriate JOINs and eager loading
7. Add pagination for large chapters
8. Write tests for all endpoints

**Definition of Done:**
- [ ] GET /api/browse/sections returns all sections with counts
- [ ] GET /api/browse/chapters returns chapters with counts and notes
- [ ] GET /api/browse/chapters/{code} returns full hierarchy with inline rates
- [ ] GET /api/browse/search returns filtered results with hierarchy path
- [ ] Pagination works for large chapters
- [ ] All endpoints follow envelope response format
- [ ] Tests pass for all endpoints

**Dependency:** Story 2-1 must be complete.

---

### Story 2.3: Tariff Schedule Browser Page

**Sprint Change Proposal:** `sprint-change-proposal-2026-02-11.md`

As a **user**,
I want **a web page where I can browse the full tariff schedule with hierarchy and FTA rates**,
So that **I no longer need to open the Excel file to find and explore HS codes**.

**Acceptance Criteria:**

**Given** I navigate to /browse
**When** the page loads
**Then** I see all 20 HS sections as expandable items showing section name (VN/EN) and chapter count

**Given** I am viewing sections
**When** I click/expand a section
**Then** I see all chapters within that section with chapter code, name, and HS code count
**And** section notes are displayed as expandable info panel

**Given** I am viewing chapters
**When** I click/expand a chapter
**Then** I see the full hierarchy: headings → subheadings → 8-digit codes
**And** chapter notes are displayed
**And** each HS code row shows inline: code, description (VN), import duty, VAT, export duty

**Given** I am viewing HS code rows
**When** I click/expand an HS code
**Then** I see the expanded detail: English description, unit, all FTA rates (grouped by import/export), special consumption tax, environmental tax, VAT reduction, policy notes

**Given** I want to find a specific chapter quickly
**When** I use the "Jump to chapter" dropdown
**Then** I can select any of the 98 chapters and the browser scrolls/navigates to it

**Given** I want to search within the tariff browser
**When** I type in the browse search bar
**Then** results are filtered in real-time matching code or description text
**And** matching codes show their hierarchy path

**Given** I am on a mobile/tablet device
**When** I view the browse page
**Then** the layout is responsive (stacked view on narrow screens, horizontal scroll for rate columns on tablet)

**Given** a chapter has many HS codes
**When** I expand it
**Then** codes load progressively (lazy loading / virtual scroll) for smooth performance

**Technical Tasks:**
1. Build frontend page: `web/src/app/browse/page.tsx`
2. Build SectionList component
3. Build ChapterView component with collapsible tree
4. Build HSCodeRow component with inline rates
5. Build HSCodeDetail expandable panel with FTA rates table
6. Build ChapterJumper dropdown component
7. Build BrowseSearch component with pg_trgm-backed search
8. Add /browse to sidebar/header navigation
9. Implement lazy loading for large chapters
10. Add keyboard navigation (arrow keys, Enter to expand/collapse)

**Definition of Done:**
- [ ] /browse page displays all 20 sections
- [ ] Sections expand to show chapters with counts
- [ ] Chapters expand to show full hierarchy with inline rates
- [ ] HS code rows show import duty, VAT, export duty inline
- [ ] HS code expansion shows all FTA rates, taxes, policy notes
- [ ] Jump-to-chapter selector works
- [ ] Search within browse works (code + description)
- [ ] Responsive layout for desktop and tablet
- [ ] Lazy loading for large chapters
- [ ] Navigation link added to sidebar/header
- [ ] Keyboard navigation functional

**Dependency:** Story 2-2 must be complete.

---

## Epic 3: User Authentication & Sessions (was Epic 2)

Users can create accounts, log in securely, and maintain persistent sessions across browser sessions.

### Story 3.1: User Registration (was Story 2.1)

As a **new user**,
I want **to create an account with my email and password**,
So that **I can access personalized features like favorites and history**.

**Acceptance Criteria:**

**Given** I am on the registration page (`/register`)
**When** I enter a valid email and password (min 8 characters)
**Then** my account is created successfully
**And** I am automatically logged in
**And** I am redirected to the search page

**Given** I try to register with an existing email
**When** I submit the registration form
**Then** I see an error message "Email already registered"
**And** I am prompted to log in instead

**Given** I enter an invalid email format
**When** I submit the registration form
**Then** I see validation error "Please enter a valid email address"
**And** the form is not submitted

**Given** I enter a password shorter than 8 characters
**When** I submit the registration form
**Then** I see validation error "Password must be at least 8 characters"

**Given** I register successfully
**When** my account is created
**Then** my password is hashed with bcrypt (cost factor >=10) (NFR-SEC2)
**And** I am assigned the "user" role by default

---

### Story 3.2: User Login (was Story 2.2)

As a **registered user**,
I want **to log in with my email and password**,
So that **I can access my personal favorites and search history**.

**Acceptance Criteria:**

**Given** I am on the login page (`/login`)
**When** I enter valid credentials
**Then** I am logged in successfully
**And** a JWT is created with 24-hour expiry (NFR-SEC3)
**And** I am redirected to the search page

**Given** I enter incorrect credentials
**When** I submit the login form
**Then** I see error message "Invalid email or password"
**And** I am not logged in

**Given** I am logged in
**When** I navigate to protected pages (favorites, history)
**Then** I can access them without re-authenticating

**Given** I am not logged in
**When** I try to access protected pages
**Then** I am redirected to the login page
**And** after login, I am redirected back to my intended destination

**Given** I am logged in
**When** I close and reopen the browser
**Then** my session is maintained (FR34)
**And** I don't need to log in again until token expires

---

### Story 3.3: User Logout (was Story 2.3)

As a **logged-in user**,
I want **to log out of the system**,
So that **I can secure my account on shared devices**.

**Acceptance Criteria:**

**Given** I am logged in
**When** I click the logout button in the user menu
**Then** I am logged out immediately
**And** my JWT is invalidated
**And** I am redirected to the login page

**Given** I have logged out
**When** I try to access protected pages
**Then** I am redirected to the login page

**Given** I am logged out
**When** I use the back button to navigate to a protected page
**Then** I am still redirected to login (no cached access)

---

### Story 3.4: Password Reset (was Story 2.4)

As a **user who forgot my password**,
I want **to reset my password via email**,
So that **I can regain access to my account**.

**Acceptance Criteria:**

**Given** I am on the forgot password page (`/forgot-password`)
**When** I enter my registered email
**Then** I see "If this email exists, a reset link has been sent"
**And** a password reset email is sent (if email exists)

**Given** I receive a password reset email
**When** I click the reset link
**Then** I am taken to a password reset form
**And** the link is valid for 1 hour

**Given** I am on the password reset form
**When** I enter a new password (min 8 characters) and confirm it
**Then** my password is updated
**And** I am redirected to login with a success message

**Given** I use an expired or invalid reset link
**When** I try to reset my password
**Then** I see "This reset link has expired or is invalid"
**And** I am prompted to request a new reset link

**Given** I enter mismatched passwords
**When** I submit the reset form
**Then** I see "Passwords do not match"

---

### Story 3.5: Role-Based Access Control (was Story 2.5)

As an **administrator**,
I want **to assign roles to users**,
So that **I can control who has admin access to data management**.

**Acceptance Criteria:**

**Given** I am an admin user
**When** I access the admin area (`/admin`)
**Then** I can see the admin dashboard
**And** I have access to data management features

**Given** I am a standard user
**When** I try to access the admin area
**Then** I am shown "Access Denied" message
**And** I am redirected to the search page

**Given** I am an admin
**When** I view the user management section
**Then** I can see a list of users with their roles
**And** I can change a user's role from "user" to "admin" or vice versa (FR35)

**Given** an admin changes a user's role
**When** the change is saved
**Then** the action is logged with timestamp and admin ID (NFR-SEC5)
**And** the user's permissions are updated immediately

**Given** the users table
**When** I check its structure
**Then** it includes: id, email, password_hash, role, created_at

---

## Epic 4: Personalization - Favorites & History (was Epic 3)

Users can save frequently-used HS codes to favorites with personal notes, and access their complete search history for quick re-lookups.

### Story 4.1: Save HS Code to Favorites (was Story 3.1)

As a **logged-in user**,
I want **to save an HS code to my favorites**,
So that **I can quickly access frequently-used codes**.

**Acceptance Criteria:**

**Given** I am viewing an HS code detail (TariffDetailPanel)
**When** I click the star/favorite icon
**Then** the HS code is added to my favorites
**And** the star icon changes to filled/active state
**And** I see a toast notification "Added to favorites"

**Given** I am viewing search results
**When** I click the star icon on a ResultCard
**Then** the HS code is added to my favorites without opening details
**And** the action is optimistic (immediate UI feedback)

**Given** the favorites database table
**When** I check its structure
**Then** it includes: id, user_id, hs_code_id, notes, created_at

**Given** I try to favorite an already-favorited code
**When** I click the star icon
**Then** the code is removed from favorites (toggle behavior)
**And** I see toast "Removed from favorites"

---

### Story 4.2: Add Notes to Favorites (was Story 3.2)

As a **logged-in user**,
I want **to add personal notes to my favorited HS codes**,
So that **I can remember why I saved them or add context**.

**Acceptance Criteria:**

**Given** I am viewing my favorites list
**When** I click on a FavoriteCard
**Then** I can see and edit the notes field (FR20)

**Given** I have a favorite without notes
**When** I add a note and save
**Then** the note is persisted
**And** I see the note preview on the FavoriteCard

**Given** I have a favorite with existing notes
**When** I edit the note and save
**Then** the note is updated
**And** I see toast "Note updated"

**Given** I am viewing a favorited HS code in TariffDetailPanel
**When** I look at the panel
**Then** I can see my saved notes for this code
**And** I can edit notes directly from the detail view

---

### Story 4.3: View and Manage Favorites List (was Story 3.3)

As a **logged-in user**,
I want **to view and manage my complete favorites list**,
So that **I can quickly access my saved HS codes**.

**Acceptance Criteria:**

**Given** I am logged in
**When** I navigate to the Favorites page (`/favorites`)
**Then** I see a list of all my favorited HS codes (FR21)
**And** the list loads in <2 seconds (NFR-P4)

**Given** I have favorites
**When** I view the favorites list
**Then** each FavoriteCard shows: HS code, description preview, note preview, date added
**And** I can click to view full details

**Given** I want to remove a favorite
**When** I click the remove/unfavorite button
**Then** the HS code is removed from my favorites (FR22)
**And** I see toast "Removed from favorites" with undo option

**Given** I accidentally remove a favorite
**When** I click "Undo" in the toast (within 5 seconds)
**Then** the favorite is restored

**Given** I have no favorites
**When** I view the favorites page
**Then** I see empty state "No favorites yet. Save HS codes for quick access."
**And** I see a link to start searching

---

### Story 4.4: Search Within Favorites (was Story 3.4)

As a **logged-in user**,
I want **to search within my favorites**,
So that **I can quickly find a specific saved code**.

**Acceptance Criteria:**

**Given** I am on the favorites page
**When** I type in the favorites search box
**Then** favorites are filtered in real-time (FR23)
**And** filtering happens client-side for speed

**Given** I search within favorites
**When** I type a partial HS code or description
**Then** matching favorites are displayed
**And** non-matching favorites are hidden

**Given** I search within favorites and find no matches
**When** results are displayed
**Then** I see "No favorites match your search"

**Given** I clear the favorites search
**When** I click clear or delete text
**Then** all favorites are shown again

---

### Story 4.5: Quick Favorites Access During Search (was Story 3.5)

As a **logged-in user**,
I want **to quickly access my favorites while searching**,
So that **I can reference saved codes without leaving the search workflow**.

**Acceptance Criteria:**

**Given** I am on the search page
**When** I look at the sidebar (desktop) or navigation
**Then** I see a "Favorites" quick access section (FR24)
**And** my most recent 5 favorites are shown

**Given** I am searching and see my favorites in the sidebar
**When** I click a favorite
**Then** the HS code detail panel opens
**And** my search context is preserved

**Given** I am on mobile/tablet
**When** I want to access favorites during search
**Then** I can tap the favorites tab in bottom navigation
**And** switch back to search results easily

---

### Story 4.6: Automatic Search History Recording (was Story 3.6)

As a **logged-in user**,
I want **my searches to be recorded automatically**,
So that **I can review and re-use past searches**.

**Acceptance Criteria:**

**Given** I am logged in and perform a search
**When** results are displayed
**Then** my search query is automatically recorded (FR25)
**And** the timestamp is saved

**Given** I select an HS code from search results
**When** I click on a result
**Then** the selected HS code is recorded with the search (FR28)

**Given** the search_history database table
**When** I check its structure
**Then** it includes: id, user_id, query, selected_hs_code_id, created_at

**Given** I search but don't select any result
**When** the history is saved
**Then** selected_hs_code_id is null

**Given** I am not logged in
**When** I perform a search
**Then** history is not recorded (requires authentication)

---

### Story 4.7: View and Re-execute Search History (was Story 3.7)

As a **logged-in user**,
I want **to view my search history and re-execute past searches**,
So that **I can quickly repeat common lookups**.

**Acceptance Criteria:**

**Given** I am logged in
**When** I navigate to the History page (`/history`)
**Then** I see my recent searches in reverse chronological order (FR26)
**And** the list loads in <2 seconds (NFR-P4)

**Given** I view my search history
**When** I look at each HistoryItem
**Then** I see: search query, selected HS code (if any), timestamp
**And** I can see which code I selected for each search (FR28)

**Given** I want to repeat a search
**When** I click on a HistoryItem
**Then** the search is re-executed with the same query (FR27)
**And** I am taken to the search page with results

**Given** I have no search history
**When** I view the history page
**Then** I see empty state "No search history yet. Your searches will appear here."

---

### Story 4.8: Clear Search History (was Story 3.8)

As a **logged-in user**,
I want **to clear my search history**,
So that **I can maintain privacy or remove clutter**.

**Acceptance Criteria:**

**Given** I am on the history page
**When** I click "Clear All History"
**Then** I see a confirmation dialog "Are you sure? This cannot be undone."

**Given** I confirm clearing history
**When** the action completes
**Then** all my search history is deleted (FR29)
**And** I see empty state on history page
**And** I see toast "History cleared"

**Given** I cancel the clear confirmation
**When** I click "Cancel"
**Then** my history is preserved
**And** the dialog closes

**Given** I want to delete a single history item
**When** I click the delete icon on a HistoryItem
**Then** only that item is removed
**And** I see toast "Search removed from history"

---

## Epic 5: Advanced Search & Discovery (was Epic 4)

Users can filter search results by chapter, receive guidance when search results have low confidence, and report data issues. Handles edge cases and ambiguous queries.

> **Note:** Story 4.1 (Hierarchical HS Code Browser) has been moved to Epic 2 as Stories 2.2 and 2.3 (Sprint Change 2026-02-11).

### Story 5.1: Chapter Filter on Search Results (was Story 4.2)

As a **user**,
I want **to filter search results by HS code chapter**,
So that **I can narrow down results when I know the general category**.

**Acceptance Criteria:**

**Given** I have search results displayed
**When** I look at the filter options
**Then** I see a "Filter by Chapter" dropdown (FR9)
**And** chapters shown are only those present in current results

**Given** I select a chapter filter (e.g., "Chapter 85")
**When** the filter is applied
**Then** only results from that chapter are shown
**And** the result count updates
**And** I see a filter badge showing active filter

**Given** I have a chapter filter active
**When** I click the clear filter button or "X" on the badge
**Then** all results are shown again

**Given** I search with a filter already active
**When** new results are returned
**Then** the filter is cleared
**And** I see all new results

**Given** multiple chapters exist in results
**When** I view the filter dropdown
**Then** chapters are sorted by HS code number
**And** each shows a count of matching results

---

### Story 5.2: Low-Confidence Search Guidance (was Story 4.3)

As a **user**,
I want **to receive guidance when search results have low confidence**,
So that **I can refine my search or try alternative approaches**.

**Acceptance Criteria:**

**Given** I search and all results have <50% confidence
**When** results are displayed
**Then** I see a guidance banner at the top (FR44)
**And** the banner suggests: "Results have low confidence. Try:"

**Given** I see the low-confidence guidance
**When** I read the suggestions
**Then** I see options like:
- "Use more specific terms"
- "Try the English/Vietnamese equivalent"
- "Browse by category"
- Suggested alternative search terms based on my query

**Given** the system suggests alternative terms
**When** I click on a suggested term
**Then** a new search is executed with that term

**Given** I search and the top result has high confidence but others are low
**When** results are displayed
**Then** the guidance banner is not shown (top result is confident)

**Given** I dismiss the guidance banner
**When** I click "X" or "Got it"
**Then** the banner is hidden for this search session
**And** it appears again on next low-confidence search

---

### Story 5.3: Data Feedback Mechanism (was Story 4.4)

As a **user**,
I want **to report incorrect or missing HS code data**,
So that **administrators can improve the data quality**.

**Acceptance Criteria:**

**Given** I am viewing TariffDetailPanel
**When** I notice incorrect data
**Then** I see a "Report Issue" link/button (FR45)

**Given** I click "Report Issue"
**When** the feedback form opens
**Then** I can select issue type: "Incorrect data", "Missing data", "Other"
**And** I can enter a description of the issue
**And** the HS code is pre-filled

**Given** I submit feedback
**When** the form is submitted
**Then** I see "Thank you for your feedback"
**And** the feedback is stored for admin review

**Given** I am not logged in
**When** I try to submit feedback
**Then** I am prompted to log in first
**And** my feedback form data is preserved

**Given** an admin wants to view feedback
**When** they access the admin dashboard
**Then** they can see a list of user-submitted feedback
**And** they can mark items as "Reviewed" or "Resolved"

---

## Epic 6: Admin Data Management (was Epic 5)

Admins can upload new tariff data (Excel), preview changes, activate updates, and rollback if needed.

### Story 6.1: Tariff Data Upload (was Story 5.1)

As an **admin**,
I want **to upload new tariff data files**,
So that **I can update the system with the latest Vietnam Customs data**.

**Acceptance Criteria:**

**Given** I am an admin on the Data Management page (`/admin/data`)
**When** I click "Upload New Data"
**Then** I see a file upload dialog accepting Excel files (.xlsx, .xls) (FR36)

**Given** I select a valid Excel file
**When** the upload begins
**Then** I see upload progress indicator
**And** the file is validated for correct format (FR42)
**And** upload completes in <5 minutes for ~20,000 records (NFR-P5)

**Given** I upload an invalid file format
**When** validation runs
**Then** I see specific error: "Invalid file format" or "Missing required columns"
**And** the upload is rejected

**Given** I upload a file with data errors
**When** validation runs
**Then** I see a list of validation errors (row numbers, issues)
**And** I can download an error report

**Given** the upload succeeds
**When** processing completes
**Then** the data is stored as a new version (not yet active)
**And** I am taken to the preview step

---

### Story 6.2: Preview Uploaded Data (was Story 5.2)

As an **admin**,
I want **to preview uploaded data before activation**,
So that **I can verify the data is correct**.

**Acceptance Criteria:**

**Given** I have uploaded a tariff file
**When** I view the preview page
**Then** I see summary statistics (FR37):
- Total HS codes in upload
- New codes (not in current data)
- Removed codes (in current, not in upload)
- Modified codes (changed rates or descriptions)

**Given** I am previewing the upload
**When** I want to see details
**Then** I can expand each category to see specific codes

**Given** I view the comparison (FR38)
**When** I look at a modified code
**Then** I see old value vs new value side-by-side
**And** changed fields are highlighted

**Given** I am satisfied with the preview
**When** I click "Proceed to Activate"
**Then** I am taken to the activation step

**Given** I am not satisfied with the preview
**When** I click "Cancel Upload"
**Then** the uploaded data is discarded
**And** I return to the data management page

---

### Story 6.3: Activate Tariff Data (was Story 5.3)

As an **admin**,
I want **to activate uploaded tariff data to make it live**,
So that **users can search the new data**.

**Acceptance Criteria:**

**Given** I have previewed and approved the upload
**When** I click "Activate Now"
**Then** I see confirmation dialog with summary of changes (FR39)

**Given** I confirm activation
**When** activation begins
**Then** I see progress indicator
**And** the previous version is marked as inactive
**And** the new version becomes active
**And** search index is updated with new data
**And** embeddings are generated for new/changed codes

**Given** activation completes
**When** I view the confirmation
**Then** I see "Data version X is now active"
**And** the data version and effective date are updated (FR18)

**Given** I cancel activation
**When** I click "Cancel"
**Then** the upload remains in pending state
**And** I can activate later or discard

**Given** activation is in progress
**When** a user performs a search
**Then** they continue to see results from the previous version
**And** new version is available only after activation completes

---

### Story 6.4: Rollback to Previous Version (was Story 5.4)

As an **admin**,
I want **to rollback to the previous tariff data version**,
So that **I can recover from a bad data update**.

**Acceptance Criteria:**

**Given** I am on the Data Management page
**When** I click "Rollback to Previous"
**Then** I see confirmation dialog showing current vs previous version (FR40)
**And** I see warning "This will replace current data with previous version"

**Given** I confirm rollback
**When** rollback begins
**Then** the previous version becomes active
**And** the current version is marked as inactive
**And** search index is updated

**Given** rollback completes
**When** I view confirmation
**Then** I see "Successfully rolled back to version X"
**And** the action is logged with timestamp and admin ID

**Given** there is no previous version (first upload)
**When** I try to rollback
**Then** the rollback button is disabled
**And** I see tooltip "No previous version available"

---

### Story 6.5: Data Version History (was Story 5.5)

As an **admin**,
I want **to view the history of data uploads and activations**,
So that **I can track changes and audit data management**.

**Acceptance Criteria:**

**Given** I am on the Data Management page
**When** I view the version history section
**Then** I see a table of all data versions (FR41):
- Version name/ID
- Source file name
- Uploaded at (timestamp)
- Activated at (timestamp, if activated)
- Status (active, inactive, pending)
- Uploaded by (admin name)

**Given** I view version history
**When** I click on a version row
**Then** I see details: record count, change summary from activation

**Given** I want to compare versions
**When** I select two versions
**Then** I can see a diff of the changes between them

**Given** I am viewing history
**When** I want to export for audit
**Then** I can download the version history as CSV

**Given** data management actions occur
**When** I check the audit log
**Then** all admin actions are logged (NFR-SEC5):
- Upload, preview, activate, rollback actions
- Timestamp, admin ID, action type, result
