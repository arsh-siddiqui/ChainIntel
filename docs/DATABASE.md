# ChainIntel — Database

## Engines

| Engine | When | Configure via |
|---|---|---|
| SQLite | Local development (default) | `DATABASE_URL=sqlite:///./data/chainintel.db` |
| PostgreSQL 14+ | Production (preferred) | `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/chainintel` |

Both engines are supported by the same SQLAlchemy 2.x models. PostgreSQL is exercised in the provided `docker-compose.yml`. SQLite connections disable `check_same_thread` for the FastAPI threadpool.

## Schema creation

Tables are created automatically on first application start (`init_db` in the FastAPI lifespan runs `Base.metadata.create_all`). There is no seeder — the live-only application starts with an empty database and fills it as investigations run.

## Migrations

Alembic is wired and ready: `backend/migrations/` targets `app.core.database.Base.metadata` with all 12 models registered, and the initial schema revision ships in `migrations/versions/`. For production upgrades use migrations instead of relying on `create_all`:

```bash
cd backend
alembic upgrade head                 # create/evolve the schema
alembic revision --autogenerate -m "<change>"   # generate new migrations from model changes
alembic downgrade -1                 # roll back the last revision
```

The database URL is read from `app.core.config.settings.database_url` (set `DATABASE_URL` in the environment or `backend/.env`), so the same migrations work against SQLite and PostgreSQL.

## Models

| Table | Purpose | Key columns |
|---|---|---|
| `wallets` | Wallet profiles | `address`, `blockchain`, `label`, `balance`, `asset`, `first_seen`, `last_seen`, `transaction_count`, `is_demo` |
| `transactions` | Normalized ledger | `tx_hash`, `blockchain`, `from_address`, `to_address`, `amount`, `asset`, `timestamp`, `block_number`, `confirmations`, `status`, `fee`, `raw`, `is_demo` |
| `investigations` | Wallet analysis runs | `case_id` (FK), `wallet_address`, `blockchain`, `status`, `risk_level`, `risk_score`, `notes`, `payload` (JSON bundle), `investigator` |
| `threat_findings` | Threat dataset records | `wallet_address`, `category`, `label`, `source`, `reference_url`, `confidence`, `first_seen`, `last_seen`, `status`, `is_demo` |
| `osint_findings` | OSINT results & restricted records | `wallet_address`, `source`, `source_category` (public/restricted/analyst), `record_type`, `finding`, `status`, `confidence`, `reference_url`, `observed_at` |
| `cases` | Investigation cases | `case_number` (unique), `title`, `description`, `status`, `priority`, `investigator` |
| `case_events` | Case timeline | `case_id` (FK), `event_type`, `description`, `created_at` |
| `alerts` | Generated alerts | `wallet_address`, `rule` (JSON), `transaction_hash`, `severity`, `status`, `is_demo` |
| `monitored_wallets` | Monitoring rules | `wallet_address` (unique), `rules` (JSON), `status`, `last_checked`, `last_tx_hash` |
| `evidence` | Chain-of-custody items | `case_id` (FK), `type`, `title`, `file_path`, `sha256`, `size_bytes`, `content_text` |
| `reports` | Generated reports | `id` (uuid), `case_id` (FK), `wallet_address`, `mode`, `payload` (JSON) |
| `audit_log` | Action history | `action`, `resource_type`, `resource_id`, `investigator`, `metadata` (JSON), `timestamp` |

## Indexes

Explicit indexes (beyond primary keys):

- `wallets`: unique `(address, blockchain)`, `blockchain`
- `transactions`: `tx_hash`, unique `(tx_hash, from_address, to_address)`, `from_address`, `to_address`, `(blockchain, timestamp)`, `timestamp`
- `investigations`: `wallet_address`
- `threat_findings`: unique `(wallet_address, source, category, label)`, `category`, `source`
- `osint_findings`: `wallet_address`, `observed_at`
- `cases`: `case_number` (unique), `status`, `created_at`
- `case_events`: `case_id`
- `alerts`: `status`, `wallet_address`
- `monitored_wallets`: unique `wallet_address`
- `evidence`: `case_id`, `sha256`
- `audit_log`: `action`, `timestamp`

## Data integrity notes

- All timestamps are naive UTC; ISO-8601 with `Z` suffix is emitted by serializers.
- Transaction deduplication is enforced at the database level by the `(tx_hash, from_address, to_address)` unique constraint — repeated investigations never duplicate rows.
- Threat imports dedupe on `(wallet_address, source, category, label)`; duplicates are counted and existing records are updated in place.
