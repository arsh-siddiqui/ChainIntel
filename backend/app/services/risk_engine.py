"""Explainable risk engine.

Every indicator carries its own name, description, evidence, weight, source and
trigger status. The overall score is the transparent sum of triggered weights.

IMPORTANT: the score is an analytical indicator, never a determination of
unlawful activity.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

DISCLAIMER = "Risk score is an analytical indicator and not a determination of unlawful activity."

BANDS = [
    (15, "LOW"),
    (40, "MODERATE"),
    (70, "ELEVATED"),
    (float("inf"), "HIGH"),
]

HIGH_SEVERITY_CATEGORIES = {"Ransomware", "Exploit", "Blacklist"}
MIXER_CATEGORY = "Suspicious Service"


def _indicator(name: str, description: str, weight: int, source: str, status: str, evidence: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "weight": weight,
        "source": source,
        "status": status,  # TRIGGERED | NOT_TRIGGERED | UNAVAILABLE
        "evidence": evidence,
    }


def _rapid_movement(transactions: list[dict], focus: str, window_minutes: int = 60, count: int = 3) -> bool:
    outgoing = sorted(
        (
            datetime.fromisoformat(tx["timestamp"].replace("Z", "+00:00"))
            for tx in transactions
            if tx.get("from_address") == focus and tx.get("timestamp")
        ),
    )
    for i in range(len(outgoing) - count + 1):
        if outgoing[i + count - 1] - outgoing[i] <= timedelta(minutes=window_minutes):
            return True
    return False


def assess(context: dict[str, Any]) -> dict[str, Any]:
    """Compute explainable risk indicators.

    context keys:
      focus_address: str
      transactions: list[normalized tx dicts]
      threat_findings: list[threat dicts for the focus wallet]
      counterparty_threats: list[threat dicts for counterparties]
      graph_stats: {node_count, edge_count, unique_wallets, total_amount}
      osint_findings: list[osint dicts]
    """
    focus = context["focus_address"]
    transactions = context.get("transactions", [])
    focus_threats = context.get("threat_findings", [])
    cp_threats = context.get("counterparty_threats", [])
    graph_stats = context.get("graph_stats", {}) or {}
    osint_findings = context.get("osint_findings", [])

    indicators: list[dict[str, Any]] = []

    # 1. Direct threat-intelligence match on the investigated wallet.
    if focus_threats:
        evidence = "; ".join(
            f"{t['category']}: {t['label']} (source: {t['source']}, confidence {t['confidence']:.2f})" for t in focus_threats[:4]
        )
        status, weight = "TRIGGERED", 40
    else:
        evidence = "No records found in configured threat datasets for this wallet."
        status, weight = "NOT_TRIGGERED", 40
    indicators.append(
        _indicator(
            "Threat intelligence match",
            "The wallet address matches records in configured threat-intelligence datasets.",
            weight,
            "Configured threat datasets",
            status,
            evidence,
        )
    )

    # 2. High-risk counterparties.
    if cp_threats:
        counterparties = sorted({t["wallet_address"] for t in cp_threats})
        evidence = f"{len(cp_threats)} record(s) across {len(counterparties)} counterparty wallet(s): {', '.join(c[:40] for c in counterparties[:5])}"
        status, weight = "TRIGGERED", 15
    else:
        evidence = "No counterparties match configured threat datasets."
        status, weight = "NOT_TRIGGERED", 15
    indicators.append(
        _indicator(
            "High-risk counterparty",
            "Wallets transacting with the investigated address match threat-intelligence records.",
            weight,
            "Configured threat datasets",
            status,
            evidence,
        )
    )

    # 3. Mixer / suspicious-service interaction.
    mixer_records = [t for t in cp_threats + focus_threats if t.get("category") == MIXER_CATEGORY]
    if mixer_records:
        evidence = "; ".join(f"{t['label']} (source: {t['source']})" for t in mixer_records[:3])
        status, weight = "TRIGGERED", 15
    else:
        evidence = "No mixer or suspicious-service records among observed counterparties."
        status, weight = "NOT_TRIGGERED", 15
    indicators.append(
        _indicator(
            "Mixer/service interaction",
            "Observed interaction with wallets tagged as mixers or suspicious services.",
            weight,
            "Configured threat datasets",
            status,
            evidence,
        )
    )

    # 4. Multiple intermediaries.
    unique_wallets = graph_stats.get("unique_wallets", 0)
    edge_count = graph_stats.get("edge_count", 0)
    if unique_wallets >= 5 and edge_count >= 8:
        status, weight = "TRIGGERED", 10
        evidence = f"Graph contains {unique_wallets} unique wallets and {edge_count} aggregated transaction edges."
    else:
        status, weight = "NOT_TRIGGERED", 10
        evidence = f"Graph contains {unique_wallets} unique wallets and {edge_count} aggregated edges (below threshold)."
    indicators.append(
        _indicator(
            "Multiple intermediary hops",
            "Funds pass through several intermediary wallets before reaching endpoints.",
            weight,
            "Transaction graph analysis",
            status,
            evidence,
        )
    )

    # 5. Rapid movement.
    if _rapid_movement(transactions, focus):
        status, weight = "TRIGGERED", 10
        evidence = f"3 or more outgoing transactions from the focus wallet occur within a 60-minute window."
    else:
        status, weight = "NOT_TRIGGERED", 10
        evidence = "No burst of rapid outgoing transactions detected."
    indicators.append(
        _indicator(
            "Rapid fund movement",
            "Outgoing transactions cluster into short time windows, a pattern used to accelerate layering.",
            weight,
            "Temporal transaction analysis",
            status,
            evidence,
        )
    )

    # 6. Transaction fragmentation (fan-out).
    fan_out: dict[str, int] = {}
    for tx in transactions:
        if tx.get("from_address") == focus and tx.get("to_address"):
            fan_out[tx["to_address"]] = fan_out.get(tx["to_address"], 0) + 1
    max_fan = max(fan_out.values(), default=0)
    if max_fan >= 5:
        status, weight = "TRIGGERED", 5
        top = max(fan_out, key=fan_out.get)
        evidence = f"{max_fan} transactions sent to the same counterparty ({top[:40]}...)."
    else:
        status, weight = "NOT_TRIGGERED", 5
        evidence = f"Maximum transactions to a single counterparty: {max_fan}."
    indicators.append(
        _indicator(
            "Transaction fragmentation",
            "Repeated small transfers to the same counterparty can indicate deliberate splitting of funds.",
            weight,
            "Transaction pattern analysis",
            status,
            evidence,
        )
    )

    # 7. External reputation (OSINT).
    reputation = [o for o in osint_findings if o.get("status") == "FOUND" and o.get("confidence", 0) >= 0.5]
    if reputation:
        evidence = "; ".join(
            f"{o.get('source_name') or o.get('source', '')}: {str(o.get('finding') or '')[:80]}" for o in reputation[:3]
        )
        status, weight = "TRIGGERED", 15
    else:
        status, weight = "NOT_TRIGGERED", 15
        evidence = "No adverse external reputation findings at or above the 0.5 confidence threshold."
    indicators.append(
        _indicator(
            "External reputation match",
            "OSINT sources report reputation information about this wallet.",
            weight,
            "OSINT providers",
            status,
            evidence,
        )
    )

    # 8. Repeated interaction with tagged addresses.
    tagged_counts: dict[str, int] = {}
    tagged_addresses = {t["wallet_address"] for t in cp_threats}
    for tx in transactions:
        counterparty = tx["to_address"] if tx.get("from_address") == focus else tx.get("from_address")
        if counterparty in tagged_addresses:
            tagged_counts[counterparty] = tagged_counts.get(counterparty, 0) + 1
    repeated = {a: n for a, n in tagged_counts.items() if n >= 3}
    if repeated:
        status, weight = "TRIGGERED", 10
        evidence = "; ".join(f"{a[:40]}... ({n} transactions)" for a, n in list(repeated.items())[:3])
    else:
        status, weight = "NOT_TRIGGERED", 10
        evidence = "No repeated (3+) interactions with tagged addresses observed."
    indicators.append(
        _indicator(
            "Repeated interaction with tagged addresses",
            "The wallet transacts repeatedly with addresses that carry threat-intelligence records.",
            weight,
            "Configured threat datasets + transaction history",
            status,
            evidence,
        )
    )

    score = sum(i["weight"] for i in indicators if i["status"] == "TRIGGERED")
    band = next(b for threshold, b in BANDS if score < threshold)
    has_high = any(t.get("category") in HIGH_SEVERITY_CATEGORIES for t in focus_threats)
    if has_high and band == "MODERATE":
        band = "ELEVATED"

    return {
        "score": score,
        "max_score": sum(i["weight"] for i in indicators),
        "band": band,
        "indicators": indicators,
        "disclaimer": DISCLAIMER,
    }
