# ChainIntel — Database

## Engine

| Engine | When | Configure via | Database Path |
|---|---|---|---|
| SQLite | Local development (default) | `DATABASE_URL=sqlite:///./data/chainintel.db` | `./data/chainintel.db` |
| SQLite | Production / Render | `DATABASE_URL=sqlite:////var/data/chainintel.db` | `/var/data/chainintel.db` |

The platform uses **SQLite** across all environments (local development, Docker containers, and Render cloud deployments). SQLite connections are configured with:
- `check_same_thread=False` to safely support multi-threaded FastAPI workers and connection pools.
- `PRAGMA foreign_keys=ON` automatically enabled via SQLAlchemy connection event hooks to enforce relational integrity.
- Automatic directory provisioning for missing parent paths (e.g. `/var/data` or `./data`).
- Persistent storage mounted on `/var/data` on Render and in Docker Compose.

## Schema Creation & Initialization

Tables are created automatically on application start (`init_db` in the FastAPI lifespan runs `Base.metadata.create_all`).
Demo seeding is idempotent: records are checked against existing data before insertion to ensure no duplicates are ever created.

## Migrations

Alembic is wired with SQLite batch mode (`render_as_batch=True`) enabled: `backend/migrations/` targets `app.core.database.Base.metadata` with all 12 models registered, and the initial schema revision ships in `migrations/versions/`. For upgrades:

```bash
cd backend
alembic upgrade head                            # create/evolve the schema
alembic revision --autogenerate -m "<change>"   # generate new migrations from model changes
alembic downgrade -1                            # roll back the last revision
```

The database URL is read from `app.core.config.settings.database_url` (or environment variable `DATABASE_URL`).

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

## Indexes & Constraints

- `wallets`: unique `(address, blockchain)`, `blockchain`
- `transactions`: `tx_hash`, unique `(tx_hash, from_address, to_address)`, `from_address`, `to_address`, `(blockchain, timestamp)`, `timestamp`
- `investigations`: `wallet_address`
- `threat_findings`: unique `(wallet_address, source, category, label)`, `category`, `source`
- `osint_findings`: `wallet_address`, `observed_at`
- `cases`: `case_number` (unique), `status`, `created_at`
- `case_events`: `case_id` (FK to `cases.id`)
- `alerts`: `status`, `wallet_address`
- `monitored_wallets`: unique `wallet_address`
- `evidence`: `case_id` (FK to `cases.id`), `sha256`
- `audit_log`: `action`, `timestamp`

## Data Integrity Notes

- All timestamps are UTC datetime objects.
- Transaction deduplication is enforced at the database level by the `(tx_hash, from_address, to_address)` unique constraint.
- Threat imports dedupe on `(wallet_address, source, category, label)`; existing records are updated in place.
- Foreign keys are enforced via `PRAGMA foreign_keys=ON` on every SQLite connection.
