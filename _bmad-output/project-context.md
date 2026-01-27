---
project_name: 'athena'
user_name: 'tinsu'
date: '2026-01-24'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 25
optimized_for_llm: true
---

# Project Context for AI Agents

_Critical rules and patterns for implementing Athena - HS Code Lookup Tool. Focus on unobvious details._

---

## Technology Stack & Versions

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Frontend | Next.js | 15+ | App Router, TypeScript |
| Backend | FastAPI | Latest | Python 3.12+, async |
| Database | PostgreSQL | 16 | With pgvector extension |
| Cache | Redis | 7 | Sessions, search cache |
| Auth | NextAuth.js | v5 (beta) | + fastapi-nextauth-jwt |
| ORM | SQLAlchemy | 2.0 | Async mode |
| State | Zustand | Latest | Single store with slices |
| Forms | React Hook Form | Latest | + Zod validation |
| Styling | Tailwind CSS | Latest | Utility-first |

---

## Critical Implementation Rules

### API Response Format (MANDATORY)

**ALL API responses MUST use envelope format:**
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

**ALL errors MUST use RFC 7807:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "type": "https://athena.example/errors/not-found",
    "title": "Not Found",
    "status": 404,
    "detail": "Specific error message",
    "instance": "/api/endpoint"
  }
}
```

### Naming Conventions (STRICT)

| Context | Convention | Example |
|---------|------------|---------|
| Database tables | snake_case, plural | `hs_codes`, `fta_rates` |
| Database columns | snake_case | `duty_rate`, `created_at` |
| API JSON fields | snake_case | `hs_code`, `duty_rate` |
| Python functions | snake_case | `get_hs_code()` |
| Python classes | PascalCase | `HSCodeService` |
| TypeScript functions | camelCase | `getHsCode()` |
| React components | PascalCase | `SearchBar.tsx` |
| TypeScript utilities | camelCase | `apiClient.ts` |

### Backend Architecture (LAYERED)

```
Request → api/*.py → services/*.py → repositories/*.py → Database
            ↓              ↓                ↓
         Thin!      Business Logic    Data Access Only
```

**Rules:**
- Route handlers (`api/`) do ONLY: validation, auth check, call service, format response
- Services contain ALL business logic
- Repositories contain ONLY database queries
- NEVER put business logic in route handlers

### Frontend Architecture (HYBRID)

- **Server Components**: Data fetching, static content
- **Client Components**: Search UI, forms, interactive elements
- **Zustand**: Single store with slices (search, favorites, auth)
- **Data fetching**: Direct to FastAPI with CORS (NOT Next.js API routes)

### Auth Flow (CRITICAL)

```
1. User → NextAuth.js login
2. NextAuth creates encrypted JWT in httpOnly cookie
3. Frontend fetch includes credentials: 'include'
4. nginx proxies /api/* to FastAPI
5. FastAPI middleware decrypts JWT using NEXTAUTH_SECRET
6. Route handler receives user context
```

**MUST share same `NEXTAUTH_SECRET` between Next.js and FastAPI!**

### Search Architecture

**Hybrid search combines THREE strategies:**
1. Vector similarity (pgvector) - semantic matching
2. pg_trgm fuzzy - typo tolerance
3. Exact match - HS code lookup

**Confidence = cosine similarity normalized to 0-100%**

### Testing Rules

- Tests are **CO-LOCATED** with source files
- `search_service.py` → `search_service_test.py` (same directory)
- `SearchBar.tsx` → `SearchBar.test.tsx` (same directory)
- Use pytest for Python, Vitest for TypeScript

### Code Quality

- Python: Use type hints everywhere
- TypeScript: Strict mode enabled
- Forms: Validate on blur (not on change)
- Error boundaries: Per-route (not global only)

---

## Anti-Patterns (NEVER DO)

- **NEVER** put business logic in route handlers
- **NEVER** use camelCase in API JSON responses
- **NEVER** create tests in separate `/tests` directory
- **NEVER** use status enums for loading states (use boolean flags)
- **NEVER** fetch via Next.js API routes (fetch FastAPI directly)
- **NEVER** store passwords without bcrypt
- **NEVER** skip the envelope response format

---

## File Locations Quick Reference

| Feature | Backend | Frontend |
|---------|---------|----------|
| Search | `api/app/api/search.py` | `web/src/app/search/` |
| HS Codes | `api/app/api/hs_codes.py` | `web/src/app/hs-codes/` |
| Favorites | `api/app/api/favorites.py` | `web/src/app/favorites/` |
| Admin | `api/app/api/admin/data.py` | `web/src/app/admin/` |
| Auth | `api/app/core/auth.py` | `web/src/lib/auth.ts` |
| Store | N/A | `web/src/lib/store.ts` |
| API Client | N/A | `web/src/lib/api.ts` |

---

## Environment Variables

**Backend (.env):**
```
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/athena
REDIS_URL=redis://redis:6379
NEXTAUTH_SECRET=<shared-with-frontend>
OPENROUTER_API_KEY=<for-embeddings>
```

**Frontend (.env.local):**
```
NEXTAUTH_URL=https://athena.example.com
NEXTAUTH_SECRET=<shared-with-backend>
NEXT_PUBLIC_API_URL=http://tinxudev.airplane-manta.ts.net:8000
```

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Refer to `_bmad-output/planning-artifacts/architecture.md` for detailed decisions

**For Humans:**
- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

---

_Last Updated: 2026-01-24_
