---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
status: complete
completedAt: 2026-01-23
inputDocuments:
  - path: _bmad-output/planning-artifacts/product-brief-athena-2026-01-23.md
    type: product-brief
    description: HS Code Lookup Tool - Vietnam Customs 2025 tariff data with multi-language search
workflowType: 'prd'
documentCounts:
  briefs: 1
  research: 0
  projectDocs: 0
  projectContext: 0
classification:
  projectType: web-application
  domain: logistics-trade-compliance
  complexity: medium-high
  projectContext: greenfield
date: 2026-01-23
author: tinsu
project_name: athena
---

# Product Requirements Document - Athena

**Author:** tinsu
**Date:** 2026-01-23
**Status:** Complete
**Version:** 1.0

---

## Executive Summary

**Athena** is a web application that transforms HS code classification for Vietnamese import/export operations. By combining official 2025 Vietnam Customs tariff data with intelligent multi-language search, the tool eliminates manual lookup inefficiencies and reduces costly misclassification penalties for logistics customs teams.

### The Problem
Vietnamese logistics companies processing import/export declarations face a critical bottleneck: HS code classification. Customs teams rely on fragmented workflows combining Excel searches, government portal lookups, and institutional memory. With hundreds of lookups daily, this manual process creates operational delays, financial penalties from misclassification, and eroded client trust.

### The Solution
A purpose-built web application featuring:
- **Intelligent Multi-Language Search:** Accept product descriptions in Vietnamese, English, and Chinese
- **Confidence-Ranked Results:** Return top HS code matches with relevance scoring
- **Complete Tariff Data:** Display duty rates, VAT, 20+ FTA preferential rates, and policy notes
- **Workflow Optimization:** History and favorites for instant repeat lookups

### Target Impact
Enable customs staff to process a 50-item declaration in minutes, not hours. Target 50% reduction in misclassification errors and 100% tool adoption within 1 month of launch.

### MVP Scope
- Multi-language semantic search (VN/EN/ZH)
- Full tariff data display (19,901 HS codes)
- User authentication, favorites, and history
- Admin tariff data upload
- Estimated timeline: 2-3 months with 1-2 developers

---

## 1. Project Classification

| Attribute | Value |
|-----------|-------|
| **Project Type** | Web Application |
| **Domain** | Logistics / Trade Compliance |
| **Complexity** | Medium-High |
| **Project Context** | Greenfield |

---

## 2. Success Criteria

### User Success

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Lookup Speed** | <10 seconds per item | Time from query input to code selection |
| **First-Match Accuracy** | 95% correct in top results | Correct HS code appears in ranked suggestions |
| **Trust Building** | Preferred over manual methods after 3 uses | User behavior tracking |
| **Result Quality** | 80% correct rate | Selected codes pass customs validation |

**User Success Definition:** Linh (customs declaration specialist) can confidently process a 50-item customs declaration in minutes, with the tool surfacing correct HS codes faster and more accurately than manual Excel/portal searching.

### Business Success

| Objective | Target | Rationale |
|-----------|--------|-----------|
| **Error Reduction** | 50% fewer misclassifications | Directly reduces penalty costs (10-20% impact per error) |
| **Full Adoption** | 100% of lookups via tool | Replace fragmented manual workflows entirely |
| **Scalable User Base** | Support 50-100 concurrent users | Enable company-wide deployment |
| **Commercialization Potential** | Validated demand at 6 months | Future revenue stream selling to other logistics companies |

### Technical Success

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Response Time** | <3 seconds for search results | Sub-10s user experience requires fast backend |
| **Data Completeness** | 100% of 19,901 HS codes searchable | Full tariff coverage is non-negotiable |
| **Multi-Language Support** | VN, EN, ZH input accepted | Matches real-world document reality |
| **Uptime** | 99.5% availability during business hours | Mission-critical for daily operations |

### Measurable Outcomes

**Phase 1 - Internal Launch (1 month):**
- Daily active users: 100% of customs team
- Lookups per day: Match current volume (hundreds)
- Average lookup time: <10 seconds
- Misclassification rate: 50% reduction vs. baseline

**Phase 2 - Commercial Validation (6 months):**
- External client interest documented
- Multi-tenant architecture ready

---

## 3. Product Scope

### MVP - Minimum Viable Product

**Core Features (Must Ship):**

1. **Intelligent Search Engine**
   - Multi-language product description input (Vietnamese, English, Chinese)
   - Semantic/fuzzy matching for ambiguous descriptions
   - Confidence-ranked results showing top HS code matches
   - Sub-10-second response time

2. **Complete Tariff Data Display**
   - 8-digit Vietnam HS code
   - Vietnamese + English descriptions
   - Unit of measure
   - Import duty rates (normal + preferential)
   - VAT rate
   - FTA preferential rates (CPTPP, EVFTA, RCEP, ACFTA, etc.)
   - Policy notes and restrictions

3. **User Management**
   - User authentication (login/logout)
   - Personal search history
   - Personal favorites (save frequently-used codes)
   - Persistence across sessions

4. **Admin Interface**
   - Tariff data upload/update (Excel ingestion)
   - Annual tariff schedule refresh capability

5. **Web Application**
   - Responsive web interface
   - Always-online (no offline requirement)

### Growth Features (Post-MVP)

| Feature | Target Phase | Rationale |
|---------|--------------|-----------|
| Multi-tenant architecture | Phase 2 | Required for SaaS commercialization |
| API for third-party integration | Phase 2 | ERP/logistics system connectivity |
| Advanced analytics/reporting | Phase 2 | Usage insights for team managers |
| Mobile native apps | Phase 2+ | Field use cases |

### Vision (Future)

- Leading HS code classification platform for Vietnamese logistics
- Regional expansion to Southeast Asian markets
- AI-powered classification with continuous learning
- Deep ERP integration ecosystem

---

## 4. User Journeys

### Journey 1: Linh - Daily Declaration Processing (Primary User, Success Path)

**The Persona:**
Linh is a mid-level customs declaration specialist at a Vietnamese logistics company. She's been doing this job for 4 years. She's good at it, but the manual lookup process drains her energy. Every morning, she opens three browser tabs: Excel tariff file, Vietnam Customs portal, and her company's internal notes. She processes 80-120 line items daily.

**Opening Scene:**
It's 8:30 AM. Linh receives a new shipment manifest from a client - 47 items. The descriptions are a mess: some Vietnamese, some English, one item just says "plastic machine parts" with a Chinese product name in parentheses. She sighs. This used to mean an hour of cross-referencing.

**Rising Action:**
Linh opens Athena. She pastes the first description: "Máy xay sinh tố gia đình 500W" (family blender 500W). Within 3 seconds, she sees ranked results. The top match shows HS code 85094010 with 85% confidence. She clicks it - sees the full details: 20% import duty, 10% VAT, CPTPP rate of 0%. She adds it to favorites for next time. She moves through the list rapidly.

Item 23 is tricky: "电子配件" (electronic accessories) - vague Chinese description. She types it in. The system returns 5 candidates with lower confidence scores. She reviews the Vietnamese/English descriptions for each, recognizes the pattern from the invoice photo, and selects the correct code.

**Climax:**
By 9:15 AM, Linh has classified all 47 items. She glances at her search history - everything is logged. She realizes she just did in 45 minutes what used to take 2+ hours. She hasn't opened the Excel file once.

**Resolution:**
Linh submits the declaration with confidence. The codes pass customs validation without issue. Her manager notices she's completing declarations faster. She has time to help train a new colleague. The tool has become her default first step.

---

### Journey 2: Linh - Ambiguous Product Recovery (Primary User, Edge Case)

**Opening Scene:**
Linh receives a shipment with an item described only as "industrial equipment parts - misc." No photos, no model numbers. The client's invoice is unhelpful.

**Rising Action:**
She searches "industrial equipment parts" in Athena. Results are scattered - too many possibilities spanning multiple chapters. Confidence scores are all below 40%.

She contacts the client for clarification. While waiting, she uses the HS code browser to navigate the tariff structure manually - Chapter 84 (machinery) vs Chapter 85 (electrical). The tool's hierarchical view helps her narrow down.

**Climax:**
The client responds: "It's replacement gears for a textile loom." Linh searches "textile loom gears" - now she gets a clear match: 84483900, "Parts of machinery of heading 84.46 or 84.47" with 78% confidence. She verifies against the code description and policy notes.

**Resolution:**
She adds "textile loom gears → 84483900" to her favorites with a note. Next time this client ships similar parts, she'll have instant lookup. The system learned nothing new, but Linh's personal library grew.

---

### Journey 3: Minh - Annual Tariff Data Update (IT/Admin User)

**The Persona:**
Minh is the IT administrator. He doesn't touch customs work, but he's responsible for keeping business systems running. Once a year, he dreads tariff update week.

**Opening Scene:**
It's December. Vietnam Customs publishes the 2026 tariff schedule Excel file. Minh downloads it - 20MB, 20,000+ rows. Last year, updating the old Excel-based system took a full day of data validation nightmares.

**Rising Action:**
Minh logs into Athena's admin panel. He navigates to "Data Management" and sees the current data version: "2025 Tariff Schedule, uploaded 2025-01-15."

He clicks "Upload New Tariff Data" and selects the 2026 Excel file. The system shows a preview: "19,947 HS codes detected. 46 new codes, 12 removed codes, 234 rate changes identified."

**Climax:**
Minh reviews the change summary. Everything looks correct against the official documentation. He clicks "Activate New Data." The system processes for 90 seconds, then confirms: "2026 Tariff Schedule active. Previous version archived."

**Resolution:**
Minh sends an email to the customs team: "2026 tariff data is live in Athena." Total time: 15 minutes. He moves on to other tasks. Next year, same simple process.

---

### Journey 4: Hoa - Team Performance Review (Team Manager)

**The Persona:**
Hoa manages a team of 8 customs specialists including Linh. She reports to the Operations Director on team efficiency and error rates.

**Opening Scene:**
Monthly review time. Hoa needs to prepare metrics for leadership showing how the new tool is performing.

**Rising Action:**
Hoa logs into Athena with her manager credentials. She accesses the usage dashboard (Phase 2 feature, but let's design for it). She sees:
- Total lookups this month: 12,847
- Average lookup time: 6.2 seconds
- Top users by volume
- Most-searched HS code categories
- Favorites usage rate

She exports the data for her presentation.

**Climax:**
Comparing to baseline metrics from before Athena, she sees clear improvement: declaration processing time down 40%, misclassification rate down from 8% to 3%.

**Resolution:**
Hoa presents to the Operations Director with confidence. The ROI case is clear. Discussion shifts to "when can we roll this out to our other branch offices?"

---

### Journey Requirements Summary

| Journey | Key Capabilities Revealed |
|---------|--------------------------|
| **Linh - Success Path** | Multi-language search, confidence ranking, favorites, history, tariff detail display, fast response time |
| **Linh - Edge Case** | Hierarchical HS code browsing, favorites with notes, handling low-confidence results gracefully |
| **Minh - Admin** | Excel data upload, change detection preview, version management, activation workflow |
| **Hoa - Manager** | Usage analytics dashboard, export capability, comparative metrics (Phase 2) |

**Capabilities by Priority:**

**MVP Must-Have:**
- Multi-language semantic search
- Confidence-ranked results
- Full tariff detail display
- Personal favorites and history
- User authentication
- Admin data upload with preview

**Phase 2:**
- Usage analytics dashboard
- Team-level reporting
- Export functionality
- Comparative metrics

---

## 5. Domain-Specific Requirements

### Compliance & Regulatory

**Data Source Authority:**
- Tariff data MUST originate from official Vietnam Customs published schedules
- System must track data version and publication date
- Users must be able to verify data currency (e.g., "Data as of: 2025 Tariff Schedule, effective Jan 1, 2025")

**Trade Agreement Compliance:**
- Must accurately represent FTA preferential rates for all active agreements:
  - CPTPP (Comprehensive and Progressive Agreement for Trans-Pacific Partnership)
  - EVFTA (EU-Vietnam Free Trade Agreement)
  - RCEP (Regional Comprehensive Economic Partnership)
  - ACFTA (ASEAN-China Free Trade Area)
  - AKFTA (ASEAN-Korea Free Trade Agreement)
  - AJCEP (ASEAN-Japan Comprehensive Economic Partnership)
  - VKFTA (Vietnam-Korea Free Trade Agreement)
  - And other bilateral/multilateral agreements in the source data

**Disclaimer Requirements:**
- Tool provides reference data only; final classification decisions remain with customs authorities
- Users should verify against official sources for high-stakes declarations
- System is not a substitute for professional customs brokerage advice

### Technical Constraints

**Data Integrity:**
- HS codes must be stored and displayed exactly as published (no truncation, no reformatting)
- Duty rates must preserve decimal precision from source data
- Policy notes and restrictions must be displayed verbatim

**Search Accuracy:**
- Confidence scores must reflect actual match quality
- Low-confidence results (<50%) should include explicit guidance to verify manually
- Search must not return false positives on HS code numbers (exact code searches must match exactly)

**Data Currency:**
- System must support annual data updates (Vietnam publishes new tariff schedules yearly)
- Admin must be able to preview changes before activation
- Historical data archival recommended but not required for MVP

### Integration Requirements

**Data Input:**
- Accept Excel format matching Vietnam Customs publication structure
- Handle Vietnamese character encoding (UTF-8) correctly
- Parse complex column structures (merged cells, multi-line descriptions)

**No External System Integration Required for MVP:**
- This is a standalone lookup tool
- No ERP/customs filing system integration in Phase 1
- API access deferred to Phase 2

### Risk Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Outdated tariff data** | Wrong duty rates, penalties | Clear data version display; admin alerts for annual updates |
| **Search returns wrong codes** | Misclassification, penalties | Confidence scoring; low-confidence warnings; manual verification guidance |
| **FTA rates incorrectly applied** | Duty overpayment or penalties | Display eligibility notes; link to FTA requirements |
| **Data upload corruption** | System unusable | Preview before activation; rollback capability |
| **Multi-language search failures** | Missed correct codes | Fallback to Vietnamese/English when no match; suggest alternative terms |

---

## 6. Innovation & Differentiation

### Product Positioning

This is a **differentiated execution** product, not a breakthrough innovation. The value proposition is doing something known extremely well for an underserved market segment.

### Key Differentiators

| Differentiator | Why It Matters |
|----------------|----------------|
| **Multi-language input (VN/EN/ZH)** | No existing Vietnam tariff tool handles Chinese product descriptions - critical for China trade |
| **Semantic/fuzzy matching** | Handles ambiguous descriptions like "plastic parts" or "electronic accessories" that exact-match tools fail on |
| **Complete FTA rate coverage** | 20+ preferential trade agreements in one place - competitors show only basic duty rates |
| **Official data foundation** | Built on actual Vietnam Customs published Excel - authoritative, not scraped |
| **Workflow optimization** | History + favorites designed for high-volume daily use (hundreds of lookups), not occasional reference |

### Competitive Landscape

| Competitor Type | Gap We Fill |
|-----------------|-------------|
| **Vietnam Customs Portal** | Authoritative but slow, not optimized for high-volume workflow |
| **Generic international HS tools** | Miss Vietnam-specific 8-digit codes and FTA rates |
| **Excel-based manual lookup** | Slow, error-prone, no search intelligence |
| **Commercial customs software** | Expensive, complex, overkill for lookup-only use case |

### Validation Approach

The core hypothesis to validate: **Semantic search can reliably match ambiguous product descriptions to correct HS codes.**

**Validation method:**
1. Test with real historical declaration data from the customs team
2. Measure first-match accuracy against human expert classifications
3. Target: 80%+ correct code in top 5 results for ambiguous descriptions

**Fallback if search accuracy is insufficient:**
- Expose hierarchical HS code browsing as primary navigation
- Use search as discovery aid, not authority
- Add "not sure" workflow that guides manual exploration

---

## 7. Web Application Technical Requirements

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Client (Browser)                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  React/Next.js SPA                                   │    │
│  │  - Search interface                                  │    │
│  │  - Results display                                   │    │
│  │  - Favorites/History management                      │    │
│  │  - Admin panel                                       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Node.js/NestJS or Python/FastAPI                   │    │
│  │  - Authentication (JWT)                              │    │
│  │  - Search orchestration                              │    │
│  │  - User data management                              │    │
│  │  - Admin endpoints                                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │  PostgreSQL    │  │  Elasticsearch │  │  Redis       │  │
│  │  - Users       │  │  - HS codes    │  │  - Sessions  │  │
│  │  - Favorites   │  │  - Full-text   │  │  - Cache     │  │
│  │  - History     │  │  - Multi-lang  │  │              │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Frontend Requirements

| Requirement | Specification |
|-------------|---------------|
| **Framework** | React with TypeScript (Next.js optional for SSR) |
| **Responsive Design** | Desktop-first, tablet-compatible (no mobile app MVP) |
| **Browser Support** | Chrome, Firefox, Edge (latest 2 versions); Safari (latest) |
| **Performance** | First Contentful Paint <2s; Time to Interactive <4s |
| **Accessibility** | WCAG 2.1 AA compliance for core workflows |

**Key UI Components:**
- Search bar with multi-language input support
- Results list with confidence scoring visualization
- HS code detail panel (tariff rates, FTA rates, notes)
- Favorites manager with notes
- Search history with re-search capability
- Admin data upload wizard

### Backend Requirements

| Requirement | Specification |
|-------------|---------------|
| **Language/Framework** | Node.js (NestJS) or Python (FastAPI) - team preference |
| **API Style** | REST (JSON) |
| **Authentication** | JWT with refresh tokens |
| **Session Management** | Redis-backed sessions |
| **Logging** | Structured JSON logging; audit trail for admin actions |

**API Endpoints (Core):**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login` | POST | User authentication |
| `/auth/refresh` | POST | Token refresh |
| `/search` | POST | HS code search (accepts query, language hint) |
| `/hs-codes/{code}` | GET | Full details for specific HS code |
| `/favorites` | GET/POST/DELETE | Manage user favorites |
| `/history` | GET | Retrieve search history |
| `/admin/data/upload` | POST | Upload new tariff Excel |
| `/admin/data/activate` | POST | Activate uploaded data |

### Search Engine Requirements

**This is the critical technical component.**

| Requirement | Specification |
|-------------|---------------|
| **Engine** | Elasticsearch (recommended) or PostgreSQL full-text + pg_trgm |
| **Multi-language** | Vietnamese, English, Chinese tokenization |
| **Matching Strategy** | Fuzzy matching + semantic similarity |
| **Response Time** | <1 second for search query processing |
| **Ranking** | BM25 with custom boosting for exact matches |
| **NotebookLM Integration** | Google NotebookLM (Gemini 3) via notebooklm_tools Python SDK |
| **Grounding Source** | Official Vietnam 2026 tariff PDF uploaded to NotebookLM |
| **Rate Limit Strategy** | KB auto-storage + Redis cache (24h TTL) to minimize API calls (~50/day free tier) |

**Search Index Structure:**
- HS code (exact match field)
- Vietnamese description (analyzed, Vietnamese tokenizer)
- English description (analyzed, English tokenizer)
- Combined searchable field (cross-language)
- Duty rates (for filtering)
- FTA applicability flags

### Database Requirements

**PostgreSQL (Relational Data):**

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `users` | User accounts | id, email, password_hash, role, created_at |
| `favorites` | Saved HS codes | user_id, hs_code, notes, created_at |
| `search_history` | Search audit | user_id, query, selected_code, timestamp |
| `data_versions` | Tariff data versions | id, version_name, uploaded_at, activated_at, file_path |

**Elasticsearch (Search Index):**
- Single index: `hs_codes`
- Document count: ~20,000
- Reindexed on data upload

### Security Requirements

| Requirement | Implementation |
|-------------|----------------|
| **Authentication** | JWT tokens, bcrypt password hashing |
| **Authorization** | Role-based (user, admin) |
| **HTTPS** | Required for all traffic |
| **Input Validation** | Server-side validation on all inputs |
| **SQL Injection** | Parameterized queries only |
| **XSS Prevention** | Content Security Policy; output encoding |
| **Rate Limiting** | 100 requests/minute per user for search |

### Deployment Requirements

| Requirement | Specification |
|-------------|---------------|
| **Hosting** | Cloud VM or container (Docker) |
| **Environment** | Single environment MVP; staging + production for Phase 2 |
| **Database Hosting** | Managed PostgreSQL (RDS/Cloud SQL) or self-hosted |
| **Search Hosting** | Managed Elasticsearch or self-hosted |
| **Backup** | Daily database backups; 7-day retention |
| **Monitoring** | Basic uptime monitoring; error alerting |

### Performance Targets

| Metric | Target |
|--------|--------|
| **Search Response** | <3 seconds end-to-end |
| **Page Load** | <4 seconds initial load |
| **Concurrent Users** | 50-100 simultaneous |
| **Uptime** | 99.5% during business hours (Mon-Sat, 7am-7pm ICT) |
| **Data Refresh** | <5 minutes for full reindex on data update |

---

## 8. Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-Solving MVP

This MVP is designed to solve a specific, validated pain point: inefficient HS code lookup for Vietnamese customs operations. The goal is not to build a platform or capture revenue - it's to prove that intelligent search can reliably classify products faster than manual methods.

**MVP Success Gate:**
- Customs team adopts tool for 100% of lookups within 1 month
- Misclassification rate drops 50% vs. baseline
- Average lookup time <10 seconds

**Resource Requirements:**
- 1-2 full-stack developers
- Part-time DevOps/infrastructure support
- Access to customs team for testing and feedback

### MVP Feature Boundaries

**Absolutely Essential (MVP Fails Without):**

| Capability | Why Essential |
|------------|---------------|
| Multi-language search | Core value proposition - handles VN/EN/ZH input |
| Full tariff data display | Users need complete duty/VAT/FTA information |
| User authentication | Personal history and favorites require user identity |
| Search history | High-volume workflow requires quick re-access |
| Favorites | Repeat lookups are a major use case |
| Admin data upload | Annual tariff updates are mandatory |

**Can Be Manual Initially:**

| Capability | Manual Workaround |
|------------|-------------------|
| User management | Admin creates accounts directly in database |
| Usage analytics | Query database logs manually |
| Data validation | Admin reviews Excel before upload |

**Explicitly Out of MVP:**

| Capability | Rationale | Target Phase |
|------------|-----------|--------------|
| Multi-tenant architecture | Single client first | Phase 2 |
| API access | Internal tool only for now | Phase 2 |
| Mobile apps | Desktop workflow is primary | Phase 2+ |
| Advanced analytics | Focus on core search value | Phase 2 |
| Offline mode | Always-connected office use | Never (deprioritized) |

### Phased Development Roadmap

**Phase 1: MVP (Target: 2-3 months)**
- Core search with multi-language support
- Full tariff data display
- User auth, history, favorites
- Admin data upload
- Internal deployment to customs team

**Phase 2: Growth (3-6 months post-MVP)**
- Usage analytics dashboard for managers
- Multi-tenant architecture for SaaS
- API access for ERP integration
- Team-level favorites sharing
- Performance optimization for scale

**Phase 3: Expansion (6-12 months post-Phase 2)**
- Mobile-responsive optimization
- AI-powered classification suggestions
- Integration marketplace
- Additional country tariff data
- Enterprise features (SSO, audit logs)

### Risk Mitigation Strategy

**Technical Risk: Search Accuracy**
- *Risk:* Semantic search may not reliably match ambiguous descriptions to correct HS codes
- *Mitigation:*
  - Build hierarchical HS code browser as fallback navigation
  - Test with real historical data before launch
  - Add confidence thresholds with manual verification prompts
  - Iterate on search algorithm based on user feedback

**Technical Risk: Multi-Language Processing**
- *Risk:* Chinese tokenization may not work well for product descriptions
- *Mitigation:*
  - Start with Vietnamese + English as primary
  - Add Chinese as best-effort with clear UX for "no results" case
  - Use established NLP libraries (ICU, Elasticsearch analyzers)

**Market Risk: User Adoption**
- *Risk:* Customs team may resist changing established workflows
- *Mitigation:*
  - Involve team in testing early
  - Make tool faster than manual method from day one
  - Allow gradual adoption (tool + fallback to Excel)
  - Track and celebrate time savings

**Resource Risk: Limited Development Capacity**
- *Risk:* Fewer developers than planned
- *Mitigation:*
  - MVP scope is already minimal
  - Use managed services (Elasticsearch Cloud, managed PostgreSQL)
  - Delay Phase 2 features rather than compromise MVP quality
  - Single-developer emergency fallback: cut admin UI, use CLI for data upload

---

## 9. Functional Requirements

> **Capability Contract:** Every feature must trace back to these requirements. If a capability is not listed here, it will not exist in the final product.

### HS Code Search

- **FR1:** Users can search for HS codes by entering product descriptions in Vietnamese
- **FR2:** Users can search for HS codes by entering product descriptions in English
- **FR3:** Users can search for HS codes by entering product descriptions in Chinese
- **FR4:** Users can search for HS codes by entering the exact HS code number
- **FR5:** Users can view search results ranked by confidence/relevance score
- **FR6:** Users can see confidence indicators (high/medium/low) for each search result
- **FR7:** Users can view full tariff details for any HS code in search results
- **FR8:** Users can browse HS codes hierarchically by Section, Chapter, and Heading
- **FR9:** Users can filter search results by HS code chapter

### Tariff Data Display

- **FR10:** Users can view the 8-digit Vietnam HS code for any tariff entry
- **FR11:** Users can view the Vietnamese description for any HS code
- **FR12:** Users can view the English description for any HS code
- **FR13:** Users can view the unit of measure for any HS code
- **FR14:** Users can view the standard import duty rate for any HS code
- **FR15:** Users can view the VAT rate for any HS code
- **FR16:** Users can view FTA preferential rates for all active import AND export trade agreements, including RCEP year-by-year rates (2022-2027) and export FTA rates (CPTPP-XK, EV-XK, UKV-XK)
- **FR17:** Users can view policy notes and restrictions for any HS code
- **FR18:** Users can view the current tariff data version and effective date

### User Favorites

- **FR19:** Users can save any HS code to their personal favorites
- **FR20:** Users can add personal notes to saved favorites
- **FR21:** Users can view their complete favorites list
- **FR22:** Users can remove HS codes from their favorites
- **FR23:** Users can search within their favorites
- **FR24:** Users can access favorites for quick re-lookup during search workflow

### Search History

- **FR25:** The system records all user searches automatically
- **FR26:** Users can view their recent search history
- **FR27:** Users can re-execute a previous search from history
- **FR28:** Users can see which HS code they selected for each historical search
- **FR29:** Users can clear their search history

### User Authentication

- **FR30:** Users can create an account with email and password
- **FR31:** Users can log in to the system with their credentials
- **FR32:** Users can log out of the system
- **FR33:** Users can reset their password if forgotten
- **FR34:** The system maintains user sessions across browser sessions
- **FR35:** Admins can assign user roles (standard user, admin)

### Admin Data Management

- **FR36:** Admins can upload new tariff data files (Excel format)
- **FR37:** Admins can preview uploaded data before activation (row count, change summary)
- **FR38:** Admins can see a comparison of changes between current and uploaded data
- **FR39:** Admins can activate uploaded tariff data to make it live
- **FR40:** Admins can roll back to the previous tariff data version
- **FR41:** Admins can view the history of data uploads and activations
- **FR42:** The system validates uploaded Excel files for correct format before processing

### System Feedback & Error Handling

- **FR43:** Users receive clear feedback when search returns no results
- **FR44:** Users receive suggestions for alternative search terms when results are low-confidence
- **FR45:** Users can report incorrect or missing HS code data (feedback mechanism)
- **FR46:** The system displays appropriate error messages for system failures
- **FR47:** Users can see a loading indicator during search operations

### Data Integrity

- **FR48:** The system preserves exact HS code formats as published (no truncation)
- **FR49:** The system preserves duty rate decimal precision from source data
- **FR50:** The system displays policy notes verbatim from source data

### Lookup History & Details

- **FR51:** The system persists classification reasoning, practical notes, and process logs for every search lookup
- **FR52:** Users can view a paginated list of all past lookups with matched HS code, confidence, and verification status
- **FR53:** Users can view full details of any past lookup including classification reasoning, practical notes, process logs, and submit corrections

### Tariff Schedule Browser (ADDED 2026-02-11)

- **FR54:** Users can browse the full tariff schedule as a collapsible tree (Section → Chapter → Heading → Subheading → 8-digit code) with inline rate data per row
- **FR55:** Users can view export duty rates for any HS code
- **FR56:** Users can view special consumption tax (TTDB) for applicable HS codes
- **FR57:** Users can view environmental protection tax (BVMT) for applicable HS codes
- **FR58:** Users can view VAT reduction eligibility for applicable HS codes
- **FR59:** Users can search/filter within the tariff browser by code number or description text
- **FR60:** Users can jump to a specific chapter via quick selector in the browser
- **FR61:** Users can view section and chapter classification notes in the browser

**NotebookLM AI Search (FR62-FR64):** _(added via sprint change 2026-02-15)_
- **FR62:** System queries NotebookLM (Gemini 3) for novel product descriptions not found in the knowledge base, using the official tariff PDF as grounding source
- **FR63:** NotebookLM classification results are automatically stored in the knowledge base for future instant retrieval (self-improving accuracy)
- **FR64:** System falls back to vector/fuzzy search when NotebookLM is unavailable (rate limit, timeout, or service outage)

---

**FR Coverage Validation:**

| Source | Covered By |
|--------|------------|
| Core search capability | FR1-FR9 |
| Tariff detail display | FR10-FR18 |
| Favorites (from journeys) | FR19-FR24 |
| History (from journeys) | FR25-FR29 |
| User auth (from scope) | FR30-FR35 |
| Admin data management (from journeys) | FR36-FR42 |
| Error handling (from domain risks) | FR43-FR47 |
| Data integrity (from domain requirements) | FR48-FR50 |
| Lookup history & details (from implementation) | FR51-FR53 |
| Tariff schedule browser (from sprint change 2026-02-11) | FR54-FR61 |
| NotebookLM AI search (from sprint change 2026-02-15) | FR62-FR64 |

---

## 10. Non-Functional Requirements

> Quality attributes that define HOW WELL the system must perform, specific to this product's needs.

### Performance

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR-P1:** Search query response time | <3 seconds (95th percentile) | Core value proposition is speed; users currently spend minutes per lookup |
| **NFR-P2:** Page initial load time | <4 seconds | First meaningful paint must be fast for workflow efficiency |
| **NFR-P3:** HS code detail retrieval | <1 second | Immediate feedback when selecting a result |
| **NFR-P4:** Favorites/History load | <2 seconds | Quick access to personal data |
| **NFR-P5:** Admin data upload processing | <5 minutes for full dataset (~20,000 records) | Annual update should not disrupt operations |

### Reliability

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR-R1:** System availability | 99.5% during business hours (Mon-Sat 7am-7pm ICT) | Mission-critical for daily customs operations |
| **NFR-R2:** Planned maintenance window | Off-hours only (after 8pm ICT) | No disruption during peak usage |
| **NFR-R3:** Data loss prevention | Zero tolerance for user favorites/history loss | Personal data is valuable to users |
| **NFR-R4:** Graceful degradation | Search returns partial results rather than failing completely | Better UX than error pages |
| **NFR-R5:** Recovery time objective (RTO) | <2 hours for full system recovery | Acceptable for internal tool |

### Scalability

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR-S1:** Concurrent users | 50-100 simultaneous | Company-wide deployment capacity |
| **NFR-S2:** Searches per minute | 500+ system-wide | High-volume workflow support |
| **NFR-S3:** Database growth | Support 5 years of search history | Long-term data retention |
| **NFR-S4:** Data scale | Support up to 50,000 HS codes | Room for growth beyond current ~20,000 |

### Security

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR-SEC1:** Data in transit | HTTPS/TLS 1.2+ for all traffic | Protect user credentials and data |
| **NFR-SEC2:** Password storage | Bcrypt with cost factor ≥10 | Industry standard for password hashing |
| **NFR-SEC3:** Session management | JWT with 24-hour expiry, refresh tokens | Balance security with usability |
| **NFR-SEC4:** Input validation | Server-side validation on all user inputs | Prevent injection attacks |
| **NFR-SEC5:** Admin access | Role-based access control; admin actions logged | Protect data management functions |
| **NFR-SEC6:** Rate limiting | 100 requests/minute per user | Prevent abuse and ensure fair access |

### Usability

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR-U1:** Search input | Single text field, no mode selection required | Minimize cognitive load for high-volume use |
| **NFR-U2:** Results display | View 10+ results without scrolling | Quick visual scanning |
| **NFR-U3:** Keyboard navigation | Tab/Enter workflow for power users | Speed optimization for experienced users |
| **NFR-U4:** Language display | Bilingual (VN + EN) descriptions shown together | No switching needed |
| **NFR-U5:** Mobile responsiveness | Functional on tablet (1024px+) | Occasional mobile access |

### Accessibility

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR-A1:** WCAG compliance | Level AA for core workflows | Good practice for business application |
| **NFR-A2:** Screen reader support | All interactive elements labeled | Support users with visual impairments |
| **NFR-A3:** Color contrast | 4.5:1 minimum for text | Readability in various lighting |
| **NFR-A4:** Keyboard operability | All functions accessible via keyboard | Power user efficiency |

### Internationalization

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR-I1:** Character encoding | UTF-8 throughout | Support Vietnamese, Chinese characters |
| **NFR-I2:** Input handling | Accept Vietnamese diacritics, Chinese characters | Multi-language search capability |
| **NFR-I3:** UI language | English interface (Vietnamese data displayed) | International team support |
| **NFR-I4:** Number formatting | Support both comma and period decimal separators | Tariff rate display |

### Monitoring & Observability

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR-M1:** Uptime monitoring | External health check every 5 minutes | Early detection of outages |
| **NFR-M2:** Error alerting | Admin notification within 5 minutes of critical errors | Rapid response capability |
| **NFR-M3:** Search analytics | Log all searches (anonymized for analysis) | Continuous improvement data |
| **NFR-M4:** Performance tracking | Response time monitoring | Detect degradation early |
