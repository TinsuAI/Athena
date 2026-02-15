# Story 3.1: NotebookLM Service & Response Parser

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **a service that queries NotebookLM with product descriptions and parses the response into structured HS code data**,
So that **the search pipeline can use NotebookLM as its primary AI classification engine**.

## Background

Three attempts at AI-based search (vector embeddings, category context enrichment, LLM query enhancement + reranking) all failed at 0% accuracy. NotebookLM (Gemini 3) with the official Vietnam 2026 tariff PDF achieves 100% accuracy across all test queries. This story creates the service wrapper, response parser, and Redis caching layer. Story 3-2 will integrate this service into the search pipeline.

**Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-15.md`

**Dependencies:** Stories 1-8 (KB schema), 1-9 (KB-enhanced search), 1-10 (expert review) must be complete (all done).

**FRs covered:** FR62 (NotebookLM query for novel descriptions)

## Acceptance Criteria

1. **AC1: Successful Query with HS Code Extraction**
   - **Given** the NotebookLM service is configured with a valid notebook ID
   - **When** I call `query("Thanh treo khăn bằng đồng mạ chrome")`
   - **Then** the service returns `{hs_code: "7418.20.00", classification: {...}, practical_notes: [...], raw_answer: "..."}`
   - **And** the HS code is extracted via regex from the NotebookLM markdown response
   - **And** classification contains material and function reasoning text

2. **AC2: HS Code Extraction**
   - **Given** NotebookLM returns an answer mentioning an HS code
   - **When** the response is parsed
   - **Then** the first HS code matching pattern `XXXX.XX.XX` is extracted
   - **And** the extracted code is returned in the result
   - **Note:** Database validation of the extracted code is performed in Story 3-2

3. **AC3: Categorized Guide (No Single HS Code)**
   - **Given** NotebookLM returns a categorized guide (no single HS code)
   - **When** the response is parsed
   - **Then** the system returns the response as guidance text
   - **And** `hs_code` is None (indicating manual classification needed)

4. **AC4: Error Handling — Unavailable Service**
   - **Given** NotebookLM is unavailable (rate limit, timeout, service down)
   - **When** the service is called
   - **Then** it raises `NotebookLMUnavailableError`
   - **And** the error includes reason (timeout/rate_limit/auth_error/service_down)

5. **AC5: Disabled Service**
   - **Given** the service is disabled via `NOTEBOOKLM_ENABLED=false`
   - **When** the service is called
   - **Then** it immediately returns None without making any API call

6. **AC6: Redis Caching**
   - **Given** a query has been previously answered by NotebookLM
   - **When** the same query is sent within 24 hours
   - **Then** the cached Redis response is returned
   - **And** no NotebookLM API call is made

## Tasks / Subtasks

- [x] Task 1: Add configuration settings (AC: #1, #5)
  - [x] 1.1 Add NotebookLM settings to `api/app/core/config.py`
- [x] Task 2: Create NotebookLM service (AC: #1, #2, #3, #4, #5, #6)
  - [x] 2.1 Create `api/app/services/notebooklm_service.py`
  - [x] 2.2 Implement `NotebookLMService` class with `query()` method
  - [x] 2.3 Implement response parser with regex HS code extraction
  - [x] 2.4 Implement Redis caching layer
  - [x] 2.5 Implement error handling with `NotebookLMUnavailableError`
- [x] Task 3: Update Docker setup (AC: #1)
  - [x] 3.1 Add `notebooklm-mcp-cli` to `api/requirements.txt`
  - [x] 3.2 Mount cookie directory in `docker-compose.dev.yml`
  - [x] 3.3 Add `NOTEBOOKLM_NOTEBOOK_ID` env var to docker-compose
- [x] Task 4: Write tests (AC: #1-#6)
  - [x] 4.1 Create `api/app/services/notebooklm_service_test.py`
  - [x] 4.2 Test happy path (query returns HS code)
  - [x] 4.3 Test response parsing edge cases (multiple codes, no code, guide text)
  - [x] 4.4 Test Redis caching (hit/miss)
  - [x] 4.5 Test error handling (timeout, rate limit, auth error, service down)
  - [x] 4.6 Test disabled service returns None

## Dev Notes

### Critical Architecture Patterns (MUST FOLLOW)

**Backend Layered Architecture — This story is BACKEND ONLY:**
```
NotebookLMService (services/)
├── wraps notebooklm_tools.core.client.NotebookLMClient
├── parses response → extracts HS code via regex
├── caches in Redis
└── raises NotebookLMUnavailableError on failure
```

**No route handler needed for this story.** The service is consumed by `search_service.py` in Story 3-2.

### Existing Code to Reference (READ THESE FIRST)

**Pattern file: `api/app/core/config.py`** — Settings pattern:
```python
class Settings(BaseSettings):
    # Add new fields here following existing pattern
    notebooklm_enabled: bool = True
    notebooklm_notebook_id: str = ""
    notebooklm_timeout: int = 120
    notebooklm_cache_ttl: int = 86400  # 24 hours
```

**Pattern file: `api/app/services/knowledge_base_service.py`** — Service class pattern:
- Dataclass for result type (`KBLookupResult`)
- Constructor takes `session: AsyncSession`
- Methods return typed results or None
- Clear docstrings with Args/Returns

**Pattern file: `api/app/services/embedding_service.py`** — Redis caching pattern:
- Constructor takes `redis_client: redis.Redis | None`
- Cache key pattern: `prefix:{hash}`
- JSON serialize/deserialize for cached values
- Graceful fallback if Redis unavailable

**Pattern file: `api/app/core/redis.py`** — Redis connection:
- Uses `redis.asyncio` with connection pool
- `get_redis()` dependency provides client
- Operations have `socket_timeout=5.0`

### NotebookLM Python SDK Reference

**Package:** `notebooklm-mcp-cli` (pip install)

**Import path:** `notebooklm_tools.core.client.NotebookLMClient`

**Usage pattern (from sprint change proposal):**
```python
from notebooklm_tools.core.client import NotebookLMClient

client = NotebookLMClient()
result = client.query(notebook_id="5d982e32-...", query_text="product description")
# result has .answer (str) and .conversation_id (str)
```

**Authentication:** Cookie-based. Cookies stored in `~/.config/notebooklm-mcp/` (or `~/.notebooklm-mcp-cli/`). Run `nlm login` once to authenticate. Cookies auto-refresh.

**IMPORTANT:** The `NotebookLMClient.query()` call is **synchronous** (uses httpx internally). Wrap in `asyncio.to_thread()` or `loop.run_in_executor()` to avoid blocking the async event loop.

### Service Implementation Guide

**File: `api/app/services/notebooklm_service.py`**

```python
import hashlib
import json
import re
from dataclasses import dataclass

import redis.asyncio as redis

from app.core.config import get_settings

# Custom exception
class NotebookLMUnavailableError(Exception):
    def __init__(self, reason: str):
        self.reason = reason  # "timeout" | "rate_limit" | "auth_error" | "service_down"
        super().__init__(f"NotebookLM unavailable: {reason}")

@dataclass
class NotebookLMResult:
    hs_code: str | None          # "7418.20.00" or None if guide/no-match
    classification: dict | None   # {"reasoning": "...", "material": "...", "function": "..."}
    practical_notes: list[str]    # Extracted practical guidance
    raw_answer: str               # Full NotebookLM markdown response

class NotebookLMService:
    def __init__(self, redis_client: redis.Redis | None = None):
        self.settings = get_settings()
        self.redis_client = redis_client

    async def query(self, query_text: str) -> NotebookLMResult | None:
        """Query NotebookLM for HS code classification."""
        # 1. Check if disabled
        # 2. Check Redis cache
        # 3. Call NotebookLMClient (via asyncio.to_thread)
        # 4. Parse response
        # 5. Cache result in Redis
        # 6. Return NotebookLMResult
```

### Response Parsing Strategy (CRITICAL)

**HS Code Regex:** `\d{4}\.\d{2}\.\d{2}` — extracts codes like `7418.20.00`

**Parsing rules:**
1. Search NotebookLM markdown answer for HS code pattern
2. Extract the FIRST match (most relevant)
3. The extracted code format `XXXX.XX.XX` needs normalization to `XXXXXXXX` (remove dots) for DB lookup in Story 3-2
4. If NO HS code pattern found → return result with `hs_code=None` (categorized guide)
5. If multiple HS codes found → use first one (primary classification)

**Classification extraction:**
- Split answer text by common section markers (e.g., lines starting with `**`, `#`, numbered lists)
- Extract reasoning about material, function, and GRI application
- Store as structured dict with key fields

**Practical notes extraction:**
- Look for bullet points, numbered items about FTA optimization, import procedures
- Extract as list of strings

### Redis Caching Strategy

**Cache key:** `nlm:{md5(query_text.lower().strip())}`

**Cache value:** JSON-serialized `NotebookLMResult`:
```json
{
  "hs_code": "7418.20.00",
  "classification": {"reasoning": "..."},
  "practical_notes": ["Use EVFTA for 3.7% rate"],
  "raw_answer": "Full markdown..."
}
```

**TTL:** `NOTEBOOKLM_CACHE_TTL` (default 86400 = 24 hours)

**Cache miss flow:** Query → Parse → Cache → Return
**Cache hit flow:** Return cached result (no API call)

**Key generation:**
```python
def _cache_key(self, query_text: str) -> str:
    normalized = query_text.lower().strip()
    query_hash = hashlib.md5(normalized.encode()).hexdigest()
    return f"nlm:{query_hash}"
```

### Error Handling

**Map NotebookLM exceptions to `NotebookLMUnavailableError`:**

| SDK Exception / Signal | Reason | Notes |
|----------------------|--------|-------|
| `asyncio.TimeoutError` / operation exceeds `notebooklm_timeout` | `"timeout"` | Wrap query call with `asyncio.wait_for()` |
| HTTP 429 from SDK | `"rate_limit"` | ~50 queries/day on free tier |
| HTTP 401/403 from SDK | `"auth_error"` | Cookies expired, needs re-auth |
| `ConnectionError`, other HTTP errors | `"service_down"` | Catch-all for network/service issues |
| Any unexpected exception from SDK | `"service_down"` | Don't let unknown errors propagate unhandled |

**IMPORTANT:** Do NOT catch `NotebookLMUnavailableError` within this service. Let it propagate to the caller (search_service.py in Story 3-2) which decides the fallback strategy.

### Docker Setup Changes

**1. `api/requirements.txt` — Add dependency:**
```
notebooklm-mcp-cli>=0.3.0
```

**2. `docker-compose.dev.yml` — Mount cookie dir + env var:**
```yaml
api:
  environment:
    NOTEBOOKLM_NOTEBOOK_ID: ${NOTEBOOKLM_NOTEBOOK_ID:-}
  volumes:
    - ~/.config/notebooklm-mcp:/root/.config/notebooklm-mcp:ro  # Cookie mount
    # OR if cookies are in ~/.notebooklm-mcp-cli/:
    # - ~/.notebooklm-mcp-cli:/root/.notebooklm-mcp-cli:ro
```

**NOTE:** The exact cookie directory path depends on the version of `notebooklm-mcp-cli`. Check with `nlm --help` or inspect `~/.config/` and `~/.notebooklm-mcp-cli/` on the host to find where cookies are stored.

### Testing Requirements

**Co-locate tests:** `api/app/services/notebooklm_service_test.py`

**Use pytest with `asyncio_mode = "auto"` (already configured in project).**

**Mock the SDK client — do NOT call real NotebookLM in tests:**
```python
from unittest.mock import AsyncMock, MagicMock, patch

# Mock NotebookLMClient
@patch("app.services.notebooklm_service.NotebookLMClient")
async def test_query_returns_hs_code(mock_client_class):
    mock_client = MagicMock()
    mock_client.query.return_value = MagicMock(
        answer="The HS code for this product is **7418.20.00**...",
        conversation_id="conv-123"
    )
    mock_client_class.return_value = mock_client
    # ...
```

**Test scenarios:**

| Test | Scenario | Expected |
|------|----------|----------|
| `test_query_returns_hs_code` | SDK returns markdown with `7418.20.00` | `NotebookLMResult(hs_code="7418.20.00", ...)` |
| `test_query_no_hs_code_returns_guide` | SDK returns categorized guide (no code pattern) | `NotebookLMResult(hs_code=None, raw_answer="...")` |
| `test_query_multiple_hs_codes_uses_first` | SDK returns text with `8509.40.00` and `8501.10.00` | Uses `8509.40.00` (first match) |
| `test_query_disabled_returns_none` | `NOTEBOOKLM_ENABLED=false` | Returns `None` immediately |
| `test_query_timeout_raises_unavailable` | SDK call exceeds timeout | `NotebookLMUnavailableError(reason="timeout")` |
| `test_query_rate_limit_raises_unavailable` | SDK returns 429 | `NotebookLMUnavailableError(reason="rate_limit")` |
| `test_query_auth_error_raises_unavailable` | SDK returns 401/403 | `NotebookLMUnavailableError(reason="auth_error")` |
| `test_query_connection_error_raises_unavailable` | Network error | `NotebookLMUnavailableError(reason="service_down")` |
| `test_redis_cache_hit` | Same query within TTL | Returns cached, no SDK call |
| `test_redis_cache_miss` | Fresh query | Calls SDK, caches result |
| `test_redis_unavailable_still_works` | Redis down | Calls SDK directly, skips cache |
| `test_cache_key_normalization` | Query with spaces/caps | Same cache key for "  COPPER rack  " and "copper rack" |

### Anti-Patterns (NEVER DO)

- **NEVER** create a route handler/endpoint for NotebookLM — it's only used internally by search_service
- **NEVER** call `NotebookLMClient.query()` directly on the async event loop — use `asyncio.to_thread()`
- **NEVER** let unknown SDK exceptions propagate without wrapping in `NotebookLMUnavailableError`
- **NEVER** hardcode the notebook ID — use `settings.notebooklm_notebook_id`
- **NEVER** cache errors in Redis — only cache successful results
- **NEVER** put business logic in this service about what to do on failure — that's search_service's job (Story 3-2)
- **NEVER** import from `app.repositories` — this service doesn't do DB queries (DB validation is Story 3-2's job)
- **NEVER** create tests in a separate `/tests` directory — co-locate at `api/app/services/notebooklm_service_test.py`

### Project Structure Notes

**Files to CREATE:**
```
api/app/services/notebooklm_service.py           # NotebookLM service + parser + exceptions
api/app/services/notebooklm_service_test.py       # Tests (co-located)
```

**Files to MODIFY:**
```
api/app/core/config.py                            # Add 4 NotebookLM settings
api/requirements.txt                              # Add notebooklm-mcp-cli
docker-compose.dev.yml                            # Add cookie volume mount + env var
```

**Files that MUST NOT be modified:**
```
api/app/services/search_service.py    — Modified in Story 3-2, NOT this story
api/app/api/**                        — No route handlers needed
api/app/models/**                     — No DB model changes
api/app/schemas/**                    — No Pydantic schema changes
api/app/repositories/**               — No repository changes
web/**                                — No frontend changes
```

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Backend | FastAPI | Latest | Python 3.12+ |
| NotebookLM SDK | notebooklm-mcp-cli | >=0.3.0 | `notebooklm_tools.core.client.NotebookLMClient` |
| Cache | Redis | 7 | `redis.asyncio`, 24h TTL |
| Testing | pytest | >=8.0 | asyncio_mode="auto", unittest.mock |
| Settings | pydantic-settings | >=2.1 | `BaseSettings` |

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-15.md — Full technical context]
- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.1 — Story requirements and ACs]
- [Source: _bmad-output/planning-artifacts/architecture.md#NotebookLM-Integration — Architecture decisions]
- [Source: _bmad-output/project-context.md — Implementation rules]
- [Source: api/app/core/config.py — Settings pattern]
- [Source: api/app/services/knowledge_base_service.py — Service class pattern]
- [Source: api/app/services/embedding_service.py — Redis caching pattern]
- [Source: api/app/core/redis.py — Redis connection pattern]
- [Source: api/requirements.txt — Current dependencies]
- [Source: docker-compose.dev.yml — Docker service configuration]
- [Source: https://github.com/jacob-bd/notebooklm-mcp-cli — NotebookLM SDK docs]

## Change Log

- 2026-02-15: Implemented NotebookLM service, response parser, Redis caching, error handling, Docker setup, and 22 unit tests covering all ACs.
- 2026-02-15: Code review fixes applied - Updated AC2 to reflect deferred DB validation, added sprint-status.yaml to File List, documented alternative cookie path, added SDK import validation test, added Redis serialization round-trip test.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Fixed test mocking: `NotebookLMClient` is lazily imported inside `_call_sdk`, so tests that need to mock the SDK must mock `_get_client_class()` instead of patching the module-level import.
- Ruff lint fixes: extracted long conditional to variable, removed unused imports, shortened test string.

### Completion Notes List

- Task 1: Added 4 NotebookLM settings to `config.py` (`notebooklm_enabled`, `notebooklm_notebook_id`, `notebooklm_timeout`, `notebooklm_cache_ttl`)
- Task 2: Created `NotebookLMService` with `query()` method, regex HS code parser (`\d{4}\.\d{2}\.\d{2}`), classification/practical notes extraction, Redis caching with `nlm:{md5}` keys and configurable TTL, `NotebookLMUnavailableError` with reason classification (timeout/rate_limit/auth_error/service_down). SDK call wrapped in `asyncio.to_thread()` + `asyncio.wait_for()`.
- Task 3: Added `notebooklm-mcp-cli>=0.3.0` to requirements.txt, mounted `~/.config/notebooklm-mcp` cookie dir and `NOTEBOOKLM_NOTEBOOK_ID` env var in docker-compose.dev.yml.
- Task 4: 24 tests all passing — covers happy path, no-code guide, multiple codes, cache hit/miss, Redis down graceful fallback, timeout/rate_limit/auth_error/service_down errors, disabled service, classification extraction, practical notes extraction, no-Redis operation, SDK import validation, and Redis serialization round-trip.
- Code Review: Fixed AC2 documentation inconsistency, added sprint-status.yaml to File List, documented alternative cookie path in docker-compose, added SDK import validation test, added Redis serialization round-trip test.

### File List

- `api/app/core/config.py` (modified) — Added 4 NotebookLM settings
- `api/app/services/notebooklm_service.py` (created) — NotebookLM service, parser, exceptions
- `api/app/services/notebooklm_service_test.py` (created) — 22 tests
- `api/requirements.txt` (modified) — Added notebooklm-mcp-cli dependency
- `docker-compose.dev.yml` (modified) — Added cookie mount + env var
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified) — Updated story status to review

