# Story 5.4: Admin User Management

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **administrator**,
I want **to create, edit, deactivate, and search user accounts**,
So that **I have full control over who can access the system**.

## Acceptance Criteria

1. **Given** I am an admin on the user management page, **When** I click "Tao nguoi dung" (Create user), **Then** I can enter email, temporary password, and role **And** the new user account is created.

2. **Given** I am viewing the user list, **When** I click edit on a user, **Then** I can modify their email and role **And** changes are saved with audit logging.

3. **Given** I am viewing the user list, **When** I click "Vo hieu hoa" (Deactivate) on a user, **Then** a confirmation dialog appears **And** upon confirmation, the user is deactivated (cannot log in).

4. **Given** I am viewing a deactivated user, **When** I click "Kich hoat lai" (Reactivate), **Then** the user account is reactivated.

5. **Given** I am on the user management page, **When** I type in the search field, **Then** users are filtered by email in real-time.

6. **Given** I try to deactivate my own account, **When** I click deactivate, **Then** I see "Khong the vo hieu hoa tai khoan cua chinh minh" (Cannot deactivate your own account).

7. **Given** I am not an admin, **When** I try to access admin endpoints, **Then** I receive 403 Forbidden.

## Tasks / Subtasks

- [x] Task 1: Add `create_user` endpoint to `api/app/api/admin.py` (AC: #1, #7)
  - [x] 1.1 `POST /api/admin/users` endpoint: accepts `{ email, password, role }`, protected by `require_admin`
  - [x] 1.2 Validate email format and password min length via Pydantic schema
  - [x] 1.3 Return 400 if email already exists
  - [x] 1.4 Hash password with bcrypt, create user, return success response

- [x] Task 2: Add `update_user` endpoint to `api/app/api/admin.py` (AC: #2, #7)
  - [x] 2.1 `PATCH /api/admin/users/{id}` endpoint: accepts `{ email?, role? }`, protected by `require_admin`
  - [x] 2.2 Return 404 if user not found
  - [x] 2.3 Return 400 if new email conflicts with existing user
  - [x] 2.4 Create audit log entry on successful update

- [x] Task 3: Add `toggle_user_status` endpoint to `api/app/api/admin.py` (AC: #3, #4, #6, #7)
  - [x] 3.1 `PATCH /api/admin/users/{id}/status` endpoint: accepts `{ is_active }`, protected by `require_admin`
  - [x] 3.2 Prevent self-deactivation (admin_user_id == target_user_id returns 400)
  - [x] 3.3 Return 404 if user not found
  - [x] 3.4 Create audit log entry on status change

- [x] Task 4: Add `search` parameter to `list_users` endpoint (AC: #5)
  - [x] 4.1 Add `search: str = Query(default="")` parameter to existing `GET /api/admin/users`
  - [x] 4.2 Pass search parameter to service and repository
  - [x] 4.3 Filter by email ILIKE `%search%` when search is non-empty

- [x] Task 5: Add AdminService methods (AC: #1-#6)
  - [x] 5.1 `create_user(admin_user_id, email, password, role)` -- check email uniqueness, hash password, create user, audit log
  - [x] 5.2 `update_user(admin_user_id, target_user_id, email?, role?)` -- validate target exists, check email uniqueness if changed, update fields, audit log
  - [x] 5.3 `toggle_user_status(admin_user_id, target_user_id, is_active)` -- prevent self-deactivation, update is_active, audit log

- [x] Task 6: Add UserRepository methods (AC: #1-#5)
  - [x] 6.1 `update_user(user_id, **fields)` -- update email and/or role
  - [x] 6.2 `update_status(user_id, is_active)` -- update is_active field
  - [x] 6.3 Update `list_all(page, per_page, search="")` to accept optional search filter

- [x] Task 7: Add Pydantic schemas in `api/app/schemas/admin.py` (AC: #1, #2, #3)
  - [x] 7.1 `AdminCreateUserRequest` -- email (validated), password (min 8), role (user/expert/admin)
  - [x] 7.2 `AdminUpdateUserRequest` -- email? (validated), role? (user/expert/admin)
  - [x] 7.3 `UserStatusRequest` -- is_active (bool)
  - [x] 7.4 Update `UserListItem` to include `is_active` field

- [x] Task 8: Expand `UserList.tsx` with create/edit/deactivate/search actions (AC: #1-#6)
  - [x] 8.1 Add search input above user table -- filters on keystroke (debounced 300ms)
  - [x] 8.2 Add "Tao nguoi dung" (Create user) button -- opens create modal/form
  - [x] 8.3 Create user form: email input, password input, role dropdown
  - [x] 8.4 Add edit button per row -- opens inline edit or modal for email/role
  - [x] 8.5 Add status column showing active/inactive indicator (green/red dot)
  - [x] 8.6 Add deactivate/reactivate toggle button per row
  - [x] 8.7 Confirmation dialog for deactivate action
  - [x] 8.8 Self-deactivation prevention: disable deactivate button for current user's row, or show error from API

- [x] Task 9: Backend tests (AC: #1-#7)
  - [x] 9.1 `api/app/api/admin_test.py`: test POST create user returns 201
  - [x] 9.2 `api/app/api/admin_test.py`: test POST create user with duplicate email returns 400
  - [x] 9.3 `api/app/api/admin_test.py`: test PATCH update user email and role
  - [x] 9.4 `api/app/api/admin_test.py`: test PATCH update user with conflicting email returns 400
  - [x] 9.5 `api/app/api/admin_test.py`: test PATCH toggle user status deactivates user
  - [x] 9.6 `api/app/api/admin_test.py`: test PATCH toggle user status reactivates user
  - [x] 9.7 `api/app/api/admin_test.py`: test self-deactivation returns 400
  - [x] 9.8 `api/app/api/admin_test.py`: test list users with search parameter filters by email
  - [x] 9.9 `api/app/api/admin_test.py`: test all admin endpoints require admin role (403 for user/expert)
  - [x] 9.10 `api/app/services/admin_service_test.py`: test create_user hashes password and creates audit log
  - [x] 9.11 `api/app/services/admin_service_test.py`: test update_user validates uniqueness and creates audit log
  - [x] 9.12 `api/app/services/admin_service_test.py`: test toggle_user_status prevents self-deactivation
  - [x] 9.13 `api/app/repositories/user_repository_test.py`: test update_user changes email and role
  - [x] 9.14 `api/app/repositories/user_repository_test.py`: test update_status changes is_active
  - [x] 9.15 `api/app/repositories/user_repository_test.py`: test list_all with search filters by email

- [x] Task 10: Frontend tests (AC: #1, #2, #3, #5, #6)
  - [x] 10.1 `web/src/app/admin/users/components/UserList.test.tsx`: test search input filters user list
  - [x] 10.2 `web/src/app/admin/users/components/UserList.test.tsx`: test create user button opens form
  - [x] 10.3 `web/src/app/admin/users/components/UserList.test.tsx`: test deactivate button shows confirmation
  - [x] 10.4 `web/src/app/admin/users/components/UserList.test.tsx`: test status column shows active/inactive

## Dev Notes

### CRITICAL: This Story EXPANDS Existing Admin User Management

This story extends the existing admin user management system with create, edit, deactivate, and search capabilities. The existing admin endpoints and UI are already functional -- you are adding to them, NOT replacing them.

**Already exists (DO NOT recreate):**
- `api/app/api/admin.py` -- Admin router with `GET /api/admin/users` (paginated list), `PATCH /api/admin/users/{id}/role` (role update), `GET /api/admin/audit-log`. Uses `require_admin` dependency, `AdminService`, rate limiting via Redis.
- `api/app/services/admin_service.py` -- `AdminService` class with `list_users()` and `update_user_role()` methods. Uses `UserRepository` and `AuditLogRepository`.
- `api/app/repositories/user_repository.py` -- `UserRepository` with `create()`, `get_by_email()`, `get_by_id()`, `update_password()`, `list_all()`, `update_role()`.
- `api/app/schemas/admin.py` -- `RoleUpdateRequest`, `UserListItem`, `UserListResponse`, `AuditLogResponse`.
- `api/app/schemas/user.py` -- `UserCreate` (with email validation), `UserResponse`, `UserLogin`, password reset schemas.
- `api/app/models/user.py` -- `User` model with `id`, `email`, `password_hash`, `role`, `is_active`, `created_at`.
- `api/app/core/auth.py` -- `require_admin`, `require_authenticated`, `require_expert`, `get_optional_user`, `get_current_user`.
- `api/app/services/auth_service.py` -- `hash_password()`, `verify_password()`, `AuthService.register_user()` (pattern for creating users with bcrypt).
- `api/app/repositories/audit_log_repository.py` -- `AuditLogRepository.create(admin_user_id, action, target_user_id, details)`.
- `web/src/app/admin/users/page.tsx` -- Simple wrapper rendering `<UserList />`.
- `web/src/app/admin/users/components/UserList.tsx` -- Table with email, role dropdown, pagination. Uses `apiClient`.
- `web/src/lib/api.ts` -- `apiClient` with `get/post/patch/put/delete` methods, `credentials: 'include'`.
- `web/src/proxy.ts` -- Route protection for `/admin/:path*`.

**What this story MODIFIES (existing files):**
- `api/app/api/admin.py` -- Add 3 new endpoints: POST create user, PATCH update user, PATCH toggle status. Add `search` param to existing `list_users`.
- `api/app/services/admin_service.py` -- Add 3 new methods: `create_user`, `update_user`, `toggle_user_status`. Update `list_users` to accept search.
- `api/app/repositories/user_repository.py` -- Add `update_user()`, `update_status()`. Update `list_all()` to accept search.
- `api/app/schemas/admin.py` -- Add `AdminCreateUserRequest`, `AdminUpdateUserRequest`, `UserStatusRequest`. Update `UserListItem` with `is_active`.
- `web/src/app/admin/users/components/UserList.tsx` -- Add search input, create user button/form, edit button, status column, deactivate/reactivate button.

**NO new files created** -- all changes go into existing files.

### Backend Architecture: Layered Pattern

Follow the strict layered architecture already established:

```
admin.py (API) -> admin_service.py (Service) -> user_repository.py + audit_log_repository.py (Repositories)
```

**Route handler (`admin.py`):** ONLY validates request, calls service, formats response with `success_response()`/`error_response()`. NO business logic.

**Service (`admin_service.py`):** ALL business logic -- email uniqueness checks, self-deactivation prevention, password hashing, audit log creation.

**Repository (`user_repository.py`):** ONLY database queries.

### API Endpoint Details

```python
# api/app/api/admin.py -- ADD these endpoints to existing router

# POST /api/admin/users
# - Protected by require_admin
# - Body: AdminCreateUserRequest { email, password, role }
# - Calls admin_service.create_user()
# - Returns success_response with created user data
# - Returns error_response 400 if email already exists

# PATCH /api/admin/users/{id}
# - Protected by require_admin
# - Body: AdminUpdateUserRequest { email?, role? }
# - Calls admin_service.update_user()
# - Returns success_response with updated user data
# - Returns error_response 404 if user not found
# - Returns error_response 400 if email conflicts

# PATCH /api/admin/users/{id}/status
# - Protected by require_admin
# - Body: UserStatusRequest { is_active }
# - Calls admin_service.toggle_user_status()
# - Returns success_response with updated user data
# - Returns error_response 400 if self-deactivation
# - Returns error_response 404 if user not found

# GET /api/admin/users (MODIFY existing)
# - Add search: str = Query(default="") parameter
# - Pass to service.list_users(page, per_page, search)
```

### New Pydantic Schemas

```python
# api/app/schemas/admin.py -- ADD these schemas

class AdminCreateUserRequest(BaseModel):
    """Schema for admin creating a new user."""
    email: str = Field(description="User email address")
    password: str = Field(min_length=8, description="Temporary password (min 8 characters)")
    role: str = Field(default="user", description="User role")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Please enter a valid email address")
        return v.lower().strip()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "expert", "admin"):
            raise ValueError("Role must be 'user', 'expert', or 'admin'")
        return v

class AdminUpdateUserRequest(BaseModel):
    """Schema for admin updating a user's profile."""
    email: str | None = Field(default=None, description="New email address")
    role: str | None = Field(default=None, description="New role")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Please enter a valid email address")
        return v.lower().strip()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v not in ("user", "expert", "admin"):
            raise ValueError("Role must be 'user', 'expert', or 'admin'")
        return v

class UserStatusRequest(BaseModel):
    """Schema for toggling user active status."""
    is_active: bool = Field(description="Whether user is active")
```

### Repository Method Patterns

```python
# api/app/repositories/user_repository.py -- ADD/MODIFY these methods

async def update_user(self, user_id: int, **fields) -> User | None:
    """Update user fields (email and/or role). Returns updated user or None."""
    if not fields:
        return await self.get_by_id(user_id)
    await self.session.execute(
        update(User).where(User.id == user_id).values(**fields)
    )
    await self.session.flush()
    return await self.get_by_id(user_id)

async def update_status(self, user_id: int, is_active: bool) -> User | None:
    """Update user is_active status. Returns updated user or None."""
    await self.session.execute(
        update(User).where(User.id == user_id).values(is_active=is_active)
    )
    await self.session.flush()
    return await self.get_by_id(user_id)

# MODIFY existing list_all to accept search
async def list_all(self, page: int, per_page: int, search: str = "") -> tuple[list[User], int]:
    """Return paginated user list with total count, optionally filtered by email."""
    base_query = select(User)
    count_query = select(func.count(User.id))

    if search:
        base_query = base_query.where(User.email.ilike(f"%{search}%"))
        count_query = count_query.where(User.email.ilike(f"%{search}%"))

    count_result = await self.session.execute(count_query)
    total = count_result.scalar_one()

    offset = (page - 1) * per_page
    result = await self.session.execute(
        base_query.order_by(User.id).offset(offset).limit(per_page)
    )
    users = list(result.scalars().all())
    return users, total
```

### Service Method Patterns

```python
# api/app/services/admin_service.py -- ADD these methods

async def create_user(self, admin_user_id: int, email: str, password: str, role: str) -> dict | None:
    """Create a new user. Returns None if email already exists."""
    existing = await self.user_repo.get_by_email(email)
    if existing is not None:
        return None  # Email already exists

    from app.services.auth_service import hash_password
    user = User(email=email, password_hash=hash_password(password), role=role)
    created = await self.user_repo.create(user)

    await self.audit_repo.create(
        admin_user_id=admin_user_id,
        action="user_created",
        target_user_id=created.id,
        details={"email": email, "role": role},
    )

    return UserListItem(
        id=created.id, email=created.email, role=created.role,
        is_active=created.is_active, created_at=created.created_at,
    ).model_dump(mode="json")

async def update_user(self, admin_user_id: int, target_user_id: int, email: str | None = None, role: str | None = None) -> dict | str:
    """Update user email and/or role. Returns dict on success, error string on failure."""
    target = await self.user_repo.get_by_id(target_user_id)
    if target is None:
        return "not_found"

    # Check email uniqueness if changing
    if email is not None and email != target.email:
        existing = await self.user_repo.get_by_email(email)
        if existing is not None:
            return "email_exists"

    fields = {}
    if email is not None:
        fields["email"] = email
    if role is not None:
        fields["role"] = role

    old_email = target.email
    old_role = target.role

    updated = await self.user_repo.update_user(target_user_id, **fields)

    await self.audit_repo.create(
        admin_user_id=admin_user_id,
        action="user_updated",
        target_user_id=target_user_id,
        details={"old_email": old_email, "new_email": email or old_email, "old_role": old_role, "new_role": role or old_role},
    )

    return UserListItem(
        id=updated.id, email=updated.email, role=updated.role,
        is_active=updated.is_active, created_at=updated.created_at,
    ).model_dump(mode="json")

async def toggle_user_status(self, admin_user_id: int, target_user_id: int, is_active: bool) -> dict | str:
    """Toggle user active status. Returns dict on success, error string on failure."""
    if admin_user_id == target_user_id:
        return "self_deactivation"

    target = await self.user_repo.get_by_id(target_user_id)
    if target is None:
        return "not_found"

    updated = await self.user_repo.update_status(target_user_id, is_active)

    await self.audit_repo.create(
        admin_user_id=admin_user_id,
        action="user_status_changed",
        target_user_id=target_user_id,
        details={"is_active": is_active},
    )

    return UserListItem(
        id=updated.id, email=updated.email, role=updated.role,
        is_active=updated.is_active, created_at=updated.created_at,
    ).model_dump(mode="json")

# MODIFY existing list_users
async def list_users(self, page: int = 1, per_page: int = 20, search: str = "") -> dict:
    """Return paginated user list, optionally filtered by email search."""
    users, total = await self.user_repo.list_all(page, per_page, search)
    return UserListResponse(
        items=[
            UserListItem(
                id=u.id, email=u.email, role=u.role,
                is_active=u.is_active, created_at=u.created_at,
            )
            for u in users
        ],
        total=total, page=page, per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    ).model_dump(mode="json")
```

### Frontend UserList.tsx Expansion

The existing `UserList.tsx` currently shows a table with email, role dropdown, and pagination. Expand it with:

1. **Search input** at the top -- `type="search"` with placeholder "Tim kiem theo email..." (Search by email...). Debounce 300ms, pass `search` query param to `GET /api/admin/users?search=query&page=1`.

2. **"Tao nguoi dung" (Create user) button** -- opens a modal or inline form with:
   - Email input (required)
   - Password input (required, min 8 chars)
   - Role dropdown (Nguoi dung / Chuyen gia / Quan tri vien)
   - "Tao" (Create) and "Huy" (Cancel) buttons
   - Calls `POST /api/admin/users`

3. **is_active status column** -- shows green dot + "Hoat dong" (Active) or red dot + "Vo hieu hoa" (Deactivated).

4. **Edit button per row** -- opens inline edit or modal for email and role. Calls `PATCH /api/admin/users/{id}`.

5. **Deactivate/Reactivate button per row:**
   - Active user: "Vo hieu hoa" button (red variant), shows `window.confirm()` dialog
   - Inactive user: "Kich hoat lai" button (green variant)
   - Current user's row: button disabled with tooltip "Khong the vo hieu hoa tai khoan cua chinh minh"
   - Calls `PATCH /api/admin/users/{id}/status`

6. **UserItem interface update**: Add `is_active: boolean` field.

7. **Current user detection**: Use `useSession()` from `next-auth/react` to get current user ID, disable self-deactivation.

**Key patterns from existing code:**
- Use `apiClient.get/post/patch` from `@/lib/api`
- Success/error message banners already exist (reuse pattern)
- Role labels: `{ user: "Nguoi dung", expert: "Chuyen gia", admin: "Quan tri vien" }`
- 401 redirect: `window.location.href = "/login"` on session expiry

### Audit Log Pattern

Follow existing pattern in `admin_service.py`:

```python
await self.audit_repo.create(
    admin_user_id=admin_user_id,
    action="user_created",         # or "user_updated", "user_status_changed"
    target_user_id=target_user_id,
    details={...},                 # Relevant change details
)
```

Actions to log:
- `user_created` -- when admin creates a user
- `user_updated` -- when admin edits user email/role
- `user_status_changed` -- when admin deactivates/reactivates a user

### Project Structure Notes

**Modified files (NO new files):**
```
api/app/api/admin.py                                  # Add create_user, update_user, toggle_status endpoints; add search to list_users
api/app/api/admin_test.py                              # Add tests for new endpoints
api/app/services/admin_service.py                      # Add create_user, update_user, toggle_user_status methods; update list_users
api/app/services/admin_service_test.py                 # Add tests for new service methods (create if doesn't exist)
api/app/repositories/user_repository.py                # Add update_user, update_status; modify list_all for search
api/app/repositories/user_repository_test.py           # Add tests for new repo methods
api/app/schemas/admin.py                               # Add AdminCreateUserRequest, AdminUpdateUserRequest, UserStatusRequest; update UserListItem
web/src/app/admin/users/components/UserList.tsx         # Add search, create, edit, deactivate/reactivate, status column
web/src/app/admin/users/components/UserList.test.tsx    # Add tests for new UI features
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| `require_admin` dependency | `api/app/core/auth.py` | Admin role gate for all endpoints |
| `AdminService` with repos + audit | `api/app/services/admin_service.py` | Service pattern with UserRepository + AuditLogRepository |
| `update_user_role` method | `api/app/services/admin_service.py` | Pattern for update + audit log + self-check |
| `hash_password()` | `api/app/services/auth_service.py` | Bcrypt hashing for admin-created users |
| `UserCreate.validate_email` | `api/app/schemas/user.py` | Email validation regex pattern |
| `RoleUpdateRequest.validate_role` | `api/app/schemas/admin.py` | Role validation (user/expert/admin) |
| `success_response()` / `error_response()` | `api/app/schemas/base.py` | Envelope response format |
| `apiClient.get()` / `apiClient.post()` / `apiClient.patch()` | `web/src/lib/api.ts` | Frontend API calls with credentials |
| Rate limiting pattern | `api/app/api/admin.py` | `_is_role_change_rate_limited()` via Redis |
| `useSession()` hook | `next-auth/react` | Detect current user for self-deactivation prevention |
| Route protection | `web/src/proxy.ts` | `/admin/:path*` already configured |

### Anti-Patterns to AVOID

- **DO NOT** create new files for admin endpoints -- add to existing `admin.py`, `admin_service.py`, `user_repository.py`
- **DO NOT** create a new `auth_service.create_user()` -- use existing `hash_password()` but implement admin-specific creation in `AdminService`
- **DO NOT** put email uniqueness checks or self-deactivation logic in route handlers -- service layer only
- **DO NOT** use camelCase in API JSON responses -- all snake_case
- **DO NOT** create tests in a separate `/tests` directory -- co-locate with source files
- **DO NOT** use Next.js API routes -- fetch FastAPI directly with `credentials: 'include'`
- **DO NOT** recreate the user table or add new columns -- `is_active` already exists on User model (added in Story 5-1)
- **DO NOT** modify `register_user` in `auth_service.py` -- admin user creation is separate from self-registration
- **DO NOT** use status enums -- use boolean `is_active` directly
- **DO NOT** skip audit logging -- every admin action (create, edit, status change) must create an audit entry
- **DO NOT** remove existing `update_user_role` endpoint -- it stays; the new `PATCH /api/admin/users/{id}` is more general and can also change roles, but the legacy endpoint remains for backward compatibility
- **DO NOT** forget to include `is_active` in `UserListItem` schema -- the frontend needs it for status display

### Previous Story Intelligence (from Stories 5-1, 5-2, 5-3)

**From Story 5-1 (expert role + auth):**
- `is_active` field already exists on User model (added via migration)
- Login flow already rejects inactive users (`InactiveUserError` in `auth_service.py`)
- User dict from auth returns `{"id": int, "email": str, "role": str}`
- Code review lessons: always add docstrings, use Vietnamese text in test assertions

**From Story 5-2 (authenticated corrections):**
- Rate limiting pattern established (per-user via Redis)
- Index patterns for efficient queries

**From Story 5-3 (expert approval):**
- `ExpertService` follows same pattern: service with repos + audit log
- `get_db_session` is the standard DB dependency (not `get_db`) -- use consistently
- Code review fixed: `get_db` was renamed to `get_db_session` for consistency across all routers

**IMPORTANT: `get_db_session` vs `get_db`:**
- The standard DB dependency is `get_db_session` from `api/app/api/deps.py`
- The existing `admin.py` already imports and uses `get_db_session` correctly
- DO NOT use `get_db` -- it doesn't exist

**Known pre-existing test failures (ignore):**
- 18 browse component test failures (unrelated)
- 17+ backend test failures in corrections, hs_codes, search, config, excel_parser, auth_integration, browse_repository (all unrelated)

### Git Intelligence

Recent commits:
- `4412360` -- feat 5-3: Expert correction approval workflow with review page
- `8d65b4e` -- feat 5-2: Authenticated corrections with pending status workflow
- `d725d14` -- feat 5-1: Add expert role, is_active field, and auth middleware dependencies
- `a4a769c` -- feat: Add confidence score tooltips to lookup and search results

Key patterns from recent work:
- All admin endpoints use `require_admin` dependency, `AdminService`, `success_response()`/`error_response()`
- `UserRepository` is the single repository for all user DB operations
- `AuditLogRepository.create()` is the standard for audit entries
- Frontend uses `apiClient` from `@/lib/api` with typed responses
- All UI text must be in Vietnamese

### Testing Requirements

**Backend tests** (pytest, asyncio_mode=auto, co-located):

1. `api/app/api/admin_test.py` (additions to existing test file):
   - `test_create_user_success` -- POST creates user, returns 200 with user data
   - `test_create_user_duplicate_email_returns_400` -- returns error for existing email
   - `test_create_user_invalid_email_returns_422` -- Pydantic validation
   - `test_create_user_short_password_returns_422` -- password min length validation
   - `test_update_user_email_and_role` -- PATCH updates fields
   - `test_update_user_not_found_returns_404`
   - `test_update_user_email_conflict_returns_400`
   - `test_toggle_status_deactivate_user` -- sets is_active=false
   - `test_toggle_status_reactivate_user` -- sets is_active=true
   - `test_toggle_status_self_deactivation_returns_400`
   - `test_toggle_status_not_found_returns_404`
   - `test_list_users_with_search_filters_by_email` -- search param works
   - `test_admin_endpoints_require_admin_role` -- 403 for non-admin

2. `api/app/services/admin_service_test.py` (create if doesn't exist):
   - `test_create_user_hashes_password_and_creates_audit_log`
   - `test_create_user_returns_none_for_duplicate_email`
   - `test_update_user_validates_email_uniqueness`
   - `test_update_user_returns_not_found_for_missing_user`
   - `test_toggle_user_status_prevents_self_deactivation`
   - `test_toggle_user_status_creates_audit_log`

3. `api/app/repositories/user_repository_test.py` (additions):
   - `test_update_user_changes_email_and_role`
   - `test_update_status_changes_is_active`
   - `test_list_all_with_search_filters_by_email`
   - `test_list_all_without_search_returns_all`

**Frontend tests** (Vitest, jsdom, co-located):

4. `web/src/app/admin/users/components/UserList.test.tsx` (additions):
   - `test_search_input_passes_query_to_api`
   - `test_create_user_button_opens_form`
   - `test_deactivate_button_shows_confirmation`
   - `test_status_column_shows_active_inactive`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.4: Admin User Management]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-18.md#Story 5-4]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Backend Architecture]
- [Source: _bmad-output/implementation-artifacts/5-3-expert-correction-approval-workflow.md]
- [Source: _bmad-output/implementation-artifacts/5-1-add-expert-role-and-auth-middleware.md]
- [Source: _bmad-output/project-context.md#Auth Flow (CRITICAL)]
- [Source: CLAUDE.md#Architecture -- Backend Layering]
- [Source: CLAUDE.md#Auth Flow]
- [Source: api/app/api/admin.py -- existing admin endpoints]
- [Source: api/app/services/admin_service.py -- existing admin service]
- [Source: api/app/repositories/user_repository.py -- existing user repository]
- [Source: api/app/schemas/admin.py -- existing admin schemas]
- [Source: api/app/models/user.py -- User model with is_active]
- [Source: api/app/services/auth_service.py -- hash_password() function]
- [Source: api/app/core/auth.py -- require_admin dependency]
- [Source: web/src/app/admin/users/components/UserList.tsx -- existing user list component]
- [Source: web/src/lib/api.ts -- apiClient]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- All 49 backend tests pass (admin_test.py: 22, admin_service_test.py: 14, user_repository_test.py: 13)
- All 12 frontend tests pass (UserList.test.tsx)
- Ruff lint: all checks pass on modified files
- ESLint: no errors on UserList.tsx
- TypeScript: no new errors introduced (pre-existing TS errors in unrelated test files)

### Completion Notes List

- Task 7 (schemas): Added AdminCreateUserRequest, AdminUpdateUserRequest, UserStatusRequest schemas. Updated UserListItem with is_active field. Email/role validators follow existing patterns from RoleUpdateRequest and UserCreate.
- Task 6 (repository): Added update_user() and update_status() methods. Modified list_all() to accept search parameter with ILIKE filter.
- Task 5 (service): Added create_user(), update_user(), toggle_user_status() methods. Updated list_users() to pass search. All methods create audit log entries. Password hashing uses existing hash_password() from auth_service.
- Tasks 1-4 (API endpoints): Added POST /api/admin/users, PATCH /api/admin/users/{id}, PATCH /api/admin/users/{id}/status. Added search param to GET /api/admin/users. All protected by require_admin. Service layer handles business logic.
- Task 8 (frontend): Expanded UserList.tsx with search input (debounced 300ms), create user modal, edit user modal, status column (green/red dot), deactivate/reactivate buttons with confirmation, self-deactivation prevention via useSession(). All Vietnamese text.
- Task 9 (backend tests): 22 admin_test.py tests, 14 admin_service_test.py tests, 13 user_repository_test.py tests -- all pass.
- Task 10 (frontend tests): 12 UserList.test.tsx tests -- all pass including 4 new tests for search, create, deactivate, and status column.

### Change Log

- 2026-02-18: Implemented Story 5.4 - Admin User Management (create, edit, deactivate, search)
- 2026-02-18: Code review by Claude Sonnet 4.6 -- fixed null safety guards in update_user and toggle_user_status (admin_service.py), fixed debounce in UserList.tsx so search API call fires after 300ms delay instead of immediately on every keystroke

### File List

- api/app/api/admin.py (modified - added create_user, update_user, toggle_user_status endpoints; added search param to list_users)
- api/app/api/admin_test.py (modified - added 10 new tests for new endpoints)
- api/app/services/admin_service.py (modified - added create_user, update_user, toggle_user_status methods; updated list_users with search)
- api/app/services/admin_service_test.py (modified - added 8 new tests for new service methods)
- api/app/repositories/user_repository.py (modified - added update_user, update_status methods; modified list_all for search)
- api/app/repositories/user_repository_test.py (modified - added 4 new tests for new repo methods)
- api/app/schemas/admin.py (modified - added AdminCreateUserRequest, AdminUpdateUserRequest, UserStatusRequest; updated UserListItem with is_active)
- web/src/app/admin/users/components/UserList.tsx (modified - added search, create, edit, status column, deactivate/reactivate)
- web/src/app/admin/users/components/UserList.test.tsx (modified - added 4 new tests for search, create, deactivate, status)
