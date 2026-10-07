"""Transaction graph analysis built on NetworkX.

Graph format returned to the frontend:
  nodes: [{id, label, type, risk, focus, tx_count}]
  edges: [{source, target, amount, asset, tx_hash, tx_hashes, timestamp, count}]
  stats: {node_count, edge_count, unique_wallets, total_amount}

Parallel transactions between the same pair are aggregated into one edge.
"""
from __future__ import annotations

from collections import deque
from typing import Any

import networkx as nx
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.envelope import AppError
from app.models import Transaction, ThreatFinding
from app.utils.datetime import iso

CATEGORY_TO_TYPE = {
    "Ransomware": "ransomware",
    "Scam": "scam",
    "Phishing": "scam",
    "Fraud": "scam",
    "Exploit": "scam",
    "Blacklist": "scam",
    "Suspicious Service": "mixer",
}

TRACE_DISCLAIMER = (
    "This is the shortest observed path in the available transaction graph (bounded by max hops and indexed data). "
    "It is NOT a claim that these funds are the illicit proceeds or that the path represents the true flow of illicit money."
)


def _node_type(address: str, threat_categories: list[str], focus: bool) -> str:
    for category in threat_categories:
        if category in CATEGORY_TO_TYPE:
            return CATEGORY_TO_TYPE[category]
    return "victim" if focus else "wallet"


def _node_risk(confidence: float) -> str:
    if confidence >= 0.7:
        return "high"
    if confidence > 0:
        return "elevated"
    return "clear"


def _label(address: str) -> str:
    """Node display label. Live-only: the address itself."""
    return address


def _addr_variants(addresses: list[str]) -> list[str]:
    """Canonical form for address comparisons.

    EVM addresses are stored lowercase (providers normalize them) so checksummed
    user input is canonicalized to lowercase. Bitcoin Base58 addresses are
    case-sensitive and matched as-is.
    """
    out: list[str] = []
    for a in addresses:
        if not a:
            continue
        canonical = a.lower() if a.startswith("0x") else a
        if canonical not in out:
            out.append(canonical)
    return out


def _txs_for_addresses(db: Session, addresses: list[str]) -> list[Transaction]:
    """Fetch transactions touching any of the given addresses.

    EVM addresses are stored lowercase by providers, so checksummed user input
    is canonicalized to lowercase before matching. Non-EVM addresses (Bitcoin
    Base58) are case-sensitive and matched as-is.
    """
    variants: list[str] = []
    for a in addresses:
        if not a:
            continue
        candidates = [a]
        if a.startswith("0x"):
            candidates.append(a.lower())
        for c in candidates:
            if c not in variants:
                variants.append(c)
    return (
        db.query(Transaction)
        .filter(or_(Transaction.from_address.in_(variants), Transaction.to_address.in_(variants)))
        .all()
    )


def _build_graph_from_txs(txs: list[Transaction], focus_address: str, threat_by_addr: dict[str, dict]) -> dict[str, Any]:
    edge_map: dict[tuple[str, str], dict] = {}
    node_tx_count: dict[str, int] = {}
    for tx in txs:
        if not tx.from_address or not tx.to_address:
            continue
        key = (tx.from_address, tx.to_address)
        entry = edge_map.setdefault(
            key, {"amount": 0.0, "asset": tx.asset, "tx_hashes": [], "timestamp": tx.timestamp, "count": 0}
        )
        entry["amount"] += tx.amount or 0.0
        entry["count"] += 1
        entry["tx_hashes"].append(tx.tx_hash)
        if tx.timestamp and (entry["timestamp"] is None or tx.timestamp > entry["timestamp"]):
            entry["timestamp"] = tx.timestamp
        node_tx_count[tx.from_address] = node_tx_count.get(tx.from_address, 0) + 1
        node_tx_count[tx.to_address] = node_tx_count.get(tx.to_address, 0) + 1

    addresses = sorted(node_tx_count)
    nodes = []
    for address in addresses:
        threat = threat_by_addr.get(address, {})
        categories = threat.get("categories", [])
        nodes.append(
            {
                "id": address,
                "label": _label(address),
                "type": _node_type(address, categories, focus=address == focus_address),
                "risk": _node_risk(threat.get("max_confidence", 0.0)),
                "focus": address == focus_address,
                "tx_count": node_tx_count.get(address, 0),
                "categories": categories,
            }
        )

    edges = [
        {
            "source": key[0],
            "target": key[1],
            "amount": round(attrs["amount"], 8),
            "asset": attrs["asset"],
            "tx_hash": attrs["tx_hashes"][0],
            "tx_hashes": attrs["tx_hashes"][:20],
            "timestamp": iso(attrs["timestamp"]),
            "count": attrs["count"],
        }
        for key, attrs in sorted(edge_map.items())
    ]
    total_amount = round(sum(e["amount"] for e in edges), 8)
    stats = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "unique_wallets": len(nodes),
        "total_amount": total_amount,
    }
    return {"nodes": nodes, "edges": edges, "stats": stats}


def _threat_map(db: Session, addresses: list[str]) -> dict[str, dict]:
    if not addresses:
        return {}
    findings = db.query(ThreatFinding).filter(ThreatFinding.wallet_address.in_(addresses)).all()
    result: dict[str, dict] = {}
    for f in findings:
        entry = result.setdefault(
            f.wallet_address, {"categories": [], "sources": [], "max_confidence": 0.0, "is_demo": f.is_demo}
        )
        if f.category not in entry["categories"]:
            entry["categories"].append(f.category)
        if f.source not in entry["sources"]:
            entry["sources"].append(f.source)
        entry["max_confidence"] = max(entry["max_confidence"], f.confidence)
    return result


def _ensure_frontier_txs(db: Session, frontier: list[str], max_fetch: int = 3):
    """Fetch live transactions for top unindexed frontier addresses so multi-hop BFS expands."""
    # Skip live network fetching in pytest unit tests to preserve test session isolation
    if hasattr(db, "is_test") or getattr(db, "in_test", False):
        return

    from app.services.blockchain.factory import provider_for_address
    import asyncio

    unindexed = []
    for addr in frontier[:max_fetch]:
        if not addr or len(addr) < 4:
            continue
        count = db.query(Transaction).filter(or_(Transaction.from_address == addr, Transaction.to_address == addr)).count()
        if count <= 1:  # Only has the single transaction with focus_address
            unindexed.append(addr)

    if not unindexed:
        return

    for addr in unindexed:
        try:
            provider, detection = provider_for_address(addr, "auto")
            if getattr(provider, "is_demo", False) or "fake" in getattr(provider, "name", "").lower():
                continue
            loop = asyncio.new_event_loop()
            try:
                res = provider.get_transactions(addr, limit=15)
                raw_txs = loop.run_until_complete(res) if asyncio.iscoroutine(res) else res
            finally:
                loop.close()

            for r in raw_txs or []:
                if not r.get("from_address") or not r.get("to_address"):
                    continue
                tx_obj = Transaction(
                    tx_hash=r["tx_hash"],
                    blockchain=r.get("blockchain") or detection.get("blockchain", "unknown"),
                    from_address=r["from_address"],
                    to_address=r["to_address"],
                    amount=r.get("amount", 0.0),
                    asset=r.get("asset", "ETH"),
                    timestamp=r.get("timestamp"),
                    block_number=r.get("block_number"),
                    confirmations=r.get("confirmations", 1),
                    status=r.get("status", "confirmed"),
                    fee=r.get("fee", 0.0),
                    is_demo=False,
                )
                db.merge(tx_obj)
            db.commit()
        except Exception:
            db.rollback()


def build_graph(db: Session, focus_address: str, hops: int = 2, max_nodes: int = 150) -> dict[str, Any]:
    """Bounded BFS from the focus address over stored and live-fetched transactions."""
    hops = max(1, min(hops, 7))
    visited = {focus_address}
    frontier = [focus_address]
    collected: dict[int, Transaction] = {}
    truncated = False

    for _ in range(hops):
        _ensure_frontier_txs(db, frontier, max_fetch=3)
        next_frontier: list[str] = []
        txs = _txs_for_addresses(db, frontier)
        for tx in txs:
            collected[tx.id] = tx
            for neighbor in (tx.to_address, tx.from_address):
                if neighbor and neighbor not in visited:
                    if len(visited) >= max_nodes:
                        truncated = True
                        continue
                    visited.add(neighbor)
                    next_frontier.append(neighbor)
        if not next_frontier or truncated:
            break
        frontier = next_frontier

    threat_by_addr = _threat_map(db, list(visited))
    # Only keep edges whose endpoints were visited - enforces the node cap.
    bounded_txs = [t for t in collected.values() if t.from_address in visited and t.to_address in visited]
    graph = _build_graph_from_txs(bounded_txs, focus_address, threat_by_addr)
    graph["stats"]["truncated"] = truncated
    graph["stats"]["hops"] = hops
    graph["focus_address"] = focus_address
    return graph


def _collect_subgraph_txs(db: Session, source: str, direction: str, max_hops: int, max_nodes: int = 300):
    """Collect only edges aligned with the traversal direction, bounded BFS from source."""
    visited = {source}
    frontier = [source]
    collected: dict[int, Transaction] = {}
    for _ in range(max_hops):
        next_frontier: list[str] = []
        txs = _txs_for_addresses(db, frontier)
        for tx in txs:
            if direction == "outgoing":
                if tx.from_address not in frontier or not tx.to_address:
                    continue
                neighbor = tx.to_address
            else:
                if tx.to_address not in frontier or not tx.from_address:
                    continue
                neighbor = tx.from_address
            collected[tx.id] = tx
            if neighbor not in visited:
                if len(visited) >= max_nodes:
                    break
                visited.add(neighbor)
                next_frontier.append(neighbor)
        if not next_frontier:
            break
        frontier = next_frontier
    return list(collected.values()), visited


def _traversal_graph(txs: list[Transaction], direction: str) -> tuple[nx.DiGraph, dict[tuple[str, str], dict]]:
    graph = nx.DiGraph()
    edge_map: dict[tuple[str, str], dict] = {}
    for tx in txs:
        if not tx.from_address or not tx.to_address:
            continue
        u, v = (tx.from_address, tx.to_address) if direction == "outgoing" else (tx.to_address, tx.from_address)
        key = (u, v)
        entry = edge_map.setdefault(key, {"amount": 0.0, "asset": tx.asset, "tx_hashes": [], "timestamp": tx.timestamp})
        entry["amount"] += tx.amount or 0.0
        entry["tx_hashes"].append(tx.tx_hash)
        if tx.timestamp and (entry["timestamp"] is None or tx.timestamp > entry["timestamp"]):
            entry["timestamp"] = tx.timestamp
    for (u, v), attrs in edge_map.items():
        graph.add_edge(u, v, **attrs)
    return graph, edge_map


def trace_funds(
    db: Session,
    source: str,
    direction: str = "outgoing",
    target: str | None = None,
    max_hops: int = 4,
) -> dict[str, Any]:
    """Bounded hop traversal with optional target-path search.

    Direction semantics:
      outgoing -> follow funds from `source` downstream (who received from it)
      incoming -> follow funds upstream to `source` (who sent to it)
    """
    max_hops = max(1, min(max_hops, 7))
    txs, visited = _collect_subgraph_txs(db, source, direction, max_hops)
    traversal, edge_map = _traversal_graph(txs, direction)
    threat_by_addr = _threat_map(db, list(visited))

    def suspicious(nodes: set[str]) -> list[dict]:
        out = []
        for address in sorted(nodes & set(threat_by_addr)):
            info = threat_by_addr[address]
            out.append(
                {
                    "address": address,
                    "label": _label(address),
                    "categories": info["categories"],
                    "sources": info["sources"],
                    "confidence": info["max_confidence"],
                }
            )
        return out

    result: dict[str, Any] = {
        "source": source,
        "direction": direction,
        "max_hops": max_hops,
        "nodes_explored": len(visited),
        "disclaimer": TRACE_DISCLAIMER,
        "suspicious_nodes": suspicious(set(visited)),
    }

    if target:
        if target not in traversal:
            result.update(
                {
                    "path": [],
                    "path_edges": [],
                    "hops": 0,
                    "total_amount": 0.0,
                    "paths": [],
                    "found": False,
                    "note": f"Target {target} was not reachable within {max_hops} hops in the observed graph.",
                }
            )
            return result
        try:
            shortest = nx.shortest_path(traversal, source, target)
        except nx.NetworkXNoPath:
            shortest = None
        simple_paths = []
        if shortest:
            try:
                simple_paths = list(nx.all_simple_paths(traversal, source, target, cutoff=max_hops))[:5]
            except Exception:  # noqa: BLE001 - path enumeration is best-effort
                simple_paths = [shortest]
        if not shortest:
            result.update({"path": [], "path_edges": [], "hops": 0, "total_amount": 0.0, "paths": [], "found": False, "note": "No directed path exists in the observed graph."})
            return result

        path_edges = []
        for u, v in zip(shortest, shortest[1:]):
            attrs = edge_map.get((u, v), {})
            display = (u, v) if direction == "outgoing" else (v, u)
            path_edges.append(
                {
                    "source": display[0],
                    "target": display[1],
                    "amount": round(attrs.get("amount", 0.0), 8),
                    "asset": attrs.get("asset", "BTC"),
                    "tx_hash": (attrs.get("tx_hashes") or [None])[0],
                    "timestamp": iso(attrs.get("timestamp")),
                }
            )
        amounts = [edge_map.get(pair, {}).get("amount", 0.0) for pair in zip(shortest, shortest[1:])]
        result.update(
            {
                "found": True,
                "path": shortest,
                "path_edges": path_edges,
                "hops": len(shortest) - 1,
                "total_amount": round(min(amounts), 8) if amounts else 0.0,
                "paths": [
                    {"path": p, "hops": len(p) - 1, "amount": round(min(edge_map.get(pair, {}).get("amount", 0.0) for pair in zip(p, p[1:])), 8) if len(p) > 1 else 0.0}
                    for p in simple_paths
                ],
                "destination_label": _label(target),
            }
        )
        return result

    # No target: BFS hop levels downstream/upstream from source.
    levels = []
    seen = {source}
    frontier = {source}
    for hop in range(1, max_hops + 1):
        next_frontier: set[str] = set()
        for node in frontier:
            if node not in traversal:
                continue
            # Traversal edges are already oriented along the walk direction
            # (reversed for incoming traces), so successors is correct for both.
            next_frontier.update(traversal.successors(node))
        next_frontier -= seen
        if not next_frontier:
            break
        levels.append({"hop": hop, "addresses": [{"address": a, "label": _label(a), "suspicious": a in threat_by_addr} for a in sorted(next_frontier)]})
        seen |= next_frontier
        frontier = next_frontier
    result["levels"] = levels
    result["asset"] = "BTC"
    return result
