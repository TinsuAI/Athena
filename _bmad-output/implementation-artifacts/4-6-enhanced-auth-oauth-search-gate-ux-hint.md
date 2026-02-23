# Story 4.6: Enhanced Auth — OAuth Login, Search Gate & Search UX Hint

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want **to log in with Google or Facebook, have my searches protected by login, and see helpful guidance when searching**,
So that **onboarding is easier and I get better search results**.

## Acceptance Criteria

1. **AC1: Google OAuth Login** — **Given** I am on `/login` or `/register`, **When** I click "Đăng nhập với Google", **Then** I am redirected to Google's OAuth consent screen, **And** after authorizing I am logged in and redirected to `/search`, **And** a user account is auto-created if none exists for my Google email.

2. **AC2: Facebook OAuth Login** — **Given** I am on `/login` or `/register`, **When** I click "Đăng nhập với Facebook", **Then** I am redirected to Facebook's OAuth consent screen, **And** after authorizing I am logged in and redirected to `/search`, **And** a user account is auto-created if none exists for my Facebook email.

3. **AC3: Account Conflict Handling** — **Given** I previously registered with email/password for email@example.com, **When** I try to log in via Google OAuth with the same email@example.com, **Then** I see: "Tài khoản này đã đăng ký bằng email/mật khẩu. Vui lòng đăng nhập bằng email và mật khẩu."

4. **AC4: Social Buttons on Login and Register Pages** — **Given** I am on `/login` or `/register`, **When** the page loads, **Then** I see "Đăng nhập với Google" button with Google branding, **And** I see "Đăng nhập với Facebook" button with Facebook branding, **And** the buttons appear with a divider "— hoặc —" separating them from email/password.

5. **AC5: OAuth Users Get Default Role** — **Given** a new user logs in via OAuth for the first time, **When** their account is created, **Then** they are assigned the default "user" role, **And** they appear in the admin user management page.

6. **AC6: Search Requires Authentication** — **Given** I am not logged in, **When** I navigate to `/search`, **Then** I am redirected to `/login?callbackUrl=%2Fsearch`, **And** after logging in I am returned to `/search`.

7. **AC7: Search Description Hint** — **Given** I am on `/search` and logged in, **When** the page loads (before I have typed anything), **Then** I see hint text below the search bar: "Mô tả chi tiết sản phẩm để có kết quả chính xác hơn (ví dụ: vật liệu, công dụng, thông số kỹ thuật)", **And** the hint is subtle/fades once the user begins typing.

## Tasks / Subtasks

- [x] Task 1: Backend — DB migration for OAuth users (AC: #1, #2, #5)
  - [x]1.1 Alembic migration: make `password_hash` nullable in `users` table (`ALTER COLUMN password_hash DROP NOT NULL`)
  - [x]1.2 Same migration: add `oauth_provider` (String(50), nullable), `oauth_id` (String(255), nullable) to `users` table
  - [x]1.3 Same migration: add composite unique index on `(oauth_provider, oauth_id)` WHERE both are NOT NULL
  - [x]1.4 Update `User` SQLAlchemy model in `api/app/models/user.py`: `password_hash` → `Mapped[str | None]` with `nullable=True`; add `oauth_provider: Mapped[str | None]` and `oauth_id: Mapped[str | None]`
  - [x]1.5 DO NOT modify `UserCreate` Pydantic schema — it remains for email/password registration only. OAuth users are created via a separate endpoint.

- [x] Task 2: Backend — OAuth user service + endpoint (AC: #1, #2, #3, #5)
  - [x]2.1 Add `AccountConflictError` exception class to `api/app/services/auth_service.py`
  - [x]2.2 Add `find_or_create_oauth_user(email, oauth_provider, oauth_id)` method to `AuthService`:
    - Lookup by email → if found with same `oauth_provider` → return existing
    - If found with different auth method (different provider or credentials user) → raise `AccountConflictError`
    - If not found → create new user with `password_hash=None`, `oauth_provider`, `oauth_id`, `role="user"`
  - [x]2.3 Add `POST /api/auth/oauth` endpoint in `api/app/api/auth.py` — accepts `{email, oauth_provider, oauth_id}`, calls `find_or_create_oauth_user()`, returns envelope response with `{id, email, role, created_at}`, returns 409 on conflict
  - [x]2.4 Tests in `api/app/services/auth_service_test.py`: found existing, created new, conflict with credentials user, new user gets role="user", new user has password_hash=None
  - [x]2.5 Tests in `api/app/api/auth_test.py`: POST /api/auth/oauth valid, existing, conflict 409, missing fields 422

- [x] Task 3: Frontend — Configure NextAuth.js OAuth providers (AC: #1, #2)
  - [x]3.1 Add `Google` provider to `web/src/lib/auth.ts` — `import Google from "next-auth/providers/google"`
  - [x]3.2 Add `Facebook` provider to `web/src/lib/auth.ts` — `import Facebook from "next-auth/providers/facebook"`
  - [x]3.3 Add `signIn` callback to NextAuth config: for OAuth providers (`account.provider !== "credentials"`), call `POST ${API_URL}/api/auth/oauth` with `{email, oauth_provider, oauth_id}` to find/create backend user, attach `id` and `role` to `user` object for JWT callback. On conflict → return `/login?error=OAuthAccountNotLinked`
  - [x]3.4 Add `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`, `AUTH_FACEBOOK_ID`, `AUTH_FACEBOOK_SECRET` to `docker-compose.dev.yml` web service environment and `.env.example`

- [x] Task 4: Social login buttons on Login + Register pages (AC: #1, #2, #3, #4)
  - [x]4.1 Add Google button to `LoginForm.tsx` — calls `signIn("google", { callbackUrl })` with Google brand styling
  - [x]4.2 Add Facebook button to `LoginForm.tsx` — calls `signIn("facebook", { callbackUrl })` with Facebook blue (#1877F2) styling
  - [x]4.3 Add "— hoặc —" divider between social buttons and email/password form section
  - [x]4.4 Mirror same social buttons + divider in `RegisterForm.tsx` (use `callbackUrl: "/search"`)
  - [x]4.5 Detect `?error=OAuthAccountNotLinked` from URL searchParams → display Vietnamese conflict message (AC3)
  - [x]4.6 Tests in `LoginForm.test.tsx`: Google/Facebook buttons render, divider renders, conflict error displays
  - [x]4.7 Tests in `RegisterForm.test.tsx` (create if not exists): social buttons render

- [x] Task 5: Protect `/search` route (AC: #6)
  - [x]5.1 Update `web/src/proxy.ts` matcher: add `"/search/:path*"` to the array
  - [x]5.2 Verify existing `callbackUrl` flow handles `/search` redirect correctly (LoginForm:48 already reads `searchParams.get("callbackUrl") || "/search"`)

- [x] Task 6: Search description hint (AC: #7)
  - [x]6.1 Update hint text below SearchBar in `web/src/app/search/page.tsx:168-171`: conditional display based on `searchQuery`
  - [x]6.2 When query is empty → show: "Mô tả chi tiết sản phẩm để có kết quả chính xác hơn (ví dụ: vật liệu, công dụng, thông số kỹ thuật)"
  - [x]6.3 When query has content → show: "Nhấn Enter hoặc bấm Tìm kiếm để tra cứu mã HS" (original text)
  - [x]6.4 Use `transition-opacity duration-300` for smooth text change

- [x] Task 7: Update Story 4-2 dev notes (doc only)
  - [x]7.1 Update route table in `_bmad-output/implementation-artifacts/4-2-user-login.md` to move `/search` from public to protected

## Dev Notes

### CRITICAL: This story combines three distinct features in one delivery

1. **Social OAuth Login** (Tasks 1-4) — Google + Facebook via NextAuth.js v5 providers
2. **Search Auth Gate** (Task 5) — `/search` moved from public to protected route
3. **Search UX Hint** (Task 6) — Detailed product description guidance text

All three are auth-layer or auth-adjacent changes. Sprint change proposal (2026-02-22) consolidates them.

### CRITICAL: Sprint Change Reversal — `/search` route

Story 4-2 documented `/search` as explicitly public per UX spec. This story **reverses** that decision per sprint change proposal 2026-02-22. Update Story 4-2 dev notes (doc only, Task 7).

### Backend OAuth Architecture

The backend needs a new `POST /api/auth/oauth` endpoint because NextAuth's `signIn` callback needs to:
1. Auto-create a user record in our DB for OAuth users (so they get an `id` and `role` for the JWT)
2. Handle the conflict case (email exists via different auth method)
3. Return `{id, email, role}` so NextAuth can include it in the JWT

**CRITICAL**: DO NOT modify `UserCreate` or the `/api/auth/register` endpoint. OAuth user creation is a separate flow via `/api/auth/oauth`. The `register_user()` method stays for email/password only.

```python
# api/app/services/auth_service.py — ADD these

class AccountConflictError(Exception):
    """Raised when OAuth email conflicts with existing credentials account."""
    pass

# ADD to AuthService class:
async def find_or_create_oauth_user(
    self, email: str, oauth_provider: str, oauth_id: str
) -> UserResponse:
    existing = await self.repo.get_by_email(email)
    if existing is not None:
        if existing.oauth_provider == oauth_provider:
            return UserResponse(
                id=existing.id, email=existing.email,
                role=existing.role, created_at=existing.created_at,
            )
        raise AccountConflictError(
            "Tài khoản này đã đăng ký bằng email/mật khẩu. "
            "Vui lòng đăng nhập bằng email và mật khẩu."
        )
    user = User(
        email=email, password_hash=None,
        oauth_provider=oauth_provider, oauth_id=oauth_id, role="user",
    )
    created = await self.repo.create(user)
    return UserResponse(
        id=created.id, email=created.email,
        role=created.role, created_at=created.created_at,
    )
```

```python
# api/app/api/auth.py — ADD endpoint

class OAuthUserRequest(BaseModel):
    email: str
    oauth_provider: str
    oauth_id: str

@router.post("/oauth")
async def oauth_find_or_create(
    data: OAuthUserRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    service = AuthService(db)
    try:
        result = await service.find_or_create_oauth_user(
            email=data.email,
            oauth_provider=data.oauth_provider,
            oauth_id=data.oauth_id,
        )
        return success_response(result.model_dump(mode="json"))
    except AccountConflictError as e:
        return error_response(
            type_uri="https://athena.example/errors/oauth-conflict",
            title="Account Conflict",
            status=409,
            detail=str(e),
            instance="/api/auth/oauth",
        )
```

### DB Migration — User Model Changes

```python
# api/app/models/user.py — MODIFY:
password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Was nullable=False
oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "google", "facebook", or None
oauth_id: Mapped[str | None] = mapped_column(String(255), nullable=True)       # Provider's user ID
```

**CRITICAL**: Migration must use `ALTER COLUMN password_hash DROP NOT NULL`. Existing users retain their `password_hash`. Only new OAuth users have `password_hash=NULL`.

Add composite unique partial index: `CREATE UNIQUE INDEX ix_users_oauth ON users (oauth_provider, oauth_id) WHERE oauth_provider IS NOT NULL AND oauth_id IS NOT NULL`

### NextAuth.js v5 OAuth Provider Configuration

```typescript
// web/src/lib/auth.ts — FULL UPDATED FILE
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";
import Facebook from "next-auth/providers/facebook";

const API_URL = process.env.API_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8980";

// ... HTTPS check unchanged ...

export const { auth, handlers, signIn, signOut } = NextAuth({
  providers: [
    Google,     // Auto-reads AUTH_GOOGLE_ID + AUTH_GOOGLE_SECRET from env
    Facebook,   // Auto-reads AUTH_FACEBOOK_ID + AUTH_FACEBOOK_SECRET from env
    Credentials({
      // ... existing credentials config unchanged ...
    }),
  ],
  session: { strategy: "jwt", maxAge: 24 * 60 * 60 },
  pages: { signIn: "/login" },
  callbacks: {
    authorized({ auth }) { return !!auth; },
    async signIn({ user, account }) {
      if (account?.provider && account.provider !== "credentials") {
        try {
          const res = await fetch(`${API_URL}/api/auth/oauth`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: user.email,
              oauth_provider: account.provider,
              oauth_id: account.providerAccountId,
            }),
          });
          const data = await res.json();
          if (!data.success) {
            return `/login?error=OAuthAccountNotLinked`;
          }
          user.id = String(data.data.id);
          (user as { role?: string }).role = data.data.role;
          return true;
        } catch {
          return false;
        }
      }
      return true;
    },
    jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = (user as { role?: string }).role;
      }
      return token;
    },
    session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        (session.user as { role?: string }).role = token.role as string;
      }
      return session;
    },
  },
});
```

**CRITICAL**: NextAuth.js v5 uses `AUTH_GOOGLE_ID` / `AUTH_GOOGLE_SECRET` env var names (with `AUTH_` prefix). NOT `GOOGLE_CLIENT_ID`. When using bare `Google` / `Facebook` provider imports (without calling as functions), env vars are auto-detected.

### OAuth Callback URLs

Dev (port 8979):
- Google: `http://localhost:8979/api/auth/callback/google`
- Facebook: `http://localhost:8979/api/auth/callback/facebook`

Production:
- Google: `https://athena.tinsu.ai/api/auth/callback/google`
- Facebook: `https://athena.tinsu.ai/api/auth/callback/facebook`

These are automatically handled by NextAuth's `handlers` export. No additional route configuration needed.

### proxy.ts Update (Task 5)

```typescript
// web/src/proxy.ts
export { auth as default } from "@/lib/auth";

export const config = {
  matcher: ["/search/:path*", "/favorites/:path*", "/history/:path*", "/admin/:path*", "/expert/:path*"],
};
```

This is the ONLY change needed for AC6. The `LoginForm.tsx:48` already reads `searchParams.get("callbackUrl") || "/search"`, so redirect-after-login works automatically.

### Social Login Buttons — UI Layout

```
┌──────────────────────────────────┐
│  [G] Đăng nhập với Google        │  ← White bg, dark text, Google icon
│  [f] Đăng nhập với Facebook      │  ← Facebook blue (#1877F2), white text
│                                  │
│          — hoặc —                │  ← text-slate-400, horizontal rules
│                                  │
│  Email: [________________]       │
│  Mật khẩu: [____________]       │
│  [Đăng nhập]                    │
└──────────────────────────────────┘
```

Use `signIn("google", { callbackUrl })` and `signIn("facebook", { callbackUrl })` — these trigger full OAuth redirect flow.

For conflict error (AC3), detect `?error=OAuthAccountNotLinked` from URL:
```tsx
const oauthError = searchParams.get("error");
if (oauthError === "OAuthAccountNotLinked") {
  // Show: "Tài khoản này đã đăng ký bằng email/mật khẩu. Vui lòng đăng nhập bằng email và mật khẩu."
}
```

### Search Hint Text (Task 6)

Current code at `web/src/app/search/page.tsx:168-171`:
```tsx
<p className="text-[12px] text-slate-400 mt-2.5 text-center font-medium">
  Nhấn Enter hoặc bấm Tìm kiếm để tra cứu mã HS
</p>
```

**Replace** with conditional text:
```tsx
<p className="text-[12px] text-slate-400 mt-2.5 text-center font-medium transition-opacity duration-300">
  {searchQuery.trim()
    ? "Nhấn Enter hoặc bấm Tìm kiếm để tra cứu mã HS"
    : "Mô tả chi tiết sản phẩm để có kết quả chính xác hơn (ví dụ: vật liệu, công dụng, thông số kỹ thuật)"}
</p>
```

The `searchQuery` variable is already available in scope (line 34).

### Environment Variables to Add

```yaml
# docker-compose.dev.yml — web service environment section, add:
AUTH_GOOGLE_ID: ${AUTH_GOOGLE_ID:-}
AUTH_GOOGLE_SECRET: ${AUTH_GOOGLE_SECRET:-}
AUTH_FACEBOOK_ID: ${AUTH_FACEBOOK_ID:-}
AUTH_FACEBOOK_SECRET: ${AUTH_FACEBOOK_SECRET:-}
```

```bash
# .env.example — append:
# OAuth Configuration (optional — social login won't work without these)
AUTH_GOOGLE_ID=your-google-oauth-client-id
AUTH_GOOGLE_SECRET=your-google-oauth-client-secret
AUTH_FACEBOOK_ID=your-facebook-app-id
AUTH_FACEBOOK_SECRET=your-facebook-app-secret
```

### Routes After This Story

| Route | Auth Required | Notes |
|-------|--------------|-------|
| `/` | No | Landing page |
| `/search` | **Yes** (NEW) | Redirects to /login with callbackUrl |
| `/browse` | No | Tariff browser stays public |
| `/lookups` | No | Lookup list stays public |
| `/favorites` | Yes | Unchanged |
| `/history` | Yes | Unchanged |
| `/admin` | Yes | Unchanged |
| `/expert` | Yes | Unchanged |
| `/login` | No | |
| `/register` | No | |

### Project Structure Notes

**New files:**
```
api/alembic/versions/YYYYMMDD_add_oauth_columns_to_users.py  # Migration
```

**Modified files:**
```
api/app/models/user.py                       # password_hash nullable, add oauth_provider, oauth_id
api/app/services/auth_service.py             # Add AccountConflictError, find_or_create_oauth_user()
api/app/services/auth_service_test.py        # Add OAuth tests
api/app/api/auth.py                          # Add OAuthUserRequest, POST /api/auth/oauth endpoint
api/app/api/auth_test.py                     # Add OAuth endpoint tests
web/src/lib/auth.ts                          # Add Google + Facebook providers, signIn callback
web/src/proxy.ts                             # Add "/search/:path*" to matcher
web/src/app/(auth)/login/LoginForm.tsx       # Add social buttons, divider, conflict error
web/src/app/(auth)/login/LoginForm.test.tsx  # Add social button tests
web/src/app/(auth)/register/RegisterForm.tsx # Add social buttons, divider
web/src/app/search/page.tsx                  # Update hint text
docker-compose.dev.yml                       # Add OAuth env vars to web service
.env.example                                 # Add OAuth env var templates
_bmad-output/implementation-artifacts/4-2-user-login.md  # Route table doc update
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| NextAuth providers config | `web/src/lib/auth.ts` | Existing Credentials provider pattern |
| `signIn()` call pattern | `web/src/app/(auth)/login/LoginForm.tsx:49` | `signIn("credentials", { redirect: false })` |
| Route protection | `web/src/proxy.ts` | Matcher array pattern |
| Backend auth endpoints | `api/app/api/auth.py` | Router prefix `/api/auth`, Depends, envelope response |
| User creation pattern | `api/app/services/auth_service.py:55-60` | `User()` constructor, `repo.create()` |
| Envelope responses | `api/app/schemas/base.py` | `success_response`, `error_response` |
| Form error display | `web/src/app/(auth)/login/LoginForm.tsx:144-151` | Server error alert pattern |
| Co-located tests | All test files | `*_test.py` / `*.test.tsx` in same directory |
| Alembic migrations | `api/alembic/versions/` | Existing migration file patterns |
| Vietnamese UI text | All auth forms | Vietnamese language for all user-facing strings |

### Anti-Patterns to AVOID

- **DO NOT** use `middleware.ts` — Next.js 16 uses `proxy.ts`
- **DO NOT** use `GOOGLE_CLIENT_ID` env var — NextAuth v5 expects `AUTH_GOOGLE_ID` (with `AUTH_` prefix)
- **DO NOT** modify `UserCreate` schema or `register_user()` — OAuth has its own endpoint
- **DO NOT** modify `authenticate_user()` — it remains for email/password only
- **DO NOT** allow OAuth users to set a password — they must continue using OAuth
- **DO NOT** store OAuth access/refresh tokens in DB — NextAuth manages those
- **DO NOT** create a separate middleware for search protection — proxy.ts matcher handles it
- **DO NOT** protect `/browse` or `/lookups` — they must remain public
- **DO NOT** use `passlib` — project uses `bcrypt` directly
- **DO NOT** use camelCase in API JSON responses — use snake_case
- **DO NOT** create tests in separate `/tests` directory — co-locate with source files
- **DO NOT** put business logic in route handlers — `find_or_create_oauth_user` goes in `AuthService`
- **DO NOT** use status enums for loading states — use boolean flags
- **DO NOT** fetch via Next.js API routes — fetch FastAPI directly with `credentials: 'include'`
- **DO NOT** use `export { auth as proxy }` — use `export { auth as default }` in proxy.ts

### Previous Story Intelligence (from 4-1 through 4-5)

**From Story 4-1 (User Registration):**
- Auth flow: RegisterForm → POST /api/auth/register → signIn("credentials") → JWT session
- bcrypt for password hashing (NOT passlib), cost factor 12
- User model: `id, email, password_hash, role, is_active, created_at`
- `UserCreate` requires `email` + `password` (min 8 chars) — leave unchanged

**From Story 4-2 (User Login):**
- `proxy.ts` (NOT middleware.ts) for route protection — already protects `/admin`, `/favorites`, `/history`, `/expert`
- LoginForm uses `searchParams.get("callbackUrl") || "/search"` — callbackUrl flow works
- JWT carries `id`, `email`, `role` via `jwt` and `session` callbacks
- `authorized` callback returns `!!auth` — works for OAuth sessions identically

**From Story 4-3 (User Logout):**
- Logout clears Zustand store + calls `signOut({ callbackUrl: "/login" })`
- Works identically for OAuth and credentials users

**From Story 4-4 (Password Reset):**
- Redis rate limiting pattern (may want for OAuth endpoint too)
- `authenticate_user()` uses constant-time bcrypt — don't touch

**From Story 4-5 (RBAC):**
- Roles: "user", "expert", "admin" — OAuth users always get "user"
- `require_admin` dependency works unchanged
- Admin user management page shows all users — OAuth users appear automatically
- `is_active` defaults to `True` — OAuth users start active

### Git Intelligence

Recent commits:
- `1927c0c` — refactor: Standardize API routes (removed trailing slashes) — all routes now NO trailing slash
- `2fe4158` through `2fb2b40` — Epic 6 completed (favorites + history)
- `a1b2da5` — Epic 5 marked done

Key patterns from recent commits:
- All API routes have NO trailing slashes
- Envelope format used consistently in all endpoints
- Tests co-located in every commit
- Fire-and-forget pattern for non-critical operations (search history recording)

### Testing Requirements

**Backend tests** (pytest, asyncio_mode=auto, co-located):

1. `api/app/services/auth_service_test.py` (additions):
   - `find_or_create_oauth_user()` — existing OAuth user found and returned
   - `find_or_create_oauth_user()` — new OAuth user created with password_hash=None, role="user"
   - `find_or_create_oauth_user()` — email conflict with credentials user raises AccountConflictError
   - `find_or_create_oauth_user()` — email conflict with different OAuth provider raises AccountConflictError

2. `api/app/api/auth_test.py` (additions):
   - `POST /api/auth/oauth` with valid data creates user → 200 with envelope
   - `POST /api/auth/oauth` with existing OAuth user returns existing → 200
   - `POST /api/auth/oauth` with conflict → 409 with Vietnamese error message
   - `POST /api/auth/oauth` missing fields → 422

**Frontend tests** (Vitest, jsdom, co-located):

3. `web/src/app/(auth)/login/LoginForm.test.tsx` (additions):
   - Google button renders with text "Đăng nhập với Google"
   - Facebook button renders with text "Đăng nhập với Facebook"
   - Divider "— hoặc —" renders between social and email sections
   - Conflict error displays when URL has `?error=OAuthAccountNotLinked`

4. `web/src/app/(auth)/register/RegisterForm.test.tsx` (additions or create):
   - Social buttons render on register page
   - Divider renders

5. Search page hint text:
   - Hint shows detailed guidance when search query is empty
   - Hint changes to instruction text when query has content

6. Regression: all existing email/password login + registration tests pass unchanged

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-22.md — PRIMARY source]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: User Authentication & Sessions]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#OAuth Notes (Sprint Change 2026-02-22)]
- [Source: _bmad-output/project-context.md#Auth Flow (CRITICAL)]
- [Source: _bmad-output/implementation-artifacts/4-5-role-based-access-control.md]
- [Source: _bmad-output/implementation-artifacts/4-2-user-login.md]
- [Source: CLAUDE.md#Auth Flow]
- [Source: CLAUDE.md#Architecture]
- [Source: web/src/lib/auth.ts — Current NextAuth config]
- [Source: web/src/proxy.ts — Current route matcher]
- [Source: web/src/app/(auth)/login/LoginForm.tsx — Current login form]
- [Source: web/src/app/(auth)/register/RegisterForm.tsx — Current register form]
- [Source: web/src/app/search/page.tsx:168-171 — Current hint text]
- [Source: api/app/models/user.py — User model]
- [Source: api/app/services/auth_service.py — AuthService]
- [Source: api/app/api/auth.py — Auth endpoints]
- [Source: api/app/schemas/user.py — User schemas]
- [Source: api/app/repositories/user_repository.py — UserRepository]
- [Source: docker-compose.dev.yml:78-82 — Web service env vars]
- [Source: .env.example — Env var templates]

## Change Log

- 2026-02-22: Story created via Sprint Change 2026-02-22 (Correct Course workflow). Covers FR71, FR72, FR73.
- 2026-02-22: Ultimate context engine analysis completed — comprehensive developer guide created.
- 2026-02-23: Code review completed. 1 critical + 2 high + 3 medium + 2 low issues found and fixed. Status set to done.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None required.

### Completion Notes List

- **Task 1**: Created Alembic migration `20260223_add_oauth_columns_to_users.py` making `password_hash` nullable, adding `oauth_provider` and `oauth_id` columns with partial unique index. Updated User SQLAlchemy model accordingly.
- **Task 2**: Added `AccountConflictError` exception and `find_or_create_oauth_user()` method to `AuthService`. Created `POST /api/auth/oauth` endpoint with `OAuthUserRequest` schema. Added 4 service tests and 4 endpoint tests — all 43 backend auth tests pass.
- **Task 3**: Added Google and Facebook providers to NextAuth.js config. Added `signIn` callback that calls backend `/api/auth/oauth` for OAuth providers, handles conflict by redirecting to `/login?error=OAuthAccountNotLinked`. Added OAuth env vars to `docker-compose.dev.yml` and `.env.example`.
- **Task 4**: Integrated social login buttons (Google with brand colors, Facebook with #1877F2) into both `LoginForm.tsx` and `RegisterForm.tsx`. Added "hoặc" divider. Added OAuth conflict error display for `OAuthAccountNotLinked`. Used `/frontend-design` skill for UI implementation. Added 6 new LoginForm tests and 3 new RegisterForm tests — all 22 frontend auth tests pass.
- **Task 5**: Added `"/search/:path*"` to proxy.ts matcher array. Existing callbackUrl flow handles redirect automatically.
- **Task 6**: Updated search page hint text to be conditional on `searchQuery` — shows detailed product description guidance when empty, search instruction when typing. Uses `transition-opacity duration-300`.
- **Task 7**: Updated Story 4-2 dev notes to reflect `/search` route change from public to protected.
- **Code Review (2026-02-23)**: 8 issues found and fixed:
  - CRITICAL: `authenticate_user()` crashed with AttributeError when OAuth user (password_hash=None) tried credentials login — fixed by using dummy_hash when `user.password_hash is None` (`auth_service.py:126`)
  - HIGH: `OAuthUserRequest.email` had no format validation — added `@field_validator("email")` with regex matching all other auth schemas (`auth.py`)
  - HIGH: Missing test for OAuth user credentials login attempt — added `test_authenticate_oauth_user_with_null_password_hash_returns_none` (`auth_service_test.py`)
  - MEDIUM: `find_or_create_oauth_user` had TOCTOU race condition with no `IntegrityError` handling — added try/except with re-fetch fallback (`auth_service.py`)
  - MEDIUM: `architecture.md` and `prd.md` were modified in git but not documented in File List — added to File List
  - LOW: AC4 divider specified "— hoặc —" but implementation rendered just "hoặc" — fixed in both LoginForm.tsx and RegisterForm.tsx (and updated tests)

### File List

**New files:**
- `api/alembic/versions/20260223_add_oauth_columns_to_users.py` — Migration for OAuth columns

**Modified files:**
- `api/app/models/user.py` — password_hash nullable, added oauth_provider + oauth_id
- `api/app/services/auth_service.py` — Added AccountConflictError, find_or_create_oauth_user()
- `api/app/services/auth_service_test.py` — Added 4 OAuth service tests
- `api/app/api/auth.py` — Added OAuthUserRequest, POST /api/auth/oauth endpoint
- `api/app/api/auth_test.py` — Added 4 OAuth endpoint tests
- `web/src/lib/auth.ts` — Added Google + Facebook providers, signIn callback
- `web/src/proxy.ts` — Added "/search/:path*" to matcher
- `web/src/app/(auth)/login/LoginForm.tsx` — Added social buttons, divider, conflict error
- `web/src/app/(auth)/login/LoginForm.test.tsx` — Updated existing tests, added 6 social button tests
- `web/src/app/(auth)/register/RegisterForm.tsx` — Added social buttons, divider
- `web/src/app/(auth)/register/RegisterForm.test.tsx` — Updated existing tests, added 3 social button tests
- `web/src/app/search/page.tsx` — Updated hint text to be conditional
- `docker-compose.dev.yml` — Added OAuth env vars to web service
- `.env.example` — Added OAuth env var templates
- `_bmad-output/implementation-artifacts/4-2-user-login.md` — Updated route table doc
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Status: done
- `_bmad-output/planning-artifacts/architecture.md` — OAuth architecture notes added
- `_bmad-output/planning-artifacts/prd.md` — FR71/FR72/FR73 requirements updated
