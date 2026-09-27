"""Transaction explorer endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import AppError, ok
from app.models import Transaction
from app.services import osint as osint_service
from app.services.serializers import tx_dict
from app.utils.datetime import parse_date
from app.utils.pagination import clamp, meta

router = APIRouter(prefix="/transactions", tags=["transactions"])

EXPLORER_TX_URLS = {
    "bitcoin": "https://mempool.space/tx/{hash}",
    "ethereum": "https://etherscan.io/tx/{hash}",
    "bsc": "https://bscscan.com/tx/{hash}",
}


@router.get("")
def list_transactions(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None, max_length=255),
    blockchain: str | None = None,
    status: str | None = None,
    start: str | None = None,
    end: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    sort_by: str = Query(default="timestamp", pattern="^(timestamp|amount|tx_hash)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = 1,
    page_size: int = 25,
):
    page, page_size = clamp(page, page_size)
    query = db.query(Transaction)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(Transaction.tx_hash.ilike(like), Transaction.from_address.ilike(like), Transaction.to_address.ilike(like))
        )
    if blockchain:
        query = query.filter(Transaction.blockchain == blockchain)
    if status:
        query = query.filter(Transaction.status == status)
    start_dt, end_dt = parse_date(start), parse_date(end)
    if start_dt:
        query = query.filter(Transaction.timestamp >= start_dt)
    if end_dt:
        query = query.filter(Transaction.timestamp <= end_dt)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)

    column = {"timestamp": Transaction.timestamp, "amount": Transaction.amount, "tx_hash": Transaction.tx_hash}[sort_by]
    query = query.order_by(column.asc() if sort_dir == "asc" else column.desc())
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return ok([tx_dict(t) for t in rows], meta(page, page_size, total))


@router.get("/{tx_hash}")
def get_transaction(tx_hash: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.tx_hash == tx_hash).one_or_none()
    if tx is None:
        raise AppError(404, "TRANSACTION_NOT_FOUND", f"Transaction {tx_hash} is not present in the indexed dataset.")
    item = tx_dict(tx)
    explorer = EXPLORER_TX_URLS.get(tx.blockchain or "")
    item["explorer_url"] = explorer.format(hash=tx_hash) if explorer else None
    item["osint"] = osint_service.correlate_transaction(tx_hash)
    return ok(item)
