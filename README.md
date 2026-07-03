# PolicySight

**Your Policy, Decoded. Your Claim, Defended.**

AI-Driven Auto Insurance Middleware — a neutral third-party tool that connects your **Policy**, **Premium**, and **Claim** into one intelligent dashboard.

## Architecture

- **Backend:** Python FastAPI
- **Frontend:** TypeScript Vite + React + MUI
- **Database:** PostgreSQL
- **AI:** OpenAI / LLM for SLIP parsing and claims analysis
- **Containerization:** Docker + Docker Compose

## Core Modules

1. **Policy Decoder** — Upload your SLIP document, AI translates legalese to plain English with gap analysis
2. **Claims Advocate** — Upload accident photos/police reports, AI calculates sub-limit payouts vs carrier offers
3. **Rate Trajectory Bot** — Predicts next year's premium using peer market data
4. **Lapse Bridge** — Automated fail-safe preventing coverage gaps during carrier switches

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Local Development

```bash
# Clone the repo
git clone <repo-url>
cd PolicySight

# Copy environment variables
cp .env.example .env

# Start with Docker
docker compose up --build
```

### Backend (without Docker)

```bash
# From project root (recommended):
python run.py

# Or from backend directory:
cd backend
source .venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 9999 --reload
```

### Frontend (without Docker)

```bash
cd frontend
npm install
npm run dev
```

## License

Proprietary — All Rights Reserved.