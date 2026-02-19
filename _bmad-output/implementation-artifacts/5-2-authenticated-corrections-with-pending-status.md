# Story 5.2: Authenticated Corrections with Pending Status

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **logged-in user**,
I want **to submit corrections to lookup records**,
So that **the knowledge base improves through accountable user contributions**.

**Background:** This story supersedes Story 1-10's anonymous correction design. Corrections now require authentication and go through an approval workflow instead of auto-verifying.

## Acceptance Criteria

1. **Given** I am not logged in, **When** I try to submit a correction, **Then** I see "Dang nhap de gui chinh sua" (Login to submit corrections) **And** the correction panel shows a login link.

2. **Given** I am logged in, **When** I submit a correction for a lookup record, **Then** the correction is saved with `correction_status = "pending"` and `is_verified = false` **And** `submitted_by_user_id` is set to my user ID **And** I see "Chinh sua da duoc gui, dang cho duyet" (Correction submitted, pending approval).

3. **Given** a lookup with a pending correction, **When** I view the lookup detail page, **Then** I see a "Dang cho duyet" (Pending) badge on the correction section.

4. **Given** a lookup already has an approved correction, **When** I try to submit another correction, **Then** I see "Tra cuu nay da duoc chinh sua" (This lookup has already been corrected).

5. **Given** I am logged in, **When** I submit more than 10 corrections per hour, **Then** I see rate limit message (per-user, not per-IP).

6. **Given** a lookup already has a pending correction, **When** I try to submit another correction, **Then** I see a message indicating a correction is already pending review.

## Tasks / Subtasks

- [x] Task 1: DB migration — Add `submitted_by_user_id`, `correction_status`, `rejection_reason` to `lookup_records` (AC: #2, #3)
  - [x] 1.1 Create Alembic migration: adds `submitted_by_user_id` (FK to users.id, nullable), `correction_status` (varchar(20), nullable), `rejection_reason` (text, nullable)
  - [x] 1.2 Verify migration is backward-compatible: existing rows get NULL for all new columns
  - [x] 1.3 Chain from `add_is_active_to_users` revision

- [x] Task 2: Update `LookupRecord` model with new fields (AC: #2, #3)
  - [x] 2.1 Add `submitted_by_user_id` (FK to users.id, nullable) to `api/app/models/lookup_record.py`
  - [x] 2.2 Add `correction_status` (String(20), nullable) — valid values: null, "pending", "approved", "rejected"
  - [x] 2.3 Add `rejection_reason` (Text, nullable)
  - [x] 2.4 Add relationship for `submitted_by_user` (to User model)

- [x] Task 3: Modify `corrections.py` — Replace anonymous access with `require_authenticated` (AC: #1, #2, #4, #5, #6)
  - [x] 3.1 Import `require_authenticated` from `api/app/core/auth.py`
  - [x] 3.2 Add `user: dict = Depends(require_authenticated)` to `submit_correction` endpoint
  - [x] 3.3 Set `submitted_by_user_id = user["id"]` on correction
  - [x] 3.4 Set `correction_status = "pending"` and keep `is_verified = false`
  - [x] 3.5 Check for existing pending correction on the lookup before allowing submission
  - [x] 3.6 Check for existing approved correction (current check for `is_verified and correct_hs_code_id`) — update error message to Vietnamese
  - [x] 3.7 Update `apply_correction` repository call → replace with new `submit_pending_correction` method

- [x] Task 4: Change rate limiting from IP-based to user-based (AC: #5)
  - [x] 4.1 Modify `check_correction_rate_limit` to accept `user_id: int` instead of `client_ip: str`
  - [x] 4.2 Change Redis key from `correction_rate:{client_ip}` to `correction_rate:user:{user_id}`
  - [x] 4.3 Remove `get_client_ip` import (no longer needed for corrections)

- [x] Task 5: Update `LookupRecordRepository` — Add `submit_pending_correction` method (AC: #2, #6)
  - [x] 5.1 Add `submit_pending_correction(record_id, correct_hs_code_id, submitted_by_user_id, notes)` method
  - [x] 5.2 This method sets `correction_status = "pending"`, `is_verified = false`, `submitted_by_user_id`, `correct_hs_code_id`, `notes`
  - [x] 5.3 Keep existing `apply_correction` method (will be used by expert approval in Story 5-3)

- [x] Task 6: Update `CorrectionPanel` component — Require login, show pending state (AC: #1, #2, #3)
  - [x] 6.1 Accept `session` or `isAuthenticated` prop (from NextAuth useSession)
  - [x] 6.2 If not authenticated, show login prompt with "Dang nhap de gui chinh sua" and a link to `/login`
  - [x] 6.3 On successful submission, show "Chinh sua da duoc gui, dang cho duyet" instead of current generic success message
  - [x] 6.4 Update confirmation dialog text to reflect pending workflow ("correction will be reviewed before applying")

- [x] Task 7: Update lookup detail page — Show correction_status badges (AC: #3)
  - [x] 7.1 In `web/src/app/lookups/[id]/page.tsx`, display correction status badge: "Đang chờ duyệt" (Pending, yellow), "Đã phê duyệt" (Approved, green), "Đã từ chối" (Rejected, red)
  - [x] 7.2 Show pending correction note if correction is pending
  - [x] 7.3 If correction is rejected, show rejection reason

- [x] Task 8: Update correction schema to include new fields (AC: #2)
  - [x] 8.1 Add `correction_status` and `submitted_by_user_id` to `CorrectionResponse`
  - [x] 8.2 Update response description strings

- [x] Task 9: Tests for authenticated correction flow (AC: #1-#6)
  - [x] 9.1 Backend: test unauthenticated user gets 401 on POST /api/corrections
  - [x] 9.2 Backend: test authenticated user can submit correction with pending status
  - [x] 9.3 Backend: test submitted_by_user_id is set correctly
  - [x] 9.4 Backend: test rate limiting is per user_id not per IP
  - [x] 9.5 Backend: test duplicate correction on already-approved lookup rejected
  - [x] 9.6 Backend: test duplicate correction on pending lookup rejected
  - [x] 9.7 Frontend: test CorrectionPanel shows login prompt when not authenticated
  - [x] 9.8 Frontend: test CorrectionPanel shows pending success message on submit

## Dev Notes

### CRITICAL: This Story Modifies the Existing Correction System from Story 1-10

This story fundamentally changes how corrections work. The existing system (Story 1-10) allows **anonymous** corrections that auto-verify. This story makes corrections **authenticated** with a **pending** approval workflow.

**Currently exists (MODIFY, do NOT recreate from scratch):**
- `api/app/api/corrections.py` — Anonymous correction endpoint with IP-based rate limiting
- `api/app/repositories/lookup_record_repository.py` — `apply_correction()` method (sets `is_verified=True` immediately)
- `api/app/schemas/correction.py` — `CorrectionRequest`, `CorrectionResponse`, `LookupRecordItem`, `PaginatedLookupResponse`
- `api/app/models/lookup_record.py` — LookupRecord model with `is_verified`, `verified_by_user_id`, `verified_at`, but **missing** `submitted_by_user_id`, `correction_status`, `rejection_reason`
- `web/src/app/search/components/CorrectionPanel.tsx` — Anonymous correction UI panel
- `web/src/app/lookups/[id]/page.tsx` — Lookup detail page (uses CorrectionPanel)
- `web/src/app/search/page.tsx` — Search page (uses CorrectionPanel)

**What this story CHANGES (modifications to existing code):**
- `corrections.py`: Replace anonymous access with `require_authenticated`, change rate limit from IP-based to user-based, set `correction_status = "pending"` instead of `is_verified = true`
- `lookup_record_repository.py`: Add new `submit_pending_correction()` method (keep `apply_correction` for expert use in Story 5-3)
- `lookup_record.py`: Add `submitted_by_user_id`, `correction_status`, `rejection_reason` columns
- `correction.py` (schemas): Add new fields to response
- `CorrectionPanel.tsx`: Add auth check, show login prompt if unauthenticated, update success message
- Lookup detail page: Add correction status badges

### Database Migration Details

```python
# api/alembic/versions/20260218_add_correction_workflow_columns.py
revision = "add_correction_workflow_columns"
down_revision = "add_is_active_to_users"

def upgrade() -> None:
    op.add_column("lookup_records", sa.Column("submitted_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("lookup_records", sa.Column("correction_status", sa.String(20), nullable=True))
    op.add_column("lookup_records", sa.Column("rejection_reason", sa.Text(), nullable=True))
    # Index for querying pending corrections (Story 5-3 will need this)
    op.create_index("idx_lookup_records_correction_status", "lookup_records", ["correction_status"])

def downgrade() -> None:
    op.drop_index("idx_lookup_records_correction_status", table_name="lookup_records")
    op.drop_column("lookup_records", "rejection_reason")
    op.drop_column("lookup_records", "correction_status")
    op.drop_column("lookup_records", "submitted_by_user_id")
```

### LookupRecord Model Updates

```python
# api/app/models/lookup_record.py — ADD these fields (after verified_at):
submitted_by_user_id: Mapped[int | None] = mapped_column(
    ForeignKey("users.id"), nullable=True
)
correction_status: Mapped[str | None] = mapped_column(
    String(20), nullable=True
)  # Valid values: null, "pending", "approved", "rejected"
rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

# ADD relationship:
submitted_by_user: Mapped["User | None"] = relationship(
    "User",
    foreign_keys=[submitted_by_user_id],
)
```

### corrections.py Endpoint Changes

**Key changes to the `submit_correction` endpoint:**

```python
# api/app/api/corrections.py — MODIFY submit_correction

from app.core.auth import require_authenticated

@router.post("", ...)
async def submit_correction(
    body: CorrectionRequest,
    user: dict = Depends(require_authenticated),  # <-- REPLACES Request param
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> dict[str, Any]:
    # User-based rate limiting instead of IP-based
    user_id = user["id"]
    allowed, remaining, reset = await check_correction_rate_limit(redis_client, user_id)
    ...

    # Check for existing APPROVED correction
    if record.is_verified and record.correct_hs_code_id:
        return error_response(
            ...,
            detail="Tra cuu nay da duoc chinh sua",
            ...
        )

    # Check for existing PENDING correction
    if record.correction_status == "pending":
        return error_response(
            type_uri="https://athena.example/errors/correction-pending",
            title="Correction Already Pending",
            status=status.HTTP_409_CONFLICT,
            detail="Chinh sua dang cho duyet",
            instance="/api/corrections",
        )

    # Submit as pending (NOT auto-verified)
    updated_record = await repo.submit_pending_correction(
        record_id=body.lookup_id,
        correct_hs_code_id=body.correct_hs_code_id,
        submitted_by_user_id=user_id,
        notes=body.notes,
    )
    ...
```

### Rate Limiting Change (IP-based to User-based)

```python
# api/app/api/corrections.py — MODIFY check_correction_rate_limit

async def check_correction_rate_limit(
    redis_client: "redis.Redis | None",
    user_id: int,  # <-- Was client_ip: str
) -> tuple[bool, int, int]:
    """Check per-user rate limit for corrections (10/hour)."""
    if not redis_client:
        return True, CORRECTION_RATE_LIMIT, CORRECTION_RATE_WINDOW

    key = f"{CORRECTION_RATE_PREFIX}user:{user_id}"  # <-- Was ...{client_ip}
    # ... rest stays the same
```

### Repository New Method

```python
# api/app/repositories/lookup_record_repository.py — ADD method

async def submit_pending_correction(
    self,
    record_id: int,
    correct_hs_code_id: int,
    submitted_by_user_id: int,
    notes: str | None = None,
) -> LookupRecord:
    """Submit a correction as pending (requires expert approval).

    Sets correction_status='pending', is_verified=false, and tracks the submitter.
    """
    await self.session.execute(
        update(LookupRecord)
        .where(LookupRecord.id == record_id)
        .values(
            correct_hs_code_id=correct_hs_code_id,
            correction_status="pending",
            is_verified=False,
            submitted_by_user_id=submitted_by_user_id,
            notes=notes,
        )
    )
    result = await self.session.execute(
        select(LookupRecord).where(LookupRecord.id == record_id)
    )
    return result.scalar_one()
```

### CorrectionPanel Auth Integration

The CorrectionPanel needs to check authentication state. Use `useSession()` from NextAuth:

```tsx
// web/src/app/search/components/CorrectionPanel.tsx — MODIFY

import { useSession } from "next-auth/react";
import Link from "next/link";

export function CorrectionPanel({ ... }) {
  const { data: session, status: authStatus } = useSession();

  // If not authenticated, show login prompt
  if (authStatus !== "loading" && !session?.user) {
    return (
      // ... panel with login prompt
      <p>Dang nhap de gui chinh sua</p>
      <Link href="/login">Dang nhap</Link>
    );
  }

  // ... existing correction form logic

  // Update success message:
  // OLD: "Cam on! De xuat cua ban se giup cai thien chat luong tim kiem"
  // NEW: "Chinh sua da duoc gui, dang cho duyet"
}
```

### Lookup Detail Page Badge Updates

```tsx
// web/src/app/lookups/[id]/page.tsx — ADD correction status badges

// Correction status badge logic:
const correctionStatusBadge = (status: string | null) => {
  switch (status) {
    case "pending":
      return <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-semibold rounded-full">Dang cho duyet</span>;
    case "approved":
      return <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs font-semibold rounded-full">Da phe duyet</span>;
    case "rejected":
      return <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-semibold rounded-full">Da tu choi</span>;
    default:
      return null;
  }
};
```

### Project Structure Notes

**Modified files:**
```
api/app/models/lookup_record.py                     # Add submitted_by_user_id, correction_status, rejection_reason
api/app/repositories/lookup_record_repository.py     # Add submit_pending_correction method
api/app/api/corrections.py                           # Replace anonymous with require_authenticated, user-based rate limit
api/app/api/corrections_test.py                      # Update tests for authenticated flow
api/app/schemas/correction.py                        # Add correction_status, submitted_by_user_id to response
web/src/app/search/components/CorrectionPanel.tsx    # Add auth check, login prompt, pending message
web/src/app/lookups/[id]/page.tsx                    # Add correction status badges
```

**New files:**
```
api/alembic/versions/20260218_add_correction_workflow_columns.py  # Migration
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| `require_authenticated` dependency | `api/app/core/auth.py` | From Story 5-1, validates JWT and returns user dict |
| `apply_correction` repository method | `api/app/repositories/lookup_record_repository.py` | Pattern for new `submit_pending_correction` |
| Redis sliding window rate limiting | `api/app/api/corrections.py` | `check_correction_rate_limit()` — change key from IP to user |
| Envelope responses | `api/app/schemas/base.py` | `success_response`, `error_response` |
| `useSession()` hook | `web/src/lib/auth.ts` | NextAuth session in client components |
| Vietnamese UI text | Existing components | All UI text must be in Vietnamese |
| Badge styling | `web/src/app/lookups/[id]/page.tsx` | Existing badge patterns in lookup detail |
| Alembic migration chaining | `api/alembic/versions/20260218_add_is_active_to_users.py` | `down_revision = "add_is_active_to_users"` |

### Anti-Patterns to AVOID

- **DO NOT** keep anonymous correction access — all corrections must require authentication
- **DO NOT** auto-verify corrections (`is_verified = true`) — set `correction_status = "pending"` and `is_verified = false`
- **DO NOT** remove the existing `apply_correction` method — Story 5-3 (expert approval) will use it
- **DO NOT** use IP-based rate limiting — switch to user-based
- **DO NOT** put business logic in route handlers — use the repository for data operations
- **DO NOT** create a separate `/tests` directory — tests are co-located
- **DO NOT** use `get_client_ip` for rate limiting — use `user["id"]` from the authenticated user
- **DO NOT** use status enums — use string values for `correction_status`
- **DO NOT** create Next.js API routes — fetch FastAPI directly with `credentials: 'include'`
- **DO NOT** forget to import `User` model properly (TYPE_CHECKING pattern for relationship)
- **DO NOT** remove the `get_unverified_lookups` endpoint — it's used by the existing correction list (may be superseded in Story 5-3 but keep for now)

### Previous Story Intelligence (from Story 5-1)

**Patterns established:**
- `require_authenticated`, `require_expert`, `get_optional_user` auth dependencies are ready in `api/app/core/auth.py`
- `is_active` check happens at login time (not in middleware), so deactivated users' existing sessions remain valid until JWT expires
- User dict from auth dependencies returns `{"id": int, "email": str, "role": str}`
- Frontend `useSession()` provides `session.user` with `{id, email, role}` in client components
- Tests use mock request pattern with `get_current_user` mocking

**Code review fixes from 5-1 to NOT repeat:**
- Always add docstrings to new methods documenting exceptions raised
- Use Vietnamese text in test assertions (not English)
- Ensure UserRole TypeScript type matches backend allowed values

**Known pre-existing test failures (ignore):**
- 18 browse component test failures (unrelated)
- 17+ backend test failures in corrections, hs_codes, search, config, excel_parser, auth_integration, browse_repository (all unrelated)

### Git Intelligence

Recent relevant commits:
- `d725d14` — feat 5-1: Add expert role, is_active field, and auth middleware dependencies
- `a4a769c` — feat: Add confidence score tooltips to lookup and search results
- `054efc7` — feat 3-3: Persist and display the full NotebookLM raw response

Key established files from Story 5-1:
- `api/app/core/auth.py` — `require_authenticated`, `require_expert`, `get_optional_user` (NEW in 5-1)
- `api/app/services/auth_service.py` — `InactiveUserError` handling (NEW in 5-1)
- `web/src/types/user.ts` — `UserRole = "user" | "expert" | "admin"` (UPDATED in 5-1)

### Testing Requirements

**Backend tests** (pytest, asyncio_mode=auto, co-located):

1. `api/app/api/corrections_test.py` (create or update):
   - `test_submit_correction_unauthenticated_returns_401` — no JWT gets 401
   - `test_submit_correction_authenticated_sets_pending_status` — correction_status = "pending", is_verified = false
   - `test_submit_correction_sets_submitted_by_user_id` — user_id from JWT
   - `test_submit_correction_rate_limit_per_user_not_ip` — different users get separate limits
   - `test_submit_correction_already_approved_returns_409` — lookup with is_verified=true
   - `test_submit_correction_already_pending_returns_409` — lookup with correction_status="pending"
   - `test_submit_correction_duplicate_hs_code_returns_400` — same code as matched

2. `api/app/repositories/lookup_record_repository_test.py` (additions):
   - `test_submit_pending_correction_sets_fields` — verify all fields set correctly
   - `test_submit_pending_correction_preserves_is_verified_false` — is_verified stays false

**Frontend tests** (Vitest, jsdom, co-located):

3. `web/src/app/search/components/CorrectionPanel.test.tsx` (create or update):
   - `test_shows_login_prompt_when_unauthenticated` — "Dang nhap de gui chinh sua" displayed
   - `test_shows_correction_form_when_authenticated` — form shown for logged-in user
   - `test_shows_pending_success_message_on_submit` — "Chinh sua da duoc gui, dang cho duyet"

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.2: Authenticated Corrections with Pending Status]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-18.md#Story 5-2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture — lookup_records table]
- [Source: _bmad-output/implementation-artifacts/5-1-add-expert-role-and-auth-middleware.md]
- [Source: _bmad-output/project-context.md#Auth Flow (CRITICAL)]
- [Source: CLAUDE.md#Architecture — Backend Layering]
- [Source: CLAUDE.md#Auth Flow]
- [Source: api/app/api/corrections.py — current anonymous correction endpoint]
- [Source: api/app/repositories/lookup_record_repository.py — apply_correction method]
- [Source: api/app/models/lookup_record.py — LookupRecord model (missing new fields)]
- [Source: api/app/schemas/correction.py — correction request/response schemas]
- [Source: api/app/core/auth.py — require_authenticated, require_expert, get_optional_user]
- [Source: web/src/app/search/components/CorrectionPanel.tsx — current anonymous panel]
- [Source: web/src/app/lookups/[id]/page.tsx — lookup detail with CorrectionPanel]
- [Source: web/src/app/search/page.tsx — search page with CorrectionPanel]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (Code Reviewer / DEV 2)

### Debug Log References

N/A

### Completion Notes List

- Code review (DEV 2) found and fixed: stale corrections_test.py still testing old anonymous API, missing CorrectionPanel.test.tsx, missing correction_status badges on lookup detail page, outdated task checkboxes.
- All HIGH and MEDIUM issues fixed automatically.
- corrections_test.py rewritten to match authenticated API (user dict param, submit_pending_correction calls, pending-status assertions).
- CorrectionPanel.test.tsx created with 9 tests covering all ACs.
- lookup detail page updated with correction_status badges (pending/approved/rejected) and pending state display.
- submit_pending_correction repository tests added to lookup_record_repository_test.py.

### File List

- `api/alembic/versions/20260218_add_correction_workflow_columns.py` (new)
- `api/app/models/lookup_record.py` (modified)
- `api/app/repositories/lookup_record_repository.py` (modified)
- `api/app/repositories/lookup_record_repository_test.py` (modified — added submit_pending_correction tests)
- `api/app/api/corrections.py` (modified)
- `api/app/api/corrections_test.py` (modified — rewritten for authenticated API)
- `api/app/schemas/correction.py` (modified)
- `api/app/schemas/lookup.py` (modified)
- `api/app/api/lookups.py` (modified)
- `web/src/app/search/components/CorrectionPanel.tsx` (modified)
- `web/src/app/search/components/CorrectionPanel.test.tsx` (new)
- `web/src/app/lookups/[id]/page.tsx` (modified — correction_status badges)
- `web/src/types/lookup.ts` (modified)
