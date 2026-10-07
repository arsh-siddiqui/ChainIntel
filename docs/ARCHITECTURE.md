# ChainIntel — Architecture

## System overview

```
┌─────────────────────────────┐
│  Next.js frontend (:3000)   │  App Router pages, TanStack Query,
│  TypeScript strict          │  React Flow graph, Recharts
└──────────────┬──────────────┘
               │ fetch http://<api>/api/*   (envelope: {success,data,meta,error})
┌──────────────▼──────────────┐
│  FastAPI backend (:8001)    │  CORS · rate limit · request-size limit
│  ┌───────────────────────┐  │
│  │ Routers (thin)        │  │  dashboard, wallets, transactions, graph,
│  │                       │  │  threats, osint, alerts, cases, evidence,
│  │                       │  │  reports, search, audit-log
│  └──────────┬────────────┘  │
│  ┌──────────▼────────────┐  │
│  │ Services (logic)      │  │  wallet_analysis (pipeline)
│  │                       │  │  blockchain/ (base, bitcoin,
│  │                       │  │    blockchain-info, ethereum, bsc, polygon,
│  │                       │  │    solana, moralis, ankr, failover, factory)
│  │                       │  │  graph_analysis (NetworkX)
│  │                       │  │  risk_engine · threat_intelligence
│  │                       │  │  osint (provider interface)
│  │                       │  │  monitoring · alert_engine
│  │                       │  │  case_service · evidence_service
│  │                       │  │  report_service (PDF/JSON/CSV)
│  └──────────┬────────────┘  │
│  ┌──────────▼────────────┐  │
│  │ SQLAlchemy models     │  │  wallets, transactions, investigations,
│  │ (indexed)             │  │  threat_findings, osint_findings, cases,
│  └──────────┬────────────┘  │  case_events, alerts, monitored_wallets,
└─────────────┼───────────────┘  evidence, reports, audit_log
              ▼
   PostgreSQL / SQLite          httpx → external APIs
```

## Key design decisions

### 1. Consistent response envelope
Every endpoint returns `{success, data, meta, error}`. `meta` carries pagination and context flags. Errors carry a stable `code` (e.g. `PROVIDER_UNAVAILABLE`, `INVALID_WALLET`, `REQUIRES_CONFIGURATION`) that the frontend maps to friendly messages and recovery actions.

### 2. Provider abstraction (failover by design)
`services/blockchain/base.py` defines the normalized contract (`get_balance`, `get_transactions`, `get_transaction`, `get_block_info`, `get_address_activity`). Implementations:

- `BitcoinProvider` — keyless mempool.space REST API with polite pagination, 429 → `PROVIDER_RATE_LIMITED`; `BlockchainInfoProvider` — keyless blockchain.info fallback (optional `api_code` raises rate limits).
- `EvmProvider` (Ethereum) / `BSCProvider` — Etherscan v2 multichain; `MoralisProvider` and `AnkrProvider` — alternative Ethereum/BSC sources; missing keys → `REQUIRES_CONFIGURATION`.

The factory (`provider_for_address`) validates and detects the chain first, then instantiates the first configured provider. When several providers are configured for a chain, a `FailoverProvider` wrapper retries the next candidate on `PROVIDER_UNAVAILABLE` / `PROVIDER_RATE_LIMITED` / `REQUIRES_CONFIGURATION` — `NOT_FOUND` propagates immediately. Selection order: Etherscan → Moralis → Ankr (EVM), mempool.space → blockchain.info (Bitcoin). Providers **never** synthesize data on failure — errors propagate as typed exceptions and become envelope errors. Adding a chain = one new provider class + factory entry; no other code changes.

### 3. Investigation pipeline
`services/wallet_analysis.run_investigation` orchestrates the full analysis and persists one `Investigation` row (with the complete JSON bundle). The pipeline is idempotent per run and reuses stored transactions to keep graphs fast.

### 4. Graph engine
`services/graph_analysis` bounds everything: BFS hop limits (1–7), node caps (`max_nodes`), aggregated parallel edges. Tracing (shortest path, multi-path, incoming/outgoing BFS levels) runs on the bounded subgraph. Every trace response embeds the disclaimer that it is the *shortest observed path*, not a claim of true illicit flow.

### 5. Explainable risk
`services/risk_engine.assess` produces indicators with `{name, description, evidence, weight, source, status}`; the score is the transparent sum of triggered weights, mapped to LOW/MODERATE/ELEVATED/HIGH. A high-severity direct threat match upgrades MODERATE → ELEVATED. The disclaimer ships with every result and every report.

### 6. OSINT honesty model
`services/osint.OSINTProvider` has two implementation classes of behavior:

- **Link-only providers** — real public sources with no stable free API. They return `status: UNAVAILABLE` with the note *"Source unavailable for automated lookup"* plus a pre-built external search URL. They never return findings.
- **Restricted/analyst records** — internal intelligence stored in the database, added by investigators or imported from restricted sources.

A future real API provider implements the interface and joins `PROVIDERS` — nothing else changes.

### 7. Monitoring engine
A single asyncio background loop (started in the FastAPI lifespan) cycles every `POLL_INTERVAL_SECONDS`:

- **Live wallets:** bounded provider polling with a per-wallet minimum interval, deduped alerts, and `last_checked`/`last_tx_hash` progress tracking. Provider failures are logged and retried next cycle — never papered over, and no synthetic events are ever generated.

### 8. Evidence integrity
Uploads are validated (extension allow-list, size cap), renamed to safe server-generated names, stored under `EVIDENCE_DIR`, and hashed with SHA-256 at rest. The evidence endpoint recomputes and compares hashes on demand (`integrity_verified`). The storage layer is a local directory today; the service interface is the swap point for object storage.

## Frontend & Motion Architecture

```
app/                    11 workstation route pages ("use client", React Query driven, AnimatePresence route transitions)
components/
  layout/               AppShell (AnimatePresence), Sidebar (layoutId active pill indicator), Header
  common/               ui primitives (Card, Motion Button, Badge, DataTable, Modal, CopyButton, RiskBadge)
  charts/               Recharts wrappers (area, donut, bar, horizontal bars)
  graph/                GraphCanvas (D3 Force Canvas + layered topology layout + exports)
  wallet/               overview cards, threat banner, risk panel, tx table, threat panel, OSINT panel
lib/                    api client (typed envelope), query client, formatters, zod validators, constants
hooks/                  useInvestigation (pipeline stepper), useHealth, useTheme
types/                  API-facing TypeScript interfaces
```

- **Framer Motion Engine**: Top-level page transitions via `AnimatePresence`, active route navigation pill with `layoutId` physics spring transitions, and staggered component entry on executive dashboards.
- **Master Documentation**: For full technical specifications, data flow diagrams, and schema definitions, see [docs/SYSTEM_DESIGN.md](SYSTEM_DESIGN.md).

## Extension points

| Want to add… | Do this |
|---|---|
| A new blockchain | New `BlockchainProvider` subclass + entry in `factory._PROVIDERS` + validation in `utils/address_validation` |
| A real OSINT API | New `OSINTProvider` subclass, add to `PROVIDERS` list |
| Object storage for evidence | Replace file I/O inside `evidence_service.save_upload/download_evidence` |
| Authentication | FastAPI dependency on routers + investigator identity in `audit.log_action`; PyJWT already in the stack guidance |
| Alembic migrations | `alembic init` pointed at `app.core.database.Base.metadata` (see docs/DATABASE.md) |
