"""Threat intelligence service: wallet matching, dataset management and import."""
from __future__ import annotations

import csv
import io
import json
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.envelope import AppError
from app.core.logging import get_logger
from app.models import ThreatFinding, THREAT_CATEGORIES
from app.utils.address_validation import validate_address
from app.utils.datetime import parse_date
from app.utils.pagination import clamp, meta

logger = get_logger("threats")

CATEGORY_ALIASES = {
    "ransomware": "Ransomware",
    "scam": "Scam",
    "phishing": "Phishing",
    "blacklist": "Blacklist",
    "blacklisted": "Blacklist",
    "fraud": "Fraud",
    "exploit": "Exploit",
    "suspicious service": "Suspicious Service",
    "suspicious_service": "Suspicious Service",
    "mixer": "Suspicious Service",
    "mixer/service": "Suspicious Service",
    "service": "Suspicious Service",
    "unknown": "Unknown",
}


def normalize_category(raw: str | None) -> str | None:
    if not raw:
        return None
    key = raw.strip().lower().replace("-", " ").replace("_", " ")
    key = " ".join(key.split())
    if key in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[key]
    return raw.strip().title() if raw.strip().title() in THREAT_CATEGORIES else None


def match_wallet(db: Session, address: str) -> list[ThreatFinding]:
    return db.query(ThreatFinding).filter(ThreatFinding.wallet_address == address).all()


def match_addresses(db: Session, addresses: list[str]) -> list[ThreatFinding]:
    if not addresses:
        return []
    return db.query(ThreatFinding).filter(ThreatFinding.wallet_address.in_(addresses)).all()


def list_threats(
    db: Session,
    search: str | None = None,
    category: str | None = None,
    source: str | None = None,
    page: int = 1,
    page_size: int = 25,
):
    page, page_size = clamp(page, page_size)
    query = db.query(ThreatFinding)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                ThreatFinding.wallet_address.ilike(like),
                ThreatFinding.label.ilike(like),
                ThreatFinding.source.ilike(like),
            )
        )
    if category:
        query = query.filter(ThreatFinding.category == category)
    if source:
        query = query.filter(ThreatFinding.source.ilike(f"%{source}%"))
    total = query.count()
    items = query.order_by(ThreatFinding.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, meta(page, page_size, total)


def category_stats(db: Session) -> list[dict[str, Any]]:
    rows = db.query(ThreatFinding.category).all()
    counts: dict[str, int] = {}
    for (category,) in rows:
        counts[category] = counts.get(category, 0) + 1
    return [{"category": c, "count": n} for c, n in sorted(counts.items(), key=lambda kv: -kv[1])]


def parse_import_file(filename: str, content: bytes) -> list[dict[str, Any]]:
    name = (filename or "").lower()
    text = content.decode("utf-8-sig", errors="replace")
    if name.endswith(".json"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AppError(400, "IMPORT_PARSE_ERROR", f"Invalid JSON file: {exc}") from exc
        if isinstance(data, dict):
            data = data.get("records") or data.get("data") or []
        if not isinstance(data, list):
            raise AppError(400, "IMPORT_PARSE_ERROR", "JSON import must be an array of records.")
        return [dict(r) for r in data if isinstance(r, dict)]
    if name.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(text))
        records = []
        for row in reader:
            cleaned = {(k or "").strip().lower().replace(" ", "_"): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k is not None}
            records.append(cleaned)
        return records
    raise AppError(400, "IMPORT_FORMAT_ERROR", "Unsupported file type. Upload a .csv or .json file.")


def _validate_record(index: int, raw: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    address = str(raw.get("address") or raw.get("wallet_address") or "").strip()
    label = str(raw.get("label") or "").strip()
    source = str(raw.get("source") or "").strip()
    if not address:
        return None, f"row {index}: missing required field 'address'"
    if not label:
        return None, f"row {index}: missing required field 'label'"
    if not source:
        return None, f"row {index}: missing required field 'source'"
    validation = validate_address(address)
    if not validation["valid"]:
        return None, f"row {index}: invalid address format ({validation['reason']})"

    category = normalize_category(str(raw.get("category") or "Unknown"))
    if category is None:
        return None, f"row {index}: unknown category '{raw.get('category')}' (allowed: {', '.join(THREAT_CATEGORIES)})"

    try:
        confidence = float(raw.get("confidence", 0.5) or 0.5)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError
    except (TypeError, ValueError):
        return None, f"row {index}: confidence must be a number between 0 and 1"

    first_seen = parse_date(str(raw["first_seen"])) if raw.get("first_seen") else None
    last_seen = parse_date(str(raw["last_seen"])) if raw.get("last_seen") else None
    if raw.get("first_seen") and first_seen is None:
        return None, f"row {index}: unparseable first_seen '{raw.get('first_seen')}' (use ISO dates)"
    if raw.get("last_seen") and last_seen is None:
        return None, f"row {index}: unparseable last_seen '{raw.get('last_seen')}' (use ISO dates)"

    reference_url = raw.get("reference_url") or None
    if reference_url and not str(reference_url).lower().startswith(("http://", "https://")):
        return None, f"row {index}: reference_url must start with http:// or https://"

    detection = validate_address(address)
    if detection["blockchain"] == "demo":
        return None, f"row {index}: DEMO- prefixed simulated addresses are not supported (live blockchain addresses only)"
    return {
        "wallet_address": address,
        "blockchain": detection["blockchain"] or str(raw.get("blockchain") or "unknown"),
        "category": category,
        "label": label,
        "source": source,
        "reference_url": reference_url,
        "confidence": confidence,
        "first_seen": first_seen,
        "last_seen": last_seen,
        "notes": raw.get("notes") or None,
        "status": "IMPORTED",
        "is_demo": False,
    }, None


def import_records(db: Session, records: list[dict[str, Any]]) -> dict[str, Any]:
    stats = {"received": len(records), "valid": 0, "invalid": 0, "duplicates": 0, "inserted": 0, "updated": 0, "errors": []}
    seen_keys: set[tuple] = set()
    for index, raw in enumerate(records, start=1):
        record, error = _validate_record(index, raw)
        if error:
            stats["invalid"] += 1
            if len(stats["errors"]) < 50:
                stats["errors"].append(error)
            continue
        key = (record["wallet_address"], record["source"], record["category"], record["label"])
        if key in seen_keys:
            stats["duplicates"] += 1
            continue
        seen_keys.add(key)
        stats["valid"] += 1
        existing = (
            db.query(ThreatFinding)
            .filter(
                ThreatFinding.wallet_address == record["wallet_address"],
                ThreatFinding.source == record["source"],
                ThreatFinding.category == record["category"],
                ThreatFinding.label == record["label"],
            )
            .one_or_none()
        )
        if existing:
            for field in ("reference_url", "confidence", "first_seen", "last_seen", "notes", "blockchain"):
                if record.get(field) is not None:
                    setattr(existing, field, record[field])
            stats["updated"] += 1
        else:
            db.add(ThreatFinding(**record))
            stats["inserted"] += 1
    db.commit()
    logger.info("Threat import finished: %s", {k: v for k, v in stats.items() if k != "errors"})
    return stats
