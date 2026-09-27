# ChainIntel — Security

## Scope & posture

ChainIntel is a **read-only analysis platform**. It never holds keys, never signs transactions, and has no fund-movement capability. The security goals are: protect investigators from malicious input, protect the integrity of evidence, and never misrepresent data provenance.

## Implemented controls

### Input validation
- Every address passes the validation engine (Base58Check decode with checksum, Bech32 checksum, EVM hex + optional EIP-55 checksum) before any provider call. Simulated `DEMO-*` addresses are rejected — the platform operates against real blockchains only.
- All request bodies are validated by Pydantic schemas (typed fields, length caps, literal enums, confidence ranges 0–1).
- Query parameters use FastAPI `Query` constraints (`ge/le`, `pattern`) — e.g. hops are clamped 1–7, sort columns are whitelisted.

### SQL injection
All database access uses SQLAlchemy ORM expressions with parameter binding. There is no string-concatenated SQL anywhere in the codebase.

### Uploads
- Extension allow-list: `.png .jpg .jpeg .gif .webp .pdf .txt .csv .json .zip .log .md .har`
- Size limit: `MAX_UPLOAD_MB` (default 10 MB), enforced both by middleware (`Content-Length`) and at read time.
- Stored names are server-generated (`uuid + sanitized basename`, characters restricted to `[A-Za-z0-9._-]`); original names are kept only as metadata.
- SHA-256 is computed over stored bytes; the evidence API recomputes and compares on demand (`integrity_verified`).

### Rate limiting & request size
- Sliding-window per-IP limiter (`RATE_LIMIT_REQUESTS` per `RATE_LIMIT_WINDOW_SECONDS`, default 120/60s) as middleware; docs/redoc paths exempt.
- Requests above the size cap are rejected with `413` before being read.
- Live blockchain polling enforces a per-wallet minimum interval (`MIN_LIVE_POLL_SECONDS`) and polite pagination sleeps to respect upstream rate limits.

### Secrets
- Keys live only in environment variables / `backend/.env` (git-ignored).
- `/api/settings/*` reports **configured vs not-configured** booleans and never returns key values; the database URL is redacted to its scheme.
- `.env.example` files contain no real credentials.

### CORS & errors
- CORS restricted to `CORS_ORIGINS` (default `http://localhost:3000`); credentials disabled.
- A global exception handler converts all unhandled errors to a sanitized envelope (`INTERNAL_ERROR`) — stack traces are logged server-side only, never sent to clients.

### Prohibited by design
- No private-key or seed-phrase input fields exist anywhere (frontend or API).
- No transaction construction, signing, or broadcast functionality.
- No scraping or crawling of dark-web sources; restricted-source records exist only as explicitly imported or analyst-entered evidence with source attribution.

## Data-provenance guarantees

| Data kind | Guarantee |
|---|---|
| Live blockchain data | Comes only from configured providers; failures raise typed errors — the system never substitutes synthetic data |
| OSINT | Simulated providers are labeled "(Simulated)"; link-only sources return `UNAVAILABLE` with an external search URL and no fabricated findings |
| Risk output | Always accompanied by the disclaimer: *"Risk score is an analytical indicator and not a determination of unlawful activity."* |

## Audit trail
Important investigator actions are recorded in `audit_log` with timestamp, action, resource, and metadata: wallet investigated, transaction viewed, case created/updated, investigation linked, evidence uploaded, alert status updated, monitor created/updated/deleted, threat database imported, report generated.

## Known limitations
- The deployment is single-user ("Investigator"); authentication is a future extension point (a JWT dependency slot is reserved in the architecture).
- The rate limiter is in-memory — for multi-node deployments, front the API with a shared limiter (e.g., a reverse proxy).
- Evidence files are stored on local disk; use object storage with server-side encryption for production.
