"""Graph analysis endpoints (fund-flow tracing)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.envelope import ok
from app.schemas.graph import TraceRequest
from app.services.graph_analysis import trace_funds

router = APIRouter(prefix="/graph", tags=["graph"])


@router.post("/trace")
def trace(request: TraceRequest, db: Session = Depends(get_db)):
    result = trace_funds(
        db,
        source=request.wallet_address,
        direction=request.direction,
        target=request.target_address,
        max_hops=request.max_hops,
    )
    return ok(result)
