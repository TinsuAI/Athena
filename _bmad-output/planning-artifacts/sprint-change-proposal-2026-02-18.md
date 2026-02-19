# Sprint Change Proposal - Advanced RBAC, Permissions & User Management

**Date:** 2026-02-18
**Author:** tinsu (facilitated by BMad Correct Course workflow)
**Status:** Draft
**Scope:** Moderate

---

## 1. Issue Summary

### Problem Statement

After completing Epic 4 (User Authentication & Sessions), the current role-based access control system is insufficient for production-quality operations. Specifically:

1. **No Expert Role:** The system only has `user` and `admin` roles. There is no "expert" role that can approve corrections to HS code classifications — a critical quality gate for the knowledge base.

2. **Anonymous, Auto-Verified Corrections:** Story 1-10 implemented corrections as anonymous and auto-verified (`is_verified = true` on submit). This means anyone can submit corrections that immediately affect the knowledge base, with no review process and no accountability.

3. **Limited User Management:** The admin panel has basic user listing and role toggling (user ↔ admin), but lacks comprehensive user management (create, edit, deactivate, search).

4. **No Permission Granularity:** There is no per-role or per-user permission system. Permissions are hardcoded as `require_admin` checks.

### Context

- **Discovery:** Post-Epic 4 implementation review by product owner
- **Evidence:** Current corrections API (`api/app/api/corrections.py`) is fully anonymous with IP-based rate limiting. The `RoleUpdateRequest` schema validates only `user` or `admin`. Story 1-10 explicitly states "Auto-verify corrections for MVP" and "Remove expert role from user model."
- **Impact:** Without an expert approval workflow, the knowledge base quality cannot be guaranteed — any visitor could poison classification data.

---

## 2. Impact Analysis

### Epic Impact

| Epic | Impact | Details |
|------|--------|---------|
| **Epic 4** (Auth, done) | No change | Foundation is solid; new epic extends it |
| **NEW Epic 5** | **New** | "Advanced RBAC, Permissions & User Management" |
| **Epic 5 → 6** (Favorites) | Renumber only | No functional change |
| **Epic 6 → 7** (Advanced Search) | Renumber only | No functional change |
| **Epic 7 → 8** (Admin Data) | Renumber only | No functional change |

### Story Impact

| Story | Impact | Details |
|-------|--------|---------|
| **Story 1-10** (Corrections) | **Superseded** | Anonymous auto-verified corrections replaced by authenticated submission + expert approval workflow. Story 1-10 remains `done` — new stories build on top. |
| **Story 4-5** (RBAC) | **Extended** | Current `user/admin` role model expanded to `user/expert/admin` |
| **Story 1-13** (Lookup Detail) | **Minor update** | Correction panel on lookup detail page needs login gate + pending/approved status display |

### Artifact Conflicts

#### PRD (`prd.md`)

| Section | Change |
|---------|--------|
| FR35 | Expand from "user, admin" to "user, expert, admin" |
| NEW FR65 | Expert can approve/reject pending corrections |
| NEW FR66 | Only logged-in users can submit corrections |
| NEW FR67 | Admin can manage permissions per role |
| NEW FR68 | Admin can manage individual user permissions (overrides) |
| NEW FR69 | Admin has full user management (create, edit, deactivate, search) |
| NEW FR70 | Corrections have pending/approved/rejected status workflow |

#### Architecture (`architecture.md`)

| Component | Change |
|-----------|--------|
| User model | Add "expert" to role enum; add `is_active` field for deactivation |
| LookupRecord model | Add `submitted_by_user_id` FK to track who submitted corrections; add `correction_status` field (pending/approved/rejected); add `rejection_reason` field |
| Auth middleware | Add `require_expert`, `require_authenticated` (any logged-in user), `get_optional_user` dependencies |
| Corrections API | Change from anonymous to authenticated; remove IP-rate-limiting (use user-based); corrections set `is_verified = false` (pending) |
| NEW Expert review API | Endpoints: list pending corrections, approve, reject |
| Admin API | Expand: create user, edit user, deactivate user, search users |
| NEW Permission model | `permissions` table, `role_permissions` table, `user_permission_overrides` table |
| NEW Permission middleware | Check permissions by role defaults + per-user overrides |

#### UX/Frontend

| Component | Change |
|-----------|--------|
| UserList.tsx | Add "Chuyên gia" (Expert) option to role dropdown; add user status column; add create/edit/deactivate actions |
| Correction panel | Require login; show pending state; remove auto-verify |
| Lookup detail page | Show correction status (pending/approved/rejected) instead of binary verified/unverified |
| NEW: Expert review page | Dashboard for experts to review pending corrections |
| NEW: Permission management page | Admin UI for role permissions and per-user overrides |

---

## 3. Recommended Approach

### Selected Path: Direct Adjustment (Option 1)

**Create a new Epic 5 with 5 stories** that extend the existing auth system. No rollbacks needed — Epic 4 provides a solid foundation.

**Rationale:**
- Low risk — builds on proven auth patterns
- No existing work invalidated
- Clear separation of concerns (new epic, new stories)
- Existing corrections code can be incrementally refactored

**Effort Estimate:** Medium (5 stories, ~1 sprint)
**Risk Level:** Low
**Timeline Impact:** +1 sprint before Epic 5 (Favorites, now Epic 6)

---

## 4. Detailed Change Proposals

### 4.1 PRD Changes

#### FR35 Modification

```
Story: PRD Section 9 - User Authentication
Section: FR35

OLD:
- **FR35:** Admins can assign user roles (standard user, admin)

NEW:
- **FR35:** Admins can assign user roles (standard user, expert, admin)

Rationale: Expert role needed for correction approval workflow
```

#### New Functional Requirements (FR65-FR70)

```
Section: PRD Section 9 - NEW "Role-Based Permissions & User Management"

NEW:
### Role-Based Permissions & User Management (ADDED 2026-02-18)

- **FR65:** Only users with the "expert" role can approve or reject pending corrections to lookup records
- **FR66:** Only authenticated (logged-in) users can submit corrections to lookup records
- **FR67:** Admins can view and configure default permissions for each role (user, expert, admin)
- **FR68:** Admins can override permissions for individual users (grant or revoke specific permissions)
- **FR69:** Admins can create, edit, deactivate, and search user accounts
- **FR70:** Corrections follow a status workflow: pending → approved/rejected by expert

Rationale: Production-quality knowledge base requires gated approval workflow and granular access control
```

### 4.2 Architecture Changes

#### User Model Expansion

```
File: api/app/models/user.py

OLD:
role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")

NEW:
role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    # Valid roles: "user", "expert", "admin"
is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

Rationale: Support expert role and soft-delete via deactivation
```

#### LookupRecord Model Expansion

```
File: api/app/models/lookup_record.py

OLD:
is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
verified_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

NEW:
is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
verified_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
submitted_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
correction_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Values: "pending", "approved", "rejected", null (no correction submitted)
rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

Rationale: Track who submitted corrections and support approval workflow
```

#### Auth Middleware Expansion

```
File: api/app/core/auth.py

NEW FUNCTIONS:
- require_authenticated(request) → dict  # Any logged-in user (user/expert/admin)
- require_expert(request) → dict  # Expert or admin role
- get_optional_user(request) → dict | None  # Returns user if logged in, None otherwise

Rationale: Granular role requirements for different endpoints
```

#### New Database Tables

```
NEW: permissions table
- id: int (PK)
- code: str (unique, e.g., "correction.submit", "correction.approve", "user.manage")
- name: str (display name)
- description: str

NEW: role_permissions table
- id: int (PK)
- role: str ("user", "expert", "admin")
- permission_code: str (FK → permissions.code)
- Unique constraint on (role, permission_code)

NEW: user_permission_overrides table
- id: int (PK)
- user_id: int (FK → users.id)
- permission_code: str (FK → permissions.code)
- granted: bool (true = grant, false = revoke)
- Unique constraint on (user_id, permission_code)

Default role permissions:
- user: correction.submit
- expert: correction.submit, correction.approve
- admin: ALL permissions

Rationale: Flexible permission system with role defaults + per-user overrides
```

### 4.3 Epic & Story Changes

#### New Epic 5: Advanced RBAC, Permissions & User Management

```
Epic: NEW Epic 5
Title: Advanced RBAC, Permissions & User Management

FRs covered: FR35 (modified), FR65, FR66, FR67, FR68, FR69, FR70

Description:
Expand the authentication system with an Expert role for correction approval,
authenticated correction submission, a permission management system with
role defaults and per-user overrides, and comprehensive admin user management.

Stories: 5 stories (see below)
```

#### Renumber Existing Epics

```
Epic 5 (Favorites & History) → Epic 6
Epic 6 (Advanced Search) → Epic 7
Epic 7 (Admin Data Management) → Epic 8

All story IDs renumber accordingly:
5-1 through 5-8 → 6-1 through 6-8
6-1 through 6-3 → 7-1 through 7-3
7-1 through 7-5 → 8-1 through 8-5
```

#### Story 5-1: Add Expert Role and Auth Middleware

```
As an administrator,
I want to assign the "expert" role to users,
So that designated experts can approve corrections to the knowledge base.

Acceptance Criteria:
- User model supports three roles: "user", "expert", "admin"
- User model has is_active field for account deactivation
- Auth middleware provides: require_authenticated, require_expert, get_optional_user
- RoleUpdateRequest validates "user", "expert", "admin"
- UserList dropdown shows three role options
- DB migration adds is_active column with default true
- Existing users unaffected (remain "user" or "admin")
- Inactive users cannot log in

Technical Tasks:
1. DB migration: Add is_active (bool, default=true) to users table
2. Update User model with is_active field
3. Update auth.py: add require_authenticated, require_expert, get_optional_user
4. Update RoleUpdateRequest validator to accept "expert"
5. Update UserList.tsx dropdown to include "Chuyên gia" (Expert)
6. Update login flow to reject inactive users
7. Tests for all new auth dependencies

FRs: FR35 (modified)
```

#### Story 5-2: Authenticated Corrections with Pending Status

```
As a logged-in user,
I want to submit corrections to lookup records,
So that the knowledge base improves through accountable user contributions.

Acceptance Criteria:
- POST /api/corrections requires authentication (no anonymous submissions)
- Corrections set correction_status = "pending" (not auto-verified)
- Corrections record submitted_by_user_id
- is_verified remains false until expert approval
- Rate limiting changes from IP-based to user-based (10/hour per user)
- Unauthenticated users see "Đăng nhập để gửi chỉnh sửa" (Login to submit corrections)
- Already-approved corrections cannot be re-submitted

Technical Tasks:
1. DB migration: Add submitted_by_user_id, correction_status, rejection_reason to lookup_records
2. Update LookupRecord model
3. Modify corrections.py: replace anonymous with require_authenticated
4. Change rate limiting from IP-based to user-based
5. Set correction_status = "pending", is_verified = false on submit
6. Update CorrectionPanel component to require login
7. Show "pending" badge on submitted corrections
8. Tests for authenticated correction flow

FRs: FR66, FR70
```

#### Story 5-3: Expert Correction Approval Workflow

```
As an expert user,
I want to review and approve or reject pending corrections,
So that the knowledge base maintains high quality through expert verification.

Acceptance Criteria:
- GET /api/expert/corrections?status=pending returns paginated pending corrections
- POST /api/expert/corrections/{id}/approve sets is_verified=true, correction_status="approved"
- POST /api/expert/corrections/{id}/reject sets correction_status="rejected" with reason
- Expert endpoints require "expert" or "admin" role
- Expert review page at /expert/corrections shows pending corrections with:
  - Original query, matched HS code, suggested correction, submitter info, notes
  - Approve / Reject buttons
- Approved corrections immediately affect knowledge base search
- Rejected corrections notify submitter (via UI status, not email)
- Audit log records all approval/rejection actions

Technical Tasks:
1. Create expert review API: api/app/api/expert.py
2. Create expert review service: api/app/services/expert_service.py
3. Build /expert/corrections page with PendingCorrectionsList component
4. Build CorrectionReviewCard component (approve/reject buttons, reasoning display)
5. Update lookup detail page to show correction_status (pending/approved/rejected)
6. Add audit logging for expert actions
7. Tests for approval/rejection workflow

FRs: FR65, FR70
```

#### Story 5-4: Admin User Management

```
As an administrator,
I want to create, edit, deactivate, and search user accounts,
So that I have full control over who can access the system.

Acceptance Criteria:
- Admin can create new users: POST /api/admin/users (email, password, role)
- Admin can edit user details: PATCH /api/admin/users/{id} (email, role)
- Admin can deactivate/reactivate users: PATCH /api/admin/users/{id}/status
- Admin can search users by email: GET /api/admin/users?search=query
- User list shows: email, role, status (active/inactive), created date, last login
- Deactivated users cannot log in but data is preserved
- Admin cannot deactivate themselves
- All admin actions logged to audit trail
- Confirmation dialog for deactivation

Technical Tasks:
1. Add create_user endpoint to admin.py
2. Add update_user endpoint to admin.py
3. Add toggle_user_status endpoint to admin.py
4. Add search parameter to list_users endpoint
5. Expand UserList.tsx with create/edit/deactivate actions
6. Add user search input to admin users page
7. Add status column and indicator to user table
8. Add last_login tracking to user model (optional)
9. Tests for all CRUD operations

FRs: FR69
```

#### Story 5-5: Admin Permission Management

```
As an administrator,
I want to manage permissions per role and per individual user,
So that I can fine-tune access control beyond the default role-based system.

Acceptance Criteria:
- Permission model with predefined permissions:
  - correction.submit: Can submit corrections
  - correction.approve: Can approve/reject corrections
  - user.manage: Can manage users
  - data.manage: Can manage tariff data
  - lookup.view_all: Can view all lookups (not just own)
- Default role permissions:
  - user: correction.submit
  - expert: correction.submit, correction.approve, lookup.view_all
  - admin: ALL permissions
- Admin can view role-level default permissions at /admin/permissions
- Admin can add/remove per-user permission overrides
- Permission check middleware: has_permission(user, "permission.code")
- Frontend shows effective permissions (role defaults + overrides) per user
- Overrides displayed as "granted" (green) or "revoked" (red) badges

Technical Tasks:
1. DB migration: Create permissions, role_permissions, user_permission_overrides tables
2. Create Permission, RolePermission, UserPermissionOverride models
3. Create permission_service.py with has_permission() check
4. Seed default permissions and role mappings
5. Create API endpoints: GET/PUT /api/admin/permissions/roles/{role}
6. Create API endpoints: GET/PUT /api/admin/permissions/users/{id}
7. Build /admin/permissions page with role-level and per-user tabs
8. Integrate permission checks into existing endpoints (replace hardcoded role checks)
9. Tests for permission checking logic

FRs: FR67, FR68
```

### 4.4 Sprint Status Changes

```
File: _bmad-output/implementation-artifacts/sprint-status.yaml

CHANGES:
- Add new Epic 5 section with 5 stories (all backlog)
- Renumber Epic 5 → 6, Epic 6 → 7, Epic 7 → 8
- Renumber all story IDs accordingly
```

---

## 5. Implementation Handoff

### Change Scope: Moderate

This requires backlog reorganization (new epic, story renumbering) and 5 new stories with backend + frontend work.

### Handoff Plan

| Recipient | Responsibility |
|-----------|---------------|
| **Scrum Master (SM)** | Create stories 5-1 through 5-5 via create-story workflow |
| **Development Team** | Implement stories in order (5-1 is foundational) |
| **Product Owner** | Approve final story acceptance criteria, prioritize against Epic 6+ |

### Implementation Order (Dependencies)

```
5-1 (Expert Role + Auth) ← Foundation, must be first
  ↓
5-2 (Authenticated Corrections) ← Depends on 5-1 auth middleware
  ↓
5-3 (Expert Approval Workflow) ← Depends on 5-2 pending status
  ↓
5-4 (User Management) ← Can run in parallel with 5-3
  ↓
5-5 (Permission Management) ← Depends on 5-1, can run in parallel with 5-3/5-4
```

### Success Criteria

- [ ] Expert role functional with correction approval/rejection
- [ ] No anonymous corrections possible
- [ ] All corrections go through pending → approved/rejected workflow
- [ ] Admin can CRUD users with role assignment (user/expert/admin)
- [ ] Permission system with role defaults and per-user overrides
- [ ] All existing functionality unaffected
- [ ] Knowledge base quality gated by expert approval

---

**Sprint Change Proposal Status:** APPROVED (2026-02-18, tinsu)
