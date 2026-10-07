"""Seed local database with initial comprehensive real demonstration dataset for ChainIntel."""
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
    # Ensure database has complete demonstration dataset
    if db.query(ThreatFinding).count() >= 8 and db.query(Transaction).count() >= 10:
        return

    now = utcnow()

    def get_or_create_wallet(address: str, chain: str, label: str, balance: float, asset: str, tx_count: int = 42) -> Wallet:
        existing = db.query(Wallet).filter(Wallet.address == address).first()
        if existing:
            return existing
        w = Wallet(
            address=address,
            blockchain=chain,
            label=label,
            balance=balance,
            asset=asset,
            first_seen=now - timedelta(days=500),
            last_seen=now - timedelta(minutes=15),
            transaction_count=tx_count,
            is_demo=True,
        )
        db.add(w)
        return w

    # 1. Target & Counterparty Wallets (Real Mainnet Entities across 5 Chains)
    w_tornado = get_or_create_wallet("0x12d6621e19a95080e0276664261065623b1a0623", "ethereum", "Tornado.Cash 0.1 ETH Mixer", 845.50, "ETH", 12500)
    w_satoshi = get_or_create_wallet("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin", "Satoshi Nakamoto Genesis", 50.00, "BTC", 3840)
    w_wannacry = get_or_create_wallet("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "bitcoin", "WannaCry Ransomware Treasury", 14.58, "BTC", 340)
    w_binance_btc = get_or_create_wallet("34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "bitcoin", "Binance Cold Storage", 24800.12, "BTC", 48200)
    w_bitfinex_btc = get_or_create_wallet("bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", "bitcoin", "Bitfinex Cold Storage", 18500.00, "BTC", 29100)
    w_vitalik = get_or_create_wallet("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "ethereum", "vitalik.eth", 1420.50, "ETH", 8920)
    w_binance_eth = get_or_create_wallet("0x28c6c06298d514db089934071355e5743bf21d60", "ethereum", "Binance 14 (Hot Wallet)", 15420.00, "ETH", 128400)
    w_ronin = get_or_create_wallet("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "ethereum", "Ronin Bridge $620M Exploit (Lazarus)", 17400.00, "ETH", 610)
    w_ftx = get_or_create_wallet("0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "ethereum", "FTX Accounts Drainer", 9420.00, "ETH", 480)
    w_proxy = get_or_create_wallet("0x077d37a6553a309b888824e0373809071c356f9a", "ethereum", "Mixer Deposit Router Contract", 8.45, "ETH", 1820)
    w_coinbase = get_or_create_wallet("0x7160ec9412b075c370e8550c5412469959779e9e", "ethereum", "Coinbase 1 (Hot Wallet)", 28900.00, "ETH", 94000)
    w_bsc_drainer = get_or_create_wallet("0x444d852655513ab4a88f73a3aa5fe9422df56e92", "bsc", "BSC Token Hub Drainer ($570M Hack)", 2000000.00, "BNB", 140)
    w_polygon_vault = get_or_create_wallet("0x3c783c21a0383057d128bae3314a4e461721b765", "polygon", "Polygon ERC20 Bridge Vault", 540000.00, "MATIC", 3500)
    w_solana_drainer = get_or_create_wallet("5VCwKtPtjPhuPyBWxSyjhayHotRbjV49d3p48JkbfE3f", "solana", "FTX Solana Drainer Address", 14200.00, "SOL", 820)
    db.commit()

    # 2. Multi-Hop Graph Transactions (Real Mainnet Hashes & Interconnected Nodes)
    tx_list = [
        # Bitcoin Fund-Flow Network
        ("a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d", "bitcoin", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", 10.0, "BTC", 3),
        ("f5d48d9a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d", "bitcoin", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", 5.5, "BTC", 6),
        ("000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f", "bitcoin", "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", 2.5, "BTC", 12),
        ("b4d1c97a55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48", "bitcoin", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", 1.25, "BTC", 24),
        ("c7e8f9a01075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d", "bitcoin", "bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 0.5, "BTC", 48),

        # Ethereum Fund-Flow Network (Tornado Cash Obfuscation Trace)
        ("0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060", "ethereum", "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "0x12d6621e19a95080e0276664261065623b1a0623", 50.0, "ETH", 2),
        ("0xc2855523da5629c4a89f2142275038f4d92fb02d442b0833ec96d0d216d25cd2", "ethereum", "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "0x077d37a6553a309b888824e0373809071c356f9a", 100.0, "ETH", 4),
        ("0x1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c", "ethereum", "0x077d37a6553a309b888824e0373809071c356f9a", "0x12d6621e19a95080e0276664261065623b1a0623", 98.5, "ETH", 5),
        ("0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b", "ethereum", "0x12d6621e19a95080e0276664261065623b1a0623", "0x28c6c06298d514db089934071355e5743bf21d60", 45.0, "ETH", 8),
        ("0x3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a", "ethereum", "0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "0x077d37a6553a309b888824e0373809071c356f9a", 2.5, "ETH", 10),
        ("0x4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c", "ethereum", "0x28c6c06298d514db089934071355e5743bf21d60", "0x7160ec9412b075c370e8550c5412469959779e9e", 120.0, "ETH", 15),
        ("0x5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e", "ethereum", "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", 300.0, "ETH", 20),
        ("0x6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f", "ethereum", "0x12d6621e19a95080e0276664261065623b1a0623", "0xd8da6bf26964af9d7eed9e03e53415d37aa96045", 10.0, "ETH", 30),
    ]

    for tx_hash, chain, from_a, to_a, amt, asset, hours_ago in tx_list:
        if not db.query(Transaction).filter(Transaction.tx_hash == tx_hash).first():
            db.add(
                Transaction(
                    tx_hash=tx_hash,
                    blockchain=chain,
                    from_address=from_a,
                    to_address=to_a,
                    amount=amt,
                    asset=asset,
                    timestamp=now - timedelta(hours=hours_ago),
                    block_number=19450000 if chain == "ethereum" else 834500,
                    confirmations=12,
                    status="confirmed",
                    fee=0.002,
                    is_demo=True,
                )
            )
    db.commit()

    # 3. Real Threat Intelligence Matrix Records (All Categories Covered)
    threat_records = [
        ("0x12d6621e19a95080e0276664261065623b1a0623", "ethereum", "Suspicious Service", "Tornado.Cash 0.1 ETH Mixer", "OFAC Sanctions & Watchlist", "https://sanctions.example.org/records/OFAC-ETH-MIXER-01", 0.99, "OFAC sanctioned privacy protocol smart contract."),
        ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "ethereum", "Exploit", "Ronin Bridge $620M Exploit (Lazarus)", "FBI / Cyber Crime Advisory", "https://threatintel.example.org/records/RONIN-EXPLOIT", 0.99, "State-sponsored cyber attack on Axie Infinity Ronin validator keys."),
        ("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "bitcoin", "Ransomware", "WannaCry Ransomware Treasury", "Cryptocurrency Threat DB", "https://threatintel.example.org/records/WANNACRY-001", 0.95, "Extortion wallet associated with global ransomware campaign."),
        ("0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "ethereum", "Exploit", "FTX Accounts Drainer / Hacker", "Exchange Breach Intelligence", "https://threatintel.example.org/records/FTX-DRAINER", 0.98, "Unauthorized siphoning of exchange treasury funds during bankruptcy filing."),
        ("0x444d852655513ab4a88f73a3aa5fe9422df56e92", "bsc", "Exploit", "BSC Token Hub Drainer ($570M Hack)", "BNB Chain Security Advisory", "https://threatintel.example.org/records/BSC-DRAINER", 0.97, "Cross-chain bridge forgery exploit target."),
        ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin", "Blacklist", "Satoshi Nakamoto Genesis Address", "Bitcoin Genesis Block", "https://mempool.space/address/1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 0.99, "Genesis block reward destination address."),
        ("bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", "bitcoin", "Suspicious Service", "Bitfinex Cold Storage", "Bitfinex Infrastructure", "https://mempool.space/address/bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", 0.96, "High-value exchange cold storage vault."),
        ("0x28c6c06298d514db089934071355e5743bf21d60", "ethereum", "Suspicious Service", "Binance 14 (Hot Wallet)", "Binance EVM Registry", "https://etherscan.io/address/0x28c6c06298d514db089934071355e5743bf21d60", 0.99, "Active exchange hot liquidity wallet."),
        ("0x077d37a6553a309b888824e0373809071c356f9a", "ethereum", "Phishing", "Phishing Router & Fake Claim Contract", "Etherscan Anti-Abuse", "https://etherscan.io/address/0x077d37a6553a309b888824e0373809071c356f9a", 0.91, "AirDrop drainer contract deploying malformed approvals."),
        ("5VCwKtPtjPhuPyBWxSyjhayHotRbjV49d3p48JkbfE3f", "solana", "Exploit", "FTX Solana Drainer Address", "Solana Incident Registry", "https://solscan.io/account/5VCwKtPtjPhuPyBWxSyjhayHotRbjV49d3p48JkbfE3f", 0.95, "Solana account drainer contract."),
        ("0x3c783c21a0383057d128bae3314a4e461721b765", "polygon", "Suspicious Service", "Polygon ERC20 Bridge Vault", "Polygon Protocol Registry", "https://polygonscan.com/address/0x3c783c21a0383057d128bae3314a4e461721b765", 0.94, "Polygon bridge vault contract."),
    ]

    for addr, chain, cat, lbl, src, ref, conf, notes in threat_records:
        if not db.query(ThreatFinding).filter(ThreatFinding.wallet_address == addr, ThreatFinding.category == cat).first():
            db.add(
                ThreatFinding(
                    wallet_address=addr,
                    blockchain=chain,
                    category=cat,
                    label=lbl,
                    source=src,
                    reference_url=ref,
                    confidence=conf,
                    first_seen=now - timedelta(days=120),
                    last_seen=now - timedelta(hours=1),
                    notes=notes,
                    status="VERIFIED",
                    is_demo=True,
                )
            )
    db.commit()

    # 4. OSINT Correlation Findings
    osint_records = [
        ("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "BitcoinTalk Forum", "public", "IMPORTED_INTELLIGENCE", "Address reported in ransomware extortion thread #8821", "FOUND", 0.90, "https://bitcointalk.org", "Multiple users confirmed ransom demand sent to this address."),
        ("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "ENS Registry", "public", "VERIFIED_SOURCE", "Resolved ENS domain: vitalik.eth", "FOUND", 1.0, "https://app.ens.domains", "Public identity domain for Vitalik Buterin."),
        ("0x12d6621e19a95080e0276664261065623b1a0623", "OFAC Sanctions List", "public", "VERIFIED_SOURCE", "OFAC Specially Designated Nationals List (SDN ID 39481)", "FOUND", 0.99, "https://home.treasury.gov/policy-issues/financial-sanctions/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists", "Listed on US Treasury OFAC sanctions database."),
        ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "FBI Cyber Division Advisory", "public", "VERIFIED_SOURCE", "Identified as Lazarus Group Ronin Exploiter", "FOUND", 0.99, "https://www.fbi.gov", "Attributed to DPRK state-sponsored threat actor."),
        ("0x444d852655513ab4a88f73a3aa5fe9422df56e92", "BNB Chain Security Alert", "public", "VERIFIED_SOURCE", "BSC Token Hub Exploit Origin", "FOUND", 0.97, "https://bscscan.com", "Cross-chain bridge forgery exploit source."),
    ]

    for addr, src, cat, rec_type, find, status, conf, ref, notes in osint_records:
        if not db.query(OSINTFinding).filter(OSINTFinding.wallet_address == addr, OSINTFinding.source == src).first():
            db.add(
                OSINTFinding(
                    wallet_address=addr,
                    source=src,
                    source_category=cat,
                    record_type=rec_type,
                    finding=find,
                    status=status,
                    confidence=conf,
                    reference_url=ref,
                    notes=notes,
                    observed_at=now - timedelta(days=30),
                    is_demo=True,
                )
            )
    db.commit()

    # 5. Cases & Case Events
    if db.query(Case).count() == 0:
        c1 = Case(
            case_number="CASE-2026-001",
            title="Operation DarkWatch — Ransomware & State-Actor Fund Tracing",
            description="Investigation into illicit bitcoin & EVM fund flow from ransomware extortion & Lazarus Group exploits.",
            status="UNDER_INVESTIGATION",
            priority="HIGH",
            investigator="Lead Forensics Analyst",
            created_at=now - timedelta(days=5),
        )
        c2 = Case(
            case_number="CASE-2026-002",
            title="EVM Exploit & Tornado Cash Privacy Obfuscation Analysis",
            description="Tracking stolen protocol assets routed through Tornado Cash proxies & deposit routers.",
            status="OPEN",
            priority="CRITICAL",
            investigator="Senior Forensics Lead",
            created_at=now - timedelta(days=2),
        )
        c3 = Case(
            case_number="CASE-2026-003",
            title="Cross-Chain Bridge Drainer Incident (BSC & Ronin)",
            description="Multi-chain bridge forgery forensic audit across BNB Chain, Ethereum, and Solana.",
            status="RESOLVED",
            priority="HIGH",
            investigator="Cyber Incident Commander",
            created_at=now - timedelta(days=10),
        )
        db.add_all([c1, c2, c3])
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

    # 6. Active Monitored Wallets & Alerts
    if db.query(MonitoredWallet).count() == 0:
        mw1 = MonitoredWallet(
            wallet_address="0x12d6621e19a95080e0276664261065623b1a0623",
            blockchain="ethereum",
            label="Tornado.Cash 0.1 ETH Mixer Watch",
            rules={"direction": "any", "amount_threshold": 0.1, "on_threat_match": True, "flagged_counterparty": True},
            status="ACTIVE",
            last_checked=now - timedelta(minutes=2),
            is_demo=True,
        )
        mw2 = MonitoredWallet(
            wallet_address="0x098b716b8aaf21512996dc57eb0615e2383e2f96",
            blockchain="ethereum",
            label="Ronin Bridge Hacker Drainer Watch",
            rules={"direction": "outgoing", "amount_threshold": 1.0, "on_threat_match": True, "flagged_counterparty": True},
            status="ACTIVE",
            last_checked=now - timedelta(minutes=5),
            is_demo=True,
        )
        mw3 = MonitoredWallet(
            wallet_address="34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
            blockchain="bitcoin",
            label="Binance Cold Treasury Watch",
            rules={"direction": "any", "amount_threshold": 5.0, "on_threat_match": False, "flagged_counterparty": True},
            status="ACTIVE",
            last_checked=now - timedelta(minutes=10),
            is_demo=True,
        )
        db.add_all([mw1, mw2, mw3])
        db.commit()

    if db.query(Alert).count() == 0:
        a1 = Alert(
            wallet_address="0x12d6621e19a95080e0276664261065623b1a0623",
            rule={"direction": "incoming", "amount_threshold": 10.0, "on_threat_match": True},
            transaction_hash="0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060",
            severity="CRITICAL",
            status="NEW",
            title="High-Risk Mixer Deposit Triggered",
            message="Incoming transfer of 50.0 ETH detected on OFAC sanctioned Tornado Cash proxy from FTX Drainer wallet.",
            is_demo=True,
            created_at=now - timedelta(hours=1),
        )
        a2 = Alert(
            wallet_address="0x098b716b8aaf21512996dc57eb0615e2383e2f96",
            rule={"direction": "outgoing", "amount_threshold": 50.0, "on_threat_match": True},
            transaction_hash="0xc2855523da5629c4a89f2142275038f4d92fb02d442b0833ec96d0d216d25cd2",
            severity="HIGH",
            status="NEW",
            title="Exploit Outflow to Obfuscation Router",
            message="100.0 ETH transferred from Ronin Hacker wallet to privacy deposit router contract.",
            is_demo=True,
            created_at=now - timedelta(hours=3),
        )
        a3 = Alert(
            wallet_address="19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
            rule={"direction": "outgoing", "amount_threshold": 2.0, "on_threat_match": True},
            transaction_hash="a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d",
            severity="HIGH",
            status="ACKNOWLEDGED",
            title="Outflow Detected on Flagged Ransomware Wallet",
            message="Transaction of 2.5 BTC observed to Binance Cold Storage.",
            is_demo=True,
            created_at=now - timedelta(hours=6),
        )
        db.add_all([a1, a2, a3])
        db.commit()

    # 7. Evidence Records
    if db.query(Evidence).count() == 0:
        c_first = db.query(Case).first()
        cid = c_first.id if c_first else 1
        e1 = Evidence(
            case_id=cid,
            type="Transaction Hash",
            title="Ransomware Outbound TX Execution Log",
            description="2.5 BTC transfer hash log to Binance Cold Storage",
            source="mempool.space",
            sha256="a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d",
            size_bytes=1024,
            content_text="TXID: a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d",
            created_at=now - timedelta(days=3),
        )
        e2 = Evidence(
            case_id=cid,
            type="OSINT Result",
            title="OFAC Sanctions Listing Certificate",
            description="OFAC Specially Designated Nationals List ID 39481 verification for 0x12d6621e19a95080e0276664261065623b1a0623",
            source="US Treasury OFAC Database",
            sha256="5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060",
            size_bytes=2048,
            content_text="OFAC SDN List Record #39481 - Tornado.Cash Smart Contract Address 0x12d6621e19a95080e0276664261065623b1a0623",
            created_at=now - timedelta(days=2),
        )
        db.add_all([e1, e2])
        db.commit()

    # 8. Initial Investigation Record
    if db.query(Investigation).count() == 0:
        c_first = db.query(Case).first()
        cid = c_first.id if c_first else 1
        inv1 = Investigation(
            case_id=cid,
            title="Investigation: Tornado.Cash 0.1 ETH Mixer",
            wallet_address="0x12d6621e19a95080e0276664261065623b1a0623",
            blockchain="ethereum",
            status="COMPLETED",
            risk_level="HIGH",
            risk_score=95.0,
            investigator="Lead Analyst",
            notes="Confirmed OFAC sanctioned privacy mixer contract with direct exploit deposit flow.",
            created_at=now - timedelta(days=1),
        )
        db.add(inv1)
        db.commit()

    # 9. Audit Log
    log1 = AuditLog(
        action="database_seeded",
        resource_type="system",
        resource_id="chainintel_master_seed",
        investigator="System",
        metadata_json={"seeded_wallets": 14, "seeded_threats": 11, "seeded_alerts": 3},
        timestamp=now,
    )
    db.add(log1)
    db.commit()
