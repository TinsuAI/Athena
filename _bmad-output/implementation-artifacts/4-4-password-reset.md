# Story 4.4: Password Reset

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user who forgot my password**,
I want **to reset my password via email**,
So that **I can regain access to my account**.

## Acceptance Criteria

1. **Given** I am on the forgot password page (`/forgot-password`), **When** I enter my registered email, **Then** I see "If this email exists, a reset link has been sent" **And** a password reset email is sent (if email exists).

2. **Given** I receive a password reset email, **When** I click the reset link, **Then** I am taken to a password reset form **And** the link is valid for 1 hour.

3. **Given** I am on the password reset form, **When** I enter a new password (min 8 characters) and confirm it, **Then** my password is updated **And** I am redirected to login with a success message.

4. **Given** I use an expired or invalid reset link, **When** I try to reset my password, **Then** I see "This reset link has expired or is invalid" **And** I am prompted to request a new reset link.

5. **Given** I enter mismatched passwords, **When** I submit the reset form, **Then** I see "Passwords do not match".

## Tasks / Subtasks

- [x] Task 1: Add password reset token model and migration (AC: #1, #2, #4)
  - [x] 1.1 Create `api/app/models/password_reset_token.py` with SQLAlchemy model: `id`, `user_id` (FK → users.id), `token_hash` (VARCHAR 255, indexed), `expires_at` (TIMESTAMP WITH TIME ZONE), `used_at` (TIMESTAMP WITH TIME ZONE, nullable), `created_at`
  - [x] 1.2 Create Alembic migration: `alembic revision --autogenerate -m "add_password_reset_tokens_table"`
  - [x] 1.3 Register model in `api/app/models/__init__.py` for Alembic autodiscovery

- [x] Task 2: Create email service (AC: #1)
  - [x] 2.1 Add email config to `api/app/core/config.py`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS` (with sensible defaults for dev: `localhost:1025` for MailHog/Mailpit)
  - [x] 2.2 Create `api/app/services/email_service.py` with `EmailService` class: async `send_password_reset_email(to_email: str, reset_url: str)` using `aiosmtplib`
  - [x] 2.3 Email template: plain text with reset link and 1-hour expiry notice
  - [x] 2.4 Add `aiosmtplib` to `requirements.txt`
  - [x] 2.5 Create `api/app/services/email_service_test.py` with co-located tests

- [x] Task 3: Create password reset repository methods (AC: #1, #2, #4)
  - [x] 3.1 Create `api/app/repositories/password_reset_repository.py` with `PasswordResetRepository` class:
    - `create(user_id: int, token_hash: str, expires_at: datetime) → PasswordResetToken`
    - `get_by_token_hash(token_hash: str) → PasswordResetToken | None`
    - `mark_used(token_id: int) → None`
    - `invalidate_all_for_user(user_id: int) → None` (invalidates any existing unused tokens)
  - [x] 3.2 Create `api/app/repositories/password_reset_repository_test.py` with co-located tests

- [x] Task 4: Add password reset methods to auth service (AC: #1, #2, #3, #4)
  - [x] 4.1 Add `update_password(user_id: int, password_hash: str) → None` to `UserRepository`
  - [x] 4.2 Add to `AuthService`:
    - `request_password_reset(email: str) → None` — generates secure token (secrets.token_urlsafe(32)), hashes it (SHA-256), stores in DB, sends email. Always returns None (no email enumeration).
    - `reset_password(token: str, new_password: str) → bool` — verifies token hash exists, not expired, not used; updates password; marks token used; invalidates other tokens for user. Returns True on success, False on invalid/expired token.
  - [x] 4.3 Add password reset request/response schemas to `api/app/schemas/user.py`:
    - `PasswordResetRequest(email: str)` with email validation
    - `PasswordResetConfirm(token: str, password: str, password_confirm: str)` with password match validation
  - [x] 4.4 Update `api/app/services/auth_service_test.py` with tests for new methods

- [x] Task 5: Create password reset API endpoints (AC: #1, #3, #4)
  - [x] 5.1 Add to `api/app/api/auth.py`:
    - `POST /api/auth/forgot-password` — accepts `PasswordResetRequest`, calls `service.request_password_reset()`, always returns success (prevents email enumeration)
    - `POST /api/auth/reset-password` — accepts `PasswordResetConfirm`, calls `service.reset_password()`, returns success or error
  - [x] 5.2 Add rate limiting to forgot-password endpoint (3 requests per email per hour) to prevent abuse
  - [x] 5.3 Update `api/app/api/auth_test.py` with tests for new endpoints

- [x] Task 6: Create Forgot Password frontend page (AC: #1)
  - [x] 6.1 Create `web/src/app/(auth)/forgot-password/page.tsx` (server component wrapper)
  - [x] 6.2 Create `web/src/app/(auth)/forgot-password/ForgotPasswordForm.tsx` (client component):
    - React Hook Form + Zod, validate on blur
    - Email input field
    - Submit button with loading state
    - Success state: "If this email exists, a reset link has been sent"
    - Link back to login page
  - [x] 6.3 Create `web/src/app/(auth)/forgot-password/ForgotPasswordForm.test.tsx` co-located tests

- [x] Task 7: Create Reset Password frontend page (AC: #2, #3, #4, #5)
  - [x] 7.1 Create `web/src/app/(auth)/reset-password/page.tsx` (server component wrapper, reads `token` from URL search params)
  - [x] 7.2 Create `web/src/app/(auth)/reset-password/ResetPasswordForm.tsx` (client component):
    - React Hook Form + Zod, validate on blur
    - New password input (min 8 chars) with visibility toggle
    - Confirm password input with visibility toggle
    - Password match validation (Zod `.refine()`)
    - Submit button with loading state
    - Success: redirect to `/login` with success message (via search param `?reset=success`)
    - Error: show "This reset link has expired or is invalid" with link to request new one
  - [x] 7.3 Create `web/src/app/(auth)/reset-password/ResetPasswordForm.test.tsx` co-located tests

- [x] Task 8: Add "Forgot password?" link to login page (AC: #1)
  - [x] 8.1 Update `web/src/app/(auth)/login/LoginForm.tsx`: add "Forgot your password?" link between password field and submit button, linking to `/forgot-password`
  - [x] 8.2 Update `web/src/app/(auth)/login/page.tsx`: show success message when `?reset=success` query param is present

- [x] Task 9: Add Mailpit to Docker Compose for development (AC: #1)
  - [x] 9.1 Add Mailpit service to `docker-compose.dev.yml` (port 1025 SMTP, port 8025 web UI)
  - [x] 9.2 Set SMTP env vars in docker-compose.dev.yml API service to point to Mailpit

## Dev Notes

### CRITICAL: This Story Requires an Email Service

This is the FIRST story that requires sending emails. There is NO existing email infrastructure in the project. The developer must:
1. Choose and configure an email sending library (recommend `aiosmtplib` for async FastAPI)
2. Add Mailpit to Docker Compose dev environment for local email testing
3. Design the token model carefully for security (hash tokens, not store plaintext)

### Security Requirements (NON-NEGOTIABLE)

1. **Token Storage**: Store SHA-256 hash of token in DB, NOT the plaintext token. The plaintext token is sent via email and used as a one-time secret.
2. **Token Generation**: Use `secrets.token_urlsafe(32)` for cryptographically secure tokens (43+ characters, URL-safe).
3. **Token Expiry**: 1 hour (per AC #2). Check `expires_at > datetime.utcnow()` on use.
4. **Single Use**: Set `used_at` timestamp when token is consumed. Reject already-used tokens.
5. **No Email Enumeration**: The forgot-password endpoint MUST always return the same response regardless of whether the email exists. "If this email exists, a reset link has been sent."
6. **Rate Limiting**: Limit forgot-password requests to prevent abuse (3 per email per hour).
7. **Invalidate Previous Tokens**: When a new reset token is requested, invalidate all existing unused tokens for that user.
8. **Password Hashing**: Use the EXISTING `hash_password()` function from `auth_service.py` (bcrypt with cost factor 12).

### Token Flow

```
1. User enters email on /forgot-password
2. POST /api/auth/forgot-password { email: "user@example.com" }
3. Backend:
   a. Look up user by email (if not found, still return success — no enumeration)
   b. Generate token: secrets.token_urlsafe(32)
   c. Hash token: hashlib.sha256(token.encode()).hexdigest()
   d. Store in password_reset_tokens: { user_id, token_hash, expires_at: now+1h }
   e. Send email with link: {FRONTEND_URL}/reset-password?token={plaintext_token}
4. User clicks link in email
5. GET /reset-password?token=abc123... (Next.js page reads token from URL)
6. User enters new password + confirmation
7. POST /api/auth/reset-password { token: "abc123...", password: "newpass", password_confirm: "newpass" }
8. Backend:
   a. Hash the submitted token: hashlib.sha256(token.encode()).hexdigest()
   b. Look up token_hash in DB
   c. Verify: exists, not expired, not used
   d. Update user's password_hash
   e. Mark token as used (set used_at)
   f. Invalidate any other tokens for this user
9. Frontend redirects to /login?reset=success
```

### Password Reset Token Model

```python
# api/app/models/password_reset_token.py
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

### Email Service Design

```python
# api/app/services/email_service.py
import aiosmtplib
from email.message import EmailMessage

class EmailService:
    def __init__(self, settings):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.use_tls = settings.smtp_use_tls

    async def send_password_reset_email(self, to_email: str, reset_url: str) -> None:
        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = "Athena - Password Reset Request"
        message.set_content(f"""You requested a password reset for your Athena account.

Click the link below to reset your password. This link is valid for 1 hour.

{reset_url}

If you did not request this, please ignore this email.
""")
        await aiosmtplib.send(
            message,
            hostname=self.host,
            port=self.port,
            username=self.user or None,
            password=self.password or None,
            start_tls=self.use_tls,
        )
```

### Config Additions

```python
# Add to api/app/core/config.py Settings class:
smtp_host: str = "localhost"
smtp_port: int = 1025  # Mailpit default
smtp_user: str = ""
smtp_password: str = ""
smtp_from_email: str = "noreply@athena.local"
smtp_use_tls: bool = False
frontend_url: str = "http://localhost:8979"  # For building reset links
```

### New API Endpoint Schemas

```python
# Add to api/app/schemas/user.py:
class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: str = Field(description="Email address for password reset")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Please enter a valid email address")
        return v.lower().strip()


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(description="Password reset token from email")
    password: str = Field(min_length=8, description="New password (min 8 characters)")
    password_confirm: str = Field(description="Password confirmation")

    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordResetConfirm":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
```

### Frontend Form Patterns (MUST FOLLOW)

Follow EXACTLY the patterns established in `LoginForm.tsx` and `RegisterForm.tsx`:
- React Hook Form + Zod
- `mode: "onBlur"` (validate on blur)
- `zodResolver(schema)`
- Error display with `role="alert"` and `aria-describedby`
- Server error state with `useState<string | null>(null)`
- Loading state with `useState(false)` and `disabled={isSubmitting}`
- API calls via `fetch` to `${NEXT_PUBLIC_API_URL}/api/auth/...` with `credentials: 'include'`
- Input styling: same Tailwind classes as LoginForm.tsx
- Password visibility toggle: same Eye/EyeOff pattern from LoginForm.tsx

### Zod Schema for Reset Password Form

```typescript
const resetPasswordSchema = z.object({
  password: z.string().min(8, "Password must be at least 8 characters"),
  passwordConfirm: z.string().min(1, "Please confirm your password"),
}).refine((data) => data.password === data.passwordConfirm, {
  message: "Passwords do not match",
  path: ["passwordConfirm"],
});
```

### Docker Compose Addition

```yaml
# Add to docker-compose.dev.yml:
  mailpit:
    image: axllent/mailpit:latest
    ports:
      - "8025:8025"   # Web UI
      - "1025:1025"   # SMTP
    restart: unless-stopped
```

Access Mailpit UI at `http://localhost:8025` to see sent emails during development.

### Project Structure Notes

- New files follow the established (auth) route group pattern
- All new frontend pages go under `web/src/app/(auth)/` matching login and register
- Backend changes are in existing auth.py router, auth_service.py, and user schemas
- New model and repository follow existing SQLAlchemy/repository patterns
- Tests are co-located with source files

### Existing Patterns to Reuse

| Pattern | Source File | What to Reuse |
|---------|-------------|---------------|
| Form + Zod validation | `web/src/app/(auth)/login/LoginForm.tsx` | React Hook Form setup, Zod resolver, onBlur mode |
| Auth page layout | `web/src/app/(auth)/login/page.tsx` | Centered card layout, metadata pattern |
| Password visibility | `web/src/app/(auth)/login/LoginForm.tsx` | Eye/EyeOff toggle with lucide-react |
| Auth API endpoints | `api/app/api/auth.py` | Router prefix, error_response/success_response |
| Auth service | `api/app/services/auth_service.py` | Service class pattern, password hashing |
| User repository | `api/app/repositories/user_repository.py` | Repository class pattern, async session |
| Pydantic validation | `api/app/schemas/user.py` | Email validator, Field() usage |
| Test mocking | `web/src/app/(auth)/login/LoginForm.test.tsx` | next-auth mock, next/navigation mock |
| Alembic migration | `api/alembic/versions/` | Existing migration patterns |

### Anti-Patterns to AVOID

- **DO NOT** store plaintext tokens in the database — hash with SHA-256
- **DO NOT** reveal whether an email exists — always return same response
- **DO NOT** use JWT for reset tokens — simple cryptographic random tokens are better for one-time use
- **DO NOT** allow expired or used tokens to work
- **DO NOT** skip rate limiting on forgot-password — prevents email bombing
- **DO NOT** use `passlib` — project uses `bcrypt` directly (established in Story 4-1)
- **DO NOT** put business logic in route handlers — all logic goes in `AuthService`
- **DO NOT** create a separate `/tests` directory — tests are co-located
- **DO NOT** use status enums for loading states — use boolean flags
- **DO NOT** fetch via Next.js API routes — fetch FastAPI directly
- **DO NOT** use `useEffect` for form submission — use React Hook Form `handleSubmit`
- **DO NOT** use `window.location` for redirects — use `useRouter().push()` from `next/navigation`

### Previous Story Intelligence (from 4-1, 4-2, 4-3)

**From Story 4-1 (User Registration):**
- Auth flow: RegisterForm -> POST /api/auth/register -> signIn("credentials") -> JWT session
- bcrypt for password hashing (NOT passlib), cost factor 12
- All auth endpoints exist in `api/app/api/auth.py`
- Integration tests pattern in `auth_integration_test.py`
- Email validation: regex pattern on both frontend (Zod) and backend (Pydantic)

**From Story 4-2 (User Login):**
- LoginForm pattern: React Hook Form + Zod, signIn("credentials", { redirect: false })
- `proxy.ts` for route protection (Next.js 16, NOT middleware.ts)
- SessionProvider wrapper in `providers.tsx`
- Header shows auth state (email + Log out / Login + Sign up)
- Test patterns: LoginForm.test.tsx mocks next-auth/react and next/navigation

**From Story 4-3 (User Logout):**
- Header.tsx logout calls `store.logout()` then `signOut({ callbackUrl: "/login" })`
- Zustand store has `logout()` action that clears user and isAuthenticated
- No backend changes needed for logout (stateless JWT, cookie-based)
- Code review fixes: error handling in logout flow, proper type casting in tests

### Git Intelligence

Recent auth commits:
- `4f753f4` — feat: implement user logout with state clearing and error handling (story 4-3)
- `effe2bd` — feat: implement user login with session persistence and route protection (story 4-2)
- `ddcf071` — feat: implement user registration with email/password auth (story 4-1)

Files created/modified in auth stories:
- `api/app/api/auth.py` — auth router with register + login endpoints
- `api/app/services/auth_service.py` — AuthService with register_user, authenticate_user
- `api/app/repositories/user_repository.py` — UserRepository with create, get_by_email, get_by_id
- `api/app/models/user.py` — User model with id, email, password_hash, role, created_at
- `api/app/schemas/user.py` — UserCreate, UserLogin, UserResponse schemas
- `web/src/lib/auth.ts` — NextAuth config with Credentials provider
- `web/src/app/(auth)/login/LoginForm.tsx` — Login form component
- `web/src/app/(auth)/register/RegisterForm.tsx` — Register form component
- `web/src/lib/store.ts` — Zustand store with auth slice (setUser, logout)
- `web/src/components/layout/Header.tsx` — Auth state display, logout button

### Testing Requirements

**Backend tests** (pytest, asyncio_mode=auto):

1. `api/app/services/email_service_test.py`:
   - Test email is sent with correct subject, body, from, to
   - Test email contains reset URL
   - Test handles SMTP connection errors gracefully

2. `api/app/repositories/password_reset_repository_test.py`:
   - Test create token record
   - Test get by token hash (found/not found)
   - Test mark used sets used_at
   - Test invalidate all for user

3. `api/app/services/auth_service_test.py` (additions):
   - Test request_password_reset with existing email (token created, email sent)
   - Test request_password_reset with non-existing email (no error, no email sent)
   - Test reset_password with valid token (password updated, token marked used)
   - Test reset_password with expired token (returns False)
   - Test reset_password with already-used token (returns False)
   - Test reset_password with invalid token (returns False)

4. `api/app/api/auth_test.py` (additions):
   - Test POST /api/auth/forgot-password with valid email returns success
   - Test POST /api/auth/forgot-password with unknown email still returns success
   - Test POST /api/auth/forgot-password with invalid email returns 400
   - Test POST /api/auth/reset-password with valid token returns success
   - Test POST /api/auth/reset-password with expired token returns error
   - Test POST /api/auth/reset-password with mismatched passwords returns 422

**Frontend tests** (Vitest, jsdom, co-located):

5. `web/src/app/(auth)/forgot-password/ForgotPasswordForm.test.tsx`:
   - Renders email input and submit button
   - Shows validation error for invalid email (onBlur)
   - Submits request and shows success message
   - Handles API error gracefully
   - Shows link to login page

6. `web/src/app/(auth)/reset-password/ResetPasswordForm.test.tsx`:
   - Renders password and confirm password inputs
   - Shows validation error for short password (onBlur)
   - Shows "Passwords do not match" for mismatched passwords
   - Submits with valid token and redirects to /login
   - Shows error for expired/invalid token
   - Shows link to request new reset

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4, Story 4.4]
- [Source: _bmad-output/planning-artifacts/prd.md#FR33 - Users can reset their password if forgotten]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Auth Flow]
- [Source: _bmad-output/planning-artifacts/architecture.md#API Response Patterns]
- [Source: _bmad-output/project-context.md#Auth Flow (CRITICAL)]
- [Source: _bmad-output/implementation-artifacts/4-1-user-registration.md]
- [Source: _bmad-output/implementation-artifacts/4-2-user-login.md]
- [Source: _bmad-output/implementation-artifacts/4-3-user-logout.md]
- [Source: CLAUDE.md#Auth Flow]
- [Source: CLAUDE.md#Backend Testing & Linting]
- [Source: CLAUDE.md#Frontend Testing & Linting]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Backend tests: 40/40 passed (email_service 4, password_reset_repository 5, auth_service 17, auth_api 14)
- Frontend tests: 23/23 passed (ForgotPasswordForm 7, ResetPasswordForm 8, LoginForm 8)
- Full backend regression: 360 passed, 0 new failures (pre-existing: 17 failed integration tests needing real DB)
- Full frontend regression: 120 passed, 0 new failures (pre-existing: 18 browse component failures)

### Completion Notes List

- Implemented complete password reset flow: forgot-password request → email with token → reset-password form → redirect to login
- Security: tokens stored as SHA-256 hashes (never plaintext), 1-hour expiry, single-use, previous tokens invalidated
- No email enumeration: forgot-password always returns success regardless of email existence
- Rate limiting: 3 requests per email per hour on forgot-password endpoint (in-memory)
- Email service uses aiosmtplib with Mailpit for local development (port 1025 SMTP, 8025 web UI)
- Frontend follows exact patterns from LoginForm.tsx: React Hook Form + Zod, onBlur validation, Eye/EyeOff toggles
- Login page shows success message when redirected from password reset (?reset=success)
- Added "Forgot your password?" link to login form

### File List

**New files:**
- `api/app/models/password_reset_token.py` — PasswordResetToken SQLAlchemy model
- `api/alembic/versions/20260215_add_password_reset_tokens_table.py` — Migration for password_reset_tokens table
- `api/app/services/email_service.py` — EmailService for sending password reset emails via aiosmtplib
- `api/app/services/email_service_test.py` — Tests for email service (4 tests)
- `api/app/repositories/password_reset_repository.py` — PasswordResetRepository for token CRUD
- `api/app/repositories/password_reset_repository_test.py` — Tests for password reset repository (5 tests)
- `web/src/app/(auth)/forgot-password/page.tsx` — Forgot password page (server component)
- `web/src/app/(auth)/forgot-password/ForgotPasswordForm.tsx` — Forgot password form (client component)
- `web/src/app/(auth)/forgot-password/ForgotPasswordForm.test.tsx` — Tests for forgot password form (7 tests)
- `web/src/app/(auth)/reset-password/page.tsx` — Reset password page (server component)
- `web/src/app/(auth)/reset-password/ResetPasswordForm.tsx` — Reset password form (client component)
- `web/src/app/(auth)/reset-password/ResetPasswordForm.test.tsx` — Tests for reset password form (8 tests)
- `web/src/app/(auth)/login/ResetSuccessMessage.tsx` — Success banner for login page after password reset

**Modified files:**
- `api/app/models/__init__.py` — Added PasswordResetToken import/export
- `api/app/core/config.py` — Added SMTP and frontend_url settings
- `api/app/repositories/user_repository.py` — Added update_password method
- `api/app/services/auth_service.py` — Added request_password_reset and reset_password methods
- `api/app/services/auth_service_test.py` — Added 7 new tests for password reset service methods
- `api/app/schemas/user.py` — Added PasswordResetRequest and PasswordResetConfirm schemas
- `api/app/api/auth.py` — Added forgot-password and reset-password endpoints with rate limiting
- `api/app/api/auth_test.py` — Added 7 new tests for password reset endpoints
- `api/requirements.txt` — Added aiosmtplib dependency
- `docker-compose.dev.yml` — Added Mailpit service and SMTP env vars for API
- `web/src/app/(auth)/login/LoginForm.tsx` — Added "Forgot your password?" link
- `web/src/app/(auth)/login/page.tsx` — Added ResetSuccessMessage component

### Code Review Fixes (DEV 2 - Claude Sonnet 4.5)

**Review Date:** 2026-02-15
**Issues Found:** 10 (3 High, 4 Medium, 3 Low)
**Issues Fixed:** 7 (all High and Medium severity)

**HIGH Severity Fixes:**
1. **Redis-based Rate Limiting** — Replaced in-memory dict with Redis for distributed rate limiting (auth.py:22-58)
   - Fixes: server restart resets, multi-worker issues, memory leak
   - Now works across multiple processes/workers
2. **Email Send Failure Tracking** — auth_service.request_password_reset() now returns bool (auth_service.py:90-135)
   - API endpoint checks return value and returns 503 error if email fails
   - Users now informed when email service is down
3. **SMTP Connection Timeout** — Added 30-second timeout to aiosmtplib.send() (email_service.py:51)
   - Prevents indefinite hanging on network issues

**MEDIUM Severity Fixes:**
4. **Index on expires_at** — Added index to migration for faster cleanup queries (migration:46-49)
5. **Cascading Delete** — Added ondelete="CASCADE" to FK constraint (migration:57)
   - Prevents orphaned reset tokens when user is deleted
6. **Efficient Rate Limiter** — Redis implementation is O(1) vs O(n) dict cleanup (same as fix #1)
7. **Error Type Checking** — ResetPasswordForm now checks error.type instead of string matching (ResetPasswordForm.tsx:86-93)

**Test Updates:**
- Updated auth_test.py to mock Redis instead of in-memory dict
- Added new test: test_forgot_password_email_send_failure()
- All tests updated to pass Redis mock as dependency

**LOW Severity (Deferred):**
- Missing .env.example update (documentation task, not code)
- No cleanup job for expired tokens (deployment/ops task)
- Test gap: E2E integration test (nice-to-have, unit tests comprehensive)

## Change Log

- 2026-02-15: Implemented Story 4-4 Password Reset — full backend (model, migration, email service, repository, auth service, API endpoints with rate limiting) and frontend (forgot-password page, reset-password page, login page updates) with 63 total tests passing
- 2026-02-15: Code Review Fixes (DEV 2) — Fixed 7 HIGH/MEDIUM issues: Redis rate limiting, email failure tracking, SMTP timeout, missing index, cascading delete, error type checking; updated tests
