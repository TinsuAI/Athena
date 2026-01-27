---
stepsCompleted: [1, 2, 3, 4]
status: complete
completedAt: '2026-01-26'
totalEpics: 5
totalStories: 27
frCoverage: '50/50 (100%)'
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
| FR8 | Epic 4 | Browse HS codes hierarchically |
| FR9 | Epic 4 | Filter by HS code chapter |
| FR10 | Epic 1 | View 8-digit HS code |
| FR11 | Epic 1 | View Vietnamese description |
| FR12 | Epic 1 | View English description |
| FR13 | Epic 1 | View unit of measure |
| FR14 | Epic 1 | View import duty rate |
| FR15 | Epic 1 | View VAT rate |
| FR16 | Epic 1 | View FTA preferential rates |
| FR17 | Epic 1 | View policy notes |
| FR18 | Epic 1 | View data version and date |
| FR19 | Epic 3 | Save to favorites |
| FR20 | Epic 3 | Add notes to favorites |
| FR21 | Epic 3 | View favorites list |
| FR22 | Epic 3 | Remove from favorites |
| FR23 | Epic 3 | Search within favorites |
| FR24 | Epic 3 | Quick access during search |
| FR25 | Epic 3 | Auto-record searches |
| FR26 | Epic 3 | View search history |
| FR27 | Epic 3 | Re-execute from history |
| FR28 | Epic 3 | See selected code in history |
| FR29 | Epic 3 | Clear search history |
| FR30 | Epic 2 | Create account |
| FR31 | Epic 2 | Login |
| FR32 | Epic 2 | Logout |
| FR33 | Epic 2 | Password reset |
| FR34 | Epic 2 | Persistent sessions |
| FR35 | Epic 2 | Role assignment |
| FR36 | Epic 5 | Upload tariff Excel |
| FR37 | Epic 5 | Preview uploaded data |
| FR38 | Epic 5 | Compare changes |
| FR39 | Epic 5 | Activate new data |
| FR40 | Epic 5 | Rollback to previous |
| FR41 | Epic 5 | View upload history |
| FR42 | Epic 5 | Validate Excel format |
| FR43 | Epic 1 | No results feedback |
| FR44 | Epic 4 | Low-confidence suggestions |
| FR45 | Epic 4 | Report data issues |
| FR46 | Epic 1 | System error messages |
| FR47 | Epic 1 | Loading indicators |
| FR48 | Epic 1 | Preserve HS code format |
| FR49 | Epic 1 | Preserve duty rate precision |
| FR50 | Epic 1 | Display policy notes verbatim |

## Epic List

### Epic 1: Core HS Code Search Experience
Users can search for HS codes in Vietnamese, English, or Chinese and view complete tariff details including duty rates, VAT, and FTA preferential rates. This is the MVP - the fundamental value proposition of Athena.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR43, FR46, FR47, FR48, FR49, FR50

**Implementation Notes:**
- Includes project scaffolding from Architecture starter template
- Sets up PostgreSQL + pgvector, hybrid search, FastAPI backend, Next.js frontend
- Builds core UI components: SearchBar, ResultCard, ConfidenceBadge, TariffDetailPanel
- Implements 150ms debounced search with loading skeletons

### Epic 2: User Authentication & Sessions
Users can create accounts, log in securely, and maintain persistent sessions across browser sessions. Enables personalization features in subsequent epics.

**FRs covered:** FR30, FR31, FR32, FR33, FR34, FR35

**Implementation Notes:**
- NextAuth.js v5 with credentials provider
- FastAPI JWT validation with fastapi-nextauth-jwt
- Role-based access (user/admin)
- Password reset flow

### Epic 3: Personalization - Favorites & History
Users can save frequently-used HS codes to favorites with personal notes, and access their complete search history for quick re-lookups. Completes the daily workflow optimization.

**FRs covered:** FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27, FR28, FR29

**Implementation Notes:**
- FavoriteCard and HistoryItem components from UX spec
- Optimistic UI updates
- Search within favorites
- One-click history re-execution

### Epic 4: Advanced Search & Discovery
Users can browse HS codes hierarchically, filter by chapter, and receive guidance when search results have low confidence. Handles edge cases and ambiguous queries.

**FRs covered:** FR8, FR9, FR44, FR45

**Implementation Notes:**
- Hierarchical HS code browser (Section → Chapter → Heading)
- Chapter filter on search results
- Low-confidence guidance with alternative term suggestions
- Feedback mechanism for reporting data issues

### Epic 5: Admin Data Management
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

### Story 1.3: Search API with Hybrid Search

As a **user**,
I want **to search for HS codes using product descriptions in any language**,
So that **I can quickly find the correct classification for my goods**.

**Acceptance Criteria:**

**Given** I am a user with a product description
**When** I send POST `/api/search` with `{"query": "máy xay sinh tố"}` (Vietnamese)
**Then** I receive results ranked by confidence score (0-100)
**And** response time is <3 seconds (NFR-P1)
**And** response format is `{"success": true, "data": {"items": [...], "total": N}}`

**Given** I search with an English description
**When** I send POST `/api/search` with `{"query": "blender machine"}`
**Then** I receive relevant HS code matches with confidence scores

**Given** I search with a Chinese description
**When** I send POST `/api/search` with `{"query": "搅拌机"}`
**Then** I receive relevant HS code matches (best effort per Architecture)

**Given** I search with an exact HS code
**When** I send POST `/api/search` with `{"query": "85094010"}`
**Then** I receive that exact HS code as the top result with 100% confidence (FR4)

**Given** I search with a query that has no matches
**When** I send POST `/api/search` with `{"query": "xyznonexistent123"}`
**Then** I receive an empty results array
**And** the response includes `{"success": true, "data": {"items": [], "total": 0}}`

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

## Epic 2: User Authentication & Sessions

Users can create accounts, log in securely, and maintain persistent sessions across browser sessions.

### Story 2.1: User Registration

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

### Story 2.2: User Login

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

### Story 2.3: User Logout

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

### Story 2.4: Password Reset

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

### Story 2.5: Role-Based Access Control

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

## Epic 3: Personalization - Favorites & History

Users can save frequently-used HS codes to favorites with personal notes, and access their complete search history for quick re-lookups.

### Story 3.1: Save HS Code to Favorites

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

### Story 3.2: Add Notes to Favorites

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

### Story 3.3: View and Manage Favorites List

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

### Story 3.4: Search Within Favorites

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

### Story 3.5: Quick Favorites Access During Search

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

### Story 3.6: Automatic Search History Recording

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

### Story 3.7: View and Re-execute Search History

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

### Story 3.8: Clear Search History

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

## Epic 4: Advanced Search & Discovery

Users can browse HS codes hierarchically, filter by chapter, and receive guidance when search results have low confidence.

### Story 4.1: Hierarchical HS Code Browser

As a **user**,
I want **to browse HS codes by their hierarchical structure**,
So that **I can navigate to the correct code when search doesn't work**.

**Acceptance Criteria:**

**Given** I navigate to the Browse page (`/browse`)
**When** the page loads
**Then** I see a list of HS code Sections (top level)
**And** each section shows its name and code range

**Given** I am viewing Sections
**When** I click on a Section (e.g., "Section XVI: Machinery")
**Then** I see the Chapters within that section (FR8)
**And** breadcrumb navigation shows my path

**Given** I am viewing Chapters
**When** I click on a Chapter (e.g., "Chapter 85: Electrical machinery")
**Then** I see the Headings within that chapter
**And** I can continue drilling down

**Given** I am viewing individual HS codes at the heading level
**When** I click on an HS code
**Then** TariffDetailPanel opens with full details

**Given** I am deep in the hierarchy
**When** I click on a breadcrumb link
**Then** I navigate back to that level
**And** my position in the hierarchy is maintained

---

### Story 4.2: Chapter Filter on Search Results

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

### Story 4.3: Low-Confidence Search Guidance

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

### Story 4.4: Data Feedback Mechanism

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

## Epic 5: Admin Data Management

Admins can upload new tariff data (Excel), preview changes, activate updates, and rollback if needed.

### Story 5.1: Tariff Data Upload

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

### Story 5.2: Preview Uploaded Data

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

### Story 5.3: Activate Tariff Data

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

### Story 5.4: Rollback to Previous Version

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

### Story 5.5: Data Version History

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
