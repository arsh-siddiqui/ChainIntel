"""Application configuration loaded from environment variables / .env."""
from __future__ import annotations

import re
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Normalize database URLs for SQLAlchemy.
    
    Render PostgreSQL URLs (postgres:// or postgresql://) are normalized to
    postgresql+psycopg:// for the psycopg v3 driver.
    """
    if not url:
        return ""
    cleaned = url.strip()
    if cleaned.startswith("postgres://"):
        return cleaned.replace("postgres://", "postgresql+psycopg://", 1)
    if cleaned.startswith("postgresql://") and "+psycopg" not in cleaned and "+psycopg2" not in cleaned:
        return cleaned.replace("postgresql://", "postgresql+psycopg://", 1)
    return cleaned


def sanitize_database_url(url: str) -> str:
    """Mask password in database URL for safe logging."""
    if not url:
        return "not_configured"
    # Replace password in postgresql+psycopg://user:password@host:port/db
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:****@", url)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ChainIntel"
    app_version: str = "1.0.0"
    app_mode: str = "LIVE"

    database_url: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_db: str = "chainintel"

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Blockchain providers (LIVE mode)
    bitcoin_api_url: str = "https://blockchain.info"
    mempool_api_url: str = "https://mempool.space/api"
    etherscan_api_key: str = ""
    etherscan_api_url: str = "https://api.etherscan.io/v2/api"
    bscscan_api_key: str = ""
    moralis_api_key: str = ""
    moralis_api_url: str = "https://deep-index.moralis.io/api/v2.2"
    ankr_api_key: str = ""
    ankr_api_url: str = "https://rpc.ankr.com/multichain"
    blockchain_api_key: str = ""

    # OSINT
    osint_provider_enabled: bool = False

    # Monitoring engine
    poll_interval_seconds: int = 60
    monitoring_enabled: bool = True

    # Security / limits
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    max_upload_mb: int = 10
    evidence_dir: str = "./data/evidence"

    @property
    def effective_database_url(self) -> str:
        """Return the effective normalized database URL.
        
        Rules:
        1. If DATABASE_URL is present in env/.env, it is ALWAYS used (never falls back to localhost).
        2. If postgres_password is set, constructs PostgreSQL URL.
        3. Only defaults to SQLite for local development when DATABASE_URL is absent.
        """
        if self.database_url and self.database_url.strip():
            return normalize_database_url(self.database_url)
        if self.postgres_password:
            raw = f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            return normalize_database_url(raw)
        return "sqlite:///./data/chainintel.db"

    @property
    def sanitized_database_url(self) -> str:
        """Sanitized DB URL for safe logging without exposing passwords."""
        return sanitize_database_url(self.effective_database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
