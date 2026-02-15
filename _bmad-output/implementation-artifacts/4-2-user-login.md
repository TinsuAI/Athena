# Story 4.2: User Login

Status: done

## Story

As a **registered user**,
I want **to log in with my email and password**,
So that **I can access my personal favorites and search history**.

## Acceptance Criteria

1. **Given** I am on the login page (`/login`), **When** I enter valid credentials, **Then** I am logged in successfully, a JWT is created with 24-hour expiry (NFR-SEC3), and I am redirected to the search page.

2. **Given** I enter incorrect credentials, **When** I submit the login form, **Then** I see error message "Invalid email or password" and I am not logged in.

3. **Given** I am logged in, **When** I navigate to protected pages (favorites, history), **Then** I can access them without re-authenticating.

4. **Given** I am not logged in, **When** I try to access protected pages, **Then** I am redirected to the login page, and after login, I am redirected back to my intended destination.

5. **Given** I am logged in, **When** I close and reopen the browser, **Then** my session is maintained (FR34) and I don't need to log in again until token expires.

## Tasks / Subtasks

- [x] Task 1: Update NextAuth.js config with JWT 24h expiry and `authorized` callback (AC: #1, #3, #5)
  - [x] 1.1 Update `web/src/lib/auth.ts`: add `session: { strategy: "jwt", maxAge: 86400 }` (24 hours)
  - [x] 1.2 Add `authorized` callback to NextAuth config for middleware integration
  - [x] 1.3 Add `callbackUrl` handling in the `signIn` page configuration

- [x] Task 2: Create Next.js proxy for route protection (AC: #3, #4)
  - [x] 2.1 Create `web/src/proxy.ts` (Next.js 16 uses `proxy.ts`, not `middleware.ts`)
  - [x] 2.2 Export `auth as proxy` from `@/lib/auth`
  - [x] 2.3 Configure matcher to protect `/favorites`, `/history`, `/admin` routes
  - [x] 2.4 Ensure `/search`, `/browse`, `/lookups`, `/login`, `/register` remain public (no login wall for search per UX spec)

- [x] Task 3: Create Login page UI (AC: #1, #2)
  - [x] 3.1 Create `web/src/app/(auth)/login/page.tsx` (server component wrapper)
  - [x] 3.2 Create `web/src/app/(auth)/login/LoginForm.tsx` (client component)
  - [x] 3.3 Use React Hook Form + Zod for validation (validate on blur)
  - [x] 3.4 Call NextAuth `signIn("credentials")` with `redirect: false`
  - [x] 3.5 Handle `callbackUrl` from URL search params for redirect-after-login (AC: #4)
  - [x] 3.6 Display server error "Invalid email or password" on failed login
  - [x] 3.7 Add link to registration page ("Don't have an account? Sign up")
  - [x] 3.8 Create `web/src/app/(auth)/login/LoginForm.test.tsx` (co-located)

- [x] Task 4: Update Header with auth state (AC: #3)
  - [x] 4.1 Update `web/src/components/layout/Header.tsx` to show login/register links when not authenticated
  - [x] 4.2 Show user email and logout link when authenticated
  - [x] 4.3 Use `useSession()` from `next-auth/react` to get auth state
  - [x] 4.4 Add `SessionProvider` wrapper in layout (required for `useSession` in client components)

- [x] Task 5: Add SessionProvider to app layout (AC: #3, #5)
  - [x] 5.1 Create `web/src/app/providers.tsx` (client component wrapping SessionProvider)
  - [x] 5.2 Update `web/src/app/layout.tsx` to wrap children in Providers

- [x] Task 6: Write tests (AC: #1-#4)
  - [x] 6.1 Create `web/src/app/(auth)/login/LoginForm.test.tsx` — form renders, validation on blur, error display, successful login redirect
  - [x] 6.2 Verify existing backend tests cover login endpoint (they do — `auth_test.py` covers POST /api/auth/login)

## Dev Notes

### CRITICAL: Backend Already Exists — This is Primarily a Frontend Story

The backend login endpoint was already created in Story 4-1:
- `POST /api/auth/login` — `api/app/api/auth.py` line 33-52
- `AuthService.authenticate_user()` — `api/app/services/auth_service.py` line 50-75
- `UserLogin` schema — `api/app/schemas/user.py` line 34-48
- `get_current_user()` dependency — `api/app/core/auth.py`
- JWT validation via `fastapi-nextauth-jwt` — already installed

**DO NOT recreate any backend code.** All backend tests already pass.

### Next.js 16: proxy.ts (NOT middleware.ts)

Next.js 16 renamed `middleware.ts` to `proxy.ts`. The proxy runs on Node.js runtime (not Edge).

```typescript
// web/src/proxy.ts
export { auth as proxy } from "@/lib/auth";

export const config = {
  matcher: ["/favorites/:path*", "/history/:path*", "/admin/:path*"],
};
```

**DO NOT** create `middleware.ts` — it is deprecated in Next.js 16.

### NextAuth.js v5 Auth Config Updates Needed

The current `auth.ts` needs these additions for this story:

```typescript
// web/src/lib/auth.ts - additions
export const { auth, handlers, signIn, signOut } = NextAuth({
  // ... existing providers config ...
  session: {
    strategy: "jwt",
    maxAge: 24 * 60 * 60, // 24 hours (AC #1, NFR-SEC3)
  },
  callbacks: {
    // ADD authorized callback for proxy/middleware
    authorized({ auth }) {
      return !!auth;
    },
    // ... existing jwt and session callbacks ...
  },
});
```

### Login Form Pattern (Mirrors RegisterForm)

Follow the exact same pattern as `web/src/app/(auth)/register/RegisterForm.tsx`:
- React Hook Form + Zod, validate on blur
- `signIn("credentials", { redirect: false })` — check result for errors
- Handle `callbackUrl` from URL search params

```typescript
// web/src/app/(auth)/login/LoginForm.tsx
"use client";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address")
    .transform((val) => val.toLowerCase().trim()),
  password: z.string().min(1, "Password is required"),
});

// On submit:
const callbackUrl = searchParams.get("callbackUrl") || "/search";
const result = await signIn("credentials", {
  email: data.email,
  password: data.password,
  redirect: false,
});
if (result?.error) {
  setServerError("Invalid email or password");
  return;
}
router.push(callbackUrl);
```

### SessionProvider Required for useSession

NextAuth.js v5 requires `SessionProvider` for client components that use `useSession()`:

```typescript
// web/src/app/providers.tsx
"use client";
import { SessionProvider } from "next-auth/react";

export function Providers({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}
```

```typescript
// web/src/app/layout.tsx
import { Providers } from "./providers";

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <Header />
          {children}
        </Providers>
      </body>
    </html>
  );
}
```

### Header Auth State Pattern

Update Header to show auth-aware navigation:

```typescript
// web/src/components/layout/Header.tsx
import { useSession, signOut } from "next-auth/react";

export function Header() {
  const { data: session, status } = useSession();
  // ...
  // Right side: if authenticated → show email + logout
  // If not authenticated → show Login / Register links
}
```

### callbackUrl Redirect Flow (AC #4)

When proxy redirects unauthenticated user:
1. User visits `/favorites` → proxy redirects to `/login?callbackUrl=%2Ffavorites`
2. LoginForm reads `callbackUrl` from search params
3. After successful login → `router.push(callbackUrl)` → user lands on `/favorites`

NextAuth.js v5 automatically appends `callbackUrl` query parameter when redirecting from the `authorized` callback.

### Password Validation Difference from Registration

Login form should NOT enforce min 8 chars on password — only check it's not empty. The backend handles credential validation. Login form validation is intentionally minimal to avoid leaking security information.

### Public vs Protected Routes

Per UX spec ("No login wall for search"):
- **Public** (no auth required): `/`, `/search`, `/browse`, `/lookups`, `/login`, `/register`
- **Protected** (auth required): `/favorites`, `/history`, `/admin`

### File Structure (Exact Paths)

**New files:**
```
web/src/proxy.ts                                    # Route protection (Next.js 16 proxy)
web/src/app/(auth)/login/page.tsx                   # Login page (server component)
web/src/app/(auth)/login/LoginForm.tsx              # Login form (client component)
web/src/app/(auth)/login/LoginForm.test.tsx         # Login form tests
web/src/app/providers.tsx                           # SessionProvider wrapper
```

**Modified files:**
```
web/src/lib/auth.ts                                 # Add maxAge, authorized callback
web/src/app/layout.tsx                              # Wrap with Providers
web/src/components/layout/Header.tsx                # Add auth state (login/logout links)
```

### Testing Requirements

**Frontend tests** (Vitest, jsdom):
- `LoginForm.test.tsx`:
  - Form renders with email and password fields
  - Validation on blur: invalid email shows error
  - Validation on blur: empty password shows error
  - Error display on failed login ("Invalid email or password")
  - Successful login calls signIn and redirects
  - callbackUrl is used for redirect after login

**Backend tests** — Already exist and pass from Story 4-1:
- `auth_test.py`: POST /api/auth/login success and failure
- `auth_service_test.py`: authenticate_user with valid/invalid credentials

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| Registration form | `web/src/app/(auth)/register/RegisterForm.tsx` | Form structure, Zod schema, signIn call, error handling |
| Registration page | `web/src/app/(auth)/register/page.tsx` | Server component wrapper pattern |
| Register form test | `web/src/app/(auth)/register/RegisterForm.test.tsx` | Test structure and mocking pattern |
| NextAuth config | `web/src/lib/auth.ts` | Extend existing config |
| API client | `web/src/lib/api.ts` | `credentials: "include"` pattern |
| User types | `web/src/types/user.ts` | `User`, `Session` types |
| Auth slice | `web/src/lib/store.ts` | `isAuthenticated`, `setUser` |

### Anti-Patterns to AVOID

- **DO NOT** create backend login logic — it already exists in Story 4-1
- **DO NOT** create `middleware.ts` — Next.js 16 uses `proxy.ts`
- **DO NOT** enforce password min length in login form — only require non-empty
- **DO NOT** put login logic in the page server component — use client component
- **DO NOT** use `redirect: true` with signIn — use `redirect: false` and handle manually for error display
- **DO NOT** protect `/search`, `/browse`, or `/lookups` routes — they must remain public
- **DO NOT** use status enums for loading states — use boolean `isSubmitting`
- **DO NOT** use Next.js API routes for auth — call NextAuth signIn directly

### Project Structure Notes

- Auth route group `(auth)` doesn't affect URL — `/login` renders from `web/src/app/(auth)/login/page.tsx`
- The proxy.ts file must be at `web/src/proxy.ts` (root of src, not inside app/)
- SessionProvider must wrap the entire app for useSession to work in any client component
- Header is already a client component ("use client") so adding useSession is straightforward

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4, Story 4.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Auth Flow]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: _bmad-output/implementation-artifacts/4-1-user-registration.md#Dev Notes]
- [Source: _bmad-output/project-context.md#Auth Flow (CRITICAL)]
- [Source: CLAUDE.md#Auth Flow]
- [Source: https://authjs.dev/getting-started/session-management/protecting]
- [Source: https://nextjs.org/docs/app/api-reference/file-conventions/proxy]

## Change Log

- 2026-02-15: Implemented user login story (all 6 tasks) — frontend-only, backend already existed from story 4-1
- 2026-02-15: Code review completed — fixed 1 HIGH + 6 MEDIUM issues (proxy export, metadata, password visibility, test coverage, autocomplete, accessibility)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

**Initial Implementation:**
- All 7 LoginForm tests pass (vitest run)
- All 12 auth tests pass (login + register combined)
- All 30 lib tests pass (store, hooks — no regressions)
- ESLint: no errors on all changed/new files
- TypeScript: 2 pre-existing errors in unrelated files (browse, search components), no new errors
- Pre-existing test failures in browse/lookup components (18 tests) are unrelated to this story

**Code Review Fixes (DEV2):**
- All 8 LoginForm tests pass (added 1 new test for error handling)
- Fixed proxy.ts export pattern (HIGH: `export { auth as default }`)
- Added metadata to login page (MEDIUM)
- Added password visibility toggle with Eye/EyeOff icons (MEDIUM)
- Added autocomplete attributes for better browser integration (MEDIUM)
- Improved accessibility: aria-describedby, aria-live, aria-busy (MEDIUM)
- Updated all tests to use placeholder selectors to avoid conflicts (MEDIUM)

### Completion Notes List

- Task 1: Updated `auth.ts` with `maxAge: 86400` (24h JWT expiry) and `authorized` callback for proxy integration. `callbackUrl` handling is automatic via NextAuth's `pages.signIn: "/login"` config.
- Task 2: Created `proxy.ts` at `web/src/proxy.ts` with matcher for `/favorites`, `/history`, `/admin`. Public routes (`/search`, `/browse`, `/lookups`, `/login`, `/register`) are not matched, staying accessible. **[Code Review Fix]** Changed export from `export { auth as proxy }` to `export { auth as default }` to fix Next.js 16 proxy pattern.
- Task 3: Created login page and form following the exact RegisterForm pattern. Login uses `signIn("credentials", { redirect: false })`, reads `callbackUrl` from search params, displays "Invalid email or password" on error, and has a "Don't have an account? Sign up" link. Password validation is `min(1)` (not empty), not `min(8)` — intentionally minimal per security guidelines. **[Code Review Fixes]** Added metadata export to page.tsx, password visibility toggle button with Eye/EyeOff icons, autocomplete="email" and autocomplete="current-password" attributes, and improved accessibility with aria-describedby on form fields.
- Task 4: Updated Header to show auth-aware navigation: Login/Sign up links for unauthenticated users, email display + Log out button for authenticated users. Uses `useSession()` from next-auth/react. **[Code Review Fix]** Improved loading state accessibility with aria-live="polite" and aria-busy="true" instead of "...".
- Task 5: Created `providers.tsx` wrapping `SessionProvider`, updated `layout.tsx` to wrap children with `<Providers>`.
- Task 6: Created 7 comprehensive tests in `LoginForm.test.tsx` covering: form rendering, email validation on blur, password validation on blur, failed login error display, successful login with redirect to /search, callbackUrl redirect, and sign-up link presence. Verified backend tests already exist and pass. **[Code Review Fix]** Added 8th test for unexpected error handling (catch block coverage) and updated all password field selectors to use placeholder instead of label to avoid conflicts with show/hide password button.

### File List

**New files:**
- `web/src/proxy.ts` — Route protection proxy (Next.js 16)
- `web/src/app/(auth)/login/page.tsx` — Login page server component
- `web/src/app/(auth)/login/LoginForm.tsx` — Login form client component
- `web/src/app/(auth)/login/LoginForm.test.tsx` — Login form tests (7 tests)
- `web/src/app/providers.tsx` — SessionProvider wrapper

**Modified files:**
- `web/src/lib/auth.ts` — Added maxAge (24h), authorized callback
- `web/src/app/layout.tsx` — Wrapped children with Providers
- `web/src/components/layout/Header.tsx` — Added auth state display (login/logout)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Story status: ready-for-dev → in-progress → review
- `_bmad-output/implementation-artifacts/4-2-user-login.md` — Updated tasks, dev record, status
