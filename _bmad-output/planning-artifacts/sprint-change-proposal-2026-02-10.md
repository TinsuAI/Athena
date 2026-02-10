# Sprint Change Proposal - Knowledge Base with Human-in-the-Loop

**Project:** Athena - HS Code Lookup Tool
**Date:** 2026-02-10
**Author:** tinsu (via Correct Course workflow)
**Status:** Pending Approval

---

## Section 1: Issue Summary

### Problem Statement

The HS code search functionality remains at **~0% accuracy** despite three separate improvement attempts. The embedding-based semantic search approach is fundamentally inadequate for HS code classification. The domain requires specialized human expertise that cannot be replicated by general-purpose AI embeddings or LLM reranking.

### Context

- **Discovered during:** Ongoing testing of Epic 1 search functionality
- **Trigger:** Search results remain incorrect after exhausting AI-based improvement approaches
- **Three failed attempts:**
  1. **Original implementation** (Stories 1-1 through 1-4): Vector search + fuzzy matching → 0% accuracy
  2. **Story 1-2.1** (Sprint Change 2026-02-02): Category context fix to enrich HS code descriptions → Still ~0%
  3. **LLM three-pronged approach** (search-accuracy-improvement-plan.md): Query enhancement + improved embeddings + LLM reranking → Still ~0%

### Root Cause Analysis

**Primary Cause:** HS code classification is a specialized domain skill that cannot be solved by matching product descriptions against tariff descriptions via embeddings or LLM reasoning alone.

**Why AI approaches fail:**
- Tariff descriptions are terse legal text (e.g., "Loại khác" / "Other") - they don't semantically match real-world product descriptions
- HS classification follows complex rules (General Rules of Interpretation) that depend on material precedence, function, and context
- Even with LLM reranking, the model lacks the domain-specific experience that human HS experts have built over years
- The embedding space doesn't capture the specialized mapping between "everyday product language" and "legal tariff classification language"

**Proposed Solution:** Build a knowledge base system with human-in-the-loop correction. Expert-verified classifications become the primary search mechanism, with AI as a fallback for novel queries.

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Status | Impact |
|------|--------|--------|
| **Epic 1: Core Search** | In Progress | **Major** - Add 3 new stories (1-8, 1-9, 1-10) for knowledge base. Modify Story 1-3 search flow. Stories 1-5 to 1-7 can proceed in parallel. |
| **Epic 2: Auth** | Backlog | **Moderate** - Need new "expert" role beyond user/admin |
| **Epic 3: Favorites/History** | Backlog | **Low** - Search history naturally feeds knowledge base |
| **Epic 4: Advanced Search** | Backlog | **Low** - Data feedback (4-4) aligns with knowledge base concept |
| **Epic 5: Admin Data** | Backlog | **None** - No changes needed |

### Story Impact

| Story | Current Status | Impact |
|-------|----------------|--------|
| 1-1 | Done | No change |
| 1-2 | Done | No change |
| 1-2.1 | Review | **Deprioritized** - Category context is less critical with knowledge base approach. Can be kept as minor improvement but no longer blocking. |
| 1-3 | Done | **Modify** - Integrate knowledge base as primary search, existing search becomes fallback |
| 1-4 | Review | **Minor update** - Display source indicator (verified vs AI suggestion) |
| 1-5 | Backlog | **Minor update** - Show verified badge on result cards |
| 1-6 | Backlog | **Minor update** - Show verification status in detail view |
| 1-7 | Backlog | No change |
| **1-8** | **NEW** | Knowledge Base Schema & Lookup Storage |
| **1-9** | **NEW** | Knowledge-Enhanced Search |
| **1-10** | **NEW** | Expert Review & Correction Interface |

### Artifact Conflicts

| Artifact | Impact | Details |
|----------|--------|---------|
| **PRD** | **Moderate** | Update search model, validation approach, success criteria, add FR51-FR54 |
| **Architecture** | **Moderate** | New table (lookup_records), updated search flow, new API endpoints, new "expert" role |
| **UX Design** | **Moderate** | New components (ExpertReviewQueue, ExpertCorrectionPanel), updated confidence badges, expert navigation tab |
| **Epics & Stories** | **Major** | 3 new stories, 1 modified story, minor updates to 3 stories |

### Technical Impact

| Component | Impact |
|-----------|--------|
| Database schema | **Add** `lookup_records` table with indexes |
| Search API (`search.py`) | **Modify** - Knowledge base lookup before vector search |
| New service (`knowledge_base_service.py`) | **Create** - KB lookup, similarity matching |
| New repository (`lookup_record_repository.py`) | **Create** - CRUD for lookup records |
| New API (`expert.py`) | **Create** - Expert review endpoints |
| New model (`lookup_record.py`) | **Create** - SQLAlchemy model |
| Auth (`auth.py`) | **Modify** - Add "expert" role |
| Frontend ResultCard | **Modify** - Show source/verified badge |
| Frontend new pages | **Create** - Expert review queue and correction panel |

---

## Section 3: Recommended Approach

### Selected Path: Direct Adjustment (Hybrid Knowledge Base)

Layer a knowledge base with human-in-the-loop correction on top of the existing search infrastructure:

1. **Knowledge base first:** Check verified expert classifications for matching queries (<100ms)
2. **AI fallback:** If no KB match, use existing vector/LLM search as suggestion (~2-3s)
3. **Expert loop:** All lookups stored for expert review and correction
4. **Continuous improvement:** Expert corrections feed back into knowledge base

### Rationale

| Factor | Assessment |
|--------|------------|
| **Why not more AI tuning?** | Three attempts at 0% accuracy prove the approach is fundamentally insufficient |
| **Why knowledge base works** | HS classification is pattern-based - the same products recur. ~60-70% of daily queries are repeat product types |
| **Cold start problem** | AI fallback handles novel queries while knowledge base is being built |
| **Leverages existing work** | All infrastructure from Stories 1-1 through 1-4 is retained and reused |
| **Growth model** | Expert reviews ~50 lookups/day → common products covered in weeks → 80% target achievable in ~1 month |

### Alternatives Considered

| Alternative | Why Not Selected |
|-------------|------------------|
| **More LLM tuning** | Three failed attempts; diminishing returns on an approach that doesn't work |
| **Custom-trained model** | Requires labeled training data we don't have; knowledge base generates this data as a byproduct |
| **Remove AI entirely** | Loses fallback for novel queries; wastes existing work |
| **Reduce MVP scope** | Unnecessary - knowledge base approach is achievable within current timeline |
| **Fine-tune embeddings** | Still won't bridge the gap between product language and tariff language |

### Effort Estimate

| Item | Effort | Risk |
|------|--------|------|
| Story 1-8 (Schema & Storage) | 1-2 days | Low |
| Story 1-9 (KB-Enhanced Search) | 2-3 days | Medium |
| Story 1-10 (Expert Correction UI) | 2-3 days | Low |
| Story 1-3 modification | 0.5 days | Low |
| Stories 1-4/1-5/1-6 minor updates | 0.5 days | Low |
| PRD/Architecture/UX doc updates | 0.5 days | Low |
| **Total** | **~7-10 days** | **Medium overall** |

### Timeline Impact

| Milestone | Impact |
|-----------|--------|
| Epic 1 completion | +7-10 days |
| MVP delivery | +1-2 weeks (but with actually working search) |
| 80% accuracy target | Achievable ~1 month after launch (with active expert review) |

---

## Section 4: Detailed Change Proposals

### 4.1 New Stories

#### Story 1-8: Knowledge Base Schema & Lookup Storage

As a **developer**,
I want **a knowledge base that stores every user lookup with a field for expert correction**,
So that **verified human classifications can enhance future search results**.

**Acceptance Criteria:**

**Given** the database is running
**When** I run the migration
**Then** the following table is created:
- `lookup_records` (id, query_text, query_hash, query_language, matched_hs_code_id, correct_hs_code_id, is_verified, verified_by_user_id, verified_at, confidence_score, search_method, notes, created_at, updated_at)

**Given** a user performs a search via POST /api/search
**When** results are returned
**Then** a lookup_record is automatically created with:
- query_text = the user's search input
- matched_hs_code_id = the top result returned by the system
- correct_hs_code_id = NULL (pending expert review)
- is_verified = false
- search_method = 'vector' | 'knowledge_base' | 'exact'

**Given** duplicate queries within 24 hours
**When** the same query text is searched again
**Then** no duplicate lookup_record is created (deduplicate by query_hash)

**Given** the lookup_records table has data
**When** I query for unverified records
**Then** I can retrieve all records where is_verified = false, ordered by created_at descending

**Technical Tasks:**
1. Create SQLAlchemy model: `api/app/models/lookup_record.py`
2. Create Alembic migration for `lookup_records` table with indexes
3. Create repository: `api/app/repositories/lookup_record_repository.py`
4. Integrate lookup storage into search API endpoint
5. Add deduplication logic by query_hash

---

#### Story 1-9: Knowledge-Enhanced Search

As a **user**,
I want **my searches to return expert-verified results when available**,
So that **I get accurate HS codes based on real expert knowledge, not just AI guesses**.

**Acceptance Criteria:**

**Given** an expert has previously verified "may xay sinh to" -> 8509.40.10
**When** another user searches "may xay sinh to"
**Then** the verified HS code 8509.40.10 is returned with source: "knowledge_base" and confidence: 100

**Given** an expert has verified "blender 500W household" -> 8509.40.10
**When** a user searches "may xay sinh to gia dinh 500W" (similar but not exact)
**Then** the system finds the similar verified query using text similarity (threshold >= 0.85)
**And** returns the verified HS code with high confidence

**Given** no verified match exists in the knowledge base
**When** a user searches for a product description
**Then** the system falls back to the existing vector/fuzzy search
**And** results are marked with source: "ai_suggestion"

**Given** the search flow processes a query
**Then** the system checks in this order:
1. Exact match in verified KB (query_hash, <50ms)
2. Similar match in verified KB (pg_trgm similarity >= 0.85, <100ms)
3. Fallback to vector search + LLM (existing pipeline, ~2-3s)

**Technical Tasks:**
1. Create service: `api/app/services/knowledge_base_service.py`
2. Implement exact match lookup by query_hash
3. Implement similarity match using pg_trgm on query_text
4. Integrate KB lookup as first step in search API
5. Add `source` and `isVerified` fields to search response schema
6. Write tests for KB hit and miss scenarios

---

#### Story 1-10: Expert Review & Correction Interface

As an **HS code expert**,
I want **to review user lookups and correct the HS code classifications**,
So that **the knowledge base grows with verified, accurate mappings**.

**Acceptance Criteria:**

**Given** I am logged in as a user with "expert" role
**When** I navigate to /expert/review
**Then** I see a list of unverified lookup records showing: query text, suggested HS code, timestamp
**And** the list is paginated (20 per page) and sortable

**Given** I am reviewing a lookup record
**When** the system's suggestion is correct
**Then** I can click "Mark Correct" (one click) to verify it

**Given** I am reviewing a lookup record
**When** the system's suggestion is wrong
**Then** I can search/autocomplete for the correct HS code
**And** I can browse the HS hierarchy to find the right code
**And** I can add notes explaining the classification reasoning

**Given** I submit a correction
**When** the correction is saved
**Then** correct_hs_code_id is set, is_verified = true, verified_by_user_id = my ID
**And** the correction is immediately available for future searches

**Given** the expert review page
**When** I view statistics
**Then** I see: total unverified, total verified today, total verified all-time

**API Endpoints:**
- GET /api/expert/lookups?verified=false&page=1
- GET /api/expert/lookups/:id
- PATCH /api/expert/lookups/:id/verify
- GET /api/expert/stats

**Technical Tasks:**
1. Add "expert" role to user model and auth middleware
2. Create API router: `api/app/api/expert.py`
3. Create Pydantic schemas: `api/app/schemas/expert.py`
4. Build frontend: ExpertReviewQueue component
5. Build frontend: ExpertCorrectionPanel component
6. Add "Review Queue" tab for expert role users

**Dependency:** Requires Story 1-8 (schema) to be complete

---

### 4.2 Story Modifications

#### Story 1-3: Search API (Modify Search Flow)

**Section: Acceptance Criteria**

Append to existing acceptance criteria:

**Given** a verified knowledge base entry exists for a query
**When** a user searches with that query (or highly similar text)
**Then** the verified result is returned first with source: "knowledge_base" and confidence: 100
**And** the search completes in <100ms (no need for vector search or LLM)

**Given** no knowledge base match exists
**When** a user searches
**Then** the existing vector/LLM pipeline executes as fallback
**And** results are returned with source: "ai_suggestion"
**And** a lookup_record is created for expert review

**Section: Response Format**

Add to response schema:
```json
{
  "source": "knowledge_base" | "ai_suggestion",
  "isVerified": true | false,
  "verifiedBy": "expert_name" | null,
  "verifiedAt": "2026-02-10T..." | null
}
```

**Section: Technical Implementation Notes**

Append:
- Search flow priority: (1) Exact KB match <50ms → (2) Similar KB match <100ms → (3) Vector + LLM ~2-3s
- All searches create a lookup_record for the knowledge base
- Knowledge base matches skip LLM reasoning (already expert-verified)

---

#### Stories 1-4, 1-5, 1-6: Minor Updates

**Story 1-4 (Search UI):** Display source indicator badge on results
**Story 1-5 (Results Display):** Show "Expert Verified" (green + checkmark) vs "AI Suggestion" (blue/yellow/red + sparkle) badges
**Story 1-6 (Detail View):** Show verification status and expert name in TariffDetailPanel

---

### 4.3 PRD Modifications

#### Executive Summary - The Solution

**OLD:**
- Intelligent Multi-Language Search
- Confidence-Ranked Results

**NEW:**
- Knowledge-Enhanced Search: Expert-verified classifications as primary results, AI suggestions for new products
- Human-in-the-Loop Correction: HS code experts review and correct classifications, continuously improving accuracy

#### Validation Approach (Section 6)

**OLD:** "Semantic search can reliably match ambiguous product descriptions to correct HS codes."

**NEW:** "A knowledge base built from expert-verified classifications can achieve high accuracy for recurring product types, while AI suggestions handle new/unseen products."

**Growth model:**
- Week 1-2: Expert reviews ~50 lookups/day, KB accuracy grows rapidly
- Month 1: Common products (~60-70% of queries) are knowledge base hits
- Month 3: 80%+ of daily lookups served from verified knowledge base

#### Success Criteria (Section 2)

Add: **Knowledge Base Growth** target: 500+ verified entries in first month

#### Functional Requirements (Section 9)

Add:
- **FR51:** System stores all search queries as lookup records for expert review
- **FR52:** Expert users can review unverified lookups and assign correct HS code
- **FR53:** Verified knowledge base entries are returned as primary results
- **FR54:** Users can distinguish between expert-verified results and AI suggestions

---

### 4.4 Architecture Modifications

#### New Table: lookup_records

```sql
lookup_records (
  id UUID PRIMARY KEY,
  query_text TEXT NOT NULL,
  query_hash VARCHAR(64) NOT NULL,
  query_language VARCHAR(5),
  matched_hs_code_id INTEGER REFERENCES hs_codes(id),
  correct_hs_code_id INTEGER REFERENCES hs_codes(id),
  is_verified BOOLEAN DEFAULT false,
  verified_by_user_id INTEGER REFERENCES users(id),
  verified_at TIMESTAMP WITH TIME ZONE,
  confidence_score FLOAT,
  search_method VARCHAR(20),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_lookup_records_query_hash ON lookup_records(query_hash);
CREATE INDEX idx_lookup_records_verified ON lookup_records(is_verified);
CREATE INDEX idx_lookup_records_query_trgm ON lookup_records
  USING gin(query_text gin_trgm_ops);
```

#### Updated Search Flow

```
User Query
    |
    v
[1. KB Exact Match] -- query_hash lookup (<50ms)
    |                         |
    hit                      miss
    |                         |
    v                         v
  Return verified      [2. KB Similar Match] -- pg_trgm >= 0.85 (<100ms)
  result                      |                         |
                             hit                      miss
                              |                         |
                              v                         v
                        Return verified      [3. AI Fallback] -- vector + LLM (~2-3s)
                        result                      |
                                                    v
                                              Return AI suggestion
                                                    |
                                                    v
                                          [4. Store lookup_record for expert review]
```

#### New Role: expert

Roles: user, expert, admin (expert inherits user permissions, admin inherits expert permissions)

#### New API Endpoints

```
GET   /api/expert/lookups            # List lookup records
GET   /api/expert/lookups/:id        # Get single lookup
PATCH /api/expert/lookups/:id/verify # Submit expert correction
GET   /api/expert/stats              # KB statistics
```

#### New Files

```
api/app/models/lookup_record.py
api/app/repositories/lookup_record_repository.py
api/app/services/knowledge_base_service.py
api/app/api/expert.py
api/app/schemas/expert.py
web/src/app/expert/review/page.tsx
web/src/app/expert/review/components/ExpertReviewQueue.tsx
web/src/app/expert/review/components/ExpertCorrectionPanel.tsx
```

---

### 4.5 UX Design Modifications

#### Confidence Badge Update

| Source | Color | Badge Text | Icon |
|--------|-------|------------|------|
| Expert Verified | Green (--success) | "Expert Verified" | Checkmark |
| AI High (80-100%) | Blue (--info) | "AI Suggestion - High" | Sparkle |
| AI Medium (50-79%) | Yellow (--warning) | "AI Suggestion - Medium" | Sparkle |
| AI Low (<50%) | Red (--error) | "AI Suggestion - Low" | Sparkle |

Green is reserved exclusively for expert-verified results.

#### New Components

- **ExpertReviewQueue:** Table of unverified lookups with filter/sort/pagination
- **ExpertCorrectionPanel:** Split view with lookup details + HS code selector + "Mark Correct" one-click

#### Navigation Update

Expert role users see an additional "Review Queue" tab with unverified count badge.

---

## Section 5: Implementation Handoff

### Change Scope Classification

**Scope: Moderate**

This change requires:
- Development team for implementation (3 new stories + modifications)
- Scrum Master for backlog reorganization (new stories, updated dependencies)
- PRD/Architecture/UX document updates

Does NOT require:
- Fundamental replan or architectural overhaul
- New infrastructure or technology changes

### Implementation Sequence

```
Phase 1: Foundation (Stories 1-8) ........................ 1-2 days
  1. Create lookup_records table + migration
  2. Create model, repository
  3. Integrate auto-storage into search API

Phase 2: KB Search (Story 1-9) .......................... 2-3 days
  4. Create knowledge_base_service
  5. Implement exact + similar match
  6. Integrate as primary search path
  7. Add source/verified fields to response

Phase 3: Expert UI (Story 1-10) ......................... 2-3 days
  8. Add expert role to auth
  9. Create expert API endpoints
  10. Build ExpertReviewQueue frontend
  11. Build ExpertCorrectionPanel frontend

Phase 4: Polish (Parallel with Phase 2-3) ............... 0.5 days
  12. Update ResultCard with source badges
  13. Update TariffDetailPanel with verification status

Phase 5: Document Updates ............................... 0.5 days
  14. Update PRD, Architecture, UX documents
  15. Update sprint-status.yaml
```

### Handoff Recipients

| Role | Responsibility |
|------|----------------|
| **Dev Team** | Implement Stories 1-8, 1-9, 1-10; modify 1-3, 1-4, 1-5, 1-6 |
| **Scrum Master** | Update sprint-status.yaml, track progress, update epics.md |
| **Product Owner** | Approve proposal, coordinate expert user onboarding |
| **HS Code Expert(s)** | Begin reviewing lookups once Story 1-10 is complete |

### Success Criteria

| Metric | Target | Timeline |
|--------|--------|----------|
| Knowledge base schema deployed | Complete | Day 2 |
| KB-enhanced search live | Complete | Day 5 |
| Expert correction UI live | Complete | Day 8 |
| First 50 expert verifications | Complete | Week 2 post-launch |
| 80% of common queries served from KB | Achieved | Month 1 post-launch |
| PRD 80% accuracy target | Achieved | Month 1-2 post-launch |

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Cold start (empty KB) | AI fallback handles all queries until KB grows |
| Expert availability | Even 20-30 corrections/day compounds rapidly |
| Similar match false positives | Conservative similarity threshold (0.85); can tune |
| KB query deduplication edge cases | Hash-based dedup + 24hr window prevents bloat |

---

## Approval

**Prepared by:** Correct Course Workflow
**Date:** 2026-02-10

**Approval Status:** [x] Approved

**Approver:** tinsu
**Date:** 2026-02-10

**Notes:**
Approved as-is. Proceed with implementation per the handoff plan.
