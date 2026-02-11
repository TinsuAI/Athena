# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Athena is an HS (Harmonized System) code lookup tool for Vietnamese import/export. Users search with natural language product descriptions (Vietnamese or English) and get tariff classification results via hybrid search (vector similarity + fuzzy text + exact match).

**Stack**: FastAPI (Python 3.12+) backend, Next.js 16 (React 19, TypeScript) frontend, PostgreSQL 16 with pgvector, Redis 7. All services run in Docker.

## Development Commands

### Start/Stop Services
```bash
docker-compose -f docker-compose.dev.yml up -d --build   # start with hot reload
docker-compose -f docker-compose.dev.yml down             # stop
docker-compose -f docker-compose.dev.yml down -v          # stop + remove volumes
```

### Ports
- **8979**: Next.js frontend
- **8980**: FastAPI backend (Swagger at /docs)
- **8981**: PostgreSQL
- **8982**: Redis

### Backend Testing & Linting (from `api/`)
```bash
pytest                                    # all tests
pytest app/services/search_service_test.py  # single file
pytest --cov=app                          # with coverage
ruff check .                              # lint
ruff format .                             # format
mypy .                                    # type check
```

### Frontend Testing & Linting (from `web/`)
```bash
npm test                    # vitest watch mode
npm run test:run            # run once
npm run test:coverage       # with coverage
npm run lint                # eslint
tsc --noEmit                # type check
```

### Database Migrations (from `api/`)
```bash
alembic revision --autogenerate -m "description"  # create migration
alembic upgrade head                               # apply migrations
alembic downgrade -1                               # rollback one
```

### Run Commands Inside Docker
```bash
docker-compose -f docker-compose.dev.yml exec api pytest
docker-compose -f docker-compose.dev.yml exec web npm test
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head
```

## Architecture

### Backend Layering (Strict)
```
Route handlers (api/)  →  Services (services/)  →  Repositories (repositories/)  →  DB
     THIN only:              ALL business            ONLY database
  validate, auth,            logic here              queries here
  call service,
  format response
```
Never put business logic in route handlers. Never put non-DB logic in repositories.

### Search Pipeline
1. **Knowledge base check** — lookup verified expert corrections first
2. **Query enhancement** — LLM extracts keywords, predicts HS chapters
3. **Embedding generation** — OpenRouter text-embedding-3-large (3072-dim), cached in Redis
4. **Hybrid search** — vector (pgvector cosine) + fuzzy (pg_trgm) + exact match; scoring: 60% vector + 40% fuzzy
5. **LLM reranking** — GRI-based classification of top candidates
6. **Record lookup** — save to knowledge base for future expert verification

### Frontend Patterns
- **State**: Zustand single store with slices (search, auth, favorites) in `web/src/lib/store.ts`
- **Data fetching**: Direct to FastAPI with CORS — never use Next.js API routes for data
- **Forms**: React Hook Form + Zod, validate on blur
- **UI components**: shadcn/ui (headless, accessible)
- **Client vs Server**: Interactive search/forms are client components; static layout is server

### API Response Format (Mandatory)
All responses use envelope format:
```json
{"success": true, "data": {...}, "error": null}
```
All errors use RFC 7807:
```json
{"success": false, "data": null, "error": {"type": "...", "title": "...", "status": 400, "detail": "...", "instance": "/api/..."}}
```

### Auth Flow
NextAuth.js creates encrypted JWT in httpOnly cookie → frontend sends `credentials: 'include'` → nginx proxies `/api/*` → FastAPI decrypts JWT using shared `NEXTAUTH_SECRET`. Both services must share the same secret.

## Conventions

### Naming
| Context | Convention | Example |
|---------|-----------|---------|
| DB tables/columns, API JSON fields | snake_case | `hs_codes`, `duty_rate` |
| Python functions | snake_case | `get_hs_code()` |
| Python classes | PascalCase | `HSCodeService` |
| TypeScript functions | camelCase | `getHsCode()` |
| React components | PascalCase files | `SearchBar.tsx` |

### Testing
Tests are **co-located** with source files (same directory):
- `search_service.py` → `search_service_test.py`
- `SearchBar.tsx` → `SearchBar.test.tsx`

Backend uses pytest with `asyncio_mode = "auto"`. Frontend uses Vitest with jsdom.

## Anti-Patterns to Avoid
- Business logic in route handlers
- camelCase in API JSON responses
- Tests in separate `/tests` directory
- Status enums for loading states (use boolean flags)
- Fetching via Next.js API routes instead of FastAPI directly
- Skipping the envelope response format

## Key Files
| Purpose | Location |
|---------|----------|
| FastAPI entry point | `api/app/main.py` |
| Search endpoint | `api/app/api/search.py` |
| Search orchestration | `api/app/services/search_service.py` |
| Hybrid search SQL | `api/app/repositories/search_repository.py` |
| Knowledge base service | `api/app/services/knowledge_base_service.py` |
| Embedding service | `api/app/services/embedding_service.py` |
| Frontend search page | `web/src/app/search/page.tsx` |
| Zustand store | `web/src/lib/store.ts` |
| API client | `web/src/lib/api.ts` |
| DB config | `api/app/core/config.py` |
| Migrations | `api/alembic/versions/` |
| Implementation rules | `_bmad-output/project-context.md` |

## Database Schema
HS code hierarchy: `hs_sections` → `hs_chapters` (2-digit) → `hs_headings` (4-digit) → `hs_subheadings` (6-digit) → `hs_codes` (8-digit, with 3072-dim embedding). Also: `fta_rates`, `data_versions`, `lookup_records` (knowledge base).
