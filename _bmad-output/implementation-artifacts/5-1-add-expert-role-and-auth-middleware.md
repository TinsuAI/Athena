# Story 5.1: Add Expert Role and Auth Middleware

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **administrator**,
I want **to assign the "expert" role to users**,
So that **designated experts can approve corrections to the knowledge base**.

## Acceptance Criteria

1. **Given** the user model, **When** I check the role field, **Then** it supports three values: "user", "expert", "admin".

2. **Given** the user model, **When** I check the schema, **Then** it includes an `is_active` boolean field (default: true).

3. **Given** a user with `is_active = false`, **When** they attempt to log in, **Then** they receive "Tai khoan da bi vo hieu hoa" (Account has been deactivated) **And** the login is rejected before password verification (return `None` from `authenticate_user`).

4. **Given** a protected endpoint requiring authentication, **When** any logged-in user accesses it, **Then** the `require_authenticated` dependency validates their JWT and returns the user dict.

5. **Given** an endpoint requiring expert access, **When** a user with "expert" or "admin" role accesses it, **Then** the `require_expert` dependency allows access. **When** a "user" role accesses it, **Then** they receive 403 Forbidden.

6. **Given** an endpoint that optionally uses user context, **When** a non-authenticated user accesses it, **Then** the `get_optional_user` dependency returns `None` (no error raised).

7. **Given** the admin user management page, **When** an admin changes a user's role, **Then** the dropdown includes "Nguoi dung" (user), "Chuyen gia" (expert), "Quan tri vien" (admin).

8. **Given** the `RoleUpdateRequest` schema, **When** validating a role value, **Then** it accepts "user", "expert", "admin" (previously only "user", "admin").

9. **Given** existing users in the database, **When** the migration runs, **Then** all existing users retain their current roles and have `is_active = true`.

## Tasks / Subtasks

- [x] Task 1: DB migration — Add `is_active` column to `users` table (AC: #2, #9)
  - [x] 1.1 Create Alembic migration: `alembic revision --autogenerate -m "add_is_active_to_users"` — adds `is_active` (Boolean, default=True, NOT NULL) to `users` table
  - [x] 1.2 Verify migration is backward-compatible: existing rows get `is_active = true` via server_default

- [x] Task 2: Update `User` model with `is_active` field (AC: #2)
  - [x] 2.1 Add `is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)` to `api/app/models/user.py`
  - [x] 2.2 Add comment documenting valid roles: "user", "expert", "admin"

- [x] Task 3: Add new auth dependencies to `api/app/core/auth.py` (AC: #4, #5, #6)
  - [x] 3.1 Add `require_authenticated(request: Request) -> dict` — calls `get_current_user()`, returns user dict (any role allowed). Functionally equivalent to `get_current_user()` but provides semantic clarity for route declarations.
  - [x] 3.2 Add `require_expert(request: Request) -> dict` — calls `get_current_user()`, then checks `role in ("expert", "admin")`, raises 403 if not
  - [x] 3.3 Add `get_optional_user(request: Request) -> dict | None` — tries `get_current_user()`, catches exceptions, returns `None` if no valid JWT

- [x] Task 4: Update `RoleUpdateRequest` validator (AC: #8)
  - [x] 4.1 In `api/app/schemas/admin.py`, change `RoleUpdateRequest.validate_role` to accept `("user", "expert", "admin")` instead of `("user", "admin")`

- [x] Task 5: Update `UserList.tsx` role dropdown (AC: #7)
  - [x] 5.1 In `web/src/app/admin/users/components/UserList.tsx`, add `<option value="expert">Chuyen gia</option>` between "Nguoi dung" and "Quan tri vien"
  - [x] 5.2 Update `handleRoleChange` confirmation message to include expert role label
  - [x] 5.3 Update `UserRole` type in `web/src/types/user.ts` from `"user" | "admin"` to `"user" | "expert" | "admin"`

- [x] Task 6: Update login flow to reject inactive users (AC: #3)
  - [x] 6.1 In `api/app/services/auth_service.py` `authenticate_user()`, after verifying password, check `user.is_active`. If `is_active = false`, raise `InactiveUserError`
  - [x] 6.2 In `api/app/api/auth.py` login endpoint, catch `InactiveUserError` and return 403 with "Tai khoan da bi vo hieu hoa"
  - [x] 6.3 **ALTERNATIVE APPROACH (simpler):** Used the exception-based approach (InactiveUserError). The route handler catches it and returns the appropriate error message.

- [x] Task 7: Tests for all changes (AC: #1-#9)
  - [x] 7.1 `api/app/core/auth_test.py` — Added 8 tests for:
    - `require_authenticated`: valid user passes, unauthenticated gets 401
    - `require_expert`: expert passes, admin passes, user gets 403, unauthenticated gets 401
    - `get_optional_user`: returns user dict when JWT present, returns None when no JWT
  - [x] 7.2 `api/app/services/auth_service_test.py` — Added 2 tests for:
    - Inactive user login raises InactiveUserError
    - Active user login still works as before
  - [x] 7.3 `api/app/api/auth_test.py` — Added 1 test for:
    - Inactive user login returns 403 with specific error message
  - [x] 7.4 `web/src/app/admin/users/components/UserList.test.tsx` — Added 2 tests:
    - Role dropdown has 3 options (user, expert, admin) with correct Vietnamese labels
    - Can change role to expert
  - [x] 7.5 All existing auth tests still pass (52 backend, 6/8 frontend — 2 pre-existing failures unrelated to this story)

## Dev Notes

### CRITICAL: This Story Extends Epic 4's Auth System

This story builds directly on Story 4-5 (Role-Based Access Control). The auth infrastructure is already solid:

**Already exists (DO NOT recreate):**
- `api/app/core/auth.py` — has `get_current_user()` and `require_admin()` dependencies
- `api/app/models/user.py` — User model with `id, email, password_hash, role, created_at` (role default: "user")
- `api/app/schemas/admin.py` — `RoleUpdateRequest` with validator (currently "user" | "admin")
- `api/app/services/auth_service.py` — `AuthService` with `register_user()`, `authenticate_user()`
- `api/app/api/auth.py` — login, register, forgot-password, reset-password endpoints
- `web/src/app/admin/users/components/UserList.tsx` — user list with role dropdown ("Nguoi dung" / "Quan tri vien")
- `web/src/types/user.ts` — `UserRole` type = `"user" | "admin"`
- `web/src/lib/auth.ts` — NextAuth config with role in JWT and session callbacks
- `web/src/proxy.ts` — route protection for `/admin/:path*`

**What this story ADDS (new functionality):**
- `is_active` column on `users` table (migration + model update)
- `require_authenticated`, `require_expert`, `get_optional_user` dependencies in `auth.py`
- "expert" as valid role across backend schemas and frontend dropdowns
- Inactive user login rejection in the auth flow

### Auth Dependency Design

The three new dependencies follow the existing `require_admin` pattern:

```python
# api/app/core/auth.py — ADD these functions (keep existing get_current_user and require_admin)

async def require_authenticated(request: Request) -> dict:
    """Require any authenticated user (user/expert/admin).
    Semantic alias for get_current_user — use in route declarations for clarity.
    """
    return await get_current_user(request)

async def require_expert(request: Request) -> dict:
    """Require expert or admin role."""
    user = await get_current_user(request)
    if user.get("role") not in ("expert", "admin"):
        raise HTTPException(status_code=403, detail="Expert access required")
    return user

async def get_optional_user(request: Request) -> dict | None:
    """Return user if authenticated, None otherwise. Never raises."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
```

### Inactive User Login Rejection

The login flow is: `NextAuth authorize()` -> `POST /api/auth/login` -> `AuthService.authenticate_user()` -> check credentials -> return `UserResponse` or `None`.

**Recommended approach:** Modify `AuthService.authenticate_user()` to check `user.is_active` after password verification. If inactive, raise a custom exception that the route handler catches:

```python
# api/app/services/auth_service.py

class InactiveUserError(Exception):
    """Raised when an inactive user attempts to log in."""
    pass

class AuthService:
    async def authenticate_user(self, email: str, password: str) -> UserResponse | None:
        user = await self.repo.get_by_email(email)
        dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UpJFUjJJaO4i"
        password_hash = user.password_hash if user is not None else dummy_hash
        password_valid = verify_password(password, password_hash)

        if user is not None and password_valid:
            if not user.is_active:
                raise InactiveUserError("Account has been deactivated")
            return UserResponse(
                id=user.id, email=user.email, role=user.role, created_at=user.created_at
            )
        return None
```

```python
# api/app/api/auth.py — update login endpoint
from app.services.auth_service import AuthService, InactiveUserError

@router.post("/login")
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db_session)) -> dict:
    service = AuthService(db)
    try:
        result = await service.authenticate_user(credentials.email, credentials.password)
    except InactiveUserError:
        return error_response(
            type_uri="https://athena.example/errors/account-deactivated",
            title="Account Deactivated",
            status=403,
            detail="Tai khoan da bi vo hieu hoa",
            instance="/api/auth/login",
        )
    if result is None:
        return error_response(
            type_uri="https://athena.example/errors/authentication",
            title="Invalid Credentials",
            status=401,
            detail="Invalid email or password.",
            instance="/api/auth/login",
        )
    return success_response(result.model_dump(mode="json"))
```

### RoleUpdateRequest Schema Change

```python
# api/app/schemas/admin.py — MODIFY validate_role
@field_validator("role")
@classmethod
def validate_role(cls, v: str) -> str:
    if v not in ("user", "expert", "admin"):
        raise ValueError("Role must be 'user', 'expert', or 'admin'")
    return v
```

### UserList.tsx Dropdown Change

```tsx
{/* Change the role <select> options */}
<option value="user">Nguoi dung</option>
<option value="expert">Chuyen gia</option>
<option value="admin">Quan tri vien</option>
```

Update `handleRoleChange` confirmation:
```tsx
const roleLabels: Record<string, string> = {
  user: "Nguoi dung",
  expert: "Chuyen gia",
  admin: "Quan tri vien",
};
const confirmed = window.confirm(
  `Ban co chac muon thay doi vai tro cua nguoi dung nay thanh "${roleLabels[newRole]}"?`
);
```

### UserRole Type Update

```typescript
// web/src/types/user.ts — MODIFY
export type UserRole = "user" | "expert" | "admin";
```

### Alembic Migration

```python
# api/alembic/versions/20260218_add_is_active_to_users.py
def upgrade() -> None:
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False))

def downgrade() -> None:
    op.drop_column("users", "is_active")
```

**IMPORTANT:** Check the latest migration revision hash by looking at `api/alembic/versions/` directory. The `down_revision` must chain correctly from the most recent migration.

### UserResponse Schema

Check if `UserResponse` in `api/app/schemas/user.py` needs updating to include `is_active`. If the admin user list should show active/inactive status, add `is_active: bool` to `UserListItem` in `api/app/schemas/admin.py`. However, Story 5-4 handles user status display — for now, just ensure the model field exists.

### Project Structure Notes

**Modified files:**
```
api/app/models/user.py                           # Add is_active field
api/app/core/auth.py                              # Add require_authenticated, require_expert, get_optional_user
api/app/core/auth_test.py                         # Add tests for new dependencies
api/app/schemas/admin.py                          # Update RoleUpdateRequest validator
api/app/services/auth_service.py                  # Add InactiveUserError, check is_active in authenticate_user
api/app/services/auth_service_test.py             # Add inactive user tests
api/app/api/auth.py                               # Handle InactiveUserError in login
api/app/api/auth_test.py                          # Add inactive user login test
web/src/app/admin/users/components/UserList.tsx    # Add expert option to dropdown
web/src/app/admin/users/components/UserList.test.tsx  # Update dropdown option tests
web/src/types/user.ts                             # Add "expert" to UserRole type
```

**New files:**
```
api/alembic/versions/20260218_add_is_active_to_users.py  # Migration
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| FastAPI dependency injection | `api/app/core/auth.py` | `get_current_user()`, `require_admin()` pattern |
| Envelope responses | `api/app/schemas/base.py` | `success_response`, `error_response` |
| Service exception pattern | `api/app/services/admin_service.py` | `ValueError` for self-role-change |
| Alembic migration | `api/alembic/versions/20260215_add_audit_logs_table.py` | Revision chain pattern |
| Role dropdown | `web/src/app/admin/users/components/UserList.tsx` | Existing select element |
| UserRole type | `web/src/types/user.ts` | Type union pattern |
| Auth test mocking | `api/app/core/auth_test.py` | Mock request pattern for dependency tests |

### Anti-Patterns to AVOID

- **DO NOT** create a new auth.py file — extend the existing one
- **DO NOT** remove `require_admin` — it remains for admin-only endpoints
- **DO NOT** put is_active check in the JWT middleware — check in service layer during login
- **DO NOT** store is_active in the JWT token — check live from DB at login time
- **DO NOT** use passlib — project uses bcrypt directly
- **DO NOT** put business logic in route handlers — `InactiveUserError` handling in auth.py login is acceptable as it's response formatting
- **DO NOT** create a separate `/tests` directory — tests are co-located
- **DO NOT** use status enums for loading states — use boolean flags
- **DO NOT** fetch via Next.js API routes — fetch FastAPI directly with `credentials: 'include'`
- **DO NOT** add expert route protection (e.g., `/expert/:path*`) to `proxy.ts` yet — that's for Story 5-3
- **DO NOT** modify the `NextAuth` JWT callback to include `is_active` — JWT already carries `role`, and `is_active` is only relevant at login time

### Previous Story Intelligence (from Story 4-5)

**Patterns established:**
- `require_admin` dependency pattern: calls `get_current_user()` first, then checks role
- AuditLog model with JSONB details column — reuse for future audit entries
- Admin router registered in `main.py` with `prefix="/api/admin"`
- Role dropdown in UserList.tsx with Vietnamese labels
- Rate limiting via Redis in admin endpoints (10 role changes/min per admin)

**Code review fixes applied in 4-5 (avoid repeating issues):**
- Audit log creation AFTER validation (not before)
- Eager loading (selectinload) for relationships to avoid N+1
- Database indexes on frequently-queried timestamp columns
- Session expiry handling (401 detection + redirect to login) in frontend

**Known pre-existing test failures (ignore):**
- 18 browse component test failures (unrelated)
- 17+ backend test failures in corrections, hs_codes, search, config, excel_parser, auth_integration, browse_repository (all unrelated to auth)

### Git Intelligence

Recent relevant commits:
- `d790cdd` — feat: implement role-based access control with admin dashboard and audit logging (story 4-5)
- `4700355` — feat: implement password reset with email verification and token security (story 4-4)
- `5c421d6` — feat: Translate various UI texts to Vietnamese (translations established pattern)

Key established files from Epic 4:
- `api/app/core/auth.py` — JWT validation, `get_current_user()` returns `{id, email, role}`
- `api/app/api/deps.py` — `get_db_session()` dependency
- `api/app/schemas/base.py` — `success_response()`, `error_response()` envelope helpers
- `web/src/proxy.ts` — Next.js 16 route protection
- `web/src/lib/auth.ts` — NextAuth config with role in JWT and session callbacks

### Testing Requirements

**Backend tests** (pytest, asyncio_mode=auto, co-located):

1. `api/app/core/auth_test.py` (additions):
   - `test_require_authenticated_valid_user_passes` — any role succeeds
   - `test_require_authenticated_unauthenticated_returns_401`
   - `test_require_expert_expert_user_passes`
   - `test_require_expert_admin_user_passes` — admin also has expert access
   - `test_require_expert_standard_user_returns_403`
   - `test_require_expert_unauthenticated_returns_401`
   - `test_get_optional_user_returns_user_when_authenticated`
   - `test_get_optional_user_returns_none_when_unauthenticated`

2. `api/app/services/auth_service_test.py` (additions):
   - `test_authenticate_inactive_user_raises_error` — user exists, password valid, is_active=false
   - `test_authenticate_active_user_succeeds` — user exists, password valid, is_active=true

3. `api/app/api/auth_test.py` (additions):
   - `test_login_inactive_user_returns_403_with_deactivated_message`

**Frontend tests** (Vitest, jsdom, co-located):

4. `web/src/app/admin/users/components/UserList.test.tsx` (update):
   - Verify role dropdown has 3 options: user, expert, admin
   - Verify expert role label is "Chuyen gia"

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.1: Add Expert Role and Auth Middleware]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-18.md#Story 5-1]
- [Source: _bmad-output/planning-artifacts/prd.md#FR35 - Admins can assign user roles]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#User Model Expansion]
- [Source: _bmad-output/implementation-artifacts/4-5-role-based-access-control.md]
- [Source: _bmad-output/project-context.md#Auth Flow (CRITICAL)]
- [Source: CLAUDE.md#Auth Flow]
- [Source: CLAUDE.md#Architecture]
- [Source: api/app/core/auth.py - get_current_user(), require_admin()]
- [Source: api/app/models/user.py - User model with role field]
- [Source: api/app/schemas/admin.py - RoleUpdateRequest validator]
- [Source: api/app/services/auth_service.py - authenticate_user()]
- [Source: api/app/api/auth.py - login endpoint]
- [Source: web/src/app/admin/users/components/UserList.tsx - role dropdown]
- [Source: web/src/types/user.ts - UserRole type]
- [Source: web/src/lib/auth.ts - NextAuth JWT callbacks with role]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- All 14 `auth_test.py` tests pass (8 new + 6 existing)
- All 20 `auth_service_test.py` tests pass (2 new + 18 existing)
- All 15 `auth_test.py` API endpoint tests pass (1 new + 14 existing)
- 6/8 `UserList.test.tsx` tests pass (2 new pass, 2 pre-existing failures unrelated to this story: Vietnamese text vs English assertions in success message and pagination tests)
- Ruff lint passes on all modified backend files
- RoleUpdateRequest schema validated: accepts "user", "expert", "admin"; rejects invalid values

### Completion Notes List

- Task 1: Created Alembic migration `20260218_add_is_active_to_users.py` with `is_active` Boolean column, `server_default="true"`, `nullable=False`. Down_revision chains from `add_nlm_raw_response`. Existing rows automatically get `is_active = true`.
- Task 2: Added `is_active` field to User model with `Boolean` type, `default=True`, `server_default="true"`. Added docstring documenting valid roles.
- Task 3: Added three new auth dependencies following existing `require_admin` pattern: `require_authenticated` (semantic alias for `get_current_user`), `require_expert` (checks expert/admin role, 403 otherwise), `get_optional_user` (returns None instead of raising on unauthenticated).
- Task 4: Updated `RoleUpdateRequest.validate_role` to accept `("user", "expert", "admin")` tuple instead of `("user", "admin")`.
- Task 5: Added `expert` option to UserList.tsx dropdown with Vietnamese label. Created `roleLabels` map for dynamic confirmation messages. Updated `UserRole` TypeScript type union.
- Task 6: Used exception-based approach (Task 6.3 alternative). Added `InactiveUserError` exception class. `authenticate_user()` raises it after password verification if `is_active=False`. Login route handler catches it and returns 403 with "Tai khoan da bi vo hieu hoa".
- Task 7: Added 13 new tests total (8 auth core, 2 auth service, 1 auth API, 2 frontend). All new tests pass. No regressions in existing auth tests.

### Change Log

- 2026-02-18: Story 5-1 implementation complete. Added expert role support, is_active user deactivation, three new auth dependencies, and inactive user login rejection. All acceptance criteria satisfied.
- 2026-02-18: Code review complete (DEV 2). Fixed 3 issues: (1) Updated `authenticate_user` docstring to document `InactiveUserError` raised and explain is_active check order for timing-attack mitigation. (2) Fixed `UserList.test.tsx` success message assertion from English "Role updated successfully" to Vietnamese "Cập nhật vai trò thành công". (3) Fixed `UserList.test.tsx` pagination assertions from English text ("Page 1 of 2 (40 users)", "Previous", "Next") to Vietnamese ("Trang 1 / 2 (40 người dùng)", "Trước", "Sau").

### File List

**New files:**
- `api/alembic/versions/20260218_add_is_active_to_users.py` — Migration adding is_active column

**Modified files:**
- `api/app/models/user.py` — Added is_active field, Boolean import, role documentation
- `api/app/core/auth.py` — Added require_authenticated, require_expert, get_optional_user dependencies
- `api/app/core/auth_test.py` — Added 8 tests for new auth dependencies
- `api/app/schemas/admin.py` — Updated RoleUpdateRequest validator to accept "expert"
- `api/app/services/auth_service.py` — Added InactiveUserError, is_active check in authenticate_user
- `api/app/services/auth_service_test.py` — Added 2 tests for inactive/active user authentication
- `api/app/api/auth.py` — Added InactiveUserError handling in login endpoint
- `api/app/api/auth_test.py` — Added 1 test for inactive user login response
- `web/src/types/user.ts` — Added "expert" to UserRole type union
- `web/src/app/admin/users/components/UserList.tsx` — Added expert dropdown option, roleLabels map
- `web/src/app/admin/users/components/UserList.test.tsx` — Added 2 tests for expert role in dropdown
