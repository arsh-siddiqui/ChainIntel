# ChainIntel

**Blockchain OSINT & Cryptocurrency Forensics Platform**

ChainIntel is a full-stack blockchain investigation platform for authorized cybersecurity, digital-forensics, threat-intelligence and academic research use. An analyst enters a cryptocurrency wallet, sees the wallet profile, examines transactions, visualizes the fund flow, checks threat intelligence and OSINT correlations, reviews explainable risk indicators, monitors the wallet, receives alerts, stores findings in an investigation case and generates a forensic report.

> **Integrity notice:** ChainIntel operates against **real blockchain APIs only** — there is no demo or simulated dataset. All blockchain data comes from live providers; unavailable providers return explicit `UNAVAILABLE` / `REQUIRES_CONFIGURATION` states; risk output is always framed as an analytical indicator — never a determination of unlawful activity.

---

## Features

- **Wallet investigation pipeline** — validate → detect chain → live provider query → transaction normalization → threat matching → OSINT correlation → graph construction → path analysis → explainable risk indicators → persisted investigation
- **Transaction explorer** — filter, sort, paginate and inspect every normalized transaction, with block-explorer links
- **Interactive graph** — React Flow canvas with risk-colored node types, bounded-hop expansion (1–7), aggregated edges, PNG/JSON export
- **Fund-flow tracing** — NetworkX shortest/bounded paths, incoming and outgoing traces, multi-path analysis, suspicious-node flagging, with honest disclaimers
- **Threat intelligence** — CSV/JSON import with full validation (invalid rows, duplicates, insert/update statistics)
- **OSINT correlation** — provider abstraction with honest *link-only* sources; "Source unavailable for automated lookup" is stated, never faked
- **Dark-web / restricted-source correlation** — metadata/evidence records only (Verified Source / Imported Intelligence / Analyst Note / Unavailable); the app never claims to have crawled the dark web
- **Explainable risk engine** — 8 transparent indicators with weight, evidence and source; LOW / MODERATE / ELEVATED / HIGH bands
- **Monitoring & alerts** — per-wallet rules (direction, amount threshold, threat match, flagged counterparty), background polling engine over live data, deduplicated alerts with lifecycle statuses
- **Investigation cases** — statuses, priorities, timeline events, linked investigations, notes
- **Evidence management** — file and note evidence with SHA-256 integrity verification and safe filename handling
- **Reports** — professional PDF (reportlab), JSON and CSV exports with embedded disclaimers
- **Audit log** — every important investigator action recorded
- **Live providers with automatic failover** — Bitcoin via keyless mempool.space (blockchain.info fallback), Ethereum/BSC via Etherscan v2, Moralis, or Ankr (any one key unlocks both chains)

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js 14 (App Router), React 18, TypeScript (strict), Tailwind CSS, TanStack Query, React Hook Form + Zod, @xyflow/react (React Flow), Recharts, Framer Motion, Lucide, sonner, date-fns |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, httpx, NetworkX, pandas, reportlab |
| Database | PostgreSQL (preferred) / SQLite (development fallback) |
| Tests | Pytest (backend), Vitest (frontend), Playwright (e2e) |

## Architecture

```
Frontend (Next.js :3000)
    ↓  fetch /api/*
FastAPI backend (:8000)
    ├── Routers (thin, per domain)
    ├── Services
    │   ├── blockchain/ (base, bitcoin, blockchain-info, ethereum, bsc, moralis, ankr, failover, factory)
    │   ├── wallet_analysis · graph_analysis · risk_engine
    │   ├── threat_intelligence · osint · monitoring · alert_engine
    │   └── case_service · evidence_service · report_service · audit
    ├── SQLAlchemy models → PostgreSQL / SQLite
    └── External blockchain APIs / public intelligence sources (provider abstraction)
```

Every API response uses a consistent envelope: `{ "success": true|false, "data": …, "meta": …, "error": … }`.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Quick start

### Option A — One-Click Desktop App (Windows / PowerShell)

Simply double-click `start-app.bat` or run:

```powershell
.\start-app.ps1
```

This automatically boots up both the FastAPI backend and Next.js frontend, opening ChainIntel in a standalone application window with full PWA installation support.

### Option B — Docker

```bash
docker compose up --build
# Frontend: http://localhost:3000   API docs: http://localhost:8000/docs
```

### Option B — Run services separately

**Backend** (Python 3.11+):

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env        # macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**Frontend** (Node 18+):

```bash
cd frontend
npm install
copy .env.local.example .env.local   # points at http://localhost:8000
npm run dev
```

Open **http://localhost:3000**. Bitcoin investigations work immediately — try the genesis address `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`.

Windows users can also run `scripts/dev.ps1`; macOS/Linux: `bash scripts/dev.sh`.

## Blockchain providers (live)

| Chain | Provider | Key required |
|---|---|---|
| Bitcoin | mempool.space (primary), blockchain.info (fallback) | ❌ No — works keylessly |
| Ethereum | Etherscan v2 → Moralis → Ankr (failover in this order) | ✅ Any ONE of the three keys |
| BNB Smart Chain | Etherscan v2 → Moralis → Ankr (failover in this order) | ✅ Any ONE of the three keys |

Configured providers are tried in order and fail over automatically on upstream failures. Unconfigured chains return `REQUIRES_CONFIGURATION`; failing providers return `PROVIDER_UNAVAILABLE` — the app never substitutes synthetic data.

## Environment variables (backend/.env)

See `backend/.env.example`. Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `APP_MODE` | `LIVE` | Always `LIVE` (the app has no demo mode) |
| `DATABASE_URL` | `sqlite:///./data/chainintel.db` | PostgreSQL recommended in production |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated origins |
| `MEMPOOL_API_URL` | `https://mempool.space/api` | Keyless Bitcoin API |
| `BLOCKCHAIN_API_KEY` | *(empty)* | Optional blockchain.info `api_code` (raises fallback rate limit; public endpoints work without it) |
| `ETHERSCAN_API_KEY` / `BSCSCAN_API_KEY` | *(empty)* | EVM chains (Etherscan v2 multichain) |
| `MORALIS_API_KEY` | *(empty)* | Alternative Ethereum/BSC source (Moralis v2.2) |
| `ANKR_API_KEY` | *(empty)* | Alternative Ethereum/BSC source (Ankr Advanced API) |
| `OSINT_PROVIDER_ENABLED` | `false` | Enables configured external OSINT adapters |
| `POLL_INTERVAL_SECONDS` | `60` | Monitoring engine cycle |
| `MONITORING_ENABLED` | `true` | Start the background monitor loop |
| `MAX_UPLOAD_MB` | `10` | Evidence upload cap |
| `EVIDENCE_DIR` | `./data/evidence` | Local evidence storage (swap for object storage later) |

API keys are read from the environment only and are **never** returned to the frontend.

## Database setup

- **Development fallback:** SQLite (zero configuration) — tables are created automatically on first start.
- **PostgreSQL (preferred):** set `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/chainintel`. For schema evolution use the shipped Alembic setup (`cd backend && alembic upgrade head`; initial revision included). See [docs/DATABASE.md](docs/DATABASE.md).

## Threat database import

Threat Intelligence → **Import CSV/JSON**. Required columns: `address`, `label`, `category`, `source`; optional: `blockchain`, `reference_url`, `confidence`, `first_seen`, `last_seen`, `notes`. The importer validates addresses (live blockchain addresses only — simulated addresses are rejected) and categories, counts received / valid / invalid / duplicates / inserted / updated, and returns row-level errors.

## Testing

```bash
# Backend
cd backend && python -m pytest

# Frontend unit tests
cd frontend && npm test

# Frontend typecheck + lint + build
cd frontend && npm run typecheck && npm run lint && npm run build

# E2E (requires both servers running; first time: npx playwright install chromium)
# Bitcoin tests run keylessly against mempool.space
cd frontend && npx playwright test
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — layers, data flow, extension points
- [docs/API.md](docs/API.md) — endpoint reference and envelope format
- [docs/DATABASE.md](docs/DATABASE.md) — models, indexes, migrations
- [docs/SECURITY.md](docs/SECURITY.md) — threat model, input handling, evidence integrity

## Limitations

- All blockchain data comes from third-party providers; verify critical findings against a full node or secondary explorer for evidentiary use.
- Live Bitcoin pagination is bounded (first ~200 transactions per investigation) to protect graph performance.
- OSINT sources without a stable free API are surfaced as *link-only* — the platform does not scrape them and does not fabricate their results.
- The risk score is an analytical indicator; it is not, and must never be presented as, proof of criminal activity.
- Authentication is intentionally out of scope for this release (single-investigator identity); the architecture reserves a place for it.
- EIP-55 checksum validation requires mixed-case input; all-lower/all-upper EVM addresses pass format validation without checksum verification.
