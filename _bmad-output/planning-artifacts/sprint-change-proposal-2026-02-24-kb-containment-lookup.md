# Sprint Change Proposal: KB Containment Lookup

**Date:** 2026-02-24
**Triggered by:** Customs-imported records not findable via partial search queries
**Scope:** Minor — Direct implementation by development team
**Affected Story:** Story 1-9 (Knowledge-Enhanced Search)

---

## Section 1: Issue Summary

### Problem Statement
The knowledge base lookup (`kb_exact_lookup`) fails to match customs-imported records when users search with partial product descriptions. Records imported via Epic 9 (Customs Data Ingestion) are stored with full product descriptions (e.g., "Vỏ hộp chính, bằng nhựa PC, kích thước 400.2*396mm. Hàng mới 100%. (920.0038701)"), but users naturally search with shorter queries (e.g., "Vỏ hộp chính, bằng nhựa PC").

### Discovery Context
Discovered immediately after completing Epic 9 customs bulk import. After importing verified customs records, partial-text searches that should match imported descriptions fall through to full AI search (NotebookLM), defeating the purpose of the knowledge base.

### Evidence
- **Imported record:** "Vỏ hộp chính, bằng nhựa PC, kích thước 400.2*396mm. Hàng mới 100%. (920.0038701)" (verified, `search_method="customs_import"`)
- **Search query:** "Vỏ hộp chính, bằng nhựa PC"
- **Result:** "No KB match found, falling back to AI search" after 153ms
- **Root cause:** SHA-256 exact hash fails (different strings → different hashes). pg_trgm similarity scores ~0.3-0.5 for short-vs-long text, well below 0.85 threshold.

---

## Section 2: Impact Analysis

### Epic Impact
| Epic | Impact | Details |
|------|--------|---------|
| Epic 1: Core HS Search | **Direct** | Story 1-9 needs containment matching step added to KB lookup |
| Epic 9: Customs Ingestion | **Indirect** | Import works correctly; fix is on retrieval side |
| All other epics | None | No dependencies affected |

### Story Impact
- **Story 1-9** (Knowledge-Enhanced Search, status: `review`): Requires enhancement — add containment match step between existing exact hash and pg_trgm similarity steps.
- No future stories require changes.

### Artifact Conflicts
- **Architecture doc**: Search pipeline description needs minor update (2-tier → 3-tier KB matching)
- **PRD**: No conflicts — FR74-77 state imported records should be "immediately searchable"; this fix fulfills that intent
- **UI/UX**: No impact — purely backend change, same response format

### Technical Impact
- 2 files modified: `knowledge_base_service.py`, `lookup_record_repository.py`
- Test files updated for new matching step
- No schema migration needed
- No new dependencies
- Existing GIN trgm index on `query_text` may support `LIKE` queries; if not, a new index can be added

---

## Section 3: Recommended Approach

### Selected: Option 1 — Direct Adjustment

Add a **containment matching step** to `KnowledgeBaseService.lookup()` between the existing exact hash match (Step 1) and pg_trgm similarity match (Step 2).

**New 3-tier KB lookup pipeline:**
1. **Exact hash match** (<5ms) — unchanged, confidence 100%
2. **Containment match** (new, <50ms) — `WHERE lower(query_text) LIKE '%' || lower(:query) || '%'`, confidence 95%, prefer shortest matching record
3. **Fuzzy similar match** (<50ms) — unchanged, pg_trgm ≥ 0.85

### Rationale
- **Low effort**: ~50 lines of code across 2 files
- **Low risk**: Purely additive — existing exact hash and pg_trgm paths remain untouched
- **High value**: Unlocks the full value of Epic 9 customs imports and any long-description KB records
- **No timeline impact**: Fits within current sprint, Story 1-9 is already in review
- Alternatives considered:
  - Lowering pg_trgm threshold (rejected: still penalizes length differences, may introduce false positives)
  - Embedding-based KB search (rejected: over-engineered for this use case)
  - Storing multiple query variants (rejected: adds complexity to import pipeline)

---

## Section 4: Detailed Change Proposals

### Change 1: Repository — Add `find_verified_containment()` method

**File:** `api/app/repositories/lookup_record_repository.py`
**Section:** After `find_verified_similar()` method

**ADD** (new method):
```python
async def find_verified_containment(
    self,
    query_text: str,
    limit: int = 1,
) -> list[tuple[LookupRecord, float]]:
    """Find verified lookup records where query_text contains the search query.

    Useful for matching short user queries against long customs-imported descriptions.
    Returns list of (record, confidence_score) tuples ordered by query_text length ASC
    (prefer shortest/most specific match).
    """
    normalized_query = query_text.strip().lower()
    if len(normalized_query) < 4:
        return []  # Avoid overly broad containment matches

    result = await self.session.execute(
        select(LookupRecord, func.length(LookupRecord.query_text).label("text_len"))
        .where(
            LookupRecord.is_verified == True,  # noqa: E712
            LookupRecord.correct_hs_code_id.isnot(None),
            func.lower(LookupRecord.query_text).contains(normalized_query),
        )
        .order_by(func.length(LookupRecord.query_text).asc())
        .limit(limit)
    )
    rows = result.all()
    return [(row.LookupRecord, 0.95) for row in rows]
```

**Rationale:** Uses SQL `LIKE '%query%'` (via SQLAlchemy `contains()`) to find verified records whose stored description contains the user's search text. Orders by length ASC to prefer the most specific (shortest) match. Minimum 4-char query prevents overly broad matches.

---

### Change 2: Service — Add containment step to `lookup()` pipeline

**File:** `api/app/services/knowledge_base_service.py`
**Section:** `lookup()` method, between Step 1 (exact hash) and Step 2 (similar text)

**OLD:**
```python
        # Step 2: Similar text match (pg_trgm, <50ms)
        similar = await self.repo.find_verified_similar(query, threshold=0.85)
```

**NEW:**
```python
        # Step 2: Containment match — short query found within long KB description (<50ms)
        containment = await self.repo.find_verified_containment(query)
        if containment:
            record, conf_score = containment[0]
            return KBLookupResult(
                hs_code_id=record.correct_hs_code_id,
                confidence=int(conf_score * 100),
                similarity_score=conf_score,
                lookup_record_id=record.id,
                verified_by_user_id=record.verified_by_user_id,
                verified_at=record.verified_at,
                match_type="containment",
            )

        # Step 3: Similar text match (pg_trgm, <50ms)
        similar = await self.repo.find_verified_similar(query, threshold=0.85)
```

**Rationale:** Inserts containment matching as Step 2 (renumbering pg_trgm to Step 3). Returns 95% confidence for containment matches since the verified record literally contains the search text. match_type="containment" enables distinct observability in process logs.

---

### Change 3: Service docstring update

**File:** `api/app/services/knowledge_base_service.py`
**Section:** `KnowledgeBaseService` class docstring

**OLD:**
```python
    """Service for looking up verified HS codes from the knowledge base.

    Checks verified expert corrections before falling back to AI search.
    Priority: exact hash match -> pg_trgm similar match -> None (caller falls back to AI).
    """
```

**NEW:**
```python
    """Service for looking up verified HS codes from the knowledge base.

    Checks verified expert corrections before falling back to AI search.
    Priority: exact hash match -> containment match -> pg_trgm similar match -> None (caller falls back to AI).
    """
```

---

### Change 4: Tests for containment matching

**File:** `api/app/services/knowledge_base_service_test.py` (or co-located test file)

**ADD** test cases:
- `test_lookup_containment_match_partial_query` — short query contained in long KB record returns match_type="containment", confidence=95
- `test_lookup_containment_match_prefers_shortest` — multiple matching records, shortest is returned first
- `test_lookup_containment_skip_very_short_query` — query < 4 chars skips containment, falls to pg_trgm
- `test_lookup_containment_case_insensitive` — mixed-case query matches lowercase stored text

**File:** `api/app/repositories/lookup_record_repository_test.py` (or co-located test file)

**ADD** test cases:
- `test_find_verified_containment_basic` — returns record when query is substring of query_text
- `test_find_verified_containment_ignores_unverified` — unverified records not returned
- `test_find_verified_containment_min_length` — queries < 4 chars return empty list

---

## Section 5: Implementation Handoff

### Scope Classification: Minor

This is a targeted code fix within an existing story (1-9) that is already in review status.

### Handoff: Development Team

| Responsibility | Owner | Action |
|---------------|-------|--------|
| Implement containment match | Dev | Add repository method + service step (Changes 1-3) |
| Write tests | Dev | Add test cases (Change 4) |
| Verify fix | Dev | Test with the imported customs record that triggered this issue |
| Code review | Dev | Run existing code-review workflow on updated Story 1-9 |
| Architecture doc | Dev | Update search pipeline description (minor) |

### Success Criteria
- Searching "Vỏ hộp chính, bằng nhựa PC" returns the customs-imported KB record with confidence=95, match_type="containment"
- Existing exact hash and pg_trgm matching paths still work unchanged
- All existing tests continue to pass
- New containment tests pass
- Process logs show "containment" match type for observability
