"""Application configuration loaded from environment variables / .env."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ChainIntel"
    app_version: str = "1.0.0"
    app_mode: str = "LIVE"  # ChainIntel runs against real blockchain APIs only

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
    # Optional blockchain.info api_code (higher rate limits); public endpoints work without it.
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
        url = self.database_url.strip() if self.database_url else ""
        if url:
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql://") and "+psycopg" not in url and "+psycopg2" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url
        if self.postgres_password:
            return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        return "sqlite:///./data/chainintel.db"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

