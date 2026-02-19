# Story 5.3: Expert Correction Approval Workflow

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **expert user**,
I want **to review and approve or reject pending corrections**,
So that **the knowledge base maintains high quality through expert verification**.

## Acceptance Criteria

1. **Given** I am logged in with "expert" or "admin" role, **When** I navigate to `/expert/corrections`, **Then** I see a paginated list of pending corrections with: original query text, matched HS code and description, suggested correct HS code and description, submitter email and submission date, and notes from submitter.

2. **Given** I am viewing a pending correction, **When** I click "Phe duyet" (Approve), **Then** `is_verified = true`, `correction_status = "approved"`, `verified_by_user_id = my ID`, `verified_at = now()` **And** the knowledge base is updated for future searches **And** I see "Da phe duyet chinh sua" (Correction approved).

3. **Given** I am viewing a pending correction, **When** I click "Tu choi" (Reject) and provide a reason, **Then** `correction_status = "rejected"`, `rejection_reason` is saved **And** the original matched HS code remains unchanged **And** I see "Da tu choi chinh sua" (Correction rejected).

4. **Given** I am a standard "user" role, **When** I try to access `/expert/corrections`, **Then** I am shown "Khong co quyen truy cap" (Access denied) **Or** redirected to login.

5. **Given** an expert approves or rejects a correction, **When** the action completes, **Then** an audit log entry is created with action type, expert user ID, lookup record ID, and decision details.

6. **Given** the pending corrections list, **When** there are many corrections, **Then** pagination works correctly with page/per_page parameters (default 20 per page).

## Tasks / Subtasks

- [x] Task 1: Create `api/app/api/expert.py` with expert review endpoints (AC: #1, #2, #3, #4, #6)
  - [x] 1.1 Create router with `prefix="/api/expert"`, `tags=["expert"]`
  - [x] 1.2 `GET /corrections` endpoint: paginated pending corrections list, protected by `require_expert`
  - [x] 1.3 `POST /corrections/{id}/approve` endpoint: approve a pending correction, protected by `require_expert`
  - [x] 1.4 `POST /corrections/{id}/reject` endpoint: reject with reason, protected by `require_expert`

- [x] Task 2: Create `api/app/services/expert_service.py` (AC: #2, #3, #5)
  - [x] 2.1 `ExpertService` class with `LookupRecordRepository` and `AuditLogRepository`
  - [x] 2.2 `list_pending_corrections(page, per_page)` method: query pending corrections with eager-loaded HS codes and submitter user
  - [x] 2.3 `approve_correction(record_id, expert_user_id)` method: set `is_verified=true`, `correction_status="approved"`, `verified_by_user_id`, `verified_at`, create audit log
  - [x] 2.4 `reject_correction(record_id, expert_user_id, reason)` method: set `correction_status="rejected"`, `rejection_reason`, create audit log

- [x] Task 3: Add repository methods for expert workflow (AC: #1, #2, #3, #6)
  - [x] 3.1 `get_pending_corrections(limit, offset)` in `LookupRecordRepository`: query `correction_status="pending"` with eager-loaded `matched_hs_code`, `correct_hs_code`, `submitted_by_user`
  - [x] 3.2 `count_pending_corrections()` in `LookupRecordRepository`
  - [x] 3.3 `approve_correction(record_id, verified_by_user_id)` in `LookupRecordRepository`: update `is_verified=True`, `correction_status="approved"`, `verified_by_user_id`, `verified_at=now()`
  - [x] 3.4 `reject_correction(record_id, rejection_reason)` in `LookupRecordRepository`: update `correction_status="rejected"`, `rejection_reason`

- [x] Task 4: Create expert schemas (AC: #1, #2, #3)
  - [x] 4.1 Create `api/app/schemas/expert.py` with `PendingCorrectionItem`, `PaginatedPendingCorrectionsResponse`, `ApproveResponse`, `RejectRequest`, `RejectResponse`

- [x] Task 5: Register expert router in `main.py` (AC: #1)
  - [x] 5.1 Import and register expert router in `api/app/main.py`

- [x] Task 6: Add `/expert/:path*` route protection in `proxy.ts` (AC: #4)
  - [x] 6.1 Add `"/expert/:path*"` to the `matcher` array in `web/src/proxy.ts`

- [x] Task 7: Build `/expert/corrections` page (AC: #1, #2, #3, #4, #6)
  - [x] 7.1 Create `web/src/app/expert/corrections/page.tsx` as client component
  - [x] 7.2 Check user role: if not expert/admin, show "Khong co quyen truy cap" (Access denied)
  - [x] 7.3 Fetch and display paginated list of pending corrections from `GET /api/expert/corrections`
  - [x] 7.4 Each card shows: query text, matched HS code + description, suggested correct HS code + description, submitter email, submission date, notes
  - [x] 7.5 "Phe duyet" (Approve) button calls `POST /api/expert/corrections/{id}/approve`
  - [x] 7.6 "Tu choi" (Reject) button opens textarea for reason, calls `POST /api/expert/corrections/{id}/reject`
  - [x] 7.7 Success/error toast messages in Vietnamese
  - [x] 7.8 Pagination controls

- [x] Task 8: Update lookup detail page to show approved/rejected status (AC: #2, #3)
  - [x] 8.1 Ensure correction status badges ("Da phe duyet"/"Da tu choi") are properly displayed (verify from Story 5-2 work)
  - [x] 8.2 Show `verified_by_user_id` info and `verified_at` on approved corrections
  - [x] 8.3 Show `rejection_reason` on rejected corrections

- [x] Task 9: Add navigation link for experts (AC: #1)
  - [x] 9.1 Add "Duyet chinh sua" (Review corrections) link in header/nav for expert and admin users

- [x] Task 10: Backend tests (AC: #1-#6)
  - [x] 10.1 `api/app/api/expert_test.py`: test GET pending corrections requires expert role
  - [x] 10.2 `api/app/api/expert_test.py`: test GET pending corrections returns paginated results
  - [x] 10.3 `api/app/api/expert_test.py`: test POST approve sets is_verified and correction_status
  - [x] 10.4 `api/app/api/expert_test.py`: test POST reject sets rejection_reason and correction_status
  - [x] 10.5 `api/app/api/expert_test.py`: test standard user gets 403 on expert endpoints
  - [x] 10.6 `api/app/api/expert_test.py`: test approve on non-pending record returns error
  - [x] 10.7 `api/app/api/expert_test.py`: test audit log created on approve/reject
  - [x] 10.8 `api/app/services/expert_service_test.py`: test approve_correction service logic
  - [x] 10.9 `api/app/services/expert_service_test.py`: test reject_correction service logic
  - [x] 10.10 `api/app/repositories/lookup_record_repository_test.py`: test get_pending_corrections
  - [x] 10.11 `api/app/repositories/lookup_record_repository_test.py`: test approve_correction repository
  - [x] 10.12 `api/app/repositories/lookup_record_repository_test.py`: test reject_correction repository

- [x] Task 11: Frontend tests (AC: #1, #2, #3, #4)
  - [x] 11.1 `web/src/app/expert/corrections/page.test.tsx`: test shows access denied for user role
  - [x] 11.2 `web/src/app/expert/corrections/page.test.tsx`: test displays pending corrections list
  - [x] 11.3 `web/src/app/expert/corrections/page.test.tsx`: test approve button triggers API call
  - [x] 11.4 `web/src/app/expert/corrections/page.test.tsx`: test reject with reason triggers API call

## Dev Notes

### CRITICAL: This Story Creates NEW Expert Endpoints and Page

This story adds the expert correction approval workflow. It builds on Stories 5-1 (expert role + auth middleware) and 5-2 (authenticated corrections with pending status). The foundation is fully in place.

**Already exists (DO NOT recreate):**
- `api/app/core/auth.py` -- `require_expert` dependency (from Story 5-1): validates JWT, checks role in ("expert", "admin"), returns user dict `{id, email, role}`, raises 403 if not expert
- `api/app/models/lookup_record.py` -- LookupRecord model with `correction_status`, `rejection_reason`, `submitted_by_user_id`, `verified_by_user_id`, `verified_at` fields (from Stories 1-8, 5-2)
- `api/app/repositories/lookup_record_repository.py` -- `apply_correction()` method that sets `is_verified=True` (from Story 1-8). **USE THIS AS PATTERN for approve, but also set `correction_status="approved"` and `verified_by_user_id`**
- `api/app/models/audit_log.py` -- AuditLog model with `admin_user_id`, `action`, `target_user_id`, `details` JSONB (from Story 4-5)
- `api/app/repositories/audit_log_repository.py` -- `create()` method for audit entries (from Story 4-5)
- `api/app/schemas/base.py` -- `success_response()`, `error_response()` envelope helpers
- `web/src/lib/api.ts` -- `apiClient` with GET/POST/PATCH/PUT/DELETE methods, `credentials: 'include'`
- `web/src/proxy.ts` -- Route protection for `/admin/:path*` (needs `/expert/:path*` added)
- `web/src/types/lookup.ts` -- `LookupDetail` with `correction_status`, `submitted_by_user_id` fields
- Correction status badges on lookup detail page (from Story 5-2): pending/approved/rejected badges

**What this story CREATES (new code):**
- `api/app/api/expert.py` -- New router with GET pending list, POST approve, POST reject
- `api/app/services/expert_service.py` -- Expert business logic (list, approve, reject)
- `api/app/schemas/expert.py` -- Pydantic schemas for expert API
- `web/src/app/expert/corrections/page.tsx` -- Expert review page
- New repository methods on `LookupRecordRepository`: `get_pending_corrections`, `count_pending_corrections`, `approve_correction`, `reject_correction`

**What this story MODIFIES (existing code):**
- `api/app/main.py` -- Register expert router
- `web/src/proxy.ts` -- Add `/expert/:path*` to matcher
- Header/nav component -- Add expert link (conditional on role)

### Backend Architecture: Layered Pattern

Follow the strict layered architecture:

```
expert.py (API) -> expert_service.py (Service) -> lookup_record_repository.py + audit_log_repository.py (Repositories)
```

**Route handler (`expert.py`):** ONLY validates request, calls service, formats response with `success_response()`/`error_response()`. NO business logic.

**Service (`expert_service.py`):** ALL business logic. Validates record exists, checks correction_status is "pending", calls repository methods, creates audit log entries.

**Repository:** ONLY database queries. New methods added to existing `LookupRecordRepository`.

### Expert API Endpoint Details

```python
# api/app/api/expert.py

# GET /api/expert/corrections?status=pending&page=1&per_page=20
# - Protected by require_expert
# - Returns paginated PendingCorrectionItem list
# - Each item includes: id, query_text, matched_hs_code (code + descriptions),
#   correct_hs_code (code + descriptions), submitter_email, submitted_at, notes

# POST /api/expert/corrections/{id}/approve
# - Protected by require_expert
# - Sets is_verified=true, correction_status="approved", verified_by_user_id, verified_at
# - Creates audit log
# - Returns approved record summary

# POST /api/expert/corrections/{id}/reject
# - Protected by require_expert
# - Body: { "reason": "string" } (required, min 1 char)
# - Sets correction_status="rejected", rejection_reason
# - Creates audit log
# - Returns rejected record summary
```

### Repository Methods to Add

```python
# api/app/repositories/lookup_record_repository.py -- ADD these methods

async def get_pending_corrections(self, limit: int = 20, offset: int = 0) -> list[LookupRecord]:
    """Get pending corrections with eager-loaded HS codes and submitter."""
    result = await self.session.execute(
        select(LookupRecord)
        .where(LookupRecord.correction_status == "pending")
        .options(
            selectinload(LookupRecord.matched_hs_code),
            selectinload(LookupRecord.correct_hs_code),
            selectinload(LookupRecord.submitted_by_user),
        )
        .order_by(LookupRecord.created_at.asc())  # Oldest first for review queue
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())

async def count_pending_corrections(self) -> int:
    """Count total pending corrections."""
    result = await self.session.execute(
        select(func.count(LookupRecord.id)).where(
            LookupRecord.correction_status == "pending"
        )
    )
    return result.scalar_one()

async def approve_correction(self, record_id: int, verified_by_user_id: int) -> LookupRecord:
    """Approve a pending correction -- sets is_verified, correction_status, verified_by_user_id, verified_at."""
    now = datetime.now(timezone.utc)
    await self.session.execute(
        update(LookupRecord)
        .where(LookupRecord.id == record_id)
        .values(
            is_verified=True,
            correction_status="approved",
            verified_by_user_id=verified_by_user_id,
            verified_at=now,
        )
    )
    result = await self.session.execute(
        select(LookupRecord).where(LookupRecord.id == record_id)
    )
    return result.scalar_one()

async def reject_correction(self, record_id: int, rejection_reason: str) -> LookupRecord:
    """Reject a pending correction -- sets correction_status and rejection_reason."""
    await self.session.execute(
        update(LookupRecord)
        .where(LookupRecord.id == record_id)
        .values(
            correction_status="rejected",
            rejection_reason=rejection_reason,
        )
    )
    result = await self.session.execute(
        select(LookupRecord).where(LookupRecord.id == record_id)
    )
    return result.scalar_one()
```

### Expert Service Pattern

```python
# api/app/services/expert_service.py

class ExpertService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.lookup_repo = LookupRecordRepository(session)
        self.audit_repo = AuditLogRepository(session)

    async def list_pending_corrections(self, page: int = 1, per_page: int = 20) -> dict:
        offset = (page - 1) * per_page
        records = await self.lookup_repo.get_pending_corrections(limit=per_page, offset=offset)
        total = await self.lookup_repo.count_pending_corrections()
        # Build response items from records
        ...

    async def approve_correction(self, record_id: int, expert_user_id: int) -> LookupRecord:
        record = await self.lookup_repo.find_by_id(record_id)
        if not record:
            raise ValueError("Record not found")
        if record.correction_status != "pending":
            raise ValueError("Only pending corrections can be approved")
        updated = await self.lookup_repo.approve_correction(record_id, expert_user_id)
        await self.audit_repo.create(
            admin_user_id=expert_user_id,
            action="correction_approved",
            details={"lookup_record_id": record_id, "correct_hs_code_id": record.correct_hs_code_id},
        )
        return updated

    async def reject_correction(self, record_id: int, expert_user_id: int, reason: str) -> LookupRecord:
        record = await self.lookup_repo.find_by_id(record_id)
        if not record:
            raise ValueError("Record not found")
        if record.correction_status != "pending":
            raise ValueError("Only pending corrections can be rejected")
        updated = await self.lookup_repo.reject_correction(record_id, reason)
        await self.audit_repo.create(
            admin_user_id=expert_user_id,
            action="correction_rejected",
            details={"lookup_record_id": record_id, "reason": reason},
        )
        return updated
```

### Expert Schemas

```python
# api/app/schemas/expert.py

class PendingCorrectionItem(BaseModel):
    id: int
    query_text: str
    matched_hs_code: str | None
    matched_description_vn: str | None
    matched_description_en: str | None
    correct_hs_code: str | None
    correct_description_vn: str | None
    correct_description_en: str | None
    submitter_email: str | None
    submitted_at: str  # created_at ISO format
    notes: str | None

class PaginatedPendingCorrectionsResponse(BaseModel):
    items: list[PendingCorrectionItem]
    total: int
    page: int
    per_page: int

class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500, description="Reason for rejecting the correction")

class ApproveResponse(BaseModel):
    id: int
    correction_status: str
    is_verified: bool
    verified_at: str | None

class RejectResponse(BaseModel):
    id: int
    correction_status: str
    rejection_reason: str
```

### Frontend Expert Review Page

The expert corrections page should be a client component at `web/src/app/expert/corrections/page.tsx`. Key points:

- Use `useSession()` from `next-auth/react` to check user role
- If role is not "expert" or "admin", show access denied message
- Fetch pending corrections from `GET /api/expert/corrections?page=1&per_page=20` using `apiClient`
- Display each correction as a card/row with all required fields
- "Phe duyet" (Approve) button: confirm dialog, then POST to approve endpoint
- "Tu choi" (Reject) button: opens textarea for reason, then POST to reject endpoint
- On success, remove the card from the list and show success toast
- Pagination controls at bottom

### Route Protection

```typescript
// web/src/proxy.ts -- ADD /expert/:path* to matcher
export const config = {
  matcher: ["/favorites/:path*", "/history/:path*", "/admin/:path*", "/expert/:path*"],
};
```

### Navigation Link

Add a "Duyet chinh sua" link in the header nav for expert and admin users. Check the existing header component to see where admin links are rendered and follow the same pattern. The link should be visible only when `session.user.role` is "expert" or "admin".

### Audit Log Pattern

Follow the existing audit log pattern from `admin_service.py`:

```python
await self.audit_repo.create(
    admin_user_id=expert_user_id,  # The expert performing the action
    action="correction_approved",   # or "correction_rejected"
    target_user_id=None,            # No target user (this is about a lookup record)
    details={
        "lookup_record_id": record_id,
        "correct_hs_code_id": record.correct_hs_code_id,  # For approve
        # or "reason": reason  # For reject
    },
)
```

### Project Structure Notes

**New files:**
```
api/app/api/expert.py                               # Expert review endpoints
api/app/api/expert_test.py                           # Expert endpoint tests
api/app/services/expert_service.py                   # Expert business logic
api/app/services/expert_service_test.py              # Expert service tests
api/app/schemas/expert.py                            # Expert API schemas
web/src/app/expert/corrections/page.tsx              # Expert review page
web/src/app/expert/corrections/page.test.tsx         # Expert page tests
```

**Modified files:**
```
api/app/main.py                                      # Register expert router
api/app/repositories/lookup_record_repository.py     # Add get_pending, count_pending, approve, reject methods
api/app/repositories/lookup_record_repository_test.py  # Add tests for new repo methods
web/src/proxy.ts                                     # Add /expert/:path* route protection
web/src/lib/api.ts                                   # Add expert API functions (optional, can use apiClient directly)
web/src/types/lookup.ts                              # Add PendingCorrectionItem type (if needed)
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| `require_expert` dependency | `api/app/core/auth.py` | Expert/admin role gate (from Story 5-1) |
| Service + repo + audit pattern | `api/app/services/admin_service.py` | `AdminService` with repos, audit log creation after validation |
| `AuditLogRepository.create()` | `api/app/repositories/audit_log_repository.py` | Audit log entry creation |
| `apply_correction()` repo method | `api/app/repositories/lookup_record_repository.py` | Pattern for setting `is_verified=True`, `verified_at` |
| `success_response()` / `error_response()` | `api/app/schemas/base.py` | Envelope response format |
| `apiClient.get()` / `apiClient.post()` | `web/src/lib/api.ts` | Frontend API calls with credentials |
| `useSession()` hook | `next-auth/react` | Session state in client components |
| Route protection matcher | `web/src/proxy.ts` | Add `/expert/:path*` |
| Admin router registration | `api/app/main.py` | `app.include_router(expert_router)` pattern |
| `selectinload` for eager loading | `api/app/repositories/lookup_record_repository.py` | Prevent N+1 on HS code and user relationships |
| Correction status badges | `web/src/app/lookups/[id]/page.tsx` | Existing pending/approved/rejected badge styling |
| Vietnamese UI text convention | All frontend components | All user-facing text in Vietnamese |

### Anti-Patterns to AVOID

- **DO NOT** put approval/rejection logic in the route handler -- service layer only
- **DO NOT** create a new repository class for expert operations -- add methods to existing `LookupRecordRepository`
- **DO NOT** skip audit logging -- every approve/reject must create an audit entry
- **DO NOT** allow approving/rejecting non-pending corrections -- validate `correction_status == "pending"` in service
- **DO NOT** use Next.js API routes for expert endpoints -- fetch FastAPI directly with `credentials: 'include'`
- **DO NOT** create tests in a separate `/tests` directory -- co-locate with source files
- **DO NOT** use status enums -- use string values for `correction_status`
- **DO NOT** use camelCase in API JSON responses -- all snake_case
- **DO NOT** forget to eager-load `matched_hs_code`, `correct_hs_code`, `submitted_by_user` relationships -- prevent N+1 queries
- **DO NOT** allow self-approval -- if submitter is the same as the expert, that's acceptable (submitters are always regular users, but just in case, don't add restrictions not in the AC)
- **DO NOT** modify the existing `apply_correction()` method -- create new `approve_correction()` and `reject_correction()` methods
- **DO NOT** forget to add the `/expert/:path*` matcher to `proxy.ts` for route protection

### Previous Story Intelligence (from Stories 5-1 and 5-2)

**From Story 5-1 (expert role + auth):**
- `require_expert` checks `role in ("expert", "admin")`, raises 403 otherwise
- User dict from auth returns `{"id": int, "email": str, "role": str}`
- `UserRole` TypeScript type is `"user" | "expert" | "admin"`
- Frontend `useSession()` provides `session.user.role`
- Code review fixes: Always add docstrings, use Vietnamese text in test assertions

**From Story 5-2 (authenticated corrections):**
- `correction_status` field added: null, "pending", "approved", "rejected"
- `submitted_by_user_id` tracks who submitted the correction
- `rejection_reason` field exists for storing reject reasons
- `submit_pending_correction()` sets `correction_status="pending"`, `is_verified=false`
- `submitted_by_user` relationship on `LookupRecord` already exists
- Correction status badges already implemented on lookup detail page (pending=yellow, approved=green, rejected=red)
- Index `idx_lookup_records_correction_status` exists on `correction_status` column for efficient pending queries
- The existing `apply_correction()` method stays -- Story 5-3 approve should use a new method that also sets `correction_status` and `verified_by_user_id`

**Known pre-existing test failures (ignore):**
- 18 browse component test failures (unrelated)
- 17+ backend test failures in corrections, hs_codes, search, config, excel_parser, auth_integration, browse_repository (all unrelated)

### Git Intelligence

Recent commits:
- `8d65b4e` -- feat 5-2: Authenticated corrections with pending status workflow
- `d725d14` -- feat 5-1: Add expert role, is_active field, and auth middleware dependencies
- `a4a769c` -- feat: Add confidence score tooltips to lookup and search results

Key files from recent work:
- `api/app/core/auth.py` -- `require_authenticated`, `require_expert`, `get_optional_user` (Story 5-1)
- `api/app/repositories/lookup_record_repository.py` -- `submit_pending_correction()`, `apply_correction()` (Story 5-2, 1-8)
- `api/app/models/lookup_record.py` -- Full model with `correction_status`, `rejection_reason`, `submitted_by_user_id`, `verified_by_user_id` (Stories 1-8, 5-2)
- `api/app/models/audit_log.py` -- AuditLog model for tracking expert actions (Story 4-5)
- `api/app/repositories/audit_log_repository.py` -- `create()` for audit entries (Story 4-5)
- `api/app/services/admin_service.py` -- Pattern for service with repo + audit logging (Story 4-5)

### Testing Requirements

**Backend tests** (pytest, asyncio_mode=auto, co-located):

1. `api/app/api/expert_test.py`:
   - `test_get_pending_corrections_requires_expert_role` -- standard user gets 403
   - `test_get_pending_corrections_unauthenticated_returns_401`
   - `test_get_pending_corrections_returns_paginated_results`
   - `test_approve_correction_sets_verified_and_status`
   - `test_approve_correction_creates_audit_log`
   - `test_reject_correction_sets_status_and_reason`
   - `test_reject_correction_creates_audit_log`
   - `test_approve_nonexistent_record_returns_404`
   - `test_approve_non_pending_record_returns_400`
   - `test_reject_without_reason_returns_422`

2. `api/app/services/expert_service_test.py`:
   - `test_approve_correction_calls_repo_and_audit`
   - `test_reject_correction_calls_repo_and_audit`
   - `test_approve_non_pending_raises_error`
   - `test_reject_non_pending_raises_error`
   - `test_approve_nonexistent_raises_error`

3. `api/app/repositories/lookup_record_repository_test.py` (additions):
   - `test_get_pending_corrections_returns_only_pending`
   - `test_count_pending_corrections`
   - `test_approve_correction_sets_all_fields`
   - `test_reject_correction_sets_status_and_reason`

**Frontend tests** (Vitest, jsdom, co-located):

4. `web/src/app/expert/corrections/page.test.tsx`:
   - `test_shows_access_denied_for_user_role`
   - `test_displays_pending_corrections_list`
   - `test_approve_button_calls_api_and_removes_card`
   - `test_reject_with_reason_calls_api`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.3: Expert Correction Approval Workflow]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-18.md#Story 5-3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Backend Architecture]
- [Source: _bmad-output/implementation-artifacts/5-1-add-expert-role-and-auth-middleware.md]
- [Source: _bmad-output/implementation-artifacts/5-2-authenticated-corrections-with-pending-status.md]
- [Source: _bmad-output/project-context.md#Auth Flow (CRITICAL)]
- [Source: CLAUDE.md#Architecture -- Backend Layering]
- [Source: CLAUDE.md#Auth Flow]
- [Source: api/app/core/auth.py -- require_expert dependency]
- [Source: api/app/models/lookup_record.py -- LookupRecord with correction fields]
- [Source: api/app/repositories/lookup_record_repository.py -- apply_correction pattern]
- [Source: api/app/models/audit_log.py -- AuditLog model]
- [Source: api/app/repositories/audit_log_repository.py -- create() method]
- [Source: api/app/services/admin_service.py -- service + audit pattern]
- [Source: api/app/schemas/base.py -- envelope response helpers]
- [Source: web/src/lib/api.ts -- apiClient]
- [Source: web/src/proxy.ts -- route protection matcher]

## Change Log

- 2026-02-18: Implemented expert correction approval workflow - all 11 tasks completed, 20 backend tests + 4 frontend tests passing.
- 2026-02-18: Code review (DEV 2) — 4 issues found and fixed automatically: (H1) expert.py standardized to use get_db instead of get_db_session for consistency with all other routers; (M1) removed unused MagicMock import from expert_service_test.py; (M2) renamed MockLookupRepo/MockAuditRepo parameters to lowercase mock_lookup_repo_cls/mock_audit_repo_cls to fix ruff N803 violations across 5 test methods; (M3) strengthened test_reject_without_reason_returns_422 to assert pydantic.ValidationError specifically instead of bare Exception. All 63 backend tests and 4 frontend tests pass. Ruff lint clean.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- All 16 expert endpoint tests pass
- All 5 expert service tests pass
- All 4 new repository tests pass (63 total repo tests passing)
- All 4 frontend tests pass
- Ruff lint check passes on all new/modified files

### Completion Notes List

- Created full expert correction approval workflow following strict layered architecture (router -> service -> repository)
- Expert API router (`/api/expert`) with GET pending corrections, POST approve, POST reject endpoints
- ExpertService handles all business logic: validates record exists, checks correction_status=="pending", calls repo, creates audit log
- Added 4 new repository methods to LookupRecordRepository: get_pending_corrections, count_pending_corrections, approve_correction, reject_correction
- Expert corrections page at `/expert/corrections` with role-based access control, paginated list, approve/reject actions with smooth dismiss animation
- Added verified_by_user_id and rejection_reason to lookup detail API response and frontend type
- Updated lookup detail page to show rejection reason for rejected corrections and verifier info for approved corrections
- Added "Duyet chinh sua" navigation link for expert/admin users in both desktop and mobile header
- Added `/expert/:path*` route protection in proxy.ts
- All UI text in Vietnamese as required

### File List

**New files:**
- api/app/api/expert.py
- api/app/api/expert_test.py
- api/app/services/expert_service.py
- api/app/services/expert_service_test.py
- api/app/schemas/expert.py
- web/src/app/expert/corrections/page.tsx
- web/src/app/expert/corrections/page.test.tsx

**Modified files:**
- api/app/main.py (registered expert router)
- api/app/repositories/lookup_record_repository.py (added get_pending_corrections, count_pending_corrections, approve_correction, reject_correction methods)
- api/app/repositories/lookup_record_repository_test.py (added 4 tests for new repo methods)
- api/app/schemas/lookup.py (added verified_by_user_id, rejection_reason fields)
- api/app/api/lookups.py (added verified_by_user_id, rejection_reason to detail response)
- web/src/proxy.ts (added /expert/:path* to matcher)
- web/src/types/lookup.ts (added verified_by_user_id, rejection_reason fields)
- web/src/app/lookups/[id]/page.tsx (added rejection reason display, verifier info)
- web/src/components/layout/Header.tsx (added expert nav link for expert/admin users)
