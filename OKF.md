# Product: PolicySight

**Type:** Concept (Sellable Tool)
**Domain:** Auto Insurance / InsurTech
**Status:** MVP Scaffolding Complete
**Stack:** Python (FastAPI), TypeScript (Vite), PostgreSQL, Docker

## Summary
PolicySight is a third-party auto insurance tool that acts as a "Digital Deputy Agent." It fills the gap left by existing market players (comparators like NerdWallet, carriers like State Farm) which are either biased or limited to price only. It connects the user's **Policy**, **Premium**, and **Claim** into one intelligent dashboard.

## Core Features (Modules)

1.  **Policy Decoder ("SLIP Transposer"):**
    - OCR-based SLIP upload → AI translates legalese → plain-English breakdown with gap analysis

2.  **Claims Advocate ("Liability Navigator"):**
    - Upload accident photos/police reports → AI calculates sub-limit aggregation → payout vs carrier offer comparison

3.  **Rate Trajectory Bot ("Renewal Oracle"):**
    - Predicts next year's premium → compares against peer market data → "Stay" or "Switch" recommendation

4.  **Lapse Bridge ("Covr-Shift"):**
    - Automated fail-safe during carrier switching → monitors renewal window → triggers bridge policy automatically

## Project Structure
```
PolicySight/
├── backend/
│   └── src/
│       ├── ai/          # LLM service (mock placeholder)
│       ├── api/         # FastAPI routes (policies, claims, rates)
│       ├── config/      # Pydantic settings
│       ├── core/        # Business logic (placeholder)
│       └── db/          # SQLAlchemy models, schema, base
├── frontend/
│   └── src/
│       ├── pages/       # PolicyDecoder, ClaimsAdvocate, Trajectory
│       └── services/    # Axios API client
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
└── .env.example
```

## Status
- **Phase 1 (MVP Scaffold):** ✅ Complete
- **Phase 2 (Architecture):** ❌ Pending
- **Phase 3 (Production):** ❌ Pending