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
    # If database already has full seed data, return
    if db.query(ThreatFinding).count() >= 5 and db.query(Transaction).count() >= 8:
        return

    now = utcnow()

    # Helper function to get or create wallet
    def get_or_create_wallet(address: str, chain: str, label: str, balance: float, asset: str) -> Wallet:
        existing = db.query(Wallet).filter(Wallet.address == address).first()
        if existing:
            return existing
        w = Wallet(
            address=address,
            blockchain=chain,
            label=label,
            balance=balance,
            asset=asset,
            first_seen=now - timedelta(days=365),
            last_seen=now - timedelta(hours=1),
            transaction_count=25,
            is_demo=True,
        )
        db.add(w)
        return w

    # 1. Target & Counterparty Wallets
    w_tornado = get_or_create_wallet("0x12d6621e19a95080e0276664261065623b1a0623", "ethereum", "Tornado.Cash 0.1 ETH Mixer", 845.5, "ETH")
    w_satoshi = get_or_create_wallet("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin", "Satoshi Nakamoto Genesis", 50.0, "BTC")
    w_wannacry = get_or_create_wallet("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "bitcoin", "WannaCry Ransomware Treasury", 14.58, "BTC")
    w_binance_btc = get_or_create_wallet("34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "bitcoin", "Binance Cold Storage", 24800.12, "BTC")
    w_bitfinex_btc = get_or_create_wallet("bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", "bitcoin", "Bitfinex Cold Storage", 18500.0, "BTC")
    w_vitalik = get_or_create_wallet("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "ethereum", "vitalik.eth", 1420.5, "ETH")
    w_binance_eth = get_or_create_wallet("0x28c6c06298d514db089934071355e5743bf21d60", "ethereum", "Binance 14 (Hot Wallet)", 15420.0, "ETH")
    w_ronin = get_or_create_wallet("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "ethereum", "Ronin Bridge $620M Exploit (Lazarus)", 17400.0, "ETH")
    w_ftx = get_or_create_wallet("0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "ethereum", "FTX Accounts Drainer", 9420.0, "ETH")
    w_proxy = get_or_create_wallet("0x077d37a6553a309b888824e0373809071c356f9a", "ethereum", "Mixer Deposit Router", 8.45, "ETH")
    w_coinbase = get_or_create_wallet("0x7160ec9412b075c370e8550c5412469959779e9e", "ethereum", "Coinbase 1 (Hot Wallet)", 28900.0, "ETH")
    db.commit()

    # 2. Multi-Hop Graph Transactions (Connecting all target presets!)
    tx_list = [
        # Bitcoin Graph (Satoshi Genesis -> Bitfinex -> Binance)
        ("tx_btc_1", "bitcoin", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", 10.0, "BTC", 3),
        ("tx_btc_2", "bitcoin", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", 5.5, "BTC", 6),
        ("tx_btc_3", "bitcoin", "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", 2.5, "BTC", 12),
        ("tx_btc_4", "bitcoin", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", 1.25, "BTC", 24),
        ("tx_btc_5", "bitcoin", "bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 0.5, "BTC", 48),

        # Ethereum Graph (Tornado Cash <-> Deposit Router <-> Vitalik <-> Binance <-> Ronin <-> FTX)
        ("tx_eth_1", "ethereum", "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "0x12d6621e19a95080e0276664261065623b1a0623", 50.0, "ETH", 2),
        ("tx_eth_2", "ethereum", "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "0x077d37a6553a309b888824e0373809071c356f9a", 100.0, "ETH", 4),
        ("tx_eth_3", "ethereum", "0x077d37a6553a309b888824e0373809071c356f9a", "0x12d6621e19a95080e0276664261065623b1a0623", 98.5, "ETH", 5),
        ("tx_eth_4", "ethereum", "0x12d6621e19a95080e0276664261065623b1a0623", "0x28c6c06298d514db089934071355e5743bf21d60", 45.0, "ETH", 8),
        ("tx_eth_5", "ethereum", "0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "0x077d37a6553a309b888824e0373809071c356f9a", 2.5, "ETH", 10),
        ("tx_eth_6", "ethereum", "0x28c6c06298d514db089934071355e5743bf21d60", "0x7160ec9412b075c370e8550c5412469959779e9e", 120.0, "ETH", 15),
        ("tx_eth_7", "ethereum", "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", 300.0, "ETH", 20),
        ("tx_eth_8", "ethereum", "0x12d6621e19a95080e0276664261065623b1a0623", "0xd8da6bf26964af9d7eed9e03e53415d37aa96045", 10.0, "ETH", 30),
    ]

    for tx_hash, chain, from_a, to_a, amt, asset, hours_ago in tx_list:
        if not db.query(Transaction).filter(Transaction.tx_hash == tx_hash).first():
            db.add(
                Transaction(
                    tx_hash=tx_hash if chain == "bitcoin" else f"0x{tx_hash}99887766554433221100aabbccddeeff",
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

    # 3. Rich Threat Intelligence Matrix Records (All Categories)
    threat_records = [
        ("0x12d6621e19a95080e0276664261065623b1a0623", "ethereum", "Suspicious Service", "Tornado.Cash 0.1 ETH Mixer", "OFAC Sanctions & Watchlist", "https://sanctions.example.org/records/OFAC-ETH-MIXER-01", 0.99, "OFAC sanctioned privacy protocol smart contract."),
        ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "ethereum", "Exploit", "Ronin Bridge $620M Exploit (Lazarus)", "FBI / Cyber Crime Alert", "https://threatintel.example.org/records/RONIN-EXPLOIT", 0.99, "State-sponsored cyber attack on Axie Infinity Ronin validator keys."),
        ("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "bitcoin", "Ransomware", "WannaCry Ransomware Treasury", "Cryptocurrency Threat DB", "https://threatintel.example.org/records/WANNACRY-001", 0.95, "Extortion wallet associated with global ransomware campaign."),
        ("0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "ethereum", "Exploit", "FTX Accounts Drainer / Hacker", "Exchange Breach Incident", "https://threatintel.example.org/records/FTX-DRAINER", 0.98, "Unauthorized siphoning of exchange treasury funds during bankruptcy filing."),
        ("0x444d852655513ab4a88f73a3aa5fe9422df56e92", "bsc", "Exploit", "BSC Token Hub Drainer ($570M Hack)", "BNB Chain Security Advisory", "https://threatintel.example.org/records/BSC-DRAINER", 0.97, "Cross-chain bridge forgery exploit target."),
        ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin", "Blacklist", "Satoshi Nakamoto Genesis Address", "Bitcoin Genesis Block", "https://mempool.space/address/1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 0.99, "Genesis block reward destination address."),
        ("bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", "bitcoin", "Suspicious Service", "Bitfinex Cold Storage", "Bitfinex Infrastructure", "https://mempool.space/address/bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", 0.96, "High-value exchange cold storage vault."),
        ("0x28c6c06298d514db089934071355e5743bf21d60", "ethereum", "Suspicious Service", "Binance 14 (Hot Wallet)", "Binance EVM Registry", "https://etherscan.io/address/0x28c6c06298d514db089934071355e5743bf21d60", 0.99, "Active exchange hot liquidity wallet."),
        ("0x077d37a6553a309b888824e0373809071c356f9a", "ethereum", "Phishing", "Phishing Router & Fake Claim Contract", "Etherscan Anti-Abuse", "https://etherscan.io/address/0x077d37a6553a309b888824e0373809071c356f9a", 0.91, "AirDrop drainer contract deploying malformed approvals."),
        ("5VCwKtPtjPhuPyBWxSyjhayHotRbjV49d3p48JkbfE3f", "solana", "Exploit", "FTX Solana Drainer Address", "Solana Incident Registry", "https://solscan.io/account/5VCwKtPtjPhuPyBWxSyjhayHotRbjV49d3p48JkbfE3f", 0.95, "Solana account drainer contract."),
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
                    first_seen=now - timedelta(days=60),
                    last_seen=now - timedelta(hours=1),
                    notes=notes,
                    status="VERIFIED",
                    is_demo=True,
                )
            )
    db.commit()

    # 4. OSINT Findings
    osint_records = [
        ("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "BitcoinTalk Forum", "public", "IMPORTED_INTELLIGENCE", "Address reported in ransomware extortion thread #8821", "FOUND", 0.90, "https://bitcointalk.org", "Multiple users confirmed ransom demand sent to this address."),
        ("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "ENS Registry", "public", "VERIFIED_SOURCE", "Resolved ENS domain: vitalik.eth", "FOUND", 1.0, "https://app.ens.domains", "Public identity domain for Vitalik Buterin."),
        ("0x12d6621e19a95080e0276664261065623b1a0623", "OFAC Sanctions List", "public", "VERIFIED_SOURCE", "OFAC Specially Designated Nationals List (SDN)", "FOUND", 0.99, "https://home.treasury.gov/policy-issues/financial-sanctions/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists", "Listed on US Treasury OFAC sanctions database."),
        ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "FBI Cyber Division Advisory", "public", "VERIFIED_SOURCE", "Identified as Lazarus Group Ronin Exploiter", "FOUND", 0.99, "https://www.fbi.gov", "Attributed to DPRK state-sponsored threat actor."),
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

    # 6. Active Alerts & Monitored Wallets (Working out of the box!)
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
            transaction_hash="0xeth_199887766554433221100aabbccddeeff",
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
            transaction_hash="0xeth_299887766554433221100aabbccddeeff",
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
            transaction_hash="tx_btc_3",
            severity="HIGH",
            status="ACKNOWLEDGED",
            title="Outflow Detected on Flagged Ransomware Wallet",
            message="Transaction of 2.5 BTC observed to Binance Cold Storage.",
            is_demo=True,
            created_at=now - timedelta(hours=6),
        )
        db.add_all([a1, a2, a3])
        db.commit()

    # 7. Audit Log
    log1 = AuditLog(
        action="database_seeded",
        resource_type="system",
        resource_id="chainintel_seed",
        investigator="System",
        metadata_json={"seeded_wallets": 10, "seeded_threats": 10, "seeded_alerts": 3},
        timestamp=now,
    )
    db.add(log1)
    db.commit()
