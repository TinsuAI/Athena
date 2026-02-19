# Story 5.5: Admin Permission Management

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **administrator**,
I want **to manage permissions per role and per individual user**,
So that **I can fine-tune access control beyond the default role-based system**.

## Acceptance Criteria

1. **Given** the permission system, **When** I check the predefined permissions, **Then** the following exist: `correction.submit`, `correction.approve`, `user.manage`, `data.manage`, `lookup.view_all`.

2. **Given** the default role permissions, **When** I check each role, **Then** defaults are: user gets `correction.submit`; expert gets `correction.submit`, `correction.approve`, `lookup.view_all`; admin gets ALL permissions.

3. **Given** I am an admin on the permission management page (`/admin/permissions`), **When** I view the "Vai tro" (Roles) tab, **Then** I see each role with its default permissions as checkboxes.

4. **Given** I am an admin on the permission management page, **When** I view the "Nguoi dung" (Users) tab and select a user, **Then** I see their effective permissions (role defaults + overrides) **And** I can grant or revoke individual permissions.

5. **Given** a user has a per-user override revoking `correction.submit`, **When** the system checks their permissions, **Then** the override takes priority over the role default.

6. **Given** a permission check is performed, **When** the middleware calls `has_permission(user, "permission.code")`, **Then** it checks: role_permissions + user_permission_overrides (overrides win).

7. **Given** I am not an admin, **When** I try to access permission management endpoints, **Then** I receive 403 Forbidden.

## Tasks / Subtasks

- [x] Task 1: DB migration -- Create `permissions`, `role_permissions`, `user_permission_overrides` tables (AC: #1, #2)
  - [x] 1.1 Create migration file `20260218_create_permission_tables.py`
  - [x] 1.2 `permissions` table: `id` (PK), `code` (varchar, unique), `name` (varchar), `description` (text)
  - [x] 1.3 `role_permissions` table: `id` (PK), `role` (varchar), `permission_code` (varchar, FK->permissions.code), unique(role, permission_code)
  - [x] 1.4 `user_permission_overrides` table: `id` (PK), `user_id` (int, FK->users.id), `permission_code` (varchar, FK->permissions.code), `granted` (bool), unique(user_id, permission_code)
  - [x] 1.5 Seed default permissions: correction.submit, correction.approve, user.manage, data.manage, lookup.view_all
  - [x] 1.6 Seed default role_permissions: user->correction.submit; expert->correction.submit, correction.approve, lookup.view_all; admin->ALL five permissions

- [x] Task 2: Create SQLAlchemy models (AC: #1, #2)
  - [x] 2.1 Create `api/app/models/permission.py` with `Permission`, `RolePermission`, `UserPermissionOverride` models
  - [x] 2.2 Register models in `api/app/models/__init__.py`

- [x] Task 3: Create `permission_service.py` with `has_permission()` check (AC: #5, #6)
  - [x] 3.1 Create `api/app/services/permission_service.py` with `PermissionService` class
  - [x] 3.2 `has_permission(user_id, role, permission_code)` -- check role_permissions + user_permission_overrides (overrides win)
  - [x] 3.3 `get_role_permissions(role)` -- return list of permission codes for a role
  - [x] 3.4 `get_user_effective_permissions(user_id, role)` -- return effective permissions (role defaults + overrides applied)
  - [x] 3.5 `update_role_permissions(role, permission_codes)` -- replace role's permissions
  - [x] 3.6 `get_user_overrides(user_id)` -- return list of user-specific overrides
  - [x] 3.7 `update_user_overrides(user_id, overrides)` -- replace user's permission overrides

- [x] Task 4: Create permission repository (AC: #1, #2, #5, #6)
  - [x] 4.1 Create `api/app/repositories/permission_repository.py` with `PermissionRepository` class
  - [x] 4.2 `list_all_permissions()` -- return all permission records
  - [x] 4.3 `get_role_permissions(role)` -- return permission codes for a role
  - [x] 4.4 `set_role_permissions(role, codes)` -- delete existing + insert new role_permissions
  - [x] 4.5 `get_user_overrides(user_id)` -- return user's permission overrides
  - [x] 4.6 `set_user_overrides(user_id, overrides)` -- delete existing + insert new overrides
  - [x] 4.7 `get_user_override(user_id, permission_code)` -- return single override or None
  - [x] 4.8 `check_permission_exists(code)` -- validate permission code exists

- [x] Task 5: Create permission API endpoints in `admin.py` (AC: #3, #4, #7)
  - [x] 5.1 `GET /api/admin/permissions/roles` -- list all roles with their permissions
  - [x] 5.2 `PUT /api/admin/permissions/roles/{role}` -- update role permissions, body: `{ permissions: ["code1", "code2"] }`
  - [x] 5.3 `GET /api/admin/permissions/users/{id}` -- user's effective permissions + overrides
  - [x] 5.4 `PUT /api/admin/permissions/users/{id}` -- update user permission overrides, body: `{ overrides: [{ code, granted }] }`
  - [x] 5.5 Add Pydantic schemas: `RolePermissionsResponse`, `UpdateRolePermissionsRequest`, `UserPermissionsResponse`, `UpdateUserPermissionsRequest`, `PermissionOverrideItem`

- [x] Task 6: Build `/admin/permissions` page with roles tab and users tab (AC: #3, #4)
  - [x] 6.1 Create `web/src/app/admin/permissions/page.tsx` -- wrapper page
  - [x] 6.2 Create `web/src/app/admin/permissions/components/PermissionManager.tsx` -- main component with tabs
  - [x] 6.3 "Vai tro" (Roles) tab -- shows each role with checkboxes for permissions, save button
  - [x] 6.4 "Nguoi dung" (Users) tab -- user search/select, shows effective permissions with override toggles
  - [x] 6.5 Add "Quan ly quyen han" (Permission management) link to admin dashboard page

- [x] Task 7: Integrate permission checks into existing endpoints (AC: #6)
  - [x] 7.1 Create `require_permission(permission_code)` dependency factory in `auth.py`
  - [x] 7.2 Replace hardcoded `require_admin` on correction approval endpoints with `require_permission("correction.approve")`
  - [x] 7.3 Replace hardcoded `require_admin` on user management endpoints with `require_permission("user.manage")`
  - [x] 7.4 Keep `require_admin` for permission management endpoints themselves (meta-permission)
  - [x] 7.5 IMPORTANT: `require_admin` stays on permission management endpoints -- only admin manages permissions

- [x] Task 8: Backend tests (AC: #1-#7)
  - [x] 8.1 `api/app/services/permission_service_test.py`: test has_permission with role defaults
  - [x] 8.2 `api/app/services/permission_service_test.py`: test has_permission with user override revoking
  - [x] 8.3 `api/app/services/permission_service_test.py`: test has_permission with user override granting
  - [x] 8.4 `api/app/services/permission_service_test.py`: test get_user_effective_permissions merges role + overrides
  - [x] 8.5 `api/app/services/permission_service_test.py`: test update_role_permissions replaces permissions
  - [x] 8.6 `api/app/services/permission_service_test.py`: test update_user_overrides replaces overrides
  - [x] 8.7 `api/app/repositories/permission_repository_test.py`: test list_all_permissions returns seeded data
  - [x] 8.8 `api/app/repositories/permission_repository_test.py`: test get_role_permissions returns correct codes
  - [x] 8.9 `api/app/repositories/permission_repository_test.py`: test set_role_permissions replaces entries
  - [x] 8.10 `api/app/repositories/permission_repository_test.py`: test get_user_overrides returns overrides
  - [x] 8.11 `api/app/repositories/permission_repository_test.py`: test set_user_overrides replaces entries
  - [x] 8.12 `api/app/api/admin_test.py`: test GET /api/admin/permissions/roles returns all roles
  - [x] 8.13 `api/app/api/admin_test.py`: test PUT /api/admin/permissions/roles/{role} updates permissions
  - [x] 8.14 `api/app/api/admin_test.py`: test GET /api/admin/permissions/users/{id} returns effective permissions
  - [x] 8.15 `api/app/api/admin_test.py`: test PUT /api/admin/permissions/users/{id} updates overrides
  - [x] 8.16 `api/app/api/admin_test.py`: test permission endpoints require admin role (403 for user/expert)

- [x] Task 9: Frontend tests (AC: #3, #4)
  - [x] 9.1 `web/src/app/admin/permissions/components/PermissionManager.test.tsx`: test roles tab shows permissions
  - [x] 9.2 `web/src/app/admin/permissions/components/PermissionManager.test.tsx`: test users tab shows user search
  - [x] 9.3 `web/src/app/admin/permissions/components/PermissionManager.test.tsx`: test permission checkbox toggles

## Dev Notes

### CRITICAL: This Story CREATES New Permission System Tables and Service

This story introduces a new permission model with three database tables (`permissions`, `role_permissions`, `user_permission_overrides`) and a `PermissionService` that provides `has_permission()` checks combining role defaults with per-user overrides.

**Already exists (DO NOT recreate):**
- `api/app/api/admin.py` -- Admin router with user management endpoints (POST create, PATCH update, PATCH status, GET list, PATCH role, GET audit-log). Uses `require_admin` dependency, `AdminService`.
- `api/app/services/admin_service.py` -- `AdminService` class with `list_users()`, `create_user()`, `update_user()`, `toggle_user_status()`, `update_user_role()` methods.
- `api/app/repositories/user_repository.py` -- `UserRepository` with `create()`, `get_by_email()`, `get_by_id()`, `update_password()`, `list_all()`, `update_role()`, `update_user()`, `update_status()`.
- `api/app/schemas/admin.py` -- `RoleUpdateRequest`, `AdminCreateUserRequest`, `AdminUpdateUserRequest`, `UserStatusRequest`, `UserListItem`, `UserListResponse`, `AuditLogResponse`.
- `api/app/models/user.py` -- `User` model with `id`, `email`, `password_hash`, `role`, `is_active`, `created_at`.
- `api/app/core/auth.py` -- `require_admin`, `require_authenticated`, `require_expert`, `get_optional_user`, `get_current_user`.
- `api/app/api/deps.py` -- `get_db_session` dependency.
- `api/app/schemas/base.py` -- `success_response()` / `error_response()` envelope helpers.
- `api/app/repositories/audit_log_repository.py` -- `AuditLogRepository.create(admin_user_id, action, target_user_id, details)`.
- `web/src/app/admin/layout.tsx` -- Admin layout with role check.
- `web/src/app/admin/page.tsx` -- Admin dashboard with link to user management.
- `web/src/app/admin/users/` -- Existing user management page.
- `web/src/lib/api.ts` -- `apiClient` with `get/post/patch/put/delete` methods, `credentials: 'include'`.

**What this story CREATES (new files):**
- `api/alembic/versions/20260218_create_permission_tables.py` -- Migration creating 3 tables + seeding defaults
- `api/app/models/permission.py` -- `Permission`, `RolePermission`, `UserPermissionOverride` models
- `api/app/services/permission_service.py` -- `PermissionService` with `has_permission()`, role/user permission CRUD
- `api/app/services/permission_service_test.py` -- Tests for permission service
- `api/app/repositories/permission_repository.py` -- `PermissionRepository` for permission DB queries
- `api/app/repositories/permission_repository_test.py` -- Tests for permission repository
- `web/src/app/admin/permissions/page.tsx` -- Permission management page wrapper
- `web/src/app/admin/permissions/components/PermissionManager.tsx` -- Main permission management UI component
- `web/src/app/admin/permissions/components/PermissionManager.test.tsx` -- Frontend tests

**What this story MODIFIES (existing files):**
- `api/app/models/__init__.py` -- Register new models: `Permission`, `RolePermission`, `UserPermissionOverride`
- `api/app/api/admin.py` -- Add 4 permission endpoints: GET/PUT roles, GET/PUT users
- `api/app/api/admin_test.py` -- Add tests for new permission endpoints
- `api/app/schemas/admin.py` -- Add permission-related schemas
- `api/app/core/auth.py` -- Add `require_permission()` dependency factory
- `web/src/app/admin/page.tsx` -- Add "Quan ly quyen han" link to dashboard

### Backend Architecture: Layered Pattern

Follow the strict layered architecture:

```
admin.py (API) -> permission_service.py (Service) -> permission_repository.py (Repository)
```

**Route handler (`admin.py`):** ONLY validates request, calls service, formats response with `success_response()`/`error_response()`. NO business logic.

**Service (`permission_service.py`):** ALL business logic -- permission resolution (role defaults + overrides), validation of permission codes, audit logging.

**Repository (`permission_repository.py`):** ONLY database queries -- CRUD on permissions, role_permissions, user_permission_overrides tables.

### Database Tables

```sql
-- Predefined permission codes
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Default permissions per role
CREATE TABLE role_permissions (
    id SERIAL PRIMARY KEY,
    role VARCHAR(20) NOT NULL,
    permission_code VARCHAR(50) NOT NULL REFERENCES permissions(code),
    UNIQUE(role, permission_code)
);

-- Per-user permission grants/revokes (overrides role defaults)
CREATE TABLE user_permission_overrides (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    permission_code VARCHAR(50) NOT NULL REFERENCES permissions(code),
    granted BOOLEAN NOT NULL,
    UNIQUE(user_id, permission_code)
);
```

**Seed data (in migration):**

```sql
-- Permissions
INSERT INTO permissions (code, name, description) VALUES
('correction.submit', 'Gui chinh sua', 'Can submit corrections to lookup records'),
('correction.approve', 'Phe duyet chinh sua', 'Can approve or reject pending corrections'),
('user.manage', 'Quan ly nguoi dung', 'Can create, edit, deactivate users'),
('data.manage', 'Quan ly du lieu', 'Can upload and manage tariff data'),
('lookup.view_all', 'Xem tat ca tra cuu', 'Can view all lookup records, not just own');

-- Role defaults
-- user role
INSERT INTO role_permissions (role, permission_code) VALUES ('user', 'correction.submit');
-- expert role
INSERT INTO role_permissions (role, permission_code) VALUES
('expert', 'correction.submit'),
('expert', 'correction.approve'),
('expert', 'lookup.view_all');
-- admin role (ALL permissions)
INSERT INTO role_permissions (role, permission_code) VALUES
('admin', 'correction.submit'),
('admin', 'correction.approve'),
('admin', 'user.manage'),
('admin', 'data.manage'),
('admin', 'lookup.view_all');
```

### SQLAlchemy Models

```python
# api/app/models/permission.py

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Permission(Base):
    """Predefined permission code."""
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class RolePermission(Base):
    """Default permission assigned to a role."""
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role", "permission_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    permission_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("permissions.code"), nullable=False
    )


class UserPermissionOverride(Base):
    """Per-user permission grant or revocation (overrides role default)."""
    __tablename__ = "user_permission_overrides"
    __table_args__ = (UniqueConstraint("user_id", "permission_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    permission_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("permissions.code"), nullable=False
    )
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
```

### API Endpoint Details

```python
# api/app/api/admin.py -- ADD these endpoints to existing router

# GET /api/admin/permissions/roles
# - Protected by require_admin
# - Returns all 3 roles (user, expert, admin) each with their permission codes
# - Calls permission_service.get_all_role_permissions()
# - Response: { roles: [{ role: "user", permissions: ["correction.submit"] }, ...] }

# PUT /api/admin/permissions/roles/{role}
# - Protected by require_admin
# - Body: { permissions: ["correction.submit", "correction.approve"] }
# - Validates role is valid (user/expert/admin), validates all permission codes exist
# - Calls permission_service.update_role_permissions(role, permissions)
# - Creates audit log entry
# - Returns success_response with updated role permissions

# GET /api/admin/permissions/users/{user_id}
# - Protected by require_admin
# - Returns user info, role defaults, overrides, and effective permissions
# - Calls permission_service.get_user_effective_permissions(user_id, role)
# - Response: { user_id, role, role_permissions: [...], overrides: [{code, granted}], effective: [...] }

# PUT /api/admin/permissions/users/{user_id}
# - Protected by require_admin
# - Body: { overrides: [{ code: "correction.submit", granted: false }] }
# - Validates all permission codes exist
# - Calls permission_service.update_user_overrides(user_id, overrides)
# - Creates audit log entry
# - Returns success_response with updated user permissions
```

### Pydantic Schemas (add to `api/app/schemas/admin.py`)

```python
class PermissionItem(BaseModel):
    """A single permission definition."""
    code: str
    name: str
    description: str | None = None

class RolePermissionsItem(BaseModel):
    """A role with its permission codes."""
    role: str
    permissions: list[str]

class RolePermissionsListResponse(BaseModel):
    """Response for listing all role permissions."""
    all_permissions: list[PermissionItem]
    roles: list[RolePermissionsItem]

class UpdateRolePermissionsRequest(BaseModel):
    """Request to update a role's permissions."""
    permissions: list[str]

class PermissionOverrideItem(BaseModel):
    """A single user permission override."""
    code: str
    granted: bool

class UserPermissionsResponse(BaseModel):
    """Response for a user's effective permissions."""
    user_id: int
    role: str
    role_permissions: list[str]
    overrides: list[PermissionOverrideItem]
    effective: list[str]

class UpdateUserPermissionsRequest(BaseModel):
    """Request to update a user's permission overrides."""
    overrides: list[PermissionOverrideItem]
```

### Permission Resolution Logic

```python
# permission_service.py -- has_permission() logic

async def has_permission(self, user_id: int, role: str, permission_code: str) -> bool:
    """Check if user has a specific permission.

    Resolution order:
    1. Check user_permission_overrides for explicit grant/revoke
    2. If no override, check role_permissions for role default
    3. If neither, permission is denied
    """
    # Check user-specific override first (overrides win)
    override = await self.permission_repo.get_user_override(user_id, permission_code)
    if override is not None:
        return override.granted

    # Fall back to role default
    role_perms = await self.permission_repo.get_role_permissions(role)
    return permission_code in role_perms
```

### Auth Middleware: `require_permission()` Factory

```python
# api/app/core/auth.py -- ADD this dependency factory

def require_permission(permission_code: str):
    """Create a dependency that checks if user has a specific permission.

    Usage in route:
        @router.post("/endpoint")
        async def handler(
            current_user: dict = Depends(require_permission("correction.approve")),
            db: AsyncSession = Depends(get_db_session),
        ):

    Resolution: user_permission_overrides > role_permissions > deny
    """
    async def _check_permission(
        request: Request,
        db: AsyncSession = Depends(get_db_session),
    ) -> dict:
        user = await get_current_user(request)
        service = PermissionService(db)
        has_perm = await service.has_permission(
            user_id=user["id"], role=user["role"], permission_code=permission_code
        )
        if not has_perm:
            raise HTTPException(status_code=403, detail=f"Permission required: {permission_code}")
        return user

    return _check_permission
```

**IMPORTANT: Where to apply `require_permission()`:**
- `expert.py` correction approval endpoints: replace `require_expert` with `require_permission("correction.approve")`
- `admin.py` user management endpoints (create, update, toggle_status, list_users): replace `require_admin` with `require_permission("user.manage")`
- `admin.py` permission management endpoints: keep `require_admin` (only admin manages permissions)
- `corrections.py` submit correction: replace `require_authenticated` with `require_permission("correction.submit")`
- NOTE: `require_admin` already checks role=="admin", which is correct for permission management endpoints themselves

### Frontend: `/admin/permissions` Page

**Two tabs:**

1. **"Vai tro" (Roles) tab:**
   - Table with one row per role (user, expert, admin)
   - Columns: Role name, then one checkbox per permission
   - Save button per role or global save
   - Calls `GET /api/admin/permissions/roles` on load
   - Calls `PUT /api/admin/permissions/roles/{role}` on save

2. **"Nguoi dung" (Users) tab:**
   - Search input to find users by email (reuse pattern from UserList.tsx)
   - Select a user to see their permissions
   - Shows: role defaults (read-only), overrides (editable toggles), effective result
   - Override toggle states: "Mac dinh" (Default/inherited), "Cap quyen" (Granted), "Thu hoi" (Revoked)
   - Calls `GET /api/admin/permissions/users/{id}` when user selected
   - Calls `PUT /api/admin/permissions/users/{id}` on save

**Key patterns:**
- Use `apiClient.get/put` from `@/lib/api`
- All UI text in Vietnamese
- Use shadcn/ui components (Tabs, Checkbox, Button, Input)
- Follow existing admin page patterns (UserList.tsx)
- Role labels: `{ user: "Nguoi dung", expert: "Chuyen gia", admin: "Quan tri vien" }`

### Admin Dashboard Update

Add permission management link to `web/src/app/admin/page.tsx`:

```tsx
<Link
  href="/admin/permissions"
  className="block rounded-lg border border-slate-200 bg-white p-6 hover:border-emerald-300 hover:shadow-sm transition-all"
>
  <h2 className="text-lg font-semibold text-slate-900">
    Quan ly quyen han
  </h2>
  <p className="text-sm text-slate-500 mt-1">
    Cau hinh quyen truy cap theo vai tro va nguoi dung
  </p>
</Link>
```

### Project Structure Notes

**New files:**
```
api/alembic/versions/20260218_create_permission_tables.py   # Migration: 3 tables + seed data
api/app/models/permission.py                                 # Permission, RolePermission, UserPermissionOverride models
api/app/services/permission_service.py                       # PermissionService with has_permission(), CRUD
api/app/services/permission_service_test.py                  # Service tests
api/app/repositories/permission_repository.py                # PermissionRepository for DB queries
api/app/repositories/permission_repository_test.py           # Repository tests
web/src/app/admin/permissions/page.tsx                       # Permission management page wrapper
web/src/app/admin/permissions/components/PermissionManager.tsx       # Permission management UI
web/src/app/admin/permissions/components/PermissionManager.test.tsx  # Frontend tests
```

**Modified files:**
```
api/app/models/__init__.py                                   # Register Permission, RolePermission, UserPermissionOverride
api/app/api/admin.py                                         # Add 4 permission endpoints
api/app/api/admin_test.py                                    # Add tests for permission endpoints
api/app/schemas/admin.py                                     # Add permission schemas
api/app/core/auth.py                                         # Add require_permission() factory
web/src/app/admin/page.tsx                                   # Add permission management link
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| `require_admin` dependency | `api/app/core/auth.py` | Admin role gate for permission mgmt endpoints |
| `get_current_user` | `api/app/core/auth.py` | Extract user from JWT for permission checks |
| `AdminService` init pattern | `api/app/services/admin_service.py` | Service with session + repositories |
| `success_response()` / `error_response()` | `api/app/schemas/base.py` | Envelope response format |
| `apiClient.get()` / `apiClient.put()` | `web/src/lib/api.ts` | Frontend API calls with credentials |
| `AuditLogRepository.create()` | `api/app/repositories/audit_log_repository.py` | Audit log entries for permission changes |
| `get_db_session` dependency | `api/app/api/deps.py` | DB session injection |
| Admin dashboard link card | `web/src/app/admin/page.tsx` | Card style for new permission link |
| UserList.tsx search pattern | `web/src/app/admin/users/components/UserList.tsx` | Debounced search input for user tab |
| Route protection | `web/src/app/admin/layout.tsx` | `/admin/*` already protected |
| Tab component pattern | shadcn/ui Tabs | Use for Roles/Users tabs |

### Anti-Patterns to AVOID

- **DO NOT** create a separate `permissions_router.py` -- add permission endpoints to existing `admin.py` router (prefix `/api/admin/permissions/...`)
- **DO NOT** put permission resolution logic in route handlers -- keep in `PermissionService`
- **DO NOT** cache permissions aggressively without invalidation -- permissions change infrequently but must be current
- **DO NOT** use camelCase in API JSON responses -- all snake_case
- **DO NOT** create tests in a separate `/tests` directory -- co-locate with source files
- **DO NOT** remove existing `require_admin`, `require_expert`, `require_authenticated` dependencies -- they remain as convenience aliases
- **DO NOT** make the migration depend on the application being running -- seed data must be in the migration itself using raw SQL inserts
- **DO NOT** use `get_db` -- use `get_db_session` from `api/app/api/deps.py`
- **DO NOT** skip audit logging -- permission changes (role permissions updated, user overrides changed) must create audit entries
- **DO NOT** allow non-admin users to access permission management endpoints -- always use `require_admin`
- **DO NOT** forget to validate permission codes against the `permissions` table before saving -- reject unknown codes with 400
- **DO NOT** use Next.js API routes -- fetch FastAPI directly with `credentials: 'include'`
- **DO NOT** use status enums for loading states -- use boolean flags
- **DO NOT** import `PermissionService` directly into `auth.py` at module level -- use lazy import inside the dependency function to avoid circular imports

### Previous Story Intelligence (from Stories 5-1 through 5-4)

**From Story 5-1 (expert role + auth):**
- User model has `id`, `email`, `password_hash`, `role` (user/expert/admin), `is_active`, `created_at`
- Auth dependencies: `require_admin`, `require_authenticated`, `require_expert`, `get_optional_user`, `get_current_user`
- User dict from auth: `{"id": int, "email": str, "role": str}`

**From Story 5-2 (authenticated corrections):**
- `corrections.py` uses `require_authenticated` for submit endpoint -- this will change to `require_permission("correction.submit")`

**From Story 5-3 (expert approval):**
- `expert.py` uses `require_expert` for approval endpoints -- this will change to `require_permission("correction.approve")`
- `ExpertService` pattern: service with repos
- `get_db_session` is the standard DB dependency (NOT `get_db`)

**From Story 5-4 (admin user management):**
- `admin.py` uses `require_admin` for all endpoints -- user management endpoints change to `require_permission("user.manage")`, permission management endpoints keep `require_admin`
- `AdminService` has `create_user`, `update_user`, `toggle_user_status`, `list_users` methods
- Audit log pattern: `await self.audit_repo.create(admin_user_id=..., action=..., target_user_id=..., details={...})`

**Known pre-existing test failures (ignore):**
- 18 browse component test failures (unrelated)
- 17+ backend test failures in corrections, hs_codes, search, config, excel_parser, auth_integration, browse_repository (all unrelated)

### Git Intelligence

Recent commits:
- `50c2d38` -- feat 5-4: Admin user management with create, edit, deactivate, search
- `4412360` -- feat 5-3: Expert correction approval workflow with review page
- `8d65b4e` -- feat 5-2: Authenticated corrections with pending status workflow
- `d725d14` -- feat 5-1: Add expert role, is_active field, and auth middleware dependencies

Key patterns from recent work:
- All admin endpoints use `require_admin` dependency, `AdminService`/service, `success_response()`/`error_response()`
- `UserRepository` / `AuditLogRepository` are the standard repo patterns
- Frontend uses `apiClient` from `@/lib/api` with typed responses
- All UI text must be in Vietnamese
- Tests are co-located with source files
- Use `get_db_session` (not `get_db`) for DB dependency
- Migration files use naming pattern `YYYYMMDD_description.py`

### Testing Requirements

**Backend tests** (pytest, asyncio_mode=auto, co-located):

1. `api/app/services/permission_service_test.py` (new file):
   - `test_has_permission_returns_true_for_role_default`
   - `test_has_permission_returns_false_for_missing_permission`
   - `test_has_permission_override_revoke_wins_over_role_default`
   - `test_has_permission_override_grant_adds_new_permission`
   - `test_get_user_effective_permissions_merges_role_and_overrides`
   - `test_update_role_permissions_replaces_existing`
   - `test_update_user_overrides_replaces_existing`

2. `api/app/repositories/permission_repository_test.py` (new file):
   - `test_list_all_permissions_returns_seeded_data`
   - `test_get_role_permissions_returns_correct_codes`
   - `test_set_role_permissions_replaces_entries`
   - `test_get_user_overrides_returns_overrides`
   - `test_set_user_overrides_replaces_entries`
   - `test_get_user_override_returns_single_override`

3. `api/app/api/admin_test.py` (additions to existing file):
   - `test_get_role_permissions_returns_all_roles`
   - `test_put_role_permissions_updates_role`
   - `test_put_role_permissions_invalid_code_returns_400`
   - `test_get_user_permissions_returns_effective`
   - `test_put_user_permissions_updates_overrides`
   - `test_permission_endpoints_require_admin_role`

**Frontend tests** (Vitest, jsdom, co-located):

4. `web/src/app/admin/permissions/components/PermissionManager.test.tsx` (new file):
   - `test_roles_tab_shows_role_permissions`
   - `test_users_tab_shows_user_search`
   - `test_permission_checkbox_toggles`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.5: Admin Permission Management]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-18.md#Story 5-5]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Tables -- permissions, role_permissions, user_permission_overrides]
- [Source: _bmad-output/planning-artifacts/architecture.md#API Endpoints -- permission management]
- [Source: _bmad-output/implementation-artifacts/5-4-admin-user-management.md]
- [Source: _bmad-output/implementation-artifacts/5-3-expert-correction-approval-workflow.md]
- [Source: _bmad-output/implementation-artifacts/5-1-add-expert-role-and-auth-middleware.md]
- [Source: _bmad-output/project-context.md#Auth Flow (CRITICAL)]
- [Source: CLAUDE.md#Architecture -- Backend Layering]
- [Source: CLAUDE.md#Auth Flow]
- [Source: api/app/api/admin.py -- existing admin endpoints]
- [Source: api/app/services/admin_service.py -- existing admin service pattern]
- [Source: api/app/core/auth.py -- existing auth dependencies]
- [Source: api/app/models/user.py -- User model]
- [Source: api/app/models/base.py -- Base model class]
- [Source: api/app/schemas/admin.py -- existing admin schemas]
- [Source: api/app/schemas/base.py -- success_response/error_response]
- [Source: api/app/api/deps.py -- get_db_session dependency]
- [Source: api/app/repositories/audit_log_repository.py -- audit log pattern]
- [Source: web/src/app/admin/page.tsx -- admin dashboard]
- [Source: web/src/app/admin/layout.tsx -- admin layout with role check]
- [Source: web/src/lib/api.ts -- apiClient]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- Frontend test fix: "Nguoi dung" text was ambiguous (appeared in both tab bar and role table). Fixed by using unique permission name "Gui chinh sua" for waitFor assertions.
- Backend tests run via Docker: `docker-compose -f docker-compose.dev.yml exec -T api python -m pytest`
- Frontend tests run via Docker: `docker-compose -f docker-compose.dev.yml exec -T web npm run test:run`

### Completion Notes List

- All 9 tasks completed (Tasks 1-9 with all subtasks)
- 62 backend tests passing (10 permission_service + 9 permission_repository + 30 admin_test + 13 other)
- 3 frontend tests passing (PermissionManager.test.tsx)
- Permission resolution: user_permission_overrides > role_permissions > deny
- `require_permission()` uses lazy import to avoid circular dependencies
- expert.py: `require_expert` -> `require_permission("correction.approve")`
- corrections.py: `require_authenticated` -> `require_permission("correction.submit")`
- admin.py user mgmt: `require_admin` -> `require_permission("user.manage")`
- admin.py permission mgmt: keeps `require_admin` (meta-permission)
- All 7 acceptance criteria met

### Change Log

- 2026-02-18: Initial implementation of all 9 tasks -- DB migration, models, service, repository, API endpoints, frontend page, permission integration, backend tests, frontend tests
- 2026-02-19: Code review fixes (2 high + 4 medium issues fixed):
  - [HIGH] Fixed `corrections_test.py`: replaced stale `require_authenticated` patch with correct `require_permission` reference (file: `api/app/api/corrections_test.py`)
  - [HIGH] Fixed `expert_test.py`: replaced tests that tested `require_expert` (no longer used on expert endpoints) with tests targeting `get_current_user` and `require_admin` which correctly reflect the new `require_permission("correction.approve")` dependency behavior (file: `api/app/api/expert_test.py`)
  - [MEDIUM] Added `data-testid="tab-roles"` and `data-testid="tab-users"` to `PermissionManager.tsx` tab buttons; fixed test to use `getByTestId` instead of fragile `getAllByRole("button")[1]` fallback (files: `PermissionManager.tsx`, `PermissionManager.test.tsx`)
  - [MEDIUM] Added `test_get_all_role_permissions_returns_all_roles_and_permissions` test to `permission_service_test.py` to cover `get_all_role_permissions()` method
  - [MEDIUM] Added `user_id` and `role` None-guard to `require_permission()` in `auth.py` to prevent silent None propagation to DB queries when JWT fields are missing
  - [MEDIUM] Fixed all unaccented Vietnamese text in `PermissionManager.tsx` and `PermissionManager.test.tsx` to use properly accented characters (project requirement)

### File List

**New files:**
- `api/alembic/versions/20260218_create_permission_tables.py` -- Migration: 3 tables (permissions, role_permissions, user_permission_overrides) + seed data
- `api/app/models/permission.py` -- Permission, RolePermission, UserPermissionOverride SQLAlchemy models
- `api/app/services/permission_service.py` -- PermissionService with has_permission(), role/user CRUD
- `api/app/services/permission_service_test.py` -- 10 service tests
- `api/app/repositories/permission_repository.py` -- PermissionRepository for DB queries
- `api/app/repositories/permission_repository_test.py` -- 9 repository tests
- `web/src/app/admin/permissions/page.tsx` -- Permission management page wrapper
- `web/src/app/admin/permissions/components/PermissionManager.tsx` -- Main permission management UI (Roles + Users tabs)
- `web/src/app/admin/permissions/components/PermissionManager.test.tsx` -- 3 frontend tests

**Modified files:**
- `api/app/models/__init__.py` -- Registered Permission, RolePermission, UserPermissionOverride models
- `api/app/schemas/admin.py` -- Added 7 permission schemas (PermissionItem, RolePermissionsItem, RolePermissionsListResponse, UpdateRolePermissionsRequest, PermissionOverrideItem, UserPermissionsResponse, UpdateUserPermissionsRequest)
- `api/app/api/admin.py` -- Added 4 permission endpoints, changed user mgmt endpoints from require_admin to require_permission("user.manage")
- `api/app/api/admin_test.py` -- Added 8 permission endpoint tests
- `api/app/core/auth.py` -- Added require_permission(permission_code) factory function
- `api/app/api/expert.py` -- Changed from require_expert to require_permission("correction.approve")
- `api/app/api/corrections.py` -- Changed from require_authenticated to require_permission("correction.submit")
- `web/src/app/admin/page.tsx` -- Added "Quan ly quyen han" link card to admin dashboard
