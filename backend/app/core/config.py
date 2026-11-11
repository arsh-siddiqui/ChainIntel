"""Application configuration loaded from environment variables / .env."""
from __future__ import annotations

import os
import re
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def is_render() -> bool:
    """Detect whether running in Render environment."""
    return os.environ.get("RENDER") is not None or os.path.exists("/var/data")


def ensure_db_directory(url: str) -> None:
    """Extract directory path from a SQLite database URL and create it if missing."""
    if not url or not url.startswith("sqlite"):
        return
    # Strip sqlite: prefix variations
    path_part = url
    for prefix in ("sqlite:////", "sqlite:///", "sqlite://"):
        if path_part.startswith(prefix):
            path_part = path_part[len(prefix):]
            if prefix == "sqlite:////" and not path_part.startswith("/"):
                path_part = "/" + path_part
            break
    if not path_part or path_part == ":memory:":
        return
    # Strip query parameters if present
    path_part = path_part.split("?")[0]
    dir_path = os.path.dirname(path_part)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)


def normalize_database_url(url: str) -> str:
    """Normalize SQLite database URLs for SQLAlchemy.
    
    Accepts full SQLite URLs (sqlite:////path, sqlite:///./path) or raw file paths.
    Ensures directories exist and guarantees compatibility across platforms.
    """
    if not url:
        default_db = "/var/data/chainintel.db" if is_render() else "./data/chainintel.db"
        res = f"sqlite:///{default_db}" if default_db.startswith("/") else f"sqlite:///{default_db}"
        if is_render() and not res.startswith("sqlite:////"):
            res = "sqlite:////var/data/chainintel.db"
        ensure_db_directory(res)
        return res

    cleaned = url.strip()

    # Legacy PostgreSQL URL fallback to SQLite
    if cleaned.startswith("postgres://") or cleaned.startswith("postgresql://"):
        cleaned = "sqlite:////var/data/chainintel.db" if is_render() else "sqlite:///./data/chainintel.db"

    # Raw file path conversion
    if not cleaned.startswith("sqlite"):
        if cleaned.startswith("/"):
            cleaned = f"sqlite:///{cleaned}"
        else:
            cleaned = f"sqlite:///{cleaned}"

    # Normalize absolute unix path (3 slashes to 4 slashes)
    if cleaned.startswith("sqlite:///var/data"):
        cleaned = cleaned.replace("sqlite:///var/data", "sqlite:////var/data", 1)

    ensure_db_directory(cleaned)
    return cleaned


def sanitize_database_url(url: str) -> str:
    """Mask credentials in database URL for safe logging."""
    if not url:
        return "not_configured"
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:****@", url)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ChainIntel"
    app_version: str = "1.0.0"
    app_mode: str = "LIVE"

    database_url: str = ""
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
    evidence_dir: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str | None) -> str:
        raw = str(v).strip() if v is not None and str(v).strip() else ""
        return normalize_database_url(raw)

    @field_validator("evidence_dir", mode="before")
    @classmethod
    def validate_evidence_dir(cls, v: str | None) -> str:
        if v is not None and str(v).strip():
            dir_path = str(v).strip()
        elif is_render():
            dir_path = "/var/data/evidence"
        else:
            dir_path = "./data/evidence"
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    @property
    def effective_database_url(self) -> str:
        """Return the effective normalized SQLite database URL."""
        if self.database_url and self.database_url.strip():
            url = normalize_database_url(self.database_url)
        elif is_render():
            url = "sqlite:////var/data/chainintel.db"
        else:
            url = "sqlite:///./data/chainintel.db"
        ensure_db_directory(url)
        return url

    @property
    def effective_evidence_dir(self) -> str:
        """Return the effective evidence directory, ensuring it exists."""
        dir_path = self.evidence_dir if self.evidence_dir and self.evidence_dir.strip() else (
            "/var/data/evidence" if is_render() else "./data/evidence"
        )
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    @property
    def sanitized_database_url(self) -> str:
        """Sanitized DB URL for safe logging."""
        return sanitize_database_url(self.effective_database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
