# Sprint Change Proposal: NotebookLM Integration as Primary Search Engine

**Date:** 2026-02-15
**Author:** tinsu (facilitated by PM agent)
**Scope:** Moderate — New service + search pipeline modification
**Status:** Approved (2026-02-15)

---

## Section 1: Issue Summary

### Problem Statement

The AI-powered search pipeline (vector embeddings + fuzzy search + LLM reranking) has **0% accuracy** for HS code classification. All three AI approaches attempted — pure vector search, category context enrichment, and LLM query enhancement with reranking — failed to reliably match product descriptions to correct HS codes. The query enhancement and reranking features are **disabled by default** because they don't work.

The system currently relies entirely on the knowledge base (expert-verified corrections), which only covers previously-seen queries.

### Discovery Context

Testing NotebookLM (Google's Gemini 3-powered RAG system) with the Vietnam 2026 tariff schedule PDF uploaded as a source produced **100% accuracy across all test queries**:

| Query | Expected | NotebookLM | Current Pipeline |
|-------|----------|------------|-----------------|
| Copper towel rack (đồng mạ chrome) | 7418.20.00 | 7418.20.00 ✅ | ❌ Disabled |
| MDF Veneer kitchen tray | 4419.90.00 | 4419.90.00 ✅ | ❌ Would fail |
| Copper shower mixer | 8481.80.59 | 8481.80.59 ✅ | ❌ Would fail |
| Blender 500W | 8509.40.00 | 8509.40.00 ✅ | ❌ Would fail |
| Vague Chinese "电子配件" | Multiple | Categorized guide ✅ | ❌ Would guess wrong |

NotebookLM correctly handles the core classification challenges:
- **Function over material** (shower mixer → valves Ch.84, not copper Ch.74)
- **Material-based grouping** (MDF tray → wood kitchen goods 4419.90, not raw MDF)
- **Surface treatment irrelevance** (chrome plating doesn't reclassify copper items)
- **FTA optimization** (identifies manufacturer origin, suggests best FTA rate)
- **Ambiguous queries** (returns categorized guide rather than wrong single answer)

### Evidence

- Notebook ID: `5d982e32-e9a6-43a2-a469-090dd46c140c`
- Source: `Bieu thue XNK 2026 (PDF - A3).pdf` (full tariff schedule)
- NotebookLM MCP: `notebooklm-mcp-cli v0.3.2` (installed via pipx)
- Python package: `notebooklm_tools.core.client.NotebookLMClient` provides direct Python API
- CLI command: `nlm query notebook <id> "<question>"`

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Impact | Details |
|------|--------|---------|
| Epic 1: Core Search | **MINOR** | Search service orchestration modified to call new NotebookLM service |
| Epic 2: Tariff Browser | None | Browse endpoints are independent of search. |
| **NEW Epic 3: NotebookLM AI Search** | **NEW** | New epic for NotebookLM integration as primary AI search path |
| Epic 3→4: Auth & Sessions | **RENUMBERED** | Auth flow unchanged. Renumbered from 3 to 4. |
| Epic 4→5: Favorites & History | **RENUMBERED** | Renumbered from 4 to 5. |
| Epic 5→6: Advanced Search | **RENUMBERED** | Renumbered from 5 to 6. |
| Epic 6→7: Admin Data | **RENUMBERED + MINOR** | Renumbered from 6 to 7. Admin tariff upload should also update NotebookLM notebook source (future consideration). |

### Story Impact

**Existing stories affected:**

| Story | Change | Rationale |
|-------|--------|-----------|
| **1.3** (Search API) | Modified | Search service orchestration adds NotebookLM call between KB and vector search |
| **1.8** (KB Schema) | None | Schema unchanged — NotebookLM results store into same lookup_records |
| **1.9** (KB-Enhanced Search) | None | KB lookup still happens first. NotebookLM replaces the AI fallback, not the KB. |
| **1.11** (Persist Lookup Details) | None | classification_data, practical_notes, process_logs still persisted from NotebookLM responses |
| **3.1–3.5** (Auth) | Renumbered to 4.1–4.5 | Epic renumber only |
| **4.1–4.8** (Favorites/History) | Renumbered to 5.1–5.8 | Epic renumber only |
| **5.1–5.3** (Advanced Search) | Renumbered to 6.1–6.3 | Epic renumber only |
| **6.1–6.5** (Admin Data) | Renumbered to 7.1–7.5 | Epic renumber only |

**New epic required:** Epic 3 — NotebookLM AI Search (Stories 3.1, 3.2)

### Artifact Conflicts

**PRD:**
- [x] No conflict with core goals — multi-language search (FR1-3) still satisfied
- [x] Confidence scoring (FR5-6) still works — NotebookLM responses parsed for HS code, local DB provides confidence
- [x] FR43 (no results feedback) — NotebookLM handles gracefully with categorized guidance
- [x] FR44 (low-confidence suggestions) — NotebookLM provides alternative classifications
- [!] **New FR consideration:** System should display "Source: NotebookLM (Gemini)" vs "Source: Knowledge Base" in results

**Architecture:**
- [!] **New external dependency:** Google NotebookLM via `notebooklm_tools` Python package
- [!] **New service:** `api/app/services/notebooklm_service.py`
- [!] **Modified service:** `api/app/services/search_service.py` — new search path
- [!] **Auth management:** NotebookLM cookies must be maintained on the server
- [!] **Rate limits:** ~50 queries/day on free tier — KB caching essential
- [x] API response format unchanged (envelope + classification + practical_notes)
- [x] Frontend unchanged — same response shape

**UX Design:**
- [x] No UI changes needed — response format is identical
- [x] Classification reasoning is actually richer from NotebookLM

**Infrastructure:**
- [!] `notebooklm-mcp-cli` must be installed in API Docker container
- [!] NotebookLM auth cookies must be available to the container
- [!] Chrome not needed at runtime (cookies pre-authenticated), but needed for initial `nlm login`

---

## Section 3: Recommended Approach

### Selected Path: Direct Adjustment (Option 1)

Add a new Epic 3 (NotebookLM AI Search) with its own stories, and modify the search service orchestration in Epic 1. Existing Epics 3-6 renumber to 4-7. No rollback needed. No MVP scope change. This is purely additive — better AI search behind the same API.

### Architecture: Hybrid Self-Improving (Option B)

```
User Query
    │
    ▼
┌─────────────────────────────┐
│ 1. Knowledge Base Lookup    │  ← Exact hash / pg_trgm similarity
│    (verified corrections)   │     <50ms, 100% confidence
└──────────┬──────────────────┘
           │ miss
           ▼
┌─────────────────────────────┐
│ 2. Redis Cache Check        │  ← Cached NotebookLM responses
│    (24h TTL)                │     <5ms
└──────────┬──────────────────┘
           │ miss
           ▼
┌─────────────────────────────┐
│ 3. NotebookLM Query         │  ← Gemini 3 RAG on tariff PDF
│    (primary AI search)      │     5-15s, grounded in actual data
│                             │
│    Parse response → extract │
│    HS code → lookup in DB   │
│    → combine structured     │
│    data + NLM reasoning     │
│                             │
│    Auto-store in KB         │  ← Self-improving: future queries hit KB
│    Cache in Redis (24h)     │
└──────────┬──────────────────┘
           │ fail (rate limit / timeout / service down)
           ▼
┌─────────────────────────────┐
│ 4. Fallback: Vector Search  │  ← Existing hybrid search pipeline
│    + Fuzzy + LLM Reranking  │     Best-effort, lower accuracy
└─────────────────────────────┘
```

### Key Design Decisions

**1. NotebookLM Python SDK (not CLI subprocess)**
- Import `notebooklm_tools.core.client.NotebookLMClient` directly
- Call `client.query(notebook_id, query_text)` → returns `{answer, conversation_id}`
- Pure Python, no subprocess overhead, proper error handling

**2. Response Parsing Strategy**
- Extract HS code from NotebookLM markdown via regex (`\d{4}\.\d{2}\.\d{2}`)
- Look up extracted code in local PostgreSQL for structured data (exact rates, FTA rates)
- Use NotebookLM text as classification reasoning (material + function analysis)
- Combine: local structured data + NotebookLM reasoning + local practical notes

**3. Rate Limit Mitigation (~50 queries/day free tier)**
- Every NotebookLM response auto-stored in knowledge base (permanent)
- Every response cached in Redis (24h TTL)
- Similar queries (pg_trgm ≥ 0.85) hit KB directly on repeat
- Over time: KB coverage grows → fewer NotebookLM calls needed
- If rate limit hit → graceful fallback to vector search

**4. Auth Cookie Management**
- Run `nlm login` once on dev/production machine
- Cookies stored in `~/.config/notebooklm-mcp/` (configurable)
- Mount cookie directory into Docker container as volume
- Session cookies refresh ~20 min; `nlm` handles auto-refresh

### Effort Estimate

| Component | Effort | Risk |
|-----------|--------|------|
| NotebookLM service (new) | Medium | Low — Python SDK is clean |
| Response parser | Medium | Medium — regex on markdown, edge cases |
| Search pipeline modification | Low | Low — adding step between KB and vector |
| KB auto-storage integration | Low | Low — reuses existing KB recording |
| Redis caching | Low | Low — same pattern as existing caches |
| Docker setup | Low | Low — pip install + cookie volume mount |
| Tests | Medium | Low |
| **Total** | **Medium** | **Medium** |

**Timeline impact:** +1 new epic (2 stories) + renumber Epics 3-6 → 4-7. Estimated 1-2 days of development.

### Trade-offs Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **A: NotebookLM only** | Simple | No fallback, rate limit blocks users | Rejected |
| **B: Hybrid (chosen)** | Self-improving, fallback, production-ready | More complex | **Selected** |
| **C: Batch pre-fill** | Fastest runtime | Requires predicting queries, maintenance | Future enhancement |

---

## Section 4: Detailed Change Proposals

### New Epic 3: NotebookLM AI Search

```
Sprint Change Proposal: sprint-change-proposal-2026-02-15.md

NotebookLM (Google Gemini 3) provides dramatically better HS code classification
than the current vector/fuzzy/LLM pipeline (100% vs 0% accuracy). This epic adds
NotebookLM as the primary AI search path with self-improving caching through the
knowledge base.

FRs covered: FR62, FR63, FR64

Implementation Notes:
- Depends on Epic 1 completion (KB schema, KB-enhanced search, lookup storage)
- Backend-only change — no frontend modifications
- Self-improving: auto-stores results in KB, reducing NotebookLM calls over time
- Graceful fallback to vector search when NotebookLM unavailable
```

### Story 3.1: NotebookLM Service & Response Parser

```
Epic: 3 (NotebookLM AI Search)
Sprint Change Proposal: sprint-change-proposal-2026-02-15.md

As a developer,
I want a service that queries NotebookLM with product descriptions and parses
the response into structured HS code data,
So that the search pipeline can use NotebookLM as its primary AI classification engine.

Acceptance Criteria:

Given the NotebookLM service is configured with a valid notebook ID
When I call query("Thanh treo khăn bằng đồng mạ chrome")
Then the service returns {hs_code: "7418.20.00", classification: {...}, practical_notes: [...], raw_answer: "..."}
And the HS code is extracted via regex from the NotebookLM markdown response
And classification contains material and function reasoning text

Given NotebookLM returns an answer mentioning an HS code
When the response is parsed
Then the first HS code matching pattern XXXX.XX.XX is extracted
And if that code exists in our database, it is used as the result
And if that code does NOT exist in our database, the response is treated as no-match

Given NotebookLM returns a categorized guide (no single HS code)
When the response is parsed
Then the system returns the response as guidance text
And hs_code is None (indicating manual classification needed)

Given NotebookLM is unavailable (rate limit, timeout, service down)
When the service is called
Then it raises a specific exception (NotebookLMUnavailableError)
And the error includes reason (timeout/rate_limit/auth_error/service_down)

Given the service is disabled via configuration
When the service is called
Then it immediately returns None without making any API call

Technical Tasks:

1. Create service: api/app/services/notebooklm_service.py
   - NotebookLMService class wrapping notebooklm_tools.core.client
   - query(query_text) → {hs_code, classification, practical_notes, raw_answer} | None
   - Response parsing: regex HS code extraction + section splitting
   - Error handling: timeout (120s), rate limit, auth errors
   - Configuration: notebook_id, enabled flag, timeout

2. Add Redis caching for NotebookLM responses
   - Key: nlm:{md5(query.lower().strip())}
   - TTL: 24 hours (configurable)
   - Value: {hs_code, classification, practical_notes, raw_answer}

3. Add configuration to api/app/core/config.py
   - NOTEBOOKLM_ENABLED: bool = True
   - NOTEBOOKLM_NOTEBOOK_ID: str
   - NOTEBOOKLM_TIMEOUT: int = 120
   - NOTEBOOKLM_CACHE_TTL: int = 86400

4. Update Docker setup
   - Add notebooklm-mcp-cli to api/requirements.txt
   - Mount cookie directory as volume in docker-compose.dev.yml

5. Write tests
   - notebooklm_service_test.py: mock client, test parsing, test error handling, test Redis caching

Definition of Done:
- [ ] NotebookLMService created with query() method
- [ ] Response parsing extracts HS code, classification, and notes
- [ ] Redis caching prevents duplicate NotebookLM calls (24h TTL)
- [ ] Configuration flags allow enabling/disabling
- [ ] Docker setup includes notebooklm-mcp-cli and cookie volume
- [ ] Tests cover happy path, parsing edge cases, caching, and error handling

Dependency: Stories 1-8, 1-9, 1-10 must be complete.
```

### Story 3.2: Integrate NotebookLM into Search Pipeline

```
Epic: 3 (NotebookLM AI Search)
Sprint Change Proposal: sprint-change-proposal-2026-02-15.md

As a user,
I want my searches to be classified by NotebookLM (Gemini 3) using the official tariff document,
So that I get accurate HS code classifications grounded in the actual Vietnam 2026 tariff schedule.

Acceptance Criteria:

Given no KB match exists for a query
When I search for "Thanh treo khăn bằng đồng mạ chrome"
Then NotebookLM is queried with the tariff notebook
And the HS code is looked up in the local database for structured rates
And classification reasoning from NotebookLM is included in the response
And the result is stored in the knowledge base (is_verified=false)
And the result is cached in Redis (24h TTL)
And source="notebooklm" in the response

Given a previous NotebookLM query is cached in Redis
When I search with the same query within 24 hours
Then the cached response is returned immediately
And source="cache" in the response
And no NotebookLM API call is made

Given NotebookLM is unavailable (rate limit, timeout, service down)
When I search for a product description
Then the system falls back to vector/fuzzy search
And process_logs include "NotebookLM unavailable, falling back to vector search"

Given NotebookLM returns a categorized guide (no single HS code)
When the result is processed
Then the system returns the guidance text as classification
And confidence is set to 0 (indicating manual classification needed)

Technical Tasks:

1. Modify service: api/app/services/search_service.py
   - Add NotebookLM step between KB lookup and vector search
   - On NotebookLM success: look up HS code in local DB, combine data
   - On NotebookLM failure: fall back to existing vector/fuzzy pipeline
   - Auto-store result in lookup_records (knowledge base)

2. Write integration tests
   - search_service integration test: verify NotebookLM → DB lookup → KB storage flow
   - search_service fallback test: verify vector search fallback on NotebookLM failure

Definition of Done:
- [ ] Search pipeline uses NotebookLM between KB and vector search
- [ ] NotebookLM results combined with local DB data (rates, descriptions)
- [ ] Results auto-stored in knowledge base (is_verified=false)
- [ ] Fallback to vector search when NotebookLM unavailable
- [ ] Process logs include NotebookLM step status
- [ ] Integration tests pass for happy path and fallback

Dependency: Story 3-1 must be complete.
```

### Modified Story: 1.3 (Search API — search_service.py changes)

```
Section: Search Pipeline Orchestration
File: api/app/services/search_service.py

OLD (current pipeline):
  1. Knowledge Base exact match
  2. Knowledge Base similar match
  3. Vector + Fuzzy hybrid search
  4. Optional LLM reranking
  5. Classification analysis

NEW (with NotebookLM — implemented in Story 3.2):
  1. Knowledge Base exact match
  2. Knowledge Base similar match
  3. Redis cache check (NotebookLM cached responses)
  4. NotebookLM query (primary AI search)  ← NEW (Epic 3)
  5. Vector + Fuzzy hybrid search (fallback) ← DEMOTED to fallback
  6. Optional LLM reranking (on vector results only)
  7. Classification analysis (skip if NotebookLM provided reasoning)

Rationale: NotebookLM provides superior classification with built-in
reasoning, making vector search a fallback rather than the primary path.
```

### Architecture Document Updates

```
File: _bmad-output/planning-artifacts/architecture.md

Section: Search & Embedding Architecture

ADD after "Search Flow" subsection:

### NotebookLM Integration (Sprint Change 2026-02-15)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **AI Search Provider** | Google NotebookLM (Gemini 3) | 100% accuracy on test queries vs 0% for vector/LLM |
| **Integration Method** | Python SDK (notebooklm_tools) | Direct import, no subprocess overhead |
| **Caching** | Redis 24h + permanent KB storage | Rate limit mitigation (~50/day free tier) |
| **Fallback** | Vector + fuzzy search | Graceful degradation if NotebookLM unavailable |

**New External Dependency:**
| Service | Purpose | Configuration |
|---------|---------|---------------|
| NotebookLM | AI-powered tariff classification | `NOTEBOOKLM_NOTEBOOK_ID`, auth cookies |

**Updated Search Flow:**
1. KB exact hash match (<5ms)
2. KB similar match (pg_trgm ≥0.85, <50ms)
3. Redis cache for NotebookLM responses (<5ms)
4. NotebookLM query via Gemini 3 (5-15s)
5. Parse response → extract HS code → DB lookup for structured data
6. Auto-store in KB + Redis cache
7. Fallback: vector + fuzzy search if NotebookLM fails

Section: Project Structure

ADD to api/app/services/:
  ├── notebooklm_service.py          # NotebookLM integration (Sprint Change 2026-02-15)
  ├── notebooklm_service_test.py
```

### PRD Updates

```
File: _bmad-output/planning-artifacts/prd.md

Section: 9. Functional Requirements → HS Code Search

ADD:
- **FR62:** System queries NotebookLM (Gemini 3) for novel product descriptions
  not found in the knowledge base, using the official tariff PDF as grounding source
- **FR63:** NotebookLM classification results are automatically stored in the
  knowledge base for future instant retrieval
- **FR64:** System falls back to vector/fuzzy search when NotebookLM is unavailable
  (rate limit, timeout, or service outage)

Section: 7. Technical Requirements → Search Engine Requirements

ADD row to table:
| **NotebookLM Integration** | Google NotebookLM via notebooklm_tools Python SDK |
| **Grounding Source** | Official Vietnam 2026 tariff PDF uploaded to NotebookLM |
| **Rate Limit Strategy** | KB auto-storage + Redis cache to minimize API calls |
```

### Epics Document Updates

```
File: _bmad-output/planning-artifacts/epics.md

STRUCTURAL CHANGES:
- Add NEW Epic 3: NotebookLM AI Search (Stories 3.1, 3.2)
- Renumber Epic 3 (Auth & Sessions) → Epic 4 (Stories 3.1-3.5 → 4.1-4.5)
- Renumber Epic 4 (Favorites & History) → Epic 5 (Stories 4.1-4.8 → 5.1-5.8)
- Renumber Epic 5 (Advanced Search) → Epic 6 (Stories 5.1-5.3 → 6.1-6.3)
- Renumber Epic 6 (Admin Data) → Epic 7 (Stories 6.1-6.5 → 7.1-7.5)

NEW Epic 3 entry in Epic List:

### Epic 3: NotebookLM AI Search (ADDED 2026-02-15)
NotebookLM (Google Gemini 3) replaces the failed vector/LLM pipeline as
the primary AI search path. Responses are parsed for HS codes, combined with
local DB data, and auto-stored in the knowledge base for self-improving accuracy.

**FRs covered:** FR62, FR63, FR64

**Implementation Notes:**
- **Sprint Change Proposal:** `sprint-change-proposal-2026-02-15.md`
- Story 3-1: NotebookLM service, response parser, Redis caching, Docker setup
- Story 3-2: Search pipeline integration, KB auto-storage, fallback chain
- 100% accuracy in testing vs 0% for vector/LLM pipeline
- Self-improving: auto-stores in KB, future similar queries skip NotebookLM

Section: FR Coverage Map

ADD:
| FR62 | Epic 3 | NotebookLM query for novel descriptions |
| FR63 | Epic 3 | Auto-store NotebookLM results in KB |
| FR64 | Epic 3 | Fallback to vector search |

UPDATE all FR references for renumbered epics:
| FR30-FR35 | Epic 3 → Epic 4 |
| FR19-FR29 | Epic 4 → Epic 5 |
| FR9, FR44, FR45 | Epic 5 → Epic 6 |
| FR36-FR42 | Epic 6 → Epic 7 |

Update header:
totalEpics: 7  # Added Epic 3 (NotebookLM), renumbered Epics 3-6 → 4-7
totalStories: 39  # Added Stories 3-1, 3-2 (NotebookLM, Sprint Change 2026-02-15)
frCoverage: '64/64 (100%)'  # Added FR62-FR64 (2026-02-15)
```

---

## Section 5: Implementation Handoff

### Scope Classification: **Moderate**

New epic (2 stories) + pipeline modification + epic renumbering, but no architectural overhaul. Backend-only change. No frontend impact.

### Handoff

| Responsibility | Role | Action |
|---------------|------|--------|
| Implement Story 3.1 | Developer | Create `notebooklm_service.py`, response parser, Redis caching, Docker setup, tests |
| Implement Story 3.2 | Developer | Update `search_service.py` with NotebookLM step, KB auto-storage, fallback, tests |
| Update planning artifacts | PM (this session) | Update PRD, epics (new Epic 3 + renumber 3-6→4-7), architecture docs |
| NotebookLM auth setup | Developer/Admin | Run `nlm login` on production machine |
| Monitor rate limits | Admin | Track daily NotebookLM query count, upgrade if needed |

### Success Criteria

- [ ] Novel queries return correct HS codes via NotebookLM (target: >80% accuracy)
- [ ] Repeat queries hit knowledge base directly (<50ms)
- [ ] Rate limit does not block users (fallback to vector search works)
- [ ] No frontend changes required
- [ ] All existing tests continue to pass

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| NotebookLM rate limit (50/day) | Users get lower-quality fallback results | KB auto-storage reduces novel queries over time; upgrade to paid tier if needed |
| NotebookLM service outage | Temporary degradation | Graceful fallback to vector search with clear process_log entry |
| Cookie auth expiration | Service interruption | Auto-refresh via notebooklm_tools; monitoring alert if auth fails |
| Response parsing fails | Wrong HS code extracted | Regex validation + DB lookup confirmation; if code not in DB, treat as no-match |
| Google detects automation | Account suspension | Use dedicated Google account; respect rate limits |

---

## Appendix: NotebookLM Response Quality Evidence

### Query 1: Copper towel rack
**Input:** "Thanh treo khăn MITO, mã A2018ANE, bằng đồng mạ chrome, kích thước 33,5x8cm, nhà sản xuất INDA S.p.a, hàng mới 100%"
**Result:** HS 7418.20.00 — correctly classified as copper bathroom fittings (chrome plating doesn't change base material classification). Identified manufacturer as Italian, recommended EVFTA C/O for 3.7% vs 30% MFN rate.

### Query 2: MDF kitchen tray
**Input:** "Khay chia bát đĩa, gỗ MDF phủ Veneer"
**Result:** HS 4419.90.00 — correctly classified as wood kitchen goods (not raw MDF board). Noted MDF as industrial wood, not tropical, therefore "Loại khác" subheading.

### Query 3: Blender
**Input:** "máy xay sinh tố gia đình 500W"
**Result:** HS 8509.40.00 — correctly classified as household food grinder/mixer. Referenced Chapter 85 Note 4(a) for classification rule. Even provided separate motor classification if imported as parts.

### Query 4: Vague Chinese
**Input:** "电子配件 (electronic accessories)"
**Result:** Comprehensive categorized guide across Ch.84-85 with 6 sub-categories, specific HS codes per category, and relevant chapter notes. No hallucinated single answer.
