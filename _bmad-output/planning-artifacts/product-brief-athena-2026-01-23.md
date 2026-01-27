---
stepsCompleted: [1, 2, 3, 4, 5, 6]
status: complete
completedAt: 2026-01-23
inputDocuments:
  - path: docs/BIEU-THUE-XNK2025.xlsx
    type: data-source
    description: Vietnam Customs 2025 Tariff Schedule - 19,901 HS codes with bilingual descriptions
date: 2026-01-23
author: tinsu
project_name: athena
---

# Product Brief: HS Code Lookup Tool

## Input Data Analysis

**Source File:** `docs/BIEU-THUE-XNK2025.xlsx`

| Attribute | Value |
|-----------|-------|
| Total Records | ~19,901 HS codes |
| Main Sheet | BT2025 |
| Languages | Vietnamese + English (built-in) |
| Key Fields | HS Code, VN Description, EN Description, Unit of Measure, Import Duty, Preferential Rates, VAT, FTA Rates (20+), Policy Notes |
| Structure | Hierarchical (Section → Chapter → Heading → 8-digit national code) |

---

## Executive Summary

A specialized web application that transforms HS code classification for Vietnamese import/export operations. By combining official 2025 Vietnam Customs tariff data with intelligent multi-language search, the tool eliminates manual lookup inefficiencies and reduces costly misclassification penalties for logistics customs teams.

**Target Impact:** Enable customs staff to process a 50-item declaration in minutes, not hours.

---

## Core Vision

### Problem Statement

Vietnamese logistics companies processing import/export declarations face a critical bottleneck: HS code classification. Customs teams currently rely on a fragmented, error-prone workflow combining Excel searches, government portal lookups, and institutional memory. With hundreds of lookups daily, this manual process creates significant operational drag.

### Problem Impact

The consequences of inefficient HS classification cascade across the business:

- **Operational Delays:** Slow lookups bottleneck declaration processing, impacting shipment timelines
- **Financial Penalties:** Misclassification triggers customs fines and duty recalculations
- **Client Relationship Damage:** Delays and errors erode trust with import/export clients who depend on timely clearance

### Why Existing Solutions Fall Short

The client has not adopted any existing HS lookup tools because:

- Generic international tools lack Vietnam-specific 8-digit codes and preferential trade agreement rates
- Government portals are authoritative but not optimized for high-volume, rapid lookup workflows
- No existing solution handles the multi-language reality (Vietnamese, English, Chinese product descriptions)

### Proposed Solution

A purpose-built web application featuring:

- **Intelligent Multi-Language Search:** Accept product descriptions in Vietnamese, English, Chinese, and other languages
- **Confidence-Ranked Results:** Return top HS code matches with relevance scoring
- **Complete Tariff Data:** Display duty rates (including 20+ FTA preferential rates), VAT, units of measure, and policy notes
- **Speed Optimization:** History tracking and favorites for instant repeat lookups
- **Official Data Foundation:** Built on the authoritative 2025 Vietnam Customs tariff schedule (19,901 codes)

### Key Differentiators

| Differentiator | Competitive Advantage |
|----------------|----------------------|
| **Official Data Source** | Built on actual 2025 Vietnam Customs tariff Excel - authoritative and complete |
| **Multi-Language Native** | Handles VN/EN/ZH input reality, not English-only afterthought |
| **Vietnam-Specific Depth** | Full 8-digit national codes + all FTA preferential rates (CPTPP, EVFTA, RCEP, etc.) |
| **Workflow-Optimized** | History + Favorites designed for high-volume daily use (hundreds of lookups) |
| **Bilingual Descriptions** | Source data already contains Vietnamese + English - no translation gaps |

---

## Target Users

### Primary Users

#### Linh - Customs Declaration Specialist

**Profile:**
- Mid-level customs staff at a Vietnamese logistics company
- Processes import/export declarations for business clients
- Handles hundreds of HS code lookups daily
- Familiar with common product categories but regularly encounters unfamiliar items

**Daily Reality:**
- Receives shipment documents from clients in mixed languages (Vietnamese, English, Chinese)
- Must assign correct 8-digit Vietnam HS codes quickly and accurately
- Works under time pressure - delays impact shipment clearance

**Core Frustration:**
Ambiguous product descriptions are the primary pain point:
- Vague descriptions: "plastic parts," "electronic accessories," "machine components"
- Foreign language documents with limited context
- Client-provided descriptions that lack technical specificity

**Current Workarounds:**
- Searches through Excel tariff files manually
- Checks Vietnam Customs government portal
- Relies on institutional memory and asks senior colleagues
- Sometimes makes educated guesses under time pressure

**Success Vision:**
- Confidently classify tricky items in seconds instead of minutes
- Handle ambiguous descriptions with intelligent suggestions
- Build a personal library of frequently-used codes for instant lookup

### Secondary Users

| User | Role | Relationship to Product |
|------|------|------------------------|
| **Team Manager** | Oversees customs team performance | Cares about throughput and error reduction; doesn't use tool directly |
| **IT/Admin** | Technical maintenance | Handles deployment, annual tariff data updates |
| **Operations Director** | Decision maker | Approves tool purchase based on ROI (time saved, penalties avoided) |

### User Journey

| Stage | Linh's Experience |
|-------|-------------------|
| **Discovery** | Introduced by management as new tool to replace manual Excel/portal searching |
| **Onboarding** | Quick start - paste or type product description, immediately see ranked results |
| **Core Usage** | Search → Review confidence-ranked matches → Select best HS code → Copy details → Move to next item |
| **"Aha" Moment** | Finds correct code for ambiguous Chinese product description in 5 seconds flat |
| **Repeat Value** | Favorites accumulate - common products become instant lookups |
| **Long-term Integration** | Tool becomes default first step for every declaration; manual Excel search becomes rare fallback |

---

## Success Metrics

### User Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Lookup Speed** | <10 seconds per item | Time from query input to code selection |
| **First-Match Accuracy** | 95% correct in top results | Correct HS code appears in ranked suggestions |
| **Trust Building** | 3 successful lookups | User consistently chooses tool over manual methods |
| **Result Quality** | 80% correct result rate | Selected codes pass customs validation |

**User Success Definition:** Linh can confidently process a 50-item customs declaration in minutes, with the tool surfacing correct HS codes faster and more accurately than manual Excel/portal searching.

### Business Objectives

| Objective | Target | Rationale |
|-----------|--------|-----------|
| **Error Reduction** | 50% fewer misclassifications | Directly reduces penalty costs (10-20% impact per error) |
| **Full Adoption** | 100% of lookups via tool | Replace fragmented manual workflows entirely |
| **Scalable User Base** | Support 50-100 concurrent users | Enable company-wide deployment |
| **Commercialization Potential** | Productize for market | Future revenue stream selling to other logistics companies |

### Key Performance Indicators

**Phase 1 - Internal Launch:**
| KPI | Target | Timeframe |
|-----|--------|-----------|
| Daily active users | 100% of customs team | Within 1 month |
| Lookups per day | Hundreds (matching current volume) | Immediate |
| Average lookup time | <10 seconds | Within 2 weeks |
| Misclassification rate | 50% reduction vs. baseline | Within 3 months |

**Phase 2 - Commercial Potential:**
| KPI | Target | Timeframe |
|-----|--------|-----------|
| External client interest | Validated demand | 6 months |
| Multi-tenant readiness | Architecture supports multiple companies | 12 months |

**ROI Calculation Basis:**
- Penalty cost impact: 10-20% of shipment value per misclassification
- Target: 50% error reduction = significant direct cost savings
- Secondary: Time savings × hundreds of daily lookups = operational efficiency gains

---

## MVP Scope

### Core Features

**1. Intelligent Search Engine**
- Multi-language product description input (Vietnamese, English, Chinese, and other languages)
- Semantic/fuzzy matching to handle ambiguous descriptions
- Confidence-ranked results showing top HS code matches
- Sub-10-second response time target

**2. Complete Tariff Data Display**
For each HS code result, display:
- 8-digit Vietnam HS code
- Vietnamese description
- English description
- Unit of measure
- Import duty rates (normal + preferential)
- VAT rate
- FTA preferential rates (CPTPP, EVFTA, RCEP, ACFTA, etc.)
- Policy notes and restrictions

**3. User Management**
- User authentication (login/logout)
- Personal search history (all lookups tracked)
- Personal favorites (save frequently-used HS codes)
- History and favorites persist across sessions

**4. Admin Interface**
- Tariff data management (upload/update Excel data)
- Annual tariff schedule refresh capability
- User management (if needed)

**5. Web Application**
- Responsive web interface
- Always-online (no offline requirement)
- Optimized for high-volume daily use

### Out of Scope for MVP

| Feature | Rationale | Target Phase |
|---------|-----------|--------------|
| Multi-tenant architecture | Focus on single-client success first | Phase 2 |
| Offline capability | Always-online acceptable for office use | Future if needed |
| API for third-party integration | Internal tool first | Phase 2 |
| Mobile native apps | Web-responsive sufficient for MVP | Phase 2 |
| Advanced analytics/reporting | Focus on core lookup value | Phase 2 |

### MVP Success Criteria

| Criteria | Threshold | Validation Method |
|----------|-----------|-------------------|
| Lookup speed | <10 seconds average | Performance monitoring |
| Result accuracy | 80% correct in top results | User feedback tracking |
| User adoption | 100% of customs team using daily | Usage analytics |
| Error reduction | 50% fewer misclassifications | Before/after comparison |
| User trust | Preferred over manual methods after 3 uses | User interviews |

**Go/No-Go Decision Point:** After 1 month of internal use, evaluate metrics to decide on:
- Continued internal rollout
- Bug fixes and refinements
- Proceeding to Phase 2 (commercialization preparation)

### Future Vision

**Phase 2: Commercial Readiness (6-12 months)**
- Multi-tenant architecture for SaaS deployment
- Subscription/licensing model
- Onboarding flow for new client companies
- Client-specific customization options

**Phase 3: Platform Expansion (12-24 months)**
- API access for ERP/logistics system integration
- Advanced analytics and reporting dashboards
- AI-powered classification suggestions with learning
- Support for additional country tariff schedules (regional expansion)
- Mobile applications for field use

**Long-term Vision:**
Transform from internal tool into the leading HS code classification platform for Vietnamese logistics companies, potentially expanding to Southeast Asian markets with similar tariff complexity.
