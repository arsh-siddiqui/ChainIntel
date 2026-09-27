"""Wallet investigation endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import AppError, ok
from app.models import Investigation, OSINTFinding, Transaction, Wallet
from app.schemas.wallet import InvestigateRequest, WalletNotesUpdate
from app.services import osint as osint_service
from app.services import threat_intelligence
from app.services.graph_analysis import build_graph
from app.services.serializers import (
    investigation_summary,
    osint_dict,
    threat_dict,
    tx_dict,
    wallet_dict,
)
from app.services.wallet_analysis import PIPELINE_STEPS, run_investigation
from app.utils.address_validation import detect_blockchain
from app.utils.datetime import parse_date
from app.utils.pagination import clamp, meta

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.get("/pipeline-steps")
def pipeline_steps():
    return ok({"steps": PIPELINE_STEPS})


@router.post("/investigate")
async def investigate(request: InvestigateRequest, db: Session = Depends(get_db)):
    bundle = await run_investigation(db, request.address, request.blockchain)
    return ok(bundle, {"mode": bundle.get("mode"), "blockchain": bundle.get("blockchain")})


@router.get("/{address}")
def get_wallet(address: str, db: Session = Depends(get_db)):
    detection = detect_blockchain(address)
    investigation = (
        db.query(Investigation)
        .filter(Investigation.wallet_address == address)
        .order_by(Investigation.created_at.desc())
        .first()
    )
    wallet = db.query(Wallet).filter(Wallet.address == address).first()
    bundle = dict(investigation.payload) if investigation and investigation.payload else None
    if bundle:
        bundle["osint"] = osint_service.correlate_wallet(address)
    return ok(
        {
            "validation": detection,
            "wallet": wallet_dict(wallet) if wallet else None,
            "investigation": investigation_summary(investigation) if investigation else None,
            "bundle": bundle,
        }
    )


@router.get("/{address}/transactions")
def wallet_transactions(
    address: str,
    db: Session = Depends(get_db),
    direction: str | None = Query(default=None, pattern="^(incoming|outgoing)$"),
    min_amount: float | None = None,
    max_amount: float | None = None,
    start: str | None = None,
    end: str | None = None,
    sort_by: str = Query(default="timestamp", pattern="^(timestamp|amount)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = 1,
    page_size: int = 25,
):
    page, page_size = clamp(page, page_size)
    # EVM addresses are stored lowercase; canonicalize checksummed input.
    variants = [address]
    if address.startswith("0x"):
        variants.append(address.lower())
    query = db.query(Transaction).filter(
        or_(Transaction.from_address.in_(variants), Transaction.to_address.in_(variants))
    )
    start_dt, end_dt = parse_date(start), parse_date(end)
    if start_dt:
        query = query.filter(Transaction.timestamp >= start_dt)
    if end_dt:
        query = query.filter(Transaction.timestamp <= end_dt)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)

    column = Transaction.timestamp if sort_by == "timestamp" else Transaction.amount
    query = query.order_by(column.asc() if sort_dir == "asc" else column.desc())
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for tx in rows:
        item = tx_dict(tx)
        item["direction"] = "outgoing" if tx.from_address == address else "incoming"
        if direction and item["direction"] != direction:
            continue
        items.append(item)
    return ok(items, meta(page, page_size, total))


@router.get("/{address}/threats")
def wallet_threats(address: str, db: Session = Depends(get_db)):
    threats = threat_intelligence.match_wallet(db, address)
    counterparty_rows = (
        db.query(Transaction.from_address, Transaction.to_address)
        .filter(or_(Transaction.from_address == address, Transaction.to_address == address))
        .all()
    )
    counterparties = set()
    for from_addr, to_addr in counterparty_rows:
        if from_addr == address and to_addr:
            counterparties.add(to_addr)
        if to_addr == address and from_addr:
            counterparties.add(from_addr)
    cp_threats = threat_intelligence.match_addresses(db, sorted(counterparties))
    return ok(
        {
            "wallet_threats": [threat_dict(t) for t in threats],
            "counterparty_threats": [threat_dict(t) for t in cp_threats],
            "counterparty_count": len(counterparties),
        }
    )


@router.get("/{address}/osint")
def wallet_osint(address: str, db: Session = Depends(get_db)):
    persisted = (
        db.query(OSINTFinding)
        .filter(OSINTFinding.wallet_address == address)
        .order_by(OSINTFinding.observed_at.desc())
        .all()
    )
    correlation = osint_service.correlate_wallet(address)
    return ok(
        {
            "persisted": [osint_dict(f) for f in persisted],
            "live_correlation": correlation,
        }
    )


@router.get("/{address}/graph")
def wallet_graph(
    address: str,
    db: Session = Depends(get_db),
    hops: int = Query(default=2, ge=1, le=7),
    max_nodes: int = Query(default=150, ge=10, le=400),
):
    graph = build_graph(db, address, hops=hops, max_nodes=max_nodes)
    return ok(graph)


@router.patch("/{address}/notes")
def update_notes(address: str, request: WalletNotesUpdate, db: Session = Depends(get_db)):
    investigation = (
        db.query(Investigation)
        .filter(Investigation.wallet_address == address)
        .order_by(Investigation.created_at.desc())
        .first()
    )
    if investigation is None:
        raise AppError(404, "INVESTIGATION_NOT_FOUND", "Run a wallet investigation before adding notes.")
    investigation.notes = request.notes
    if investigation.payload:
        investigation.payload["notes"] = request.notes
    db.commit()
    return ok(investigation_summary(investigation))
