# Sprint Change Proposal

**Project:** Athena - HS Code Lookup Tool
**Date:** 2026-02-02
**Author:** tinsu (via Correct Course workflow)
**Status:** Pending Approval

---

## Section 1: Issue Summary

### Problem Statement

The HS code search functionality returns **0% accuracy** across 100 test queries. The system is functionally complete (Stories 1-3, 1-4 done) but fails to return correct HS codes for product descriptions.

### Context

- **Discovered during:** Testing of Story 1-3 (Search API) and Story 1-4 (Search UI)
- **Trigger:** User testing revealed search results were consistently incorrect
- **Evidence collected:**
  - 100 searches performed, 0 returned correct HS codes
  - ~33% wrong chapter entirely (e.g., copper fixture classified as valve instead of sanitary ware)
  - ~33% right chapter but wrong subheading (e.g., MDF classified as bamboo)
  - ~33% close but not exact match

### Root Cause Analysis

**Primary Cause:** The `TariffHierarchyParser` (tariff import script) skips category indicator rows from the Vietnam Customs Excel file.

**Technical Details:**

The Excel file contains hierarchical category indicators like:

```
4419    Bộ đồ ăn và bộ đồ làm bếp, bằng gỗ  (Heading)
        - Từ tre:                            ← CATEGORY INDICATOR (no code)
        - - 4419.11.00 Thớt cắt bánh mì...
        - - 4419.12.00 Đũa
        - - 4419.19.00 Loại khác             ← "Other BAMBOO"
        - Từ gỗ nhiệt đới
        - - 4419.20.00
        - Loại khác
        - - 4419.90.00                       ← "Other WOOD (not bamboo)"
```

The parser code at line 327 skips rows without 8-digit codes:

```python
if code_val is None:
    continue  # Skips "- Từ tre:" category rows!
```

**Result:** The database stores both `4419.19.00` and `4419.90.00` with description "Loại khác" (Other), losing the crucial context that one is "Other bamboo" and one is "Other wood in general".

**Impact on LLM:** The reranking LLM cannot distinguish between codes when their descriptions are identical. It sees two "Loại khác" options with no context about which applies to bamboo vs other materials.

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Status | Impact |
|------|--------|--------|
| **Epic 1: Core Search** | In Progress | Stories 1-3, 1-4 done but need validation after fix. Stories 1-5 to 1-7 blocked until fix complete. |
| **Epic 2: Auth** | Backlog | No impact - independent of search accuracy |
| **Epic 3: Favorites/History** | Backlog | No impact - depends on working search, which fix enables |
| **Epic 4: Advanced Search** | Backlog | No impact |
| **Epic 5: Admin Data** | Backlog | Minor impact - import script changes benefit future data updates |

### Story Impact

| Story | Current Status | Impact |
|-------|----------------|--------|
| 1-1 | Done | No change needed |
| 1-2 | Done | No change needed - schema is correct |
| 1-3 | Done | **Needs re-validation** after data fix |
| 1-4 | Review | **Needs re-validation** after data fix |
| 1-5 to 1-7 | Backlog | **Blocked** - should not proceed until accuracy is fixed |

### Artifact Conflicts

| Artifact | Conflict? | Details |
|----------|-----------|---------|
| **PRD** | No | PRD specifies 80% accuracy (FR5, FR6). Fix enables this target. No PRD changes needed. |
| **Architecture** | Minor | Should document category context requirement in data model section. Non-blocking. |
| **UX Design** | No | UI displays search results correctly. Issue is data quality, not display. |
| **Epics & Stories** | Yes | Need to add new story (1-2.1) for the fix. |

### Technical Impact

| Component | Impact |
|-----------|--------|
| `tariff_hierarchy_parser.py` | **Modify** - Track category context, append to child codes |
| `generate_embeddings.py` | **Minor update** - May need to include category in embedding text |
| Database | **Re-import** - All HS codes need re-import with category context |
| Embeddings | **Regenerate** - All 11,871 HS code embeddings need regeneration |
| Redis Cache | **Clear** - Search and reranking caches must be cleared |

---

## Section 3: Recommended Approach

### Selected Path: Direct Adjustment

**Rationale:**

1. **Root cause is clearly identified** - Missing category context in import
2. **Fix is localized** - Only 2 files need modification
3. **No architectural changes required** - Data model is correct, just data quality issue
4. **Low risk** - Improving data quality, not changing search logic
5. **Bounded effort** - 1-2 days of development + testing
6. **Enables PRD target** - 80% accuracy becomes achievable

### Alternatives Considered

| Alternative | Why Not Selected |
|-------------|------------------|
| **Rollback stories** | Nothing to roll back - code is correct, data is the issue |
| **Reduce MVP scope** | Unnecessary - fix is straightforward and enables full MVP |
| **Train custom AI model** | Overkill - the issue is missing data context, not AI capability |
| **Manual lookup table** | Doesn't scale - 11,871 codes, not maintainable |

---

## Section 4: Detailed Change Proposals

### New Story: 1-2.1 Fix Category Context Import

**Insert after Story 1-2, before Story 1-3 re-validation**

```markdown
### Story 1-2.1: Fix Category Context Import

As a **developer**,
I want **the tariff import to capture category indicator rows and append context to HS codes**,
So that **search can distinguish between codes like "Other bamboo" vs "Other wood"**.

**Acceptance Criteria:**

**Given** the Excel row "- Từ tre:" (indent level 1, no 8-digit code)
**When** the parser processes subsequent 8-digit codes at deeper indent levels
**Then** those codes include category context in their description_vn field

**Given** HS code 4419.19.00 (currently "- - Loại khác")
**When** re-import completes
**Then** description becomes "- - Loại khác [Từ tre / Of bamboo]"

**Given** HS code 4419.90.00 (currently "- Loại khác")
**When** re-import completes
**Then** description becomes "- Loại khác [không thuộc tre hoặc gỗ nhiệt đới]"

**Given** the data is re-imported with category context
**When** I search for "Khay chia bát đĩa, gỗ MDF phủ Veneer"
**Then** the search returns 4419.90.00 (not 4419.19.00)

**Given** the data is re-imported with category context
**When** embeddings are regenerated with --force-regenerate
**Then** all 11,871 HS codes have embeddings that include category context

**Technical Tasks:**

1. Modify `TariffHierarchyParser.parse_hierarchy()`:
   - Add `category_stack: list[tuple[int, str]]` to track (indent_level, category_name)
   - When row has description but no 8-digit code and starts with "- ": push to stack
   - When indent level decreases: pop categories at higher indent levels
   - When creating HSCodeData: append category context from stack to description_vn

2. Re-import tariff data:
   ```bash
   docker exec athena-api python -m app.scripts.import_tariff_hierarchy
   ```

3. Regenerate all embeddings:
   ```bash
   docker exec athena-api python -m app.scripts.generate_embeddings --force-regenerate
   ```

4. Clear all caches:
   ```bash
   docker exec athena-redis redis-cli FLUSHALL
   ```

5. Validate with test queries

**Definition of Done:**
- [ ] Parser captures category indicator rows
- [ ] Category context appended to child HS code descriptions
- [ ] Data re-imported successfully
- [ ] Embeddings regenerated (11,871 codes)
- [ ] Caches cleared
- [ ] MDF kitchenware query returns 4419.90.00
- [ ] Copper mixer query returns 7418.20.00
- [ ] At least 10 test queries validated
```

### Story Modifications

#### Story 1-3: Add Re-validation Task

Add to Story 1-3 acceptance criteria:

```markdown
**Given** Story 1-2.1 is complete (category context fix)
**When** I search for "Khay chia bát đĩa, gỗ MDF phủ Veneer"
**Then** the API returns HS code 4419.90.00 (not 4419.19.00)

**Given** Story 1-2.1 is complete
**When** I search for "Bộ trộn nước nóng lạnh cho vòi sen, bằng đồng"
**Then** the API returns HS code 7418.20.00 (not 8481.80.98)
```

#### Story 1-4: Add Re-validation Task

Add to Story 1-4 acceptance criteria:

```markdown
**Given** Story 1-2.1 is complete and Story 1-3 re-validated
**When** I use the search UI with test queries
**Then** correct HS codes are displayed with appropriate confidence scores
```

---

## Section 5: Implementation Handoff

### Change Scope Classification

**Scope: Minor**

This change can be implemented directly by the development team without requiring:
- Product Owner / Scrum Master backlog reorganization
- Product Manager strategic review
- Solution Architect architectural changes

### Implementation Sequence

```
1. Create Story 1-2.1 in sprint backlog
   └── Assign to: Dev team
   └── Priority: Blocking (before 1-5, 1-6, 1-7)

2. Implement parser changes
   └── File: api/app/services/tariff_hierarchy_parser.py
   └── Est: 4-6 hours

3. Re-import data
   └── Command: python -m app.scripts.import_tariff_hierarchy
   └── Est: 5 minutes

4. Regenerate embeddings
   └── Command: python -m app.scripts.generate_embeddings --force-regenerate
   └── Est: 30-60 minutes

5. Clear caches
   └── Command: redis-cli FLUSHALL
   └── Est: 1 minute

6. Validate accuracy
   └── Test with original 100 queries
   └── Target: >50% immediate improvement

7. Re-validate Stories 1-3, 1-4
   └── Run acceptance criteria tests
   └── Update status to "done" if passing

8. Resume Epic 1 (Stories 1-5, 1-6, 1-7)
```

### Handoff Recipients

| Role | Responsibility |
|------|----------------|
| **Dev Team** | Implement Story 1-2.1, re-import, regenerate, validate |
| **Scrum Master** | Update sprint-status.yaml, track progress |
| **Product Owner** | Review validation results, approve story completion |

### Success Criteria

| Metric | Target |
|--------|--------|
| **Search accuracy** | >50% improvement from 0% baseline |
| **MDF kitchenware test** | Returns 4419.90.00 |
| **Copper mixer test** | Returns 7418.20.00 |
| **Category context coverage** | All multi-level headings have context |
| **Embedding regeneration** | 100% of 11,871 codes |

### Timeline Impact

| Milestone | Impact |
|-----------|--------|
| **Story 1-2.1** | +1-2 days to Epic 1 |
| **Epic 1 completion** | Delayed by 1-2 days |
| **MVP delivery** | Minimal impact - fix is bounded |

---

## Section 6: Appendix

### Test Queries for Validation

| Query | Expected Code | Notes |
|-------|---------------|-------|
| Khay chia bát đĩa, gỗ MDF phủ Veneer | 4419.90.00 | MDF = other wood, not bamboo |
| Bộ trộn nước nóng lạnh cho vòi sen, bằng đồng | 7418.20.00 | Copper bathroom fixture = sanitary ware |
| Đũa tre | 4419.12.00 | Bamboo chopsticks |
| Thớt gỗ nhiệt đới | 4419.20.00 | Tropical wood cutting board |
| Mắc treo quần áo bằng gỗ | 4421.10.00 | Wooden clothes hanger |

### Technical Reference

**Category Stack Algorithm:**

```python
# Pseudocode for category tracking
category_stack = []  # [(indent_level, category_name), ...]

for row in rows:
    indent = row.indent_level
    desc = row.description_vn
    code = row.hs_code

    # Pop categories at same or higher indent (moving to sibling or parent)
    while category_stack and category_stack[-1][0] >= indent:
        category_stack.pop()

    if code is None and desc.startswith("- "):
        # This is a category indicator
        category_name = desc.strip("- ").strip(":")
        category_stack.append((indent, category_name))

    elif len(code) == 8:
        # This is an HS code - append category context
        if category_stack:
            context = " / ".join([c[1] for c in category_stack])
            desc = f"{desc} [{context}]"

        create_hs_code(code, desc, ...)
```

---

## Approval

**Prepared by:** Correct Course Workflow
**Date:** 2026-02-02

**Approval Status:** [ ] Approved / [ ] Needs Revision / [ ] Rejected

**Approver:** _______________
**Date:** _______________

**Notes:**
_______________________________________________
_______________________________________________
