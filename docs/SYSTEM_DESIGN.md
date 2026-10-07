# ChainIntel — Master System Design & Technical Specification

> **System Edition:** Workstation v2.0  
> **Target Environment:** Multi-Chain OSINT & Forensic Cryptocurrency Telemetry  
> **Repository:** [ChainIntel GitHub](https://github.com/arsh-siddiqui/ChainIntel)

---

## 1. Executive Summary & Core Objective

**ChainIntel** is a production-grade, high-performance **Blockchain Intelligence & OSINT Investigation Engine**. Designed for cybersecurity researchers, digital forensics teams, and compliance analysts, ChainIntel provides real-time transaction tracing, heuristic risk assessment, interactive D3 force-directed fund flow mapping, threat intelligence correlation, and court-admissible dossier generation.

---

## 2. High-Level Architecture

ChainIntel follows a decoupled, **Layered Client-Server Architecture** operating over standardized REST APIs and Server-Sent Events (SSE).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       NEXT.JS 14 FRONTEND WORKSTATION                       │
│ (App Router • Framer Motion • TanStack Query • Tailwind CSS • D3 Graph Canvas) │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / REST / SSE Streaming
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                            FASTAPI BACKEND ENGINE                           │
│     (Async ASGI • CORS Security • Rate Limiting • API Envelope Specs)       │
├─────────────────────────────────────────────────────────────────────────────┤
│                           SERVICE & ANALYTICS LAYER                         │
│  ┌──────────────────┬──────────────────┬──────────────────┬──────────────┐  │
│  │ Wallet Analytics │ Graph Heuristics │ Threat Intel     │ OSINT Scraper│  │
│  ├──────────────────┼──────────────────┼──────────────────┼──────────────┤  │
│  │ Risk Score Engine│ Alert Engine SSE │ Report Generator │ Audit Logger │  │
│  └──────────────────┴──────────────────┴──────────────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                      MULTI-CHAIN RPC FAILOVER ADAPTER ENGINE                │
│   ┌───────────────┬───────────────────┬────────────────┬────────────────┐   │
│   │ Bitcoin (BTC) │ EVM (ETH,BSC,Poly)│ Solana (SOL)   │ Moralis / Ankr │   │
│   └───────────────┴───────────────────┴────────────────┴────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                         PERSISTENCE & STORAGE LAYER                         │
│ (SQLAlchemy ORM • Alembic Migrations • SQLite / PostgreSQL • File Storage)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Modules & Component Architecture

### 3.1 Frontend Workstation (Next.js 14 + Framer Motion)
- **App Router Architecture**: 11 dedicated workstation routes (`/dashboard`, `/wallet`, `/graph`, `/threat-intelligence`, `/osint`, `/transactions`, `/alerts`, `/investigations`, `/evidence`, `/reports`, `/settings`).
- **Interactive Motion Engine**: `AnimatePresence` top-level page slide transitions, Framer Motion `layoutId="sidebar-active-pill"` physics spring indicator for navigation, staggered container animations for executive KPI dashboards.
- **Visual Canvas Engine**: Interactive D3 force-directed canvas rendering fund flow topologies with value-proportional edge thickness, leaf-node clustering, and multi-hop node tracing.
- **Typography & Theme System**: Responsive dark/light theme switching with custom Google Fonts (`Plus Jakarta Sans` & `JetBrains Mono`), cyber glassmorphic panels, and tailored risk badge indicators.

### 3.2 Backend Forensic Engine (FastAPI + Python 3.11+)
- **Asynchronous Execution**: Built on Starlette/Uvicorn ASGI runner for low-latency non-blocking network I/O.
- **API Envelope Specification**: Every HTTP endpoint wraps output in a predictable structure:
  ```json
  {
    "success": true,
    "data": { ... },
    "error": null,
    "meta": { "timestamp": 1728323500, "count": 25 }
  }
  ```
- **Real-Time Streaming**: Server-Sent Events (SSE) streaming (`/api/alerts/stream`) delivering immediate alert pushes to active analyst sessions.

---

## 4. Multi-Chain RPC Failover & Provider Abstraction

ChainIntel implements an autonomous **RPC Provider Fallback Engine** (`backend/app/services/blockchain/`).

```
Request Wallet / TX Data
         │
         ▼
 ┌──────────────────────┐
 │  Chain Auto-Detector │
 └──────────┬───────────┘
            │
            ├──────► Bitcoin ─────► Primary: Mempool.space ──(On 429/Err)──► Fallback: Blockchain.info
            │
            ├──────► EVM Chains ──► Primary: Etherscan v2 ──(On 429/Err)──► Secondary: Moralis ──► Fallback: Ankr
            │
            └──────► Solana ──────► Primary: Solana Mainnet-Beta RPC ──► Fallback: Preseeded Telemetry
```

---

## 5. Database Schema & Data Models

Managed via **SQLAlchemy 2.0 ORM** and **Alembic** migrations (`backend/app/models/`):

1. **`Wallet`**: Indexed target wallets with balances, threat level, and verification status.
2. **`Transaction`**: On-chain transfer records with normalized token values and block hashes.
3. **`ThreatIntel`**: Malicious entity database (OFAC sanctions, ransomware attributions, darknet mixers).
4. **`OsintRecord`**: Extracted web metadata, Etherscan labels, and public forum attributions.
5. **`Case`**: Forensic investigation dossiers with investigator assignments and priority status.
6. **`Evidence`**: Chain-of-custody evidence files with mandatory **SHA-256 cryptographic checksums**.
7. **`MonitoringRule` & `Alert`**: Automated watcher conditions and triggered threshold events.
8. **`AuditLog`**: Immutable ledger of all investigator actions for legal compliance.

---

## 6. Security, Integrity & Compliance

- **Cryptographic Evidence Verification**: Every uploaded file is hashed at rest with SHA-256. Re-validation checks ensure file integrity has not been tampered with.
- **Sanitization & RegEx Validation**: Multichain regex validators enforce target address formats before network queries (`0x...` EVM, `1...`/`3...`/`bc1...` BTC, Base58 SOL).
- **Environment Isolation**: API credentials are standard server-side secrets, never exposed to client browsers.

---

## 7. Testing Strategy (109/109 Tests Passing)

The project includes a comprehensive **pytest** backend testing suite (`backend/tests/`):

- **Unit & Provider Tests**: RPC failover provider cascades, risk engine score weighting, multichain regex validation.
- **Integration & Pipeline Tests**: Complete E2E investigation workflow, case dossier exports, threat CSV/JSON importer validation.
- **Verification Execution**: `109 passed in 7.02s`.

---

## 8. CI/CD & Deployment Pipeline

- **Frontend**: Deployed on **Vercel** (`Next.js 14 App Router` static + dynamic builds).
- **Backend**: Containerized via **Docker**, **docker-compose**, and **Render** (`render.yaml`).
- **Automation Scripts**: Standalone `start-app.bat` and `start-app.ps1` scripts for one-click local desktop launch.
