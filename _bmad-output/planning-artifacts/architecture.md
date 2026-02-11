---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
status: 'complete'
completedAt: '2026-01-24'
inputDocuments:
  - path: _bmad-output/planning-artifacts/product-brief-athena-2026-01-23.md
    type: product-brief
    description: HS Code Lookup Tool for Vietnam Customs
  - path: _bmad-output/planning-artifacts/prd.md
    type: prd
    description: Complete PRD with functional/non-functional requirements
  - path: docs/other-tool-sample.md
    type: reference
    description: Sample output showing expected HS code classification format with justification
workflowType: 'architecture'
project_name: 'athena'
user_name: 'tinsu'
date: '2026-01-23'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
50 requirements across 9 capability domains:
- **Search (FR1-9):** Multi-language input, confidence ranking, hierarchical browsing, chapter filtering
- **Display (FR10-18):** Complete tariff data including 20+ FTA rates, policy notes, version tracking
- **Personalization (FR19-29):** Favorites with notes, search history with re-execution
- **Auth (FR30-35):** User accounts, sessions, role-based access
- **Admin (FR36-42):** Excel upload, change preview, activation, rollback
- **Quality (FR43-50):** Error handling, data integrity preservation

**Non-Functional Requirements:**
| Category | Key Targets |
|----------|-------------|
| Performance | <3s search, <4s page load, 500+ searches/min |
| Reliability | 99.5% uptime (business hours), <2hr RTO |
| Security | JWT auth, HTTPS, bcrypt, rate limiting (100 req/min) |
| Scalability | 50-100 concurrent users, 50K HS codes capacity |
| Accessibility | WCAG 2.1 AA compliance |
| I18n | UTF-8, VN/EN/ZH character handling |

**Scale & Complexity:**
- Primary domain: Full-stack web application (search-intensive)
- Complexity level: Medium-High
- Estimated architectural components: 6-8 major subsystems

### Technical Constraints & Dependencies

1. **Data Source Lock-in:** Must parse Vietnam Customs Excel format with merged cells, multi-line descriptions, and 20+ FTA rate columns
2. **Search Engine Requirement:** Fuzzy/semantic matching across Vietnamese, English, and Chinese text requires specialized NLP tokenization
3. **Confidence Scoring:** Search results must include meaningful relevance scores to guide user decisions
4. **Data Versioning:** Annual tariff updates require version management with preview and rollback

### Cross-Cutting Concerns Identified

| Concern | Impact |
|---------|--------|
| **Multi-language handling** | Affects search indexing, display, input validation |
| **Authentication/Authorization** | User vs Admin roles across all endpoints |
| **Audit logging** | Admin actions, search history, data changes |
| **Data version awareness** | All queries must respect active tariff version |
| **Error handling** | Graceful degradation with user guidance |

### Critical Architectural Questions Surfaced

**Search Architecture (Highest Risk):**
The PRD's "semantic/fuzzy matching" requirement is underspecified. Two interpretations:
1. **Typo tolerance** (fuzzy): Solvable with pg_trgm or Elasticsearch
2. **Meaning matching** (semantic): Requires embedding-based search

Recommendation: Validate with stakeholders which is actually needed. The sample output showing "justification" reasoning suggests semantic understanding is expected.

**Preliminary Technology Leanings:**
| Component | Leaning | Rationale |
|-----------|---------|-----------|
| Search | PostgreSQL + pgvector | Single DB, sufficient scale, semantic capability |
| Embeddings | API-based (OpenAI/Cohere) | Avoid self-hosting ML infra for MVP |
| Backend | Python/FastAPI | Strong NLP/Excel ecosystem |
| Database | PostgreSQL | Already needed, consolidate |
| Cache | Redis (if needed) | Session management, but may be overkill for MVP |

**Deferred Decisions:**
- Frontend framework (React vs Next.js) - less critical, standard choice
- Deployment infrastructure - depends on client constraints

## Starter Template Evaluation

### Primary Technology Domain

Full-stack web application with separated frontend/backend architecture.

### Technology Stack Decision

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | Next.js 15+ (App Router) | SSR capability, React ecosystem, TypeScript |
| **Backend** | FastAPI (Python 3.12+) | Async performance, strong NLP/ML ecosystem |
| **Database** | PostgreSQL 16 + pgvector | Single DB for relational + vector search |
| **Auth** | NextAuth.js v5 + fastapi-nextauth-jwt | Frontend sessions, backend JWT validation |
| **Deployment** | Docker + nginx reverse proxy | Dedicated server, containerized |

### Initialization Commands

**Frontend:**
```bash
npx create-next-app@latest athena-web --typescript --tailwind --eslint --app --src-dir --turbopack
cd athena-web && npm install next-auth@beta
```

**Backend:**
```bash
mkdir athena-api && cd athena-api
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn sqlalchemy[asyncio] asyncpg alembic pydantic-settings
pip install fastapi-nextauth-jwt pgvector python-jose passlib[bcrypt]
```

### Project Structure

```
athena/
├── web/                    # Next.js frontend
│   ├── src/
│   │   ├── app/           # App Router pages
│   │   ├── components/    # React components
│   │   └── lib/           # Utilities, auth config
│   └── package.json
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── core/          # Config, security
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   ├── alembic/           # Migrations
│   └── pyproject.toml
├── docker-compose.yml
└── nginx.conf              # Reverse proxy
```

### Architectural Decisions Established

- **Styling:** Tailwind CSS (Next.js default)
- **State Management:** React Server Components + minimal client state
- **API Communication:** REST (JSON), potential tRPC for type-safety later
- **ORM:** SQLAlchemy 2.0 async with Alembic migrations
- **Vector Search:** pgvector extension, embeddings via OpenAI/Cohere API
- **Testing:** pytest (backend), Vitest/Playwright (frontend)

### Key Integration: Auth Flow

1. User authenticates via NextAuth.js (frontend)
2. NextAuth creates encrypted JWT in cookie
3. Frontend requests to `/api/*` proxied to FastAPI via nginx
4. FastAPI validates JWT using `fastapi-nextauth-jwt` with shared secret
5. Protected routes receive decoded user identity

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Search architecture: Hybrid (vector + fuzzy + exact)
- Embedding provider: OpenRouter API (configurable models)
- Data model: Normalized with version column
- Auth flow: NextAuth.js → FastAPI JWT validation

**Important Decisions (Shape Architecture):**
- Caching: Full Redis stack
- API pattern: Action-based REST
- Frontend state: Zustand + React Hook Form
- Deployment: Docker Compose multi-service

**Deferred Decisions (Post-MVP):**
- CDN/edge caching
- Horizontal scaling / load balancing
- Advanced observability (OpenTelemetry)

### Search & Embedding Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Embedding Provider** | OpenRouter API | Model flexibility, no vendor lock-in |
| **Search Strategy** | Hybrid | Vector (semantic) + pg_trgm (typos) + exact (HS codes) |
| **Confidence Display** | Percentage | Cosine similarity normalized to 0-100% |
| **Vector Storage** | pgvector extension | Single database, sufficient scale |

**Search Flow:**
1. User query → generate embedding via OpenRouter
2. Parallel execution:
   - Vector similarity search (pgvector)
   - Fuzzy text match (pg_trgm)
   - Exact HS code match (if query looks like code)
3. Merge and rank results by combined score
4. Return top N with confidence percentages

### Data Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Data Model** | Hierarchical + Normalized | Full HS hierarchy (sections→chapters→headings→subheadings→codes) + `fta_rates` |
| **Versioning** | Version column | `data_version_id` FK, active version in system config |
| **Caching** | Full Redis | Sessions, search results, hot HS codes |
| **ORM** | SQLAlchemy 2.0 async | Type-safe, async support, Alembic migrations |

**HS Code Hierarchy Structure:**
```
SECTION (PHẦN)              - 20 sections (I-XXI, skipping XV per HS standard)
  └─ CHAPTER (Chương)         - 98 chapters (01-98)
       └─ HEADING (Nhóm)          - 4-digit codes (e.g., 0101)
            └─ SUBHEADING (Phân nhóm) - 6-digit codes (e.g., 010121)
                 └─ HS CODE (Mã hàng)     - 8-digit codes (e.g., 01012100)
```

**Core Tables:**
```sql
-- Hierarchy tables (follow Harmonized System international standard)
hs_sections (id, section_number, section_roman, name_vn, name_en, notes_vn, notes_en, created_at)

hs_chapters (id, chapter_code, section_id, name_vn, name_en, notes_vn, notes_en, created_at)

hs_headings (id, heading_code, chapter_id, name_vn, name_en, created_at)

hs_subheadings (id, subheading_code, heading_id, name_vn, name_en, indent_level, created_at)

-- National tariff line (8-digit Vietnam-specific codes)
hs_codes (id, code, subheading_id, description_vn, description_en, unit, duty_rate, vat_rate,
          export_duty_rate, special_consumption_tax, environmental_tax, vat_reduction,
          policy_notes, indent_level, embedding, data_version_id, created_at)

fta_rates (id, hs_code_id, agreement_code, preferential_rate, conditions,
           rate_year, is_export, legal_document, effective_date, created_at)

data_versions (id, name, source_file, uploaded_at, activated_at, is_active)

lookup_records (id, query_text, query_hash, query_language, matched_hs_code_id,
               correct_hs_code_id, is_verified, verified_by_user_id, verified_at,
               confidence_score, search_method, notes,
               classification_data JSONB, practical_notes JSONB, process_logs JSONB,
               created_at, updated_at)

users (id, email, password_hash, role, created_at)

favorites (id, user_id, hs_code_id, notes, created_at)

search_history (id, user_id, query, selected_hs_code_id, created_at)
```

**Hierarchy Navigation Queries:**
```sql
-- Get full hierarchy path for an HS code
SELECT s.section_roman, s.name_vn as section_name,
       c.chapter_code, c.name_vn as chapter_name,
       h.heading_code, h.name_vn as heading_name,
       sh.subheading_code, sh.name_vn as subheading_name,
       hc.code, hc.description_vn
FROM hs_codes hc
JOIN hs_subheadings sh ON hc.subheading_id = sh.id
JOIN hs_headings h ON sh.heading_id = h.id
JOIN hs_chapters c ON h.chapter_id = c.id
JOIN hs_sections s ON c.section_id = s.id
WHERE hc.code = '01012100';

-- Browse all HS codes under a chapter
SELECT hc.* FROM hs_codes hc
JOIN hs_subheadings sh ON hc.subheading_id = sh.id
JOIN hs_headings h ON sh.heading_id = h.id
WHERE h.chapter_id = (SELECT id FROM hs_chapters WHERE chapter_code = '01');
```

### Authentication & Security

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Frontend Auth** | NextAuth.js v5 | Modern, Next.js native, session management |
| **Backend Validation** | fastapi-nextauth-jwt | Decrypts NextAuth JWTs, shared secret |
| **Password Hashing** | bcrypt (passlib) | Industry standard |
| **Authorization** | Role-based (user/admin) | Simple, sufficient for MVP |

**Auth Flow:**
1. User logs in via NextAuth.js (credentials provider)
2. NextAuth creates encrypted JWT in httpOnly cookie
3. Frontend requests include cookie automatically
4. nginx proxies `/api/*` to FastAPI with cookie
5. FastAPI middleware decrypts JWT, extracts user identity
6. Route handlers receive authenticated user context

### API & Communication Patterns

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Endpoint Style** | Action-based REST | Clear intent: `/api/search`, `/api/lookup` |
| **Error Format** | Simple JSON | `{error, code, details?}` |
| **Rate Limiting** | Layered | nginx (DDoS) + FastAPI/Redis (per-user) |
| **Logging** | Standard | Method, path, user_id, status, duration |
| **CORS** | Configured | Allow Next.js origin to call FastAPI directly |

**API Endpoints:**
```
POST /api/auth/login          # NextAuth handles
POST /api/auth/logout         # NextAuth handles

POST /api/search              # Main HS code search
GET  /api/hs-codes/{code}     # Single code details
GET  /api/hs-codes/browse     # Hierarchical browsing

GET  /api/favorites           # List user favorites
POST /api/favorites           # Add favorite
DELETE /api/favorites/{id}    # Remove favorite

GET  /api/history             # Search history
DELETE /api/history           # Clear history

GET  /api/lookups            # List all lookups (paginated, filterable by verified)
GET  /api/lookups/{id}       # Full lookup detail with classification, notes, logs

GET  /api/browse/sections                  # All sections with chapter counts
GET  /api/browse/chapters?section_id={id}  # Chapters in section with counts + notes
GET  /api/browse/chapters/{chapter_code}   # Full chapter: headings → subheadings → codes with inline rates
GET  /api/browse/search?q={text}&chapter={code}  # Text search within browse (pg_trgm + exact code)

POST /api/admin/data/upload   # Upload tariff Excel
POST /api/admin/data/preview  # Preview changes
POST /api/admin/data/activate # Activate new version
POST /api/admin/data/rollback # Rollback to previous
```

### Frontend Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Component Strategy** | Hybrid | Server for data, Client for search UI |
| **Data Fetching** | Direct FastAPI | Client-side fetch with CORS |
| **Search State** | Zustand | Lightweight, localStorage persistence |
| **Forms** | React Hook Form + Zod | Performant, type-safe validation |
| **Styling** | Tailwind CSS | Utility-first, consistent design |

**Key Frontend Patterns:**
- Search page: Client component with Zustand state
- Results list: Client component, infinite scroll or pagination
- HS code detail: Can be server component (static data)
- Favorites/History: Client components with optimistic updates

### Infrastructure & Deployment

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Containerization** | Docker Compose multi-service | Clean separation, easy scaling |
| **Routing** | nginx path-based | `/` → web, `/api/*` → api |
| **Env Management** | Docker env files | `.env.development`, `.env.production` |
| **Monitoring** | Minimal | Docker logs + Sentry errors |
| **Backups** | pg_dump cron | Daily dumps to object storage |

**Docker Compose Services:**
```yaml
services:
  nginx:      # Reverse proxy, SSL termination
  web:        # Next.js frontend
  api:        # FastAPI backend
  postgres:   # PostgreSQL + pgvector
  redis:      # Sessions, cache, rate limits
```

### Decision Impact Analysis

**Implementation Sequence:**
1. Database schema + migrations (PostgreSQL + pgvector)
2. FastAPI core + auth middleware
3. Search service (embeddings + hybrid search)
4. Next.js setup + NextAuth
5. Core UI (search, results, details)
6. User features (favorites, history)
7. Admin features (data upload)
8. Docker Compose + nginx
9. Deployment + monitoring

**Cross-Component Dependencies:**
- Search depends on: PostgreSQL, pgvector, Redis, OpenRouter API
- Auth depends on: NextAuth ↔ FastAPI shared secret
- Frontend depends on: CORS configuration, API contracts
- Admin depends on: Excel parsing, embedding generation pipeline

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Addressed:** 5 areas where AI agents could make incompatible choices

### Naming Patterns

**Database Naming Conventions:**
| Element | Convention | Example |
|---------|------------|---------|
| Tables | snake_case, plural | `hs_codes`, `fta_rates`, `search_history` |
| Columns | snake_case | `hs_code`, `duty_rate`, `created_at` |
| Foreign keys | `{table}_id` | `user_id`, `hs_code_id`, `data_version_id` |
| Indexes | `idx_{table}_{columns}` | `idx_hs_codes_code`, `idx_favorites_user_id` |
| Constraints | `{table}_{type}_{columns}` | `users_pk_id`, `favorites_fk_user_id` |

**API Naming Conventions:**
| Element | Convention | Example |
|---------|------------|---------|
| Endpoints | Action-based, lowercase | `/api/search`, `/api/favorites` |
| JSON fields | snake_case | `hs_code`, `duty_rate`, `created_at` |
| Query params | snake_case | `?page=1&per_page=20` |
| Headers | Standard HTTP | `Authorization`, `Content-Type` |

**Code Naming Conventions:**

*Python (FastAPI):*
| Element | Convention | Example |
|---------|------------|---------|
| Functions | snake_case | `get_hs_code()`, `search_codes()` |
| Variables | snake_case | `hs_code`, `search_results` |
| Classes | PascalCase | `HSCodeService`, `SearchRepository` |
| Constants | UPPER_SNAKE | `MAX_RESULTS`, `DEFAULT_PAGE_SIZE` |
| Files | snake_case | `hs_code_service.py`, `search_router.py` |

*TypeScript (Next.js):*
| Element | Convention | Example |
|---------|------------|---------|
| Functions | camelCase | `getHsCode()`, `searchCodes()` |
| Variables | camelCase | `hsCode`, `searchResults` |
| Components | PascalCase | `SearchBar`, `ResultsList` |
| Types/Interfaces | PascalCase | `HSCode`, `SearchResult` |
| Files (components) | PascalCase | `SearchBar.tsx`, `ResultsList.tsx` |
| Files (utilities) | camelCase | `apiClient.ts`, `formatDate.ts` |

### Structure Patterns

**Test Organization (Co-located):**
```
api/
├── app/
│   ├── services/
│   │   ├── search_service.py
│   │   └── search_service_test.py    # Co-located
│   └── repositories/
│       ├── hs_code_repository.py
│       └── hs_code_repository_test.py

web/
├── src/
│   ├── components/
│   │   ├── SearchBar.tsx
│   │   └── SearchBar.test.tsx        # Co-located
```

**Frontend Organization (Hybrid):**
```
web/src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth route group
│   │   ├── login/
│   │   └── register/
│   ├── search/            # Feature routes
│   │   ├── page.tsx
│   │   └── components/    # Feature-specific components
│   ├── favorites/
│   └── admin/
├── components/            # Shared UI components
│   ├── ui/               # Primitives (Button, Input, Card)
│   └── layout/           # Layout components (Header, Sidebar)
├── lib/                  # Utilities
│   ├── api.ts           # API client
│   ├── store.ts         # Zustand store
│   └── utils.ts         # Helpers
└── types/               # TypeScript types
```

**Backend Organization (Layered):**
```
api/app/
├── api/                  # Route handlers (thin)
│   ├── search.py
│   ├── favorites.py
│   └── admin.py
├── services/            # Business logic
│   ├── search_service.py
│   ├── embedding_service.py
│   └── excel_parser_service.py
├── repositories/        # Data access
│   ├── hs_code_repository.py
│   ├── favorites_repository.py
│   └── user_repository.py
├── schemas/             # Pydantic models
│   ├── search.py
│   ├── hs_code.py
│   └── responses.py
├── models/              # SQLAlchemy models (hierarchical HS code structure)
│   ├── hs_section.py    # Section (PHẦN) - top-level
│   ├── hs_chapter.py    # Chapter (Chương) - 2-digit
│   ├── hs_heading.py    # Heading (Nhóm) - 4-digit
│   ├── hs_subheading.py # Subheading (Phân nhóm) - 6-digit
│   ├── hs_code.py       # HS Code (Mã hàng) - 8-digit
│   ├── fta_rate.py
│   ├── data_version.py
│   └── user.py
└── core/                # Config, deps, middleware
    ├── config.py
    ├── database.py
    └── auth.py
```

### API Response Patterns

**Success Response (Envelope):**
```json
{
  "success": true,
  "data": {
    "hs_code": "85094010",
    "description_vn": "Máy xay sinh tố gia đình",
    "duty_rate": 20.0
  },
  "error": null
}
```

**List Response (Paginated):**
```json
{
  "success": true,
  "data": {
    "items": [
      { "hs_code": "85094010", "confidence": 0.92 },
      { "hs_code": "85094090", "confidence": 0.78 }
    ],
    "total": 47,
    "page": 1,
    "per_page": 20,
    "pages": 3
  },
  "error": null
}
```

**Error Response (RFC 7807):**
```json
{
  "success": false,
  "data": null,
  "error": {
    "type": "https://athena.example/errors/not-found",
    "title": "HS Code Not Found",
    "status": 404,
    "detail": "No HS code matching '99999999' exists in the current tariff data.",
    "instance": "/api/hs-codes/99999999"
  }
}
```

**Common Error Types:**
| HTTP Status | Type Suffix | Usage |
|-------------|-------------|-------|
| 400 | `/errors/validation` | Invalid input data |
| 401 | `/errors/unauthorized` | Missing/invalid auth |
| 403 | `/errors/forbidden` | Insufficient permissions |
| 404 | `/errors/not-found` | Resource not found |
| 429 | `/errors/rate-limited` | Too many requests |
| 500 | `/errors/internal` | Server error |

### State & Communication Patterns

**Zustand Store (Single with Slices):**
```typescript
// lib/store.ts
interface AppState {
  // Search slice
  searchQuery: string;
  searchResults: SearchResult[];
  isSearching: boolean;
  setSearchQuery: (query: string) => void;

  // Favorites slice
  favorites: Favorite[];
  isFavoritesLoading: boolean;
  addFavorite: (hsCode: string) => void;

  // Auth slice
  user: User | null;
  isAuthenticated: boolean;
}

export const useStore = create<AppState>((set) => ({
  // Implementation
}));
```

**Loading State Pattern (Boolean Flags):**
```typescript
// Per-feature loading states
isSearching: boolean;
isLoadingFavorites: boolean;
isLoadingHistory: boolean;
isSaving: boolean;

// Error states
searchError: Error | null;
favoritesError: Error | null;
```

**In-Component Fetching Pattern:**
```typescript
// components/SearchResults.tsx
function SearchResults({ query }: Props) {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!query) return;

    setIsLoading(true);
    setError(null);

    fetch(`${API_URL}/api/search`, {
      method: 'POST',
      body: JSON.stringify({ query }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) setResults(data.data.items);
        else throw new Error(data.error.detail);
      })
      .catch(setError)
      .finally(() => setIsLoading(false));
  }, [query]);

  // Render...
}
```

### Process Patterns

**Error Boundary Strategy (Per-Route):**
```typescript
// app/search/error.tsx
'use client';

export default function SearchError({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div>
      <h2>Search failed</h2>
      <p>{error.message}</p>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

**Form Validation (On Blur with React Hook Form + Zod):**
```typescript
const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Minimum 8 characters'),
});

function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    mode: 'onBlur',  // Validate on blur
  });
  // ...
}
```

**API Error Handling (Global + Explicit):**
```typescript
// lib/api.ts
const apiClient = {
  async fetch<T>(url: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_URL}${url}`, {
      ...options,
      credentials: 'include',
    });

    const data = await res.json();

    // Global handling for common errors
    if (res.status === 401) {
      window.location.href = '/login';
      throw new Error('Session expired');
    }

    if (!data.success) {
      throw new ApiError(data.error);
    }

    return data.data;
  }
};
```

**Date/Time Formatting:**
```typescript
// lib/utils.ts
import { format, parseISO } from 'date-fns';
import { vi } from 'date-fns/locale';

// API always uses ISO 8601
const API_DATE_FORMAT = "yyyy-MM-dd'T'HH:mm:ss'Z'";

// Display uses Vietnamese format
export function formatDisplayDate(isoString: string): string {
  return format(parseISO(isoString), 'dd/MM/yyyy HH:mm', { locale: vi });
}

// Database uses TIMESTAMP WITH TIME ZONE (handled by SQLAlchemy)
```

### Enforcement Guidelines

**All AI Agents MUST:**
1. Follow naming conventions exactly (snake_case for DB/API, language-specific for code)
2. Use the envelope response format for ALL API responses
3. Place tests co-located with source files
4. Use the layered architecture for backend (api → services → repositories)
5. Include RFC 7807 error structure for all error responses
6. Use boolean flags for loading states, not status enums

**Pattern Verification:**
- Pre-commit hooks validate file naming
- API response schemas enforced via Pydantic
- TypeScript strict mode catches naming violations
- Code review checklist includes pattern compliance

**Pattern Updates:**
- Propose changes via PR to architecture document
- All agents must acknowledge updated patterns
- Breaking pattern changes require migration plan

## Project Structure & Boundaries

### Complete Project Directory Structure

```
athena/
├── README.md
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── .gitignore
├── nginx/
│   ├── nginx.conf
│   └── ssl/                          # SSL certificates (gitignored)
│
├── web/                              # Next.js Frontend
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── postcss.config.js
│   ├── .env.local
│   ├── .env.example
│   ├── Dockerfile
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # Landing/redirect to search
│   │   │   ├── error.tsx             # Global error boundary
│   │   │   ├── loading.tsx
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   └── LoginForm.tsx
│   │   │   │   └── register/
│   │   │   │       ├── page.tsx
│   │   │   │       └── RegisterForm.tsx
│   │   │   ├── search/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── error.tsx
│   │   │   │   ├── loading.tsx
│   │   │   │   └── components/
│   │   │   │       ├── SearchBar.tsx
│   │   │   │       ├── SearchBar.test.tsx
│   │   │   │       ├── ResultsList.tsx
│   │   │   │       ├── ResultsList.test.tsx
│   │   │   │       ├── ResultCard.tsx
│   │   │   │       └── ConfidenceBadge.tsx
│   │   │   ├── hs-codes/
│   │   │   │   └── [code]/
│   │   │   │       ├── page.tsx      # HS code detail view
│   │   │   │       └── components/
│   │   │   │           ├── TariffDetails.tsx
│   │   │   │           ├── FTARatesTable.tsx
│   │   │   │           └── PolicyNotes.tsx
│   │   │   ├── favorites/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── error.tsx
│   │   │   │   └── components/
│   │   │   │       ├── FavoritesList.tsx
│   │   │   │       └── FavoriteCard.tsx
│   │   │   ├── history/
│   │   │   │   ├── page.tsx
│   │   │   │   └── components/
│   │   │   │       └── HistoryList.tsx
│   │   │   ├── lookups/
│   │   │   │   ├── page.tsx          # Lookup history list
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx      # Lookup detail view
│   │   │   │       └── components/
│   │   │   │           ├── LookupDetail.tsx
│   │   │   │           └── ProcessLogTimeline.tsx
│   │   │   ├── browse/                       # Tariff Schedule Browser (Sprint Change 2026-02-11)
│   │   │   │   ├── page.tsx
│   │   │   │   └── components/
│   │   │   │       ├── SectionList.tsx
│   │   │   │       ├── ChapterView.tsx
│   │   │   │       ├── HSCodeRow.tsx
│   │   │   │       ├── HSCodeDetail.tsx
│   │   │   │       ├── ChapterJumper.tsx
│   │   │   │       └── BrowseSearch.tsx
│   │   │   ├── admin/
│   │   │   │   ├── layout.tsx        # Admin layout with guard
│   │   │   │   ├── page.tsx          # Admin dashboard
│   │   │   │   └── data/
│   │   │   │       ├── page.tsx      # Data management
│   │   │   │       └── components/
│   │   │   │           ├── UploadWizard.tsx
│   │   │   │           ├── ChangePreview.tsx
│   │   │   │           └── VersionHistory.tsx
│   │   │   └── api/
│   │   │       └── auth/
│   │   │           └── [...nextauth]/
│   │   │               └── route.ts  # NextAuth handler
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Button.test.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Table.tsx
│   │   │   │   ├── Badge.tsx
│   │   │   │   ├── Spinner.tsx
│   │   │   │   └── Modal.tsx
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       ├── Footer.tsx
│   │   │       └── UserMenu.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                # API client with error handling
│   │   │   ├── api.test.ts
│   │   │   ├── auth.ts               # NextAuth configuration
│   │   │   ├── store.ts              # Zustand store
│   │   │   ├── store.test.ts
│   │   │   ├── utils.ts              # Helpers (formatDate, etc.)
│   │   │   └── constants.ts
│   │   └── types/
│   │       ├── api.ts                # API response types
│   │       ├── hs-code.ts
│   │       ├── user.ts
│   │       └── search.ts
│   └── public/
│       ├── favicon.ico
│       └── images/
│
├── api/                              # FastAPI Backend
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── .env
│   ├── .env.example
│   ├── Dockerfile
│   ├── pytest.ini
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py               # Dependency injection
│   │   │   ├── search.py
│   │   │   ├── search_test.py
│   │   │   ├── lookups.py
│   │   │   ├── lookups_test.py
│   │   │   ├── browse.py             # Tariff browse endpoints (Sprint Change 2026-02-11)
│   │   │   ├── browse_test.py
│   │   │   ├── hs_codes.py
│   │   │   ├── hs_codes_test.py
│   │   │   ├── favorites.py
│   │   │   ├── favorites_test.py
│   │   │   ├── history.py
│   │   │   ├── history_test.py
│   │   │   └── admin/
│   │   │       ├── __init__.py
│   │   │       ├── data.py
│   │   │       └── data_test.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── search_service.py
│   │   │   ├── search_service_test.py
│   │   │   ├── embedding_service.py
│   │   │   ├── embedding_service_test.py
│   │   │   ├── excel_parser_service.py       # Basic flat Excel parsing
│   │   │   ├── excel_parser_service_test.py
│   │   │   ├── tariff_hierarchy_parser.py    # Full hierarchy extraction
│   │   │   ├── browse_service.py             # Tariff browse business logic (Sprint Change 2026-02-11)
│   │   │   ├── browse_service_test.py
│   │   │   └── cache_service.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── hs_code_repository.py
│   │   │   ├── hs_code_repository_test.py
│   │   │   ├── browse_repository.py          # Tariff browse data access (Sprint Change 2026-02-11)
│   │   │   ├── browse_repository_test.py
│   │   │   ├── favorites_repository.py
│   │   │   ├── favorites_repository_test.py
│   │   │   ├── history_repository.py
│   │   │   ├── user_repository.py
│   │   │   └── data_version_repository.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Envelope response schemas
│   │   │   ├── search.py
│   │   │   ├── hs_code.py
│   │   │   ├── browse.py             # Browse response schemas (Sprint Change 2026-02-11)
│   │   │   ├── favorites.py
│   │   │   ├── history.py
│   │   │   ├── lookup.py
│   │   │   ├── user.py
│   │   │   └── admin.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # SQLAlchemy base
│   │   │   ├── hs_section.py         # Section (PHẦN) - 20 sections
│   │   │   ├── hs_chapter.py         # Chapter (Chương) - 98 chapters
│   │   │   ├── hs_heading.py         # Heading (Nhóm) - 4-digit codes
│   │   │   ├── hs_subheading.py      # Subheading (Phân nhóm) - 6-digit codes
│   │   │   ├── hs_code.py            # HS Code (Mã hàng) - 8-digit codes
│   │   │   ├── fta_rate.py
│   │   │   ├── data_version.py
│   │   │   ├── user.py
│   │   │   ├── favorite.py
│   │   │   └── search_history.py
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── config.py             # Pydantic settings
│   │       ├── database.py           # Async SQLAlchemy setup
│   │       ├── redis.py              # Redis connection
│   │       ├── auth.py               # JWT validation middleware
│   │       ├── auth_test.py
│   │       ├── errors.py             # RFC 7807 error handlers
│   │       └── logging.py            # Structured logging
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 20260127_..._add_hs_codes_fta_rates_data_versions.py
│   │       └── 20260128_add_hs_hierarchy_tables.py
│   └── scripts/
│       ├── import_tariff_data.py         # Basic flat data import
│       ├── import_tariff_hierarchy.py    # Full hierarchical import (recommended)
│       └── backup.sh                     # pg_dump backup script
│
├── data/                             # Sample/test data (gitignored in prod)
│   └── sample_tariff.xlsx
│
└── docs/
    ├── api.md                        # API documentation
    ├── deployment.md
    └── development.md
```

### Architectural Boundaries

**API Boundaries:**
| Boundary | Location | Responsibility |
|----------|----------|----------------|
| HTTP Entry | `api/app/api/*.py` | Request validation, auth check, response formatting |
| Service Layer | `api/app/services/*.py` | Business logic, orchestration |
| Repository Layer | `api/app/repositories/*.py` | Data access, query building |
| External APIs | `api/app/services/embedding_service.py` | OpenRouter API calls |

**Component Boundaries (Frontend):**
| Boundary | Location | Responsibility |
|----------|----------|----------------|
| Pages | `web/src/app/*/page.tsx` | Route handling, data orchestration |
| Feature Components | `web/src/app/*/components/` | Feature-specific UI |
| Shared UI | `web/src/components/ui/` | Reusable primitives |
| State | `web/src/lib/store.ts` | Global application state |
| API Client | `web/src/lib/api.ts` | HTTP communication |

**Data Boundaries:**
| Boundary | Tables | Access Pattern |
|----------|--------|----------------|
| HS Code Hierarchy | `hs_sections`, `hs_chapters`, `hs_headings`, `hs_subheadings` | Read-only, static hierarchy |
| HS Code Domain | `hs_codes`, `fta_rates`, `data_versions` | Read-heavy, versioned |
| User Domain | `users`, `favorites`, `search_history` | User-scoped CRUD |
| Cache Layer | Redis | Sessions, search results, hot data |

### Requirements to Structure Mapping

**FR1-9: HS Code Search**
- API: `api/app/api/search.py`, `api/app/api/hs_codes.py`
- Services: `api/app/services/search_service.py`, `embedding_service.py`
- Repository: `api/app/repositories/hs_code_repository.py`
- Models: `api/app/models/hs_*.py` (full hierarchy for browsing)
- Frontend: `web/src/app/search/`, `web/src/app/hs-codes/`

**FR10-18: Tariff Data Display**
- Models: `api/app/models/hs_section.py`, `hs_chapter.py`, `hs_heading.py`, `hs_subheading.py`, `hs_code.py`, `fta_rate.py`
- Schemas: `api/app/schemas/hs_code.py`
- Frontend: `web/src/app/hs-codes/[code]/components/`
- Note: Use hierarchy for breadcrumb navigation (Section → Chapter → Heading → Subheading → HS Code)

**FR19-29: Favorites & History**
- API: `api/app/api/favorites.py`, `history.py`
- Repository: `api/app/repositories/favorites_repository.py`, `history_repository.py`
- Frontend: `web/src/app/favorites/`, `web/src/app/history/`

**FR51-53: Lookup History & Details**
- API: `api/app/api/lookups.py`
- Repository: `api/app/repositories/lookup_record_repository.py`
- Models: `api/app/models/lookup_record.py` (extended with JSONB columns)
- Schemas: `api/app/schemas/lookup.py`
- Frontend: `web/src/app/lookups/`, `web/src/app/lookups/[id]/`

**FR54-61: Tariff Schedule Browser (Sprint Change 2026-02-11)**
- API: `api/app/api/browse.py`
- Services: `api/app/services/browse_service.py`
- Repository: `api/app/repositories/browse_repository.py`
- Models: `api/app/models/hs_code.py` (expanded: export_duty_rate, special_consumption_tax, environmental_tax, vat_reduction), `fta_rate.py` (expanded: rate_year, is_export, legal_document, effective_date)
- Schemas: `api/app/schemas/browse.py`
- Frontend: `web/src/app/browse/` (SectionList, ChapterView, HSCodeRow, HSCodeDetail, ChapterJumper, BrowseSearch)
- Parser: `api/app/services/tariff_hierarchy_parser.py` (expanded for Excel columns CD, CG, CJ-CR, CS, CW + export FTA sheets)

**FR30-35: User Authentication**
- Backend: `api/app/core/auth.py`, `api/app/repositories/user_repository.py`
- Frontend: `web/src/lib/auth.ts`, `web/src/app/(auth)/`

**FR36-42: Admin Data Management**
- API: `api/app/api/admin/data.py`
- Services: `api/app/services/tariff_hierarchy_parser.py` (full hierarchy), `excel_parser_service.py` (flat)
- Scripts: `api/app/scripts/import_tariff_hierarchy.py`
- Frontend: `web/src/app/admin/data/`

### Integration Points

**Internal Communication:**
```
[Browser] → [nginx:80/443]
                ├── / → [web:3000] (Next.js)
                └── /api/* → [api:8000] (FastAPI)
                                 ├── [PostgreSQL:5432]
                                 ├── [Redis:6379]
                                 └── [OpenRouter API] (external)
```

**External Integrations:**
| Service | Purpose | Configuration |
|---------|---------|---------------|
| OpenRouter API | Embedding generation | `OPENROUTER_API_KEY` env var |
| Sentry | Error tracking | `SENTRY_DSN` env var |

**Data Flow:**
```
User Query → API → Embedding Service → OpenRouter
                         ↓
              Search Service → pgvector similarity
                         ↓
              Repository → PostgreSQL
                         ↓
              Response → Redis Cache → API → Frontend
```

### Docker Compose Services

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
      - api

  web:
    build: ./web
    environment:
      - NEXTAUTH_URL=https://athena.example.com
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - API_URL=http://api:8000
    depends_on:
      - api

  api:
    build: ./api
    environment:
      - DATABASE_URL=postgresql+asyncpg://...
      - REDIS_URL=redis://redis:6379
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    depends_on:
      - postgres
      - redis

  postgres:
    image: pgvector/pgvector:pg16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=athena
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Development Workflow

**Local Development:**
```bash
# Start infrastructure
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Backend (terminal 1)
cd api && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd web && npm run dev
```

**Test Execution:**
```bash
# Backend tests
cd api && pytest

# Frontend tests
cd web && npm test

# E2E tests (Playwright)
cd web && npm run test:e2e
```

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
All technology choices work together without conflicts:
- Next.js 15+ frontend communicates with FastAPI via nginx reverse proxy
- NextAuth.js v5 tokens validated by FastAPI using `fastapi-nextauth-jwt`
- PostgreSQL 16 with pgvector provides unified relational + vector storage
- Redis 7 handles sessions, caching, and rate limiting
- OpenRouter API enables configurable embedding models

**Pattern Consistency:**
Implementation patterns fully support architectural decisions:
- Naming conventions align with technology standards (snake_case for Python/DB/API, camelCase for TypeScript)
- Envelope response format enforced via Pydantic schemas
- Layered backend architecture enables clean separation of concerns

**Structure Alignment:**
Project structure enables all architectural decisions:
- Monorepo supports independent frontend/backend development
- Co-located tests simplify maintenance
- Clear boundaries between features and shared components

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:**
All 50 functional requirements have explicit architectural support:
- Search (FR1-9): Hybrid search with pgvector + pg_trgm + exact match
- Display (FR10-18): Normalized data model with FTA rates
- Personalization (FR19-29): User-scoped favorites and history
- Auth (FR30-35): NextAuth.js with FastAPI JWT validation
- Admin (FR36-42): Excel upload pipeline with version management
- Quality (FR43-50): RFC 7807 errors, envelope responses

**Non-Functional Requirements Coverage:**
| Requirement | Architectural Support |
|-------------|----------------------|
| <3s search | Async FastAPI, pgvector indexing, Redis cache |
| 50-100 concurrent | Async stack, connection pooling |
| 99.5% uptime | Docker health checks, graceful shutdown |
| Security | JWT encryption, HTTPS, bcrypt, rate limiting |
| Accessibility | Tailwind classes, semantic HTML patterns |
| Multi-language | UTF-8 throughout, multi-language tokenization |

### Implementation Readiness Validation ✅

**Decision Completeness:**
- All critical decisions documented with specific versions
- Technology trade-offs recorded for future reference
- Deferred decisions clearly marked

**Structure Completeness:**
- ~80 files and directories explicitly defined
- Every FR category mapped to specific code locations
- All integration points documented

**Pattern Completeness:**
- 5 potential conflict areas addressed with clear conventions
- Concrete code examples provided for all patterns
- Enforcement guidelines defined for AI agents

### Imported Data Statistics (Story 1.2 Completed)

**Vietnam 2026 Tariff Schedule (BIEU-THUE-XNK-2026.xlsx):**
| Entity | Count | Notes |
|--------|-------|-------|
| Sections | 20 | I-XXI (XV skipped per HS standard) |
| Chapters | 98 | 01-98 |
| Headings | 1,269 | 4-digit codes |
| Subheadings | 5,786 | 6-digit codes |
| HS Codes | 11,871 | 8-digit national tariff lines |
| FTA Rates | 211,391 | 18 FTA agreements |

**FTA Agreements Imported:**
*Import:* ACFTA, ATIGA, AJCEP, VJEPA, AKFTA, AANZFTA, AIFTA, VKFTA, VCFTA, VN-EAEU, CPTPP, AHKFTA, VNCU, EVFTA, UKVFTA, VN-LAO, VIFTA, RCEPT
*Export (pending Story 2-1):* CPTPP-XK, EV-XK, UKV-XK

**Import Performance:**
- Total import time: ~76 seconds
- All HS codes linked to hierarchy (100% coverage)
- Section/chapter notes extracted for reference

### Gap Analysis Results

**Critical Gaps:** None

**Important Gaps (Post-MVP):**
| Gap | Impact | Recommendation |
|-----|--------|----------------|
| Logging aggregation | Production debugging harder | Add Loki/ELK later |
| API versioning | Breaking changes harder | Add `/v1/` prefix if needed |
| Connection pool config | Default may not be optimal | Tune after load testing |

**Nice-to-Have Gaps:**
- Storybook for UI component development
- Pre-commit hook configuration details
- OpenAPI documentation customization

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed (Medium-High)
- [x] Technical constraints identified (Excel parsing, multi-language search)
- [x] Cross-cutting concerns mapped (auth, logging, versioning, errors)

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified (Next.js, FastAPI, PostgreSQL, Redis)
- [x] Integration patterns defined (nginx routing, JWT flow)
- [x] Performance considerations addressed (async, caching, indexing)

**✅ Implementation Patterns**
- [x] Naming conventions established (5 areas)
- [x] Structure patterns defined (co-located tests, layered backend, hybrid frontend)
- [x] Communication patterns specified (envelope responses, RFC 7807 errors)
- [x] Process patterns documented (error boundaries, form validation, date formatting)

**✅ Project Structure**
- [x] Complete directory structure defined (~80 files/directories)
- [x] Component boundaries established (API → Service → Repository)
- [x] Integration points mapped (nginx, Docker Compose)
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** HIGH

**Key Strengths:**
1. Single database (PostgreSQL + pgvector) reduces operational complexity
2. Well-defined patterns prevent AI agent conflicts
3. Proven technology stack with good ecosystem support
4. Clear separation between frontend and backend enables parallel development
5. Comprehensive requirements mapping ensures nothing is missed

**Areas for Future Enhancement:**
1. Add observability stack (Prometheus/Grafana) for production monitoring
2. Consider CDN for static assets if global users are needed
3. Evaluate horizontal scaling when user base grows beyond MVP

### Implementation Handoff

**AI Agent Guidelines:**
1. Follow all architectural decisions exactly as documented
2. Use implementation patterns consistently across all components
3. Respect project structure and boundaries
4. Refer to this document for all architectural questions
5. When in doubt, prefer simplicity over cleverness

**First Implementation Priority:**
```bash
# 1. Initialize project structure
mkdir -p athena/{web,api,nginx,data,docs}

# 2. Set up FastAPI backend
cd athena/api
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn sqlalchemy[asyncio] asyncpg alembic
pip install pgvector fastapi-nextauth-jwt pydantic-settings

# 3. Set up Next.js frontend
cd ../web
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir
npm install next-auth@beta zustand react-hook-form @hookform/resolvers zod

# 4. Start infrastructure
cd ..
docker-compose -f docker-compose.dev.yml up -d postgres redis
```

## Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** 2026-01-24
**Document Location:** `_bmad-output/planning-artifacts/architecture.md`

### Final Architecture Deliverables

**Complete Architecture Document**
- All architectural decisions documented with specific versions
- Implementation patterns ensuring AI agent consistency
- Complete project structure with all files and directories
- Requirements to architecture mapping
- Validation confirming coherence and completeness

**Implementation Ready Foundation**
- 25+ architectural decisions made
- 15+ implementation patterns defined
- 8 major architectural components specified
- 50 functional requirements fully supported

**AI Agent Implementation Guide**
- Technology stack with verified versions
- Consistency rules that prevent implementation conflicts
- Project structure with clear boundaries
- Integration patterns and communication standards

### Quality Assurance Checklist

**✅ Architecture Coherence**
- [x] All decisions work together without conflicts
- [x] Technology choices are compatible
- [x] Patterns support the architectural decisions
- [x] Structure aligns with all choices

**✅ Requirements Coverage**
- [x] All functional requirements are supported
- [x] All non-functional requirements are addressed
- [x] Cross-cutting concerns are handled
- [x] Integration points are defined

**✅ Implementation Readiness**
- [x] Decisions are specific and actionable
- [x] Patterns prevent agent conflicts
- [x] Structure is complete and unambiguous
- [x] Examples are provided for clarity

### Project Success Factors

**Clear Decision Framework**
Every technology choice was made collaboratively with clear rationale, ensuring all stakeholders understand the architectural direction.

**Consistency Guarantee**
Implementation patterns and rules ensure that multiple AI agents will produce compatible, consistent code that works together seamlessly.

**Complete Coverage**
All project requirements are architecturally supported, with clear mapping from business needs to technical implementation.

**Solid Foundation**
The chosen technology stack and architectural patterns provide a production-ready foundation following current best practices.

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** Begin implementation using the architectural decisions and patterns documented herein.

**Document Maintenance:** Update this architecture when major technical decisions are made during implementation.

