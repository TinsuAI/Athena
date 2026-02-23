# Sprint Change Proposal — 2026-02-22

**Project:** Athena
**Author:** tinsu (via Correct Course workflow)
**Date:** 2026-02-22
**Status:** Approved — 2026-02-22

---

## Section 1: Issue Summary

**Problem Statement:**
Three new requirements extend the existing authentication and search experience:

1. **Social OAuth Login** — Users should be able to log in via Google and Facebook accounts, in addition to the existing email/password flow.

2. **Search Auth Gate** — Only logged-in users should be able to perform HS code searches. This reverses the previous design decision ("no login wall for search per UX spec") from Story 4-2.

3. **Search UX Guidance** — The search page should display hint text encouraging users to provide detailed product descriptions for better results.

**When/How Discovered:**
Raised by product owner (tinsu) on 2026-02-22 during active sprint. All three changes are consolidated into a single new story.

**Key Conflict:**
Story 4-2 (`user-login.md`) documented `/search` as explicitly public per UX spec. Change #2 reverses that. Story 4-2's dev notes will be updated (doc only, no re-implementation).

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Current Status | Impact |
|------|---------------|--------|
| Epic 1 — Core HS Code Search | in-progress | Story 1-4 (in review) — **no changes needed**; new story handles proxy.ts and hint text as separate concerns |
| Epic 4 — User Authentication | done | Reopen: add Story 4-6. Status → in-progress |
| All others | various | Not affected |

### Story Impact

| Story | Status | Change Required |
|-------|--------|----------------|
| **1-4** Search Page UI | review | No AC changes — new story owns the search page additions |
| **4-2** User Login | done | Dev notes doc update only (route table: `/search` now protected) |
| **4-6** *(NEW)* Enhanced Auth & Search UX | — | Single new story covering all three changes |

### Artifact Conflicts

| Artifact | Conflict | Action |
|----------|----------|--------|
| PRD (FR30-FR35) | No OAuth FRs; no search auth-gate FR | Add FR71, FR72, FR73 |
| `web/src/proxy.ts` | Matcher explicitly excludes `/search` | Add `/search/:path*` to matcher |
| `web/src/lib/auth.ts` | Only CredentialsProvider configured | Add GoogleProvider, FacebookProvider |
| `docker-compose.dev.yml` | No OAuth env vars | Add GOOGLE_CLIENT_ID/SECRET, FACEBOOK_CLIENT_ID/SECRET |
| Story 4-2 dev notes | Documents `/search` as explicitly public | Update route table (doc only) |

### Technical Impact

- `web/src/proxy.ts` — add `/search/:path*` to matcher
- `web/src/lib/auth.ts` — add GoogleProvider + FacebookProvider
- `web/src/app/(auth)/login/LoginForm.tsx` — add social login buttons
- `web/src/app/(auth)/register/RegisterForm.tsx` — add social login buttons
- `web/src/app/search/page.tsx` or `SearchBar.tsx` — add UX hint text
- DB migration — `password_hash` nullable; add `oauth_provider`, `oauth_id` columns
- New Alembic migration file

---

## Section 3: Recommended Approach

**Selected Path: Direct Adjustment — Single New Story**

All three changes consolidated into Story 4-6. This is the simplest delivery unit: one story, one code review, one deploy. Story 1-4 remains untouched in its current review state.

**Rationale:**
- OAuth, auth gate, and UX hint are all auth-layer or auth-adjacent changes — cohesive in one story
- Story 1-4 is in `review` — cleaner not to modify its ACs mid-review
- The new story modifies `proxy.ts` and `search/page.tsx` independently; no dependency conflict with Story 1-4
- Backend DB migration (nullable password_hash) is contained and non-breaking

**Effort:** Medium | **Risk:** Low | **Timeline Impact:** Minimal

---

## Section 4: Detailed Change Proposals

### A. PRD — Add Functional Requirements

**Section:** User Authentication (FR30-FR35) — append:

```
NEW:
- FR71: Users can log in using their Google account (OAuth 2.0)
- FR72: Users can log in using their Facebook account (OAuth 2.0)
- FR73: Only authenticated users can perform HS code searches;
        unauthenticated users are redirected to /login with callbackUrl=/search
```

**Section:** HS Code Search (FR1-FR9) — add note after FR9:

```
Note: Search (FR1-FR9) requires authentication (FR73). Unauthenticated users
accessing /search are redirected to /login?callbackUrl=%2Fsearch.
```

---

### B. Story 4-2 (User Login) — Dev Notes Update Only

**Section:** "Public vs Protected Routes"

```
OLD:
- **Public** (no auth required): `/`, `/search`, `/browse`, `/lookups`, `/login`, `/register`
- **Protected** (auth required): `/favorites`, `/history`, `/admin`

NEW:
UPDATED 2026-02-22 (Sprint Change — Story 4-6):
- **Public** (no auth required): `/`, `/browse`, `/lookups`, `/login`, `/register`
- **Protected** (auth required): `/search`, `/favorites`, `/history`, `/admin`
proxy.ts updated in Story 4-6.
```

---

### C. New Story 4-6: Enhanced Auth & Search UX

**Epic:** Epic 4 — User Authentication & Sessions
**Story ID:** 4-6
**Status:** New → backlog

```
Story 4.6: Enhanced Auth — OAuth Login, Search Gate & Search UX Hint

As a user,
I want to log in with Google or Facebook, have my searches protected by login,
and see helpful guidance when searching,
So that onboarding is easier and I get better search results.

Acceptance Criteria:

AC1: Google OAuth Login
  Given I am on /login or /register
  When I click "Đăng nhập với Google"
  Then I am redirected to Google's OAuth consent screen
  And after authorizing, I am logged in and redirected to /search
  And a user account is auto-created if none exists for my Google email

AC2: Facebook OAuth Login
  Given I am on /login or /register
  When I click "Đăng nhập với Facebook"
  Then I am redirected to Facebook's OAuth consent screen
  And after authorizing, I am logged in and redirected to /search
  And a user account is auto-created if none exists for my Facebook email

AC3: Account Conflict Handling
  Given I previously registered with email/password for email@example.com
  When I try to log in via Google OAuth with the same email@example.com
  Then I see: "Tài khoản này đã đăng ký bằng email/mật khẩu.
    Vui lòng đăng nhập bằng email và mật khẩu."

AC4: Social Buttons on Login and Register Pages
  Given I am on /login or /register
  When the page loads
  Then I see "Đăng nhập với Google" button with Google branding
  And I see "Đăng nhập với Facebook" button with Facebook branding
  And the buttons appear with a divider "— hoặc —" separating them from email/password

AC5: OAuth Users Get Default Role
  Given a new user logs in via OAuth for the first time
  When their account is created
  Then they are assigned the default "user" role
  And they appear in the admin user management page

AC6: Search Requires Authentication
  Given I am not logged in
  When I navigate to /search
  Then I am redirected to /login?callbackUrl=%2Fsearch
  And after logging in, I am returned to /search

AC7: Search Description Hint
  Given I am on /search and logged in
  When the page loads (before I have typed anything)
  Then I see hint text below the search bar:
    "Mô tả chi tiết sản phẩm để có kết quả chính xác hơn
     (ví dụ: vật liệu, công dụng, thông số kỹ thuật)"
  And the hint is subtle/fades once the user begins typing

Tasks:
- [ ] Task 1: Backend — DB migration for OAuth users
  - [ ] 1.1 Alembic migration: make password_hash nullable in users table
  - [ ] 1.2 Alembic migration: add oauth_provider (str, nullable), oauth_id (str, nullable) to users table
  - [ ] 1.3 Update User SQLAlchemy model to reflect nullable password_hash
  - [ ] 1.4 Update UserCreate Pydantic schema (optional password)
  - [ ] 1.5 Add findOrCreateOAuthUser() to AuthService:
            lookup by email+provider; create if not found; raise conflict if
            email exists with different auth method
  - [ ] 1.6 Tests: findOrCreateOAuthUser (found, created, conflict cases)

- [ ] Task 2: Frontend — Configure NextAuth.js OAuth providers
  - [ ] 2.1 Add GoogleProvider to web/src/lib/auth.ts
            import { Google } from "@auth/core/providers/google"
  - [ ] 2.2 Add FacebookProvider to web/src/lib/auth.ts
            import { Facebook } from "@auth/core/providers/facebook"
  - [ ] 2.3 Update NextAuth signIn callback to call backend findOrCreate endpoint
            for OAuth users (same JWT/session flow as email users)
  - [ ] 2.4 Add conflict detection in signIn callback → return false with error
  - [ ] 2.5 Add GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, FACEBOOK_CLIENT_ID,
            FACEBOOK_CLIENT_SECRET to docker-compose.dev.yml and .env.example

- [ ] Task 3: Social login buttons on Login + Register pages (AC1, AC2, AC4)
  - [ ] 3.1 Add Google button to LoginForm.tsx (signIn("google"))
  - [ ] 3.2 Add Facebook button to LoginForm.tsx (signIn("facebook"))
  - [ ] 3.3 Add "— hoặc —" divider between social and email/password sections
  - [ ] 3.4 Mirror same buttons in RegisterForm.tsx
  - [ ] 3.5 Display conflict error message (AC3) when signIn callback returns error

- [ ] Task 4: Protect /search route (AC6)
  - [ ] 4.1 Update web/src/proxy.ts matcher: add "/search/:path*"
  - [ ] 4.2 Verify existing callbackUrl flow handles /search redirect correctly
            (no changes to LoginForm needed — callbackUrl is automatic)

- [ ] Task 5: Search description hint (AC7)
  - [ ] 5.1 Add hint text component below SearchBar in web/src/app/search/page.tsx
  - [ ] 5.2 Hide/fade hint when searchQuery is non-empty (read from Zustand store)
  - [ ] 5.3 Vietnamese text: "Mô tả chi tiết sản phẩm để có kết quả chính xác hơn
            (ví dụ: vật liệu, công dụng, thông số kỹ thuật)"

- [ ] Task 6: Tests
  - [ ] 6.1 Backend: OAuth user creation, findOrCreateOAuthUser, conflict case
  - [ ] 6.2 Frontend: LoginForm — Google/Facebook buttons render and call signIn
  - [ ] 6.3 Frontend: search page — hint text shows when query empty, hides when typing
  - [ ] 6.4 Regression: existing email/password login tests still pass

Dev Notes:
- NextAuth.js v5 providers: import { Google } from "@auth/core/providers/google"
  and import { Facebook } from "@auth/core/providers/facebook"
- OAuth callback URLs for dev:
    http://localhost:8979/api/auth/callback/google
    http://localhost:8979/api/auth/callback/facebook
- Google console: console.cloud.google.com → Credentials → OAuth 2.0 Client ID
- Facebook: developers.facebook.com → My Apps → Facebook Login product
- The shared JWT flow (NEXTAUTH_SECRET) is unchanged; OAuth tokens wrap in the
  same NextAuth JWT that FastAPI decrypts via fastapi-nextauth-jwt
- password_hash nullable migration is non-breaking for existing email users
  (they still have password_hash set)
- proxy.ts: Next.js 16 uses proxy.ts (not middleware.ts) — export { auth as default }
- DO NOT protect /browse, /lookups — those remain public
```

---

### D. Architecture Update

**File:** `_bmad-output/planning-artifacts/architecture.md`
**Section:** Authentication & Security — append:

```
OAuth Providers (Sprint Change 2026-02-22, Story 4-6):
- GoogleProvider + FacebookProvider via NextAuth.js v5 @auth/core
- OAuth users: password_hash=NULL, oauth_provider + oauth_id columns on users table
- Account conflict policy: email registered via credentials cannot use OAuth with
  same email (and vice versa); user shown explicit Vietnamese error message
- Same JWT flow: NextAuth wraps OAuth session in signed JWT → FastAPI decrypts
- New env vars: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
                FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET
- /search added to protected routes in proxy.ts (Story 4-6)
```

---

## Section 5: Implementation Handoff

### Change Scope: Moderate

| Recipient | Action |
|-----------|--------|
| **SM / Story Creator** | 1) Create Story 4-6 file from proposal above; 2) Update Story 4-2 dev notes (route table, doc only); 3) Update PRD (FR71-73); 4) Update architecture doc; 5) Reopen Epic 4 in sprint-status.yaml |
| **Development Team** | Implement Story 4-6 after current in-review stories clear |
| **Product Owner** | Provision Google Cloud Console + Facebook Developer app credentials |

### Execution Order

1. Update Story 4-2 dev notes (doc only — immediately)
2. Update PRD (add FR71, FR72, FR73)
3. Update architecture doc
4. Create Story 4-6 file
5. Reopen Epic 4 in sprint-status.yaml (done → in-progress)
6. Dev implements Story 4-6

### Success Criteria

- [ ] `/search` returns redirect to `/login?callbackUrl=%2Fsearch` for unauthenticated requests
- [ ] Google OAuth end-to-end: user created, JWT issued, lands on /search
- [ ] Facebook OAuth end-to-end: user created, JWT issued, lands on /search
- [ ] Conflict case: same email via different method shows Vietnamese error message
- [ ] Social buttons visible on both /login and /register
- [ ] OAuth users appear in admin user management (FR69)
- [ ] Search page shows Vietnamese hint text before first keystroke; fades on typing
- [ ] All existing email/password auth tests pass (no regression)
