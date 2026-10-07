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


KNOWN_ENTITIES = {
    # Bitcoin Genesis & Exchanges
    "1a1zp1ep5qgefi2dmptftl5slmv7divfna": {"label": "Satoshi Nakamoto / Genesis Address", "category": "Blacklist", "source": "Bitcoin Genesis Block"},
    "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo": {"label": "Binance Cold Wallet", "category": "Suspicious Service", "source": "Binance Infrastructure"},
    "bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr": {"label": "Bitfinex Cold Storage", "category": "Suspicious Service", "source": "Bitfinex Infrastructure"},
    "1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ": {"label": "Binance Hot Wallet 1", "category": "Suspicious Service", "source": "Binance Infrastructure"},
    # EVM Exchanges & Mixers & Exploits
    "0x28c6c06298d514db089934071355e5743bf21d60": {"label": "Binance 14 (Hot Wallet)", "category": "Suspicious Service", "source": "Binance EVM"},
    "0x7160ec9412b075c370e8550c5412469959779e9e": {"label": "Coinbase 1 (Hot Wallet)", "category": "Suspicious Service", "source": "Coinbase EVM"},
    "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503": {"label": "Binance Hot Wallet 6", "category": "Suspicious Service", "source": "Binance EVM"},
    "0x0000000000000000000000000000000000000000": {"label": "Null / Burn Address", "category": "Blacklist", "source": "EVM Protocol"},
    "0xd8da6bf26964af9d7eed9e03e53415d37aa96045": {"label": "vitalik.eth (Vitalik Buterin)", "category": "Suspicious Service", "source": "ENS Public Registry"},
    "0x12d6621e19a95080e0276664261065623b1a0623": {"label": "Tornado.Cash 0.1 ETH Mixer", "category": "Mixer", "source": "OFAC Sanctions List"},
    "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": {"label": "Tornado.Cash 1 ETH Mixer", "category": "Mixer", "source": "OFAC Sanctions List"},
    "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf": {"label": "Tornado.Cash 10 ETH Mixer", "category": "Mixer", "source": "OFAC Sanctions List"},
    "0xa160cd373370618f30b240960c381d650eb19b0d": {"label": "Tornado.Cash 100 ETH Mixer", "category": "Mixer", "source": "OFAC Sanctions List"},
    "0x098b716b8aaf21512996dc57eb0615e2383e2f96": {"label": "Ronin Bridge $620M Exploit (Lazarus Group)", "category": "Exploit", "source": "FBI / Cyber Crime Alert"},
    "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9": {"label": "FTX Accounts Drainer / Hacker", "category": "Exploit", "source": "Exchange Breach Incident"},
    "0x444d852655513ab4a88f73a3aa5fe9422df56e92": {"label": "BSC Token Hub Drainer ($570M Hack)", "category": "Exploit", "source": "BNB Chain Security Alert"},
    "0x3c783c21a0383057d128bae3314a4e461721b765": {"label": "Polygon ERC20 Bridge Vault", "category": "Suspicious Service", "source": "Polygon Protocol Registry"},
    # Solana Threats
    "5vcwktptjphupybwxsyjhayhotrbjv49d3p48jkbfe3f": {"label": "FTX Solana Drainer Address", "category": "Exploit", "source": "Solana Incident Registry"},
    "4k3dyjzvzp8emzwuxbcjevwskkk59s5icnly3qrke3r": {"label": "Raydium Liquidity Pool Authority", "category": "Suspicious Service", "source": "Solana Protocol Registry"},
}


def match_wallet(db: Session, address: str) -> list[ThreatFinding]:
    db_matches = db.query(ThreatFinding).filter(ThreatFinding.wallet_address == address).all()
    addr_lower = (address or "").strip().lower()
    if addr_lower in KNOWN_ENTITIES and not any(m.label == KNOWN_ENTITIES[addr_lower]["label"] for m in db_matches):
        meta_info = KNOWN_ENTITIES[addr_lower]
        synthetic = ThreatFinding(
            wallet_address=address,
            label=meta_info["label"],
            category=meta_info["category"],
            source=meta_info["source"],
            confidence=0.99,
        )
        db_matches.insert(0, synthetic)
    return db_matches


def match_addresses(db: Session, addresses: list[str]) -> list[ThreatFinding]:
    if not addresses:
        return []
    db_matches = db.query(ThreatFinding).filter(ThreatFinding.wallet_address.in_(addresses)).all()
    for addr in addresses:
        addr_lower = (addr or "").strip().lower()
        if addr_lower in KNOWN_ENTITIES and not any(m.wallet_address == addr for m in db_matches):
            meta_info = KNOWN_ENTITIES[addr_lower]
            db_matches.append(
                ThreatFinding(
                    wallet_address=addr,
                    label=meta_info["label"],
                    category=meta_info["category"],
                    source=meta_info["source"],
                    confidence=0.99,
                )
            )
    return db_matches


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
        if error or record is None:
            stats["invalid"] += 1
            if len(stats["errors"]) < 50 and error:
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
