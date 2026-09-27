# ChainIntel Backend

FastAPI service powering the ChainIntel blockchain OSINT platform.

## Quickstart

```bash
pip install -r requirements.txt
copy .env.example .env        # macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on first start. Bitcoin investigations work keylessly; add an Etherscan/Moralis/Ankr key to `.env` for Ethereum and BSC.

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/api/health

## Tests

```bash
python -m pytest              # hermetic suite (84 tests; no network access, no API keys)
```

## Layout

- `app/core/` — config, database, logging, security middleware, response envelope
- `app/models/` — SQLAlchemy ORM models (indexed)
- `app/schemas/` — Pydantic request schemas
- `app/routers/` — thin HTTP layer per domain
- `app/services/` — business logic (live blockchain providers, pipeline, graph, risk, threats, OSINT, monitoring, alerts, cases, evidence, reports)
- `app/utils/` — address validation, hashing, datetime, pagination
- `migrations/` — Alembic setup (initial schema revision included)
- `tests/` — pytest suite (uses a deterministic fake provider; never touches real APIs)

See the root `README.md` and `docs/` for architecture, API and security details.
