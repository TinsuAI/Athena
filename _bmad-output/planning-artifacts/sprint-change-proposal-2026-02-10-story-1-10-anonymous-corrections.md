# Sprint Change Proposal: Anonymous Corrections for Story 1.10

**Date:** 2026-02-10
**Author:** John (Product Manager)
**User:** tinsu
**Trigger:** Story 1.10 implementation planning
**Change Scope:** Minor - Single story modification
**Status:** APPROVED

---

## 1. Issue Summary

### Problem Statement
Story 1.10 was originally designed requiring an "expert role" with authentication to submit corrections. This adds unnecessary complexity:
- Need to manage expert role vs regular user role
- Separate `/expert/review` page
- Protected API endpoints for experts only

### Simplified Approach
Remove the expert role requirement and allow **anyone** to submit corrections directly from the search page without logging in. This:
- Removes role complexity from auth system
- Lowers friction for experts to contribute
- Simplifies UI (inline corrections vs separate page)

### Scope
**Only Story 1.10 is affected.** Epic 2 (authentication) and Epic 3 (favorites/history) remain unchanged.

---

## 2. Impact Analysis

### Epic Impact

| Epic | Status | Impact |
|------|--------|--------|
| **Epic 1: Core Search** | ✅ Active | Story 1.10 rewritten for anonymous corrections |
| **Epic 2: User Authentication** | ✅ **UNCHANGED** | Still needed for favorites/history |
| **Epic 3: Favorites & History** | ✅ **UNCHANGED** | Still requires user login |
| **Epic 4: Advanced Search** | ✅ **UNCHANGED** | No dependencies |
| **Epic 5: Admin Data Mgmt** | ✅ **UNCHANGED** | Still uses admin role |

**Total Stories Impacted:** 1 story (only 1.10)

### Artifact Conflicts

#### PRD Modifications
- **FR30-35 (Authentication):** KEEP - still needed for favorites/history
- **FR19-29 (Favorites/History):** KEEP - unchanged
- **No functional requirements removed**

**Modified:**
- Story 1.10 implementation approach only

#### Architecture Changes

**Authentication System: KEEP (Unchanged)**
- NextAuth.js v5 - Still needed
- JWT validation - Still needed
- Users table - Still needed (for favorites/history)

**ONLY CHANGE:**
- Remove "expert" role from user model (only need "user" and "admin")
- Make correction API endpoints public (no auth required)
- Add rate limiting to public correction endpoints

**Database Schema Changes:**

```sql
-- users table: Remove expert role, keep user/admin
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  password_hash VARCHAR NOT NULL,
  role VARCHAR DEFAULT 'user',  -- 'user' or 'admin' (no 'expert')
  created_at TIMESTAMP DEFAULT NOW()
);

-- lookup_records: Remove verified_by_user_id (anonymous corrections)
ALTER TABLE lookup_records
  DROP COLUMN verified_by_user_id;
```

**API Endpoints Modified:**
```
# Make these public (no auth required, rate-limited)
GET  /api/corrections/lookups       # Anyone can view pending corrections
POST /api/corrections               # Anyone can submit corrections

# These stay protected (auth required)
GET  /api/favorites                 # User must be logged in
POST /api/favorites                 # User must be logged in
GET  /api/history                   # User must be logged in
```

#### UX Design Changes

**REMOVE:**
- `/expert/review` page (separate expert interface)
- Expert role badge/indicator in UI

**ADD:**
- "Suggest Correction" button on search ResultCards
- Inline CorrectionPanel (slides in from search page)

**KEEP (Unchanged):**
- Login/register pages (still needed for favorites/history)
- User profile menu
- Favorites page
- History page
- All authentication flows

---

## 3. Recommended Approach

**Selected Path:** Direct Adjustment (Modify Story 1.10 Only)

### Implementation Changes

**Story 1.10 Rewrite:**

**OLD Approach:**
- Expert role required
- Login to access /expert/review page
- Protected API endpoints
- Expert-only review queue

**NEW Approach:**
- No login required
- Inline correction UI on search page
- Public API endpoints (rate-limited)
- Anonymous corrections auto-verified

---

## 4. Detailed Change Proposals

### Change 1: Story 1.10 Complete Rewrite

**File:** `_bmad-output/planning-artifacts/epics.md`

**Action:** Replace Story 1.10 (lines 759-812)

**NEW Story 1.10:**

```markdown
### Story 1.10: Anonymous Correction Interface (ADDED 2026-02-10)

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
```

---

### Change 2: Remove Expert Role from User Model

**File:** `api/app/models/user.py`

**OLD:**
```python
class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum('user', 'admin', 'expert'), default='user')  # 3 roles
    created_at = Column(DateTime, default=datetime.utcnow)
```

**NEW:**
```python
class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum('user', 'admin'), default='user')  # Only 2 roles
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

### Change 3: Architecture Document Update

**File:** `_bmad-output/planning-artifacts/architecture.md`

**Action:** Add section after line 285 (Authentication section)

**NEW Section:**

```markdown
### Story 1.10 Simplification (2026-02-10)

**Expert Role Removed:**
The original design included a third user role "expert" for managing correction submissions. This has been simplified:

**OLD Approach:**
- User roles: user, admin, expert
- Expert-only review interface at /expert/review
- Protected correction endpoints requiring expert login

**NEW Approach:**
- User roles: user, admin (expert role removed)
- Anonymous correction submission from search page
- Public correction endpoints with rate limiting
- No expert authentication required

**Impact:**
- Simpler role management (2 roles instead of 3)
- Lower friction for experts (no login required)
- Faster implementation (no expert role logic)

**Authentication Still Required For:**
- User favorites (Epic 3)
- Search history (Epic 3)
- Admin data management (Epic 5)
```

---

### Change 4: UX Design Update

**File:** `_bmad-output/planning-artifacts/ux-design-specification.md`

**Action:** Add section after line 640

**NEW Section:**

```markdown
### Anonymous Correction Pattern (Story 1.10 Simplified)

**Design Decision:** Remove expert login requirement, enable anonymous corrections

**User Flow:**
1. User sees incorrect search result on /search page
2. Clicks "Suggest Correction" button (no login prompt)
3. CorrectionPanel slides in with HS code autocomplete
4. User selects correct code, adds optional notes
5. Submits → "Thanks!" toast → panel closes
6. Correction immediately improves future searches

**Components:**

#### CorrectionButton
- **Location:** Bottom of each ResultCard
- **Style:** Ghost button, "Suggest Correction" text
- **No auth required:** Anyone can click

#### CorrectionPanel
- **Layout:** Slide-in from right (similar to TariffDetailPanel)
- **Fields:**
  - Current suggestion (read-only, highlighted in yellow)
  - Search correct HS code (autocomplete dropdown)
  - Optional notes (textarea, 200 char max)
  - Submit button (primary)
- **Rate limit:** Disable after 10 submissions/hour
- **Success:** Green toast "Thanks for improving search quality!"

**No Expert Badge/Role:**
- Remove any "expert" role indicators from UI
- Corrections are anonymous (no user attribution)
- Simple spam prevention via rate limiting
```

---

## 5. Implementation Handoff

### Route To: **Development Team**

**Scope:** Minor changes - direct implementation

### Implementation Checklist

#### Backend Changes
- [ ] Remove expert role from `api/app/models/user.py`
- [ ] Create migration to remove expert role from database
- [ ] Create `api/app/api/corrections.py` with public endpoints
- [ ] Implement rate limiting middleware (10 corrections/hour per IP)
- [ ] Remove `verified_by_user_id` column from `lookup_records` table
- [ ] Auto-verify corrections (set `is_verified = true` on submission)
- [ ] Add deduplication logic (same IP + same correction = skip)

#### Frontend Changes
- [ ] Create `web/src/app/search/components/CorrectionButton.tsx`
- [ ] Create `web/src/app/search/components/CorrectionPanel.tsx`
- [ ] Add CorrectionButton to `ResultCard.tsx` component
- [ ] Implement HS code autocomplete in CorrectionPanel
- [ ] Add success toast notification
- [ ] Delete `web/src/app/expert/` directory (if exists)
- [ ] Remove expert role references from navigation/UI

#### Documentation Updates
- [ ] Update Story 1.10 in `epics.md` with new acceptance criteria
- [ ] Add expert role removal note to `architecture.md`
- [ ] Update `ux-design-specification.md` with correction pattern

#### Testing
- [ ] Test anonymous correction submission flow
- [ ] Verify rate limiting enforces 10/hour per IP
- [ ] Test corrections immediately improve search results
- [ ] Verify no authentication errors on public endpoints
- [ ] Test spam prevention (duplicate submissions)

---

## 6. Success Criteria

- ✅ Anyone can submit corrections without creating an account
- ✅ Corrections are rate-limited to prevent spam (10/hour per IP)
- ✅ Corrections immediately improve search results
- ✅ No expert role exists in database or auth system
- ✅ Inline correction UI integrated into search page
- ✅ No `/expert/review` page or expert-specific routes

---

## 7. Timeline Impact

**Impact:** None - simplifies implementation, may slightly accelerate delivery

**Estimate:** Story 1.10 implementation ~3-5 days

---

## 8. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Spam corrections | Medium | Rate limiting (10/hr per IP), deduplication |
| Low-quality corrections | Low | Manual review queue can be added in Phase 2 |
| No accountability | Low | Track by IP, can add auth in Phase 2 if needed |

---

**APPROVED BY:** tinsu
**DATE:** 2026-02-10
**STATUS:** Ready for implementation

---

**Next Steps:**
1. Development team implements changes
2. Test anonymous correction flow
3. Deploy to production
4. Monitor correction quality and spam levels
