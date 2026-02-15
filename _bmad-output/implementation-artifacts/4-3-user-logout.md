# Story 4.3: User Logout

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **logged-in user**,
I want **to log out of the system**,
So that **I can secure my account on shared devices**.

## Acceptance Criteria

1. **Given** I am logged in, **When** I click the logout button in the user menu, **Then** I am logged out immediately, my JWT cookie is cleared, and I am redirected to the login page.

2. **Given** I have logged out, **When** I try to access protected pages (`/favorites`, `/history`, `/admin`), **Then** I am redirected to the login page.

3. **Given** I am logged out, **When** I use the back button to navigate to a protected page, **Then** I am still redirected to login (no cached access).

## Tasks / Subtasks

- [x] Task 1: Fix logout redirect destination and add state clearing (AC: #1)
  - [x] 1.1 Update `web/src/components/layout/Header.tsx`: change `signOut({ callbackUrl: "/search" })` to `signOut({ callbackUrl: "/login" })` to match AC requirement
  - [x] 1.2 Add Zustand store `logout()` action to `web/src/lib/store.ts` that clears auth state (`setUser(null)`) — ensures client-side state is clean after signOut
  - [x] 1.3 Update Header.tsx logout button handler: call store `logout()` before `signOut()` to clear Zustand state immediately (prevents brief flash of authenticated UI during redirect)

- [x] Task 2: Ensure back-button protection on protected pages (AC: #3)
  - [x] 2.1 Verify `proxy.ts` already intercepts back-button navigation to protected routes (it does — proxy runs on every request)
  - [x] 2.2 Add `Cache-Control: no-store` response header to protected page responses via a shared protected layout — create `web/src/app/(protected)/layout.tsx` that sets `export const dynamic = 'force-dynamic'` and uses `headers()` to add no-cache headers
  - [x] 2.3 Move the favorites/history/admin route matchers to use the `(protected)` route group if not already — OR simply add cache-control metadata to existing page.tsx files for `/favorites`, `/history`, `/admin` routes

  **NOTE:** Protected pages (`/favorites`, `/history`, `/admin`) don't exist yet as full implementations. The proxy.ts already handles server-side redirect. For back-button protection, the developer should verify that Next.js dynamic rendering + proxy.ts is sufficient. If browser caching is an issue, add `Cache-Control` headers in a test scenario. This task may be marked as "verified working" if proxy.ts handles it correctly without additional changes.

- [x] Task 3: Write frontend tests for logout flow (AC: #1-#3)
  - [x] 3.1 Create `web/src/components/layout/Header.test.tsx` (co-located) testing:
    - Renders logout button when session exists
    - Clicking logout calls `signOut({ callbackUrl: "/login" })`
    - Logout clears Zustand auth state
  - [x] 3.2 Test that unauthenticated state shows login/register links (not logout)
  - [x] 3.3 Verify the store `logout()` action resets `isAuthenticated` and `user` to defaults

## Dev Notes

### CRITICAL: This is a Tiny Frontend-Only Story

Almost everything needed for logout was already built in Story 4-2:
- **Header.tsx** (line 77): Already has `signOut({ callbackUrl: "/search" })` — just need to change to `/login`
- **proxy.ts**: Already protects `/favorites`, `/history`, `/admin` routes
- **NextAuth signOut()**: Already clears the JWT httpOnly cookie
- **SessionProvider**: Already wraps the app (from Story 4-2)
- **No backend changes needed**: NextAuth handles logout entirely via its built-in route handler

### What Actually Needs to Change

1. **Header.tsx**: Change `callbackUrl: "/search"` to `callbackUrl: "/login"` (1-line change)
2. **store.ts**: Add a `logout()` action that calls `setUser(null)` (clears Zustand state)
3. **Header.tsx**: Update logout handler to call `logout()` before `signOut()`
4. **Tests**: Write tests for the logout flow

### NextAuth.js v5 signOut Behavior

`signOut()` from `next-auth/react` does the following:
1. Makes a POST request to NextAuth's built-in signout endpoint (`/api/auth/signout`)
2. NextAuth clears the `authjs.session-token` httpOnly cookie
3. Redirects to `callbackUrl` (we set this to `/login`)

The JWT is a **stateless token in a cookie** — there's no server-side session store to invalidate. Clearing the cookie IS the invalidation. Once the cookie is gone:
- `proxy.ts` will redirect any protected route access to `/login`
- `useSession()` will return `status: "unauthenticated"`
- Header will show login/register links instead of user email

### Back-Button Protection (AC #3)

The `proxy.ts` (Next.js 16 proxy) runs server-side on **every request**, including browser back-button navigation for server-rendered pages. Since the proxy checks auth on each request, navigating "back" to a protected page will trigger a redirect to `/login`.

For **client-side cached pages**, the `SessionProvider` re-checks the session status. If the cookie is gone, `useSession()` returns unauthenticated, and any client-side auth checks will fail.

**No additional cache-control headers should be needed** because:
- Next.js dynamic routes already set appropriate cache headers
- The proxy intercepts every server request
- Client components re-evaluate session on mount

However, if testing reveals the browser serves a stale cached page, add `Cache-Control: no-store` to protected layouts.

### Zustand State Clearing

The current Header.tsx calls `signOut()` directly. This triggers a page redirect, so the Zustand store naturally resets (page reload clears in-memory state). However, it's good practice to explicitly clear the auth state BEFORE signOut for:
- Preventing a brief flash of authenticated UI during redirect
- Supporting future SPA-style navigation where page doesn't fully reload
- Making the logout action explicit and testable

```typescript
// store.ts addition
logout: () => set({ user: null, isAuthenticated: false }),
```

```typescript
// Header.tsx update
const logout = useStore((s) => s.logout);
const handleLogout = () => {
  logout();
  signOut({ callbackUrl: "/login" });
};
```

### File Structure (Exact Paths)

**Modified files:**
```
web/src/components/layout/Header.tsx       # Change callbackUrl, add store logout call
web/src/lib/store.ts                       # Add logout() action to auth slice
```

**New files:**
```
web/src/components/layout/Header.test.tsx  # Logout flow tests (co-located)
```

### Testing Requirements

**Frontend tests** (Vitest, jsdom):
- `Header.test.tsx`:
  - Renders logout button when session active
  - Clicking logout calls signOut with `callbackUrl: "/login"`
  - Clicking logout clears Zustand auth state
  - Renders login/register links when no session
  - Shows email when session has user

**Backend tests**: None needed — no backend changes.

**Mock setup for Header tests:**
```typescript
// Mock next-auth/react
vi.mock("next-auth/react", () => ({
  useSession: vi.fn(),
  signOut: vi.fn(),
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/search"),
}));
```

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| signOut usage | `web/src/components/layout/Header.tsx` | Already using signOut from next-auth/react |
| Zustand actions | `web/src/lib/store.ts` | Follow existing `setUser()` pattern |
| Test mocking | `web/src/app/(auth)/login/LoginForm.test.tsx` | Mock patterns for next-auth |
| Component test | `web/src/app/(auth)/register/RegisterForm.test.tsx` | Vitest + React Testing Library patterns |

### Anti-Patterns to AVOID

- **DO NOT** create a backend logout endpoint — NextAuth handles this entirely
- **DO NOT** try to "invalidate" the JWT server-side — it's a stateless cookie, clearing it IS invalidation
- **DO NOT** add complex token blacklisting — overkill for this architecture (NextAuth cookie-based JWT)
- **DO NOT** redirect to `/search` after logout — AC explicitly says `/login`
- **DO NOT** use `window.location` for redirect — use NextAuth's `callbackUrl` which handles it properly
- **DO NOT** put tests in a separate `/tests` directory — co-locate with source
- **DO NOT** add extra confirmation modal before logout — AC says "logged out immediately"
- **DO NOT** over-engineer this — it's essentially a 3-line code change + tests

### Previous Story Intelligence (from 4-1 and 4-2)

**From Story 4-1 (User Registration):**
- Auth flow: RegisterForm → POST /api/auth/register → signIn("credentials") → JWT session
- bcrypt for password hashing (NOT passlib)
- All auth endpoints already exist and tested
- Integration tests pattern established in `auth_integration_test.py`

**From Story 4-2 (User Login):**
- LoginForm pattern: React Hook Form + Zod, signIn("credentials", { redirect: false })
- `proxy.ts` created for route protection (Next.js 16 pattern, NOT middleware.ts)
- SessionProvider wrapper in `providers.tsx`
- Header already shows auth state (email + Log out / Login + Sign up)
- **signOut is already imported and used** — just needs redirect URL fix
- Test patterns: LoginForm.test.tsx mocks next-auth/react and next/navigation

**Code Review Findings Applied in 4-2:**
- Proxy export must be `export { auth as default }` (not `export { auth as proxy }`)
- Password visibility toggle added
- Autocomplete attributes for better browser integration
- Accessibility improvements (aria-describedby, aria-live, aria-busy)

### Git Intelligence

Recent commits show the auth stories were just implemented:
- `effe2bd` — feat: implement user login with session persistence and route protection (story 4-2)
- `ddcf071` — feat: implement user registration with email/password auth (story 4-1)

The Header.tsx was last modified in story 4-2. The signOut function is already wired up. This story is primarily a correction (redirect URL) and formalization (tests, state clearing).

### Project Structure Notes

- Header is at `web/src/components/layout/Header.tsx` (shared layout component)
- Store is at `web/src/lib/store.ts` (single Zustand store with slices)
- Tests co-located: Header.test.tsx goes next to Header.tsx
- No new routes or pages needed for this story
- proxy.ts already handles the protected route → login redirect flow

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4, Story 4.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Auth Flow]
- [Source: _bmad-output/planning-artifacts/prd.md#FR32 - Users can log out of the system]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Experience Mechanics]
- [Source: _bmad-output/project-context.md#Auth Flow (CRITICAL)]
- [Source: _bmad-output/implementation-artifacts/4-1-user-registration.md#Dev Notes]
- [Source: _bmad-output/implementation-artifacts/4-2-user-login.md#Dev Notes]
- [Source: CLAUDE.md#Auth Flow]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation with no debugging needed.

### Completion Notes List

**Initial Implementation (DEV1):**
- Changed `signOut({ callbackUrl: "/search" })` to `signOut({ callbackUrl: "/login" })` in Header.tsx (AC #1)
- Added `logout()` action to Zustand auth slice that resets `user` to null and `isAuthenticated` to false
- Updated Header.tsx logout handler to call `logout()` before `signOut()` to clear client state immediately
- Verified `proxy.ts` already handles back-button protection via server-side auth check on every request (AC #2, #3)
- Task 2.2/2.3 verified as not needed — proxy.ts + SessionProvider cover back-button protection without additional cache headers
- Created Header.test.tsx with 5 tests: logout button rendering, callbackUrl verification, Zustand state clearing, unauthenticated state, email display
- Added 2 auth slice tests to store.test.ts: logout resets state, logout is no-op when already logged out
- All 22 new/modified tests pass; no regressions in auth-related tests (30/30 pass)
- Pre-existing test failures in browse components (SectionList, ChapterView, BrowseSearch) and RegisterForm are unrelated to this story

**Code Review Fixes (DEV2):**
- Fixed 3 HIGH + 4 MEDIUM issues found in adversarial code review
- Added sprint-status.yaml to File List (was missing from documentation)
- Improved Header.test.tsx mock implementation to be more maintainable (full store state mock)
- Fixed type casting in store.test.ts (proper User type import instead of `as const`)
- Added error handling (try/catch) to logout flow in Header.tsx
- Added 2 new test cases: error handling test, rapid click test
- Documented test coverage strategy and integration test limitation in Header.test.tsx
- All 24 tests passing after review fixes

### Change Log

- 2026-02-15: Implemented user logout (story 4-3) — redirect fix, Zustand state clearing, co-located tests

### File List

**Modified:**
- `web/src/components/layout/Header.tsx` — Changed callbackUrl from "/search" to "/login", added store import and logout() call
- `web/src/lib/store.ts` — Added `logout()` action to AuthState interface and implementation
- `web/src/lib/store.test.ts` — Added auth slice tests for logout action
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Updated story status from in-progress to review

**New:**
- `web/src/components/layout/Header.test.tsx` — 5 tests for logout flow and auth state display
