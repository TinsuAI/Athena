# Plan: Improve HS Code Search Accuracy

## Problem Statement

The HS code search returns incorrect results. Example:
- **Query:** "Đầu bịt tay nắm dùng cho hộc tủ, bằng nhôm mạ chrome" (furniture drawer handle end cap)
- **Got:** 8716.90.13 (trailer parts) - 45% match
- **Expected:** 8302.42.90 (furniture fittings from base metal)

### Root Cause
1. Vector embeddings only use short Vietnamese tariff descriptions
2. 60% vector weight dominates - semantic mismatch pulls wrong results
3. No understanding of HS classification rules (material vs function precedence)

## Solution: Three-Pronged Approach

```
User Query
    ↓
┌─────────────────────────────────────────┐
│  1. LLM QUERY ENHANCEMENT               │
│  Extract: material, function, category  │
│  Generate: enhanced search query        │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  2. IMPROVED EMBEDDINGS                 │
│  Richer context: desc + chapter + notes │
│  Better semantic matching               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  3. LLM RE-RANKING                      │
│  Top 10 results → LLM picks best match  │
│  Applies HS classification rules (GRI)  │
└─────────────────────────────────────────┘
    ↓
Best HS Code Match
```

---

## Phase 1: LLM Query Enhancement

### 1.1 Create `QueryEnhancementService`

**File:** `api/app/services/query_enhancement_service.py`

```python
class QueryEnhancementService:
    """Extracts classification features from product descriptions."""

    async def enhance_query(self, query: str) -> EnhancedQuery:
        """
        Returns:
            EnhancedQuery with:
            - material: "nhôm mạ chrome" → "aluminum, chrome-plated, base metal"
            - function: "đầu bịt tay nắm" → "handle end cap, furniture fitting"
            - category: "hộc tủ" → "furniture, cabinet, interior"
            - enhanced_query: combined search-optimized text
        """
```

### 1.2 LLM Prompt for Query Enhancement

```python
QUERY_ENHANCEMENT_PROMPT = """Analyze this product for HS classification:

Product: {query}

Extract and translate to Vietnamese+English keywords:
1. Material (vật liệu): What is it made of?
2. Function (chức năng): What does it do?
3. Category (danh mục): What product category? (furniture/machinery/vehicle/etc.)
4. Key HS chapters likely relevant

Return JSON:
{
  "material_keywords": ["nhôm", "aluminum", "kim loại cơ bản", "base metal"],
  "function_keywords": ["đầu bịt", "end cap", "phụ kiện nội thất", "furniture fitting"],
  "category": "furniture_fittings",
  "likely_chapters": ["83", "76"],
  "enhanced_query": "phụ kiện nội thất bằng nhôm đầu bịt tay nắm furniture fittings aluminum handle end cap"
}"""
```

---

## Phase 2: Improve Embeddings

### 2.1 Modify Embedding Generation Script

**File:** `api/app/scripts/generate_embeddings.py`

Change from:
```python
# Current: Only description_vn
text = code.description_vn
```

To:
```python
# New: Rich context embedding
text = build_embedding_text(code)

def build_embedding_text(code: HSCode) -> str:
    parts = []

    # Add chapter context
    if code.subheading and code.subheading.heading:
        heading = code.subheading.heading
        if heading.chapter:
            parts.append(f"Chương {heading.chapter.code}: {heading.chapter.name_vn}")
        parts.append(f"Nhóm {heading.code}: {heading.name_vn}")

    # Add descriptions (both languages)
    parts.append(code.description_vn)
    if code.description_en:
        parts.append(code.description_en)

    # Add policy notes if relevant
    if code.policy_notes:
        parts.append(code.policy_notes[:200])

    return " | ".join(parts)
```

### 2.2 Re-generate All Embeddings

```bash
# After code changes, run:
python -m app.scripts.generate_embeddings --force-regenerate
```

---

## Phase 3: LLM Re-ranking

### 3.1 Create `RerankingService`

**File:** `api/app/services/reranking_service.py`

```python
class RerankingService:
    """Re-ranks search results using LLM with HS classification knowledge."""

    async def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        top_k: int = 1
    ) -> list[SearchResult]:
        """
        Takes top 10 search results, asks LLM to pick best match.
        Returns reordered list with best match first.
        """
```

### 3.2 LLM Prompt for Re-ranking

```python
RERANKING_PROMPT = """Bạn là chuyên gia phân loại hải quan Việt Nam.

Sản phẩm cần phân loại: {query}

Các mã HS ứng viên:
{candidates}

Quy tắc phân loại (GRI):
1. Phân loại theo mô tả cụ thể nhất
2. Hàng hỗn hợp: theo thành phần tạo đặc tính chủ yếu
3. Phụ kiện nội thất kim loại → Chương 83 (không phải chương kim loại)
4. Phụ tùng xe → Chương 87 (chỉ khi thực sự dùng cho xe)

Chọn mã HS phù hợp nhất. Trả về JSON:
{
  "best_match": "8302.42.90",
  "confidence": 85,
  "reasoning": "Sản phẩm là phụ kiện nội thất (đầu bịt tay nắm tủ), không phải phụ tùng xe..."
}"""
```

---

## Phase 4: Integration

### 4.1 Update Search Flow

**File:** `api/app/api/search.py`

```python
@router.post("/search")
async def search_hs_codes(...):
    # 1. Enhance query (if LLM available)
    if query_enhancer:
        enhanced = await query_enhancer.enhance_query(body.query)
        search_query = enhanced.enhanced_query
    else:
        search_query = body.query

    # 2. Perform search (with improved embeddings)
    results = await search_service.search(query=search_query, limit=10)

    # 3. Re-rank results (if LLM available)
    if reranker and len(results) > 1:
        results = await reranker.rerank(body.query, results)

    # 4. Return best result with classification reasoning
    best_result = results[0]
    ...
```

### 4.2 Add Feature Flag

**File:** `api/app/core/config.py`

```python
class Settings(BaseSettings):
    # Existing
    openrouter_api_key: str = ""
    llm_reasoning_model: str = "openai/gpt-4o-mini"

    # New
    enable_query_enhancement: bool = True
    enable_reranking: bool = True
    reranking_candidates: int = 10
```

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `api/app/services/query_enhancement_service.py` | Create | LLM query enhancement |
| `api/app/services/reranking_service.py` | Create | LLM re-ranking service |
| `api/app/scripts/generate_embeddings.py` | Modify | Richer embedding context |
| `api/app/api/search.py` | Modify | Integrate enhancement + reranking |
| `api/app/core/config.py` | Modify | Add feature flags |

---

## Implementation Task List

### Task 0: Fix LLM Service (PREREQUISITE)
**Priority:** Critical - blocks all other tasks
**File:** `api/app/services/llm_reasoning_service.py`

- [ ] 0.1 Test OpenRouter API directly with curl:
  ```bash
  curl -X POST https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": "Hello"}]}'
  ```
- [ ] 0.2 Log full HTTP response body (not just status code) in `_generate_with_retry()`
- [ ] 0.3 Check if API key is being read correctly from environment
- [ ] 0.4 Verify model name format is correct for OpenRouter
- [ ] 0.5 Test with a different model (e.g., `anthropic/claude-3-haiku`)
- [ ] 0.6 Add error handling for rate limits and quota exceeded

---

### Task 1: Create Re-ranking Service
**Priority:** High - fastest impact on accuracy
**New File:** `api/app/services/reranking_service.py`

- [ ] 1.1 Create `RerankingService` class with Redis caching
- [ ] 1.2 Implement `rerank(query, candidates, top_k)` async method
- [ ] 1.3 Design re-ranking prompt with GRI rules (see Phase 3 above)
- [ ] 1.4 Parse LLM response to extract best match and reasoning
- [ ] 1.5 Handle fallback when LLM fails (return original order)
- [ ] 1.6 Add cache key: hash of (query + sorted candidate codes)
- [ ] 1.7 Write unit tests for reranking logic

---

### Task 2: Create Query Enhancement Service
**Priority:** Medium - improves embedding match quality
**New File:** `api/app/services/query_enhancement_service.py`

- [ ] 2.1 Create `QueryEnhancementService` class with Redis caching
- [ ] 2.2 Create `EnhancedQuery` dataclass with fields:
  - `material_keywords: list[str]`
  - `function_keywords: list[str]`
  - `category: str`
  - `likely_chapters: list[str]`
  - `enhanced_query: str`
- [ ] 2.3 Implement `enhance_query(query)` async method
- [ ] 2.4 Design enhancement prompt (see Phase 1 above)
- [ ] 2.5 Parse LLM response to EnhancedQuery
- [ ] 2.6 Handle fallback (return original query unchanged)
- [ ] 2.7 Write unit tests

---

### Task 3: Integrate Services into Search API
**Priority:** High - connects new services
**File:** `api/app/api/search.py`

- [ ] 3.1 Import new services
- [ ] 3.2 Create service instances conditionally (if API key available)
- [ ] 3.3 Call query enhancement before search
- [ ] 3.4 Pass enhanced query to search service
- [ ] 3.5 Get top 10 results instead of just 1
- [ ] 3.6 Call reranking service on results
- [ ] 3.7 Return best reranked result
- [ ] 3.8 Update classification reasoning to use reranking reasoning

---

### Task 4: Add Configuration Options
**Priority:** Low - nice to have
**File:** `api/app/core/config.py`

- [ ] 4.1 Add `enable_query_enhancement: bool = True`
- [ ] 4.2 Add `enable_reranking: bool = True`
- [ ] 4.3 Add `reranking_candidates: int = 10`
- [ ] 4.4 Document new environment variables

---

### Task 5: Improve Embedding Generation
**Priority:** Medium - longer task, can be done in parallel
**File:** `api/app/scripts/generate_embeddings.py`

- [ ] 5.1 Create `build_embedding_text(code: HSCode)` function
- [ ] 5.2 Include chapter name in embedding text
- [ ] 5.3 Include heading name in embedding text
- [ ] 5.4 Include both Vietnamese AND English descriptions
- [ ] 5.5 Include policy_notes (truncated to 200 chars)
- [ ] 5.6 Add `--force-regenerate` flag to script
- [ ] 5.7 Test with sample codes before full regeneration
- [ ] 5.8 Run full regeneration (may take hours for large dataset)

---

### Task 6: Testing & Validation
**Priority:** High - verify improvements

- [ ] 6.1 Test furniture fittings query → expect 8302.42.90
- [ ] 6.2 Test plumbing fixtures query → expect 8481.80.xx
- [ ] 6.3 Test material-based query → expect correct chapter
- [ ] 6.4 Measure latency (target: <3s total)
- [ ] 6.5 Test cache hits (second search should be faster)
- [ ] 6.6 Test fallback when LLM unavailable

---

## Verification

### Test Cases

1. **Furniture fittings:**
   - Query: "Đầu bịt tay nắm dùng cho hộc tủ, bằng nhôm mạ chrome"
   - Expected: 8302.42.90 (NOT 8716.90.13)

2. **Plumbing fixtures:**
   - Query: "Vòi lavabo bằng đồng mạ chrome"
   - Expected: 8481.80.xx (valves) NOT 7418.xx (copper articles)

3. **Materials properly classified:**
   - Query: "Dây đồng nguyên chất"
   - Expected: 7408.xx (copper wire)

### Performance

- Query enhancement: +500ms (cached after first call)
- Re-ranking: +1-2s (LLM call)
- Total acceptable latency: <3s for better accuracy

---

## Caching Strategy

- **Query enhancement:** Cache by query hash (24h TTL)
- **Re-ranking:** Cache by (query + candidate codes) hash (24h TTL)
- Improves latency for repeated searches

---

## Implementation Notes for Developers

### Service Pattern
All new services should follow the pattern in `llm_reasoning_service.py`:
- Accept `redis_client` for caching
- Accept optional `model` parameter
- Use `httpx.AsyncClient` for HTTP calls
- Implement retry logic with exponential backoff
- Cache results with appropriate TTL

### Error Handling
- All LLM calls should have fallback behavior
- If query enhancement fails → use original query
- If reranking fails → use original search order
- Log errors but don't fail the request

### Testing Commands
```bash
# Run API tests
cd api && source .venv/bin/activate
pytest app/services/ -v

# Test search manually
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Đầu bịt tay nắm dùng cho hộc tủ, bằng nhôm mạ chrome"}'

# Regenerate embeddings
python -m app.scripts.generate_embeddings --force-regenerate
```

### Key Files Reference
| File | Purpose |
|------|---------|
| `api/app/services/llm_reasoning_service.py` | Existing LLM service (reference pattern) |
| `api/app/services/embedding_service.py` | Embedding generation (reference pattern) |
| `api/app/repositories/search_repository.py` | Search queries (vector + fuzzy) |
| `api/app/services/search_service.py` | Search orchestration |
| `api/app/api/search.py` | API endpoint |
