# Story 4.1: User Registration

Status: done

## Story

As a **new user**,
I want **to create an account with my email and password**,
So that **I can access personalized features like favorites and history**.

## Acceptance Criteria

1. **Given** I am on the registration page (`/register`), **When** I enter a valid email and password (min 8 characters), **Then** my account is created successfully, I am automatically logged in, and I am redirected to the search page.

2. **Given** I try to register with an existing email, **When** I submit the registration form, **Then** I see an error message "Email already registered" and I am prompted to log in instead.

3. **Given** I enter an invalid email format, **When** I submit the registration form, **Then** I see validation error "Please enter a valid email address" and the form is not submitted.

4. **Given** I enter a password shorter than 8 characters, **When** I submit the registration form, **Then** I see validation error "Password must be at least 8 characters".

5. **Given** I register successfully, **When** my account is created, **Then** my password is hashed with bcrypt (cost factor >= 10) (NFR-SEC2) and I am assigned the "user" role by default.

## Tasks / Subtasks

- [x] Task 1: Create User SQLAlchemy model + Alembic migration (AC: #1, #5)
  - [x] 1.1 Create `api/app/models/user.py` with User model (id, email, password_hash, role, created_at)
  - [x] 1.2 Register model in `api/app/models/__init__.py`
  - [x] 1.3 Create Alembic migration: `alembic revision --autogenerate -m "add_users_table"`
  - [x] 1.4 Add unique constraint on email, index on email
  - [x] 1.5 Add FK constraint from `lookup_records.verified_by_user_id` to `users.id` (deferred from Story 1.8)

- [x] Task 2: Create User Pydantic schemas (AC: #1-#4)
  - [x] 2.1 Create `api/app/schemas/user.py` with: `UserCreate` (email, password), `UserResponse` (id, email, role, created_at), `UserLogin` (email, password)
  - [x] 2.2 Ensure all fields use snake_case per naming conventions

- [x] Task 3: Create User repository (AC: #1, #2)
  - [x] 3.1 Create `api/app/repositories/user_repository.py` with: `create()`, `get_by_email()`, `get_by_id()`
  - [x] 3.2 Create `api/app/repositories/user_repository_test.py` (co-located)

- [x] Task 4: Create Auth service with bcrypt password hashing (AC: #1, #2, #5)
  - [x] 4.1 Create `api/app/services/auth_service.py` with: `register_user()`, `hash_password()`, `verify_password()`
  - [x] 4.2 Use `bcrypt` library directly (NOT passlib - see Dev Notes)
  - [x] 4.3 Enforce bcrypt cost factor >= 10 (rounds=12 recommended)
  - [x] 4.4 Handle duplicate email with clear error
  - [x] 4.5 Create `api/app/services/auth_service_test.py` (co-located)

- [x] Task 5: Create registration API endpoint (AC: #1-#5)
  - [x] 5.1 Create `api/app/api/auth.py` with `POST /api/auth/register`
  - [x] 5.2 Use envelope response format (`success_response` / `error_response` from `schemas/base.py`)
  - [x] 5.3 Return RFC 7807 errors for validation failures and duplicate email
  - [x] 5.4 Register router in `api/app/main.py`
  - [x] 5.5 Create `api/app/api/auth_test.py` (co-located)

- [x] Task 6: Create NextAuth.js v5 configuration (AC: #1)
  - [x] 6.1 Create `web/src/lib/auth.ts` (replace stub) with NextAuth v5 config using Credentials provider
  - [x] 6.2 Create `web/src/app/api/auth/[...nextauth]/route.ts` handler
  - [x] 6.3 Configure JWT strategy with shared `NEXTAUTH_SECRET`
  - [x] 6.4 Configure session callback to include user id and role

- [x] Task 7: Create FastAPI JWT validation middleware (AC: #1)
  - [x] 7.1 Create `api/app/core/auth.py` with: `get_current_user()` dependency, JWT decryption using `fastapi-nextauth-jwt`
  - [x] 7.2 Create `api/app/core/auth_test.py` (co-located)

- [x] Task 8: Create Registration page UI (AC: #1-#4)
  - [x] 8.1 Create `web/src/app/(auth)/register/page.tsx` (server component wrapper)
  - [x] 8.2 Create `web/src/app/(auth)/register/RegisterForm.tsx` (client component)
  - [x] 8.3 Use React Hook Form + Zod for validation (validate on blur)
  - [x] 8.4 Call FastAPI `POST /api/auth/register` directly (NOT Next.js API routes)
  - [x] 8.5 On success: call NextAuth `signIn("credentials")` to create session
  - [x] 8.6 On success: redirect to `/search`
  - [x] 8.7 Handle duplicate email error with link to login
  - [x] 8.8 Create `web/src/app/(auth)/register/RegisterForm.test.tsx` (co-located)

- [x] Task 9: Update Zustand store auth slice (AC: #1)
  - [x] 9.1 Update `web/src/lib/store.ts` auth slice with `user` object and `setUser()` action
  - [x] 9.2 Sync auth state with NextAuth session (setUser sets isAuthenticated automatically)

## Dev Notes

### CRITICAL: passlib is BROKEN - Use bcrypt directly

passlib (1.7.4) is **unmaintained** and **incompatible with bcrypt >= 5.0.0**. The project currently has `passlib[bcrypt]>=1.7.4` in requirements.txt but it has never been used yet.

**DO THIS:**
```python
# api/app/services/auth_service.py
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
```

**DO NOT DO THIS:**
```python
# BROKEN - passlib + bcrypt 5.0 incompatible
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])
```

**Update requirements.txt**: Replace `passlib[bcrypt]>=1.7.4` with `bcrypt>=4.0.0`.

### Auth Flow Architecture

The registration flow spans both backend and frontend:

```
1. User fills RegisterForm → POST /api/auth/register (FastAPI)
2. FastAPI creates user in DB → returns { success: true, data: { id, email, role } }
3. Frontend calls signIn("credentials", { email, password }) (NextAuth.js)
4. NextAuth.js authorize() → POST /api/auth/login (FastAPI validates credentials)
5. NextAuth creates encrypted JWT in httpOnly cookie
6. Frontend redirects to /search
```

**Both services MUST share the same `NEXTAUTH_SECRET`** for JWT encryption/decryption.

### NextAuth.js v5 Configuration Pattern

NextAuth v5 (Auth.js) uses this structure:
- Config file: `web/src/lib/auth.ts` exports `{ auth, handlers, signIn, signOut }`
- Route handler: `web/src/app/api/auth/[...nextauth]/route.ts` re-exports `handlers`
- Middleware: `web/src/middleware.ts` for route protection (optional for this story, needed in 4.2)

```typescript
// web/src/lib/auth.ts
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

export const { auth, handlers, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      credentials: { email: {}, password: {} },
      async authorize(credentials) {
        // Call FastAPI login endpoint
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(credentials),
        });
        const data = await res.json();
        if (data.success) return data.data; // { id, email, role }
        return null;
      },
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    jwt({ token, user }) {
      if (user) { token.id = user.id; token.role = user.role; }
      return token;
    },
    session({ session, token }) {
      session.user.id = token.id as string;
      session.user.role = token.role as string;
      return session;
    },
  },
});
```

### fastapi-nextauth-jwt (v2.1.1)

This package decrypts NextAuth.js JWTs on the FastAPI side:

```python
# api/app/core/auth.py
from fastapi import Depends, HTTPException, Request
from fastapi_nextauth_jwt import NextAuthJWT

JWT = NextAuthJWT(secret=settings.nextauth_secret)

async def get_current_user(request: Request) -> dict:
    """Extract user from NextAuth JWT cookie."""
    try:
        token = JWT(request)
        return {"id": token.get("id"), "email": token.get("email"), "role": token.get("role")}
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")
```

### Registration API Endpoint Pattern

Follow the existing pattern from `api/app/api/search.py` and `api/app/api/corrections.py`:

```python
# api/app/api/auth.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.base import success_response, error_response
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db_session)):
    service = AuthService(db)
    result = await service.register_user(user_data)
    if result is None:
        return error_response(
            type_uri="https://athena.example/errors/validation",
            title="Email Already Registered",
            status=409,
            detail="An account with this email already exists. Please log in instead.",
            instance="/api/auth/register",
        )
    return success_response(result)
```

### User Model Pattern

Follow existing model patterns from `api/app/models/lookup_record.py`:

```python
# api/app/models/user.py
from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

### Frontend Registration Form Pattern

Follow existing form patterns - use React Hook Form + Zod, validate on blur:

```typescript
// web/src/app/(auth)/register/RegisterForm.tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { signIn } from "next-auth/react";

const schema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
```

### File Structure (Exact Paths)

**Backend (new files):**
```
api/app/models/user.py                    # User SQLAlchemy model
api/app/schemas/user.py                   # UserCreate, UserResponse
api/app/repositories/user_repository.py   # DB queries only
api/app/repositories/user_repository_test.py
api/app/services/auth_service.py          # Business logic (hash, register)
api/app/services/auth_service_test.py
api/app/api/auth.py                       # POST /api/auth/register, POST /api/auth/login
api/app/api/auth_test.py
api/app/core/auth.py                      # JWT validation dependency
api/app/core/auth_test.py
api/alembic/versions/YYYYMMDD_add_users_table.py  # Migration
```

**Frontend (new/modified files):**
```
web/src/lib/auth.ts                       # REPLACE stub with full NextAuth v5 config
web/src/app/api/auth/[...nextauth]/route.ts  # NextAuth route handler
web/src/app/(auth)/register/page.tsx      # Registration page
web/src/app/(auth)/register/RegisterForm.tsx  # Registration form component
web/src/app/(auth)/register/RegisterForm.test.tsx
```

**Modified files:**
```
api/app/models/__init__.py                # Add User import
api/app/main.py                           # Register auth router
api/requirements.txt                      # Replace passlib with bcrypt
api/pyproject.toml                        # Replace passlib with bcrypt
web/src/lib/store.ts                      # Update auth slice with user object
```

### Testing Requirements

**Backend tests** (pytest, async):
- `auth_service_test.py`: Test password hashing (bcrypt rounds >= 10), registration with valid data, duplicate email handling
- `user_repository_test.py`: Test create_user, get_by_email, get_by_id
- `auth_test.py` (API): Test POST /api/auth/register success, duplicate email 409, validation errors 422

**Frontend tests** (Vitest, jsdom):
- `RegisterForm.test.tsx`: Test form renders, validation on blur (invalid email, short password), successful submission, error display for duplicate email

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| Envelope response | `api/app/schemas/base.py` | `success_response()`, `error_response()` |
| Router registration | `api/app/main.py` | Follow `search_router`, `browse_router` pattern |
| DB session dependency | `api/app/api/deps.py` | `get_db_session()` |
| Model structure | `api/app/models/lookup_record.py` | `Mapped[]`, `mapped_column()` pattern |
| API test pattern | `api/app/api/search_test.py` | `AsyncClient`, `httpx` |
| Frontend form | UX spec | React Hook Form + Zod, validate on blur |
| Type definitions | `web/src/types/user.ts` | `User`, `UserRole`, `Session` types already defined |
| API client | `web/src/lib/api.ts` | Uses `credentials: "include"` already |

### Anti-Patterns to AVOID

- **DO NOT** put registration business logic in the route handler - use AuthService
- **DO NOT** use passlib (broken with bcrypt 5.0)
- **DO NOT** use camelCase in API JSON responses
- **DO NOT** create tests in a separate `/tests` directory
- **DO NOT** use Next.js API routes for data fetching - call FastAPI directly
- **DO NOT** use status enums for loading states - use boolean flags
- **DO NOT** create an "expert" role - only "user" and "admin" exist (see main.py comment)
- **DO NOT** add password confirmation field - not in AC (keep it simple for MVP)

### Project Structure Notes

- Auth route group uses `(auth)` folder convention in Next.js App Router - parentheses mean it doesn't affect URL
- The `web/src/app/(auth)/register/page.tsx` renders at `/register` (not `/auth/register`)
- Backend layering is strict: `api/auth.py` (thin) -> `services/auth_service.py` (logic) -> `repositories/user_repository.py` (DB)
- The login endpoint (`POST /api/auth/login`) is also needed in this story because NextAuth's authorize() callback calls it

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4, Story 4.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Auth Flow]
- [Source: _bmad-output/planning-artifacts/architecture.md#Backend Organization (Layered)]
- [Source: _bmad-output/planning-artifacts/architecture.md#API Response Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Form Patterns]
- [Source: _bmad-output/project-context.md#Auth Flow (CRITICAL)]
- [Source: CLAUDE.md#Auth Flow]
- [Source: CLAUDE.md#Backend Testing & Linting]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Debug Log References
- Installed `fastapi-nextauth-jwt` and `bcrypt` in Docker container (packages added to requirements.txt/pyproject.toml)
- Replaced `passlib[bcrypt]>=1.7.4` with `bcrypt>=4.0.0` as specified in Dev Notes
- Used regex-based email validation in Pydantic schemas to avoid adding `email-validator` dependency
- Lint fix: removed unused `Depends` import from `api/app/core/auth.py`

### Completion Notes List
- All 9 tasks and subtasks completed
- Backend: 25 new tests passing (5 repo + 11 service + 6 API + 3 JWT)
- Frontend: 5 new tests passing (RegisterForm)
- No new regressions introduced (pre-existing failures in browse/corrections/excel tests unchanged)
- All linting checks pass
- Full auth flow: RegisterForm → POST /api/auth/register → signIn("credentials") → POST /api/auth/login → JWT session → redirect /search
- Replaced UserInDB schema with UserLogin schema (login endpoint needed for NextAuth authorize callback)
- Login endpoint added alongside register (required by auth flow architecture)

### File List

**New files:**
- `api/app/models/user.py` — User SQLAlchemy model
- `api/app/schemas/user.py` — UserCreate, UserResponse, UserLogin schemas
- `api/app/repositories/user_repository.py` — User DB queries
- `api/app/repositories/user_repository_test.py` — 5 tests
- `api/app/services/auth_service.py` — AuthService with bcrypt hashing
- `api/app/services/auth_service_test.py` — 11 tests
- `api/app/api/auth.py` — POST /api/auth/register, POST /api/auth/login
- `api/app/api/auth_test.py` — 6 tests
- `api/app/api/auth_integration_test.py` — 7 integration tests (DB)
- `api/app/core/auth.py` — JWT validation dependency (fastapi-nextauth-jwt)
- `api/app/core/auth_test.py` — 3 tests
- `api/alembic/versions/20260215_add_users_table.py` — Migration: users table + FK
- `web/src/app/api/auth/[...nextauth]/route.ts` — NextAuth route handler
- `web/src/app/(auth)/register/page.tsx` — Registration page
- `web/src/app/(auth)/register/RegisterForm.tsx` — Registration form component
- `web/src/app/(auth)/register/RegisterForm.test.tsx` — 5 tests

**Modified files:**
- `api/app/models/__init__.py` — Added User import
- `api/app/models/lookup_record.py` — Added FK on verified_by_user_id → users.id
- `api/app/main.py` — Registered auth_router
- `api/requirements.txt` — Replaced passlib with bcrypt, added fastapi-nextauth-jwt
- `api/pyproject.toml` — Replaced passlib with bcrypt, added fastapi-nextauth-jwt
- `web/src/lib/auth.ts` — Replaced stub with full NextAuth v5 config, added HTTPS enforcement
- `web/src/lib/store.ts` — Added user object and setUser() to auth slice
- `web/src/app/(auth)/register/RegisterForm.tsx` — Added email normalization, error logging
- `api/app/services/auth_service.py` — Fixed timing attack in authenticate_user
- `api/app/core/auth.py` — Added error logging in JWT validation
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Updated story status tracking

### Code Review Fixes Applied (DEV2)
**Issues Fixed:** 7 HIGH/MEDIUM issues resolved
1. **[HIGH]** Added integration tests with real database (7 tests in auth_integration_test.py)
2. **[MEDIUM]** Fixed timing attack vulnerability in authenticate_user (constant-time password check)
3. **[MEDIUM]** Added error logging to JWT validation exception handler
4. **[MEDIUM]** Added error logging to RegisterForm catch block
5. **[MEDIUM]** Added HTTPS enforcement check for production in auth.ts
6. **[MEDIUM]** Added email normalization (.toLowerCase().trim()) to frontend Zod schema
7. **[MEDIUM]** Updated File List to include sprint-status.yaml and review fixes

### Change Log
- 2026-02-15: Story 4-1 implemented — User registration with full auth flow (backend + frontend)
- 2026-02-15: Code review fixes applied — Security improvements, integration tests, error handling
