"""Wallet investigation pipeline.

POST /api/wallets/investigate runs this pipeline:
validate -> identify blockchain -> provider query -> wallet profile ->
transaction normalization -> threat matching -> OSINT correlation ->
graph construction -> path analysis -> risk indicators -> persist.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session

from app.core.envelope import AppError
from app.core.logging import get_logger
from app.models import Investigation, ThreatFinding, Transaction, Wallet
from app.services import osint as osint_service
from app.services import threat_intelligence
from app.services.audit import log_action
from app.services.blockchain.base import BlockchainProvider, ProviderError
from app.services.blockchain.factory import provider_for_address
from app.services.graph_analysis import build_graph, trace_funds
from app.services.risk_engine import assess as assess_risk
from app.services.serializers import threat_dict, tx_dict
from app.utils.datetime import iso, utcnow

logger = get_logger("wallet_analysis")

EXPLORER_URLS = {
    "bitcoin": "https://mempool.space/address/{address}",
    "ethereum": "https://etherscan.io/address/{address}",
    "bsc": "https://bscscan.com/address/{address}",
    "polygon": "https://polygonscan.com/address/{address}",
    "solana": "https://solscan.io/account/{address}",
}

PIPELINE_STEPS = [
    "Validating wallet address",
    "Detecting blockchain",
    "Fetching blockchain data",
    "Analyzing transactions",
    "Checking threat intelligence",
    "Correlating OSINT",
    "Building transaction graph",
    "Calculating risk indicators",
    "Completed",
]


async def _safe(provider_method, *args, **kwargs):
    try:
        return await provider_method(*args, **kwargs)
    except ProviderError as exc:
        raise AppError(
            503,
            exc.code if exc.code == "REQUIRES_CONFIGURATION" else "PROVIDER_UNAVAILABLE",
            exc.message,
            {"provider_status": "NOT_CONFIGURED" if exc.code == "REQUIRES_CONFIGURATION" else "UNAVAILABLE"},
        ) from exc


def _upsert_wallet(db: Session, address: str, chain: str, balance: dict, activity: dict, provider: BlockchainProvider) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.address == address, Wallet.blockchain == chain).one_or_none()
    if wallet is None:
        wallet = Wallet(address=address, blockchain=chain, is_demo=provider.is_demo)
        db.add(wallet)
    wallet.balance = float(balance.get("balance", 0.0))
    wallet.asset = balance.get("asset", provider.asset)
    wallet.first_seen = activity.get("first_seen") or wallet.first_seen
    wallet.last_seen = activity.get("last_seen") or wallet.last_seen
    wallet.transaction_count = activity.get("tx_count", wallet.transaction_count)
    wallet.is_demo = provider.is_demo
    db.commit()
    return wallet


def _persist_transactions(db: Session, chain: str, txs: list[dict]) -> int:
    valid_txs = [tx for tx in txs if tx.get("tx_hash")]
    if not valid_txs:
        return 0
    hashes = list({tx["tx_hash"] for tx in valid_txs})
    existing_rows = (
        db.query(Transaction.tx_hash, Transaction.from_address, Transaction.to_address)
        .filter(Transaction.tx_hash.in_(hashes))
        .all()
    )
    existing_set = set(existing_rows)

    new_models = []
    for tx in valid_txs:
        key = (tx["tx_hash"], tx.get("from_address"), tx.get("to_address"))
        if key in existing_set:
            continue
        timestamp = tx.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
        new_models.append(
            Transaction(
                tx_hash=tx["tx_hash"],
                blockchain=chain,
                from_address=tx.get("from_address"),
                to_address=tx.get("to_address"),
                amount=tx.get("amount", 0.0),
                asset=tx.get("asset", "BTC"),
                timestamp=timestamp or utcnow(),
                block_number=tx.get("block_number"),
                confirmations=tx.get("confirmations", 0),
                status=tx.get("status", "confirmed"),
                fee=tx.get("fee"),
                is_demo=False,
            )
        )
        existing_set.add(key)
    if new_models:
        db.add_all(new_models)
        db.commit()
    return len(new_models)


def _wallet_summary(address: str, chain: str, wallet: Wallet, balance: dict, txs: list[dict], activity: dict, provider_name: str | None = None) -> dict:
    incoming = round(sum(t.get("amount", 0.0) for t in txs if t.get("to_address") == address), 8)
    outgoing = round(sum(t.get("amount", 0.0) for t in txs if t.get("from_address") == address), 8)
    counterparties = {t["to_address"] for t in txs if t.get("from_address") == address and t.get("to_address")}
    counterparties |= {t["from_address"] for t in txs if t.get("to_address") == address and t.get("from_address")}
    return {
        "address": address,
        "blockchain": chain,
        "label": wallet.label if wallet else None,
        "balance": balance.get("balance", 0.0),
        "pending_balance": balance.get("pending_balance"),
        "asset": balance.get("asset", "BTC"),
        "transaction_count": activity.get("tx_count", len(txs)),
        "first_activity": iso(activity.get("first_seen")) if isinstance(activity.get("first_seen"), datetime) else activity.get("first_seen"),
        "last_activity": iso(activity.get("last_seen")) if isinstance(activity.get("last_seen"), datetime) else activity.get("last_seen"),
        "incoming_volume": incoming,
        "outgoing_volume": outgoing,
        "unique_counterparties": len(counterparties),
        "explorer_url": EXPLORER_URLS.get(chain, EXPLORER_URLS["bitcoin"]) and EXPLORER_URLS[chain].format(address=address) if EXPLORER_URLS.get(chain) else None,
        "provider": provider_name,
        "is_demo": False,
    }


async def run_investigation(
    db: Session,
    address: str,
    blockchain: str = "auto",
    investigator: str = "Investigator",
) -> dict[str, Any]:
    provider, detection = provider_for_address(address, blockchain)
    chain = detection["blockchain"]
    logger.info("Investigation started for %s on %s via %s", address, chain, provider.name)

    balance = await _safe(provider.get_balance, address)
    activity = await _safe(provider.get_address_activity, address)
    txs = await _safe(provider.get_transactions, address, 150)

    wallet = _upsert_wallet(db, address, chain, balance, activity, provider)
    _persist_transactions(db, chain, txs)

    # Threat intelligence
    focus_threats = threat_intelligence.match_wallet(db, address)
    counterparties: set[str] = set()
    for tx in txs:
        if tx.get("from_address") == address and tx.get("to_address"):
            counterparties.add(tx["to_address"])
        if tx.get("to_address") == address and tx.get("from_address"):
            counterparties.add(tx["from_address"])
    cp_threats = threat_intelligence.match_addresses(db, sorted(counterparties))

    # OSINT correlation
    osint_results = osint_service.correlate_wallet(address)
    _persist_osint_findings(db, address, osint_results)

    # Graph + fund flow
    graph = build_graph(db, address, hops=2, max_nodes=150)
    fund_flow = trace_funds(db, address, direction="outgoing", max_hops=3)

    # Risk indicators
    tx_dicts = [tx_dict(t) for t in txs]
    risk = assess_risk(
        {
            "focus_address": address,
            "transactions": tx_dicts,
            "threat_findings": [threat_dict(t) for t in focus_threats],
            "counterparty_threats": [threat_dict(t) for t in cp_threats],
            "graph_stats": graph.get("stats", {}),
            "osint_findings": osint_results["results"],
        }
    )

    bundle = {
        "investigation_id": None,
        "generated_at": iso(utcnow()),
        "mode": "LIVE",
        "address": address,
        "blockchain": chain,
        "provider": {"name": provider.name, "status": "OK", "is_demo": False},
        "wallet": _wallet_summary(address, chain, wallet, balance, txs, activity, provider.name),
        "transactions": tx_dicts,
        "threats": [threat_dict(t) for t in focus_threats],
        "counterparty_threats": [threat_dict(t) for t in cp_threats],
        "osint": osint_results,
        "graph": graph,
        "fund_flow": fund_flow,
        "risk": risk,
    }

    investigation = Investigation(
        case_id=None,
        title=f"Investigation: {_short(address)}",
        wallet_address=address,
        blockchain=chain,
        status="COMPLETED",
        risk_level=risk["band"],
        risk_score=risk["score"],
        investigator=investigator,
        payload=bundle,
    )
    db.add(investigation)
    db.commit()
    bundle["investigation_id"] = investigation.id
    db.query(Investigation).filter(Investigation.id == investigation.id).update({"payload": bundle})
    db.commit()

    log_action(
        db,
        "wallet_investigated",
        "wallet",
        address,
        {"blockchain": chain, "risk_band": risk["band"], "threat_matches": len(focus_threats), "provider": provider.name},
        investigator,
    )
    logger.info("Investigation completed for %s (risk=%s)", address, risk["band"])
    return bundle


def _persist_osint_findings(db: Session, address: str, osint_results: dict) -> None:
    from app.models import OSINTFinding

    valid_results = [r for r in osint_results.get("results", []) if r["status"] in ("FOUND", "NOT_FOUND")]
    if not valid_results:
        return

    sources = [r["source_name"] for r in valid_results]
    existing_map = {
        f.source: f
        for f in db.query(OSINTFinding)
        .filter(OSINTFinding.wallet_address == address, OSINTFinding.source.in_(sources))
        .all()
    }

    for result in valid_results:
        source_name = result["source_name"]
        existing = existing_map.get(source_name)
        values = {
            "finding": result.get("finding"),
            "status": result["status"],
            "confidence": result.get("confidence", 0.0),
            "reference_url": result.get("reference_url"),
            "notes": result.get("notes"),
            "observed_at": utcnow(),
            "is_demo": result.get("is_demo", False),
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            db.add(
                OSINTFinding(
                    wallet_address=address,
                    source=source_name,
                    source_category="public",
                    **values,
                )
            )
    db.commit()


def _short(address: str) -> str:
    return address if len(address) <= 20 else f"{address[:10]}...{address[-6:]}"
