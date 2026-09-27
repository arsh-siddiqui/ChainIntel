"""Global search across wallets, transactions, cases and threat findings."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import ok
from app.models import Case, ThreatFinding, Transaction, Wallet
from app.services.serializers import case_dict, threat_dict, tx_dict, wallet_dict

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def global_search(db: Session = Depends(get_db), q: str = Query(min_length=2, max_length=255)):
    like = f"%{q}%"
    limit = 5

    wallets = (
        db.query(Wallet).filter(or_(Wallet.address.ilike(like), Wallet.label.ilike(like))).limit(limit).all()
    )
    transactions = db.query(Transaction).filter(Transaction.tx_hash.ilike(like)).limit(limit).all()
    cases = db.query(Case).filter(or_(Case.case_number.ilike(like), Case.title.ilike(like))).limit(limit).all()
    threats = (
        db.query(ThreatFinding)
        .filter(or_(ThreatFinding.wallet_address.ilike(like), ThreatFinding.label.ilike(like), ThreatFinding.source.ilike(like)))
        .limit(limit)
        .all()
    )
    return ok(
        {
            "query": q,
            "wallets": [wallet_dict(w) for w in wallets],
            "transactions": [tx_dict(t) for t in transactions],
            "cases": [case_dict(c) for c in cases],
            "threats": [threat_dict(t) for t in threats],
        },
        {"counts": {"wallets": len(wallets), "transactions": len(transactions), "cases": len(cases), "threats": len(threats)}},
    )
