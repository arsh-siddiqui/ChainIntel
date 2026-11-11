"""One-time database schema initialization and idempotent seeding command.

Used during deployment or setup to run migrations/schemas and initial seeding
in a separate one-time step BEFORE starting Gunicorn workers.

Usage:
    python -m app.core.init_db
"""
from __future__ import annotations

import sys
from app.core.database import init_db
from app.core.logging import get_logger

logger = get_logger("init_db")


def main() -> None:
    logger.info("Executing one-time database schema creation and idempotent seed...")
    try:
        init_db(seed=True)
        logger.info("One-time database initialization completed successfully.")
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
