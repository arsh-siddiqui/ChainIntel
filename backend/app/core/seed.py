"""Seed local database with initial demonstration dataset for ChainIntel."""
from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import (
    Alert,
    AuditLog,
    Case,
    CaseEvent,
    Evidence,
    Investigation,
    MonitoredWallet,
    OSINTFinding,
    ThreatFinding,
    Transaction,
    Wallet,
)
from app.utils.datetime import utcnow


def seed_db(db: Session) -> None:
    # Only seed if database has no wallets
    if db.query(Wallet).first() is not None:
        return

    now = utcnow()

    # 1. Wallets
    w1 = Wallet(
        address="19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
        blockchain="bitcoin",
        label="WannaCry Ransomware Treasury",
        balance=14.582,
        asset="BTC",
        first_seen=now - timedelta(days=120),
        last_seen=now - timedelta(hours=2),
        transaction_count=42,
        is_demo=True,
    )
    w2 = Wallet(
        address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        blockchain="bitcoin",
        label="Satoshi Genesis Address",
        balance=50.0,
        asset="BTC",
        first_seen=now - timedelta(days=3000),
        last_seen=now - timedelta(days=100),
        transaction_count=18,
        is_demo=True,
    )
    w3 = Wallet(
        address="34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
        blockchain="bitcoin",
        label="Binance Cold Storage",
        balance=24800.12,
        asset="BTC",
        first_seen=now - timedelta(days=800),
        last_seen=now - timedelta(minutes=15),
        transaction_count=15200,
        is_demo=True,
    )
    w4 = Wallet(
        address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        blockchain="ethereum",
        label="vitalik.eth",
        balance=1420.5,
        asset="ETH",
        first_seen=now - timedelta(days=1500),
        last_seen=now - timedelta(hours=1),
        transaction_count=892,
        is_demo=True,
    )
    w5 = Wallet(
        address="0x077d37a6553a309b888824e0373809071c356f9a",
        blockchain="ethereum",
        label="Flagged Mixer Deposit Router",
        balance=8.45,
        asset="ETH",
        first_seen=now - timedelta(days=45),
        last_seen=now - timedelta(minutes=30),
        transaction_count=134,
        is_demo=True,
    )
    db.add_all([w1, w2, w3, w4, w5])
    db.commit()

    # 2. Transactions
    txs = [
        Transaction(
            tx_hash="a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d",
            blockchain="bitcoin",
            from_address="19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
            to_address="34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
            amount=2.5,
            asset="BTC",
            timestamp=now - timedelta(hours=3),
            block_number=834521,
            confirmations=6,
            status="confirmed",
            fee=0.00015,
            is_demo=True,
        ),
        Transaction(
            tx_hash="f5d48d9a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d",
            blockchain="bitcoin",
            from_address="34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
            to_address="19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
            amount=5.0,
            asset="BTC",
            timestamp=now - timedelta(days=1),
            block_number=834400,
            confirmations=144,
            status="confirmed",
            fee=0.00021,
            is_demo=True,
        ),
        Transaction(
            tx_hash="0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b",
            blockchain="ethereum",
            from_address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
            to_address="0x077d37a6553a309b888824e0373809071c356f9a",
            amount=1.2,
            asset="ETH",
            timestamp=now - timedelta(hours=5),
            block_number=19451200,
            confirmations=120,
            status="confirmed",
            fee=0.0035,
            is_demo=True,
        ),
        Transaction(
            tx_hash="0x1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c",
            blockchain="ethereum",
            from_address="0x077d37a6553a309b888824e0373809071c356f9a",
            to_address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
            amount=4.8,
            asset="ETH",
            timestamp=now - timedelta(days=2),
            block_number=19438000,
            confirmations=1400,
            status="confirmed",
            fee=0.0042,
            is_demo=True,
        ),
    ]
    db.add_all(txs)
    db.commit()

    # 3. Threat Findings
    t1 = ThreatFinding(
        wallet_address="19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
        blockchain="bitcoin",
        category="Ransomware",
        label="WannaCry Extortion Wallet",
        source="Cryptocurrency Threat Intelligence DB",
        reference_url="https://threatintel.example.org/records/WANNACRY-001",
        confidence=0.95,
        first_seen=now - timedelta(days=120),
        last_seen=now - timedelta(hours=2),
        notes="High-risk wallet associated with ransomware ransom collections.",
        status="VERIFIED",
        is_demo=True,
    )
    t2 = ThreatFinding(
        wallet_address="0x077d37a6553a309b888824e0373809071c356f9a",
        blockchain="ethereum",
        category="Suspicious Service",
        label="Tornado.Cash Deposit Proxy",
        source="OFAC Sanctions & Mixer Watchlist",
        reference_url="https://sanctions.example.org/details/ETH-MIXER-99",
        confidence=0.88,
        first_seen=now - timedelta(days=45),
        last_seen=now - timedelta(minutes=30),
        notes="Flagged privacy protocol contract for illicit asset obfuscation.",
        status="VERIFIED",
        is_demo=True,
    )
    db.add_all([t1, t2])
    db.commit()

    # 4. OSINT Findings
    o1 = OSINTFinding(
        wallet_address="19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
        source="BitcoinTalk Forum",
        source_category="public",
        record_type="IMPORTED_INTELLIGENCE",
        finding="Address reported in extortion thread #8821",
        status="FOUND",
        confidence=0.9,
        reference_url="https://bitcointalk.org",
        notes="Multiple users confirmed ransom demand sent to this address.",
        observed_at=now - timedelta(days=100),
        is_demo=True,
    )
    o2 = OSINTFinding(
        wallet_address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        source="ENS Registry",
        source_category="public",
        record_type="VERIFIED_SOURCE",
        finding="Resolved ENS domain: vitalik.eth",
        status="FOUND",
        confidence=1.0,
        reference_url="https://app.ens.domains",
        notes="Public identity domain for Vitalik Buterin.",
        observed_at=now - timedelta(days=500),
        is_demo=True,
    )
    db.add_all([o1, o2])
    db.commit()

    # 5. Cases & Case Events
    c1 = Case(
        case_number="CASE-2026-001",
        title="Operation DarkWatch - WannaCry Fund Tracing",
        description="Investigation into illicit bitcoin flow from ransomware extortion wallet.",
        status="UNDER_INVESTIGATION",
        priority="HIGH",
        investigator="Lead Analyst",
        created_at=now - timedelta(days=5),
    )
    c2 = Case(
        case_number="CASE-2026-002",
        title="EVM Exploit Mixer Fund Laundering",
        description="Tracking stolen protocol assets routed through Tornado Cash proxies.",
        status="OPEN",
        priority="CRITICAL",
        investigator="Senior Forensics Lead",
        created_at=now - timedelta(days=2),
    )
    db.add_all([c1, c2])
    db.commit()

    ce1 = CaseEvent(
        case_id=c1.id,
        event_type="wallet_added",
        description="Added target wallet 19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P to investigation.",
        created_at=now - timedelta(days=5),
    )
    ce2 = CaseEvent(
        case_id=c1.id,
        event_type="evidence_attached",
        description="Attached transaction execution graph and threat intelligence report.",
        created_at=now - timedelta(days=3),
    )
    db.add_all([ce1, ce2])
    db.commit()

    # 6. Alerts & Monitored Wallets
    a1 = Alert(
        wallet_address="19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
        rule={"name": "Large Ransomware Outflow", "threshold": 2.0},
        transaction_hash="a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d",
        severity="HIGH",
        status="NEW",
        title="Outflow Detected on Flagged Ransomware Wallet",
        message="Transaction of 2.5 BTC observed to Binance Cold Storage.",
        is_demo=True,
        created_at=now - timedelta(hours=3),
    )
    a2 = Alert(
        wallet_address="0x077d37a6553a309b888824e0373809071c356f9a",
        rule={"name": "Mixer Deposit Alert", "protocol": "Tornado"},
        transaction_hash="0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b",
        severity="CRITICAL",
        status="NEW",
        title="Mixer Deposit Executed",
        message="Interaction detected with privacy protocol contract.",
        is_demo=True,
        created_at=now - timedelta(hours=5),
    )
    mw1 = MonitoredWallet(
        wallet_address="19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
        blockchain="bitcoin",
        label="WannaCry Treasury Watch",
        rules={"notify_on_transfer": True, "min_amount": 0.5},
        status="ACTIVE",
        last_checked=now - timedelta(minutes=5),
        last_tx_hash="a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d",
        is_demo=True,
    )
    db.add_all([a1, a2, mw1])
    db.commit()

    # 7. Evidence
    e1 = Evidence(
        case_id=c1.id,
        type="Transaction Hash",
        title="Ransomware Outbound TX",
        description="2.5 BTC transfer hash log",
        source="mempool.space",
        sha256="a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d",
        size_bytes=1024,
        content_text="TXID: a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d",
        created_at=now - timedelta(days=3),
    )
    db.add(e1)
    db.commit()

    # 8. Initial Investigation Record
    inv1 = Investigation(
        case_id=c1.id,
        title="Investigation: 19R2w9h5dK...N3m4P",
        wallet_address="19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
        blockchain="bitcoin",
        status="COMPLETED",
        risk_level="HIGH",
        risk_score=85.0,
        investigator="Lead Analyst",
        notes="Confirmed connection to ransomware extortion activity.",
        created_at=now - timedelta(days=1),
    )
    db.add(inv1)
    db.commit()

    # 9. Audit Log
    log1 = AuditLog(
        action="database_initialized",
        resource_type="system",
        resource_id="postgres_seed",
        investigator="System",
        metadata_json={"seed_wallets": 5, "seed_transactions": 4, "seed_cases": 2},
        timestamp=now,
    )
    db.add(log1)
    db.commit()
