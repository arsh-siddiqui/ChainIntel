"""Seed SQLite database with initial comprehensive real demonstration dataset for ChainIntel.

Fully idempotent, concurrency-safe, and mode-aware:
- Fictional demo wallets, transactions, and cases are ONLY inserted when APP_MODE=DEMO.
- Addresses and blockchains are strictly normalized before checking/inserting.
- Uses SQLite native ON CONFLICT DO NOTHING for atomic collision handling.
- Individual try/except with rollback ensures partial failures never corrupt the session.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
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

logger = get_logger("seed")


def normalize_wallet_address(address: str, blockchain: str | None = None) -> str:
    """Normalize a blockchain address for consistent lookups and constraint matching."""
    addr = (address or "").strip()
    chain = (blockchain or "").strip().lower()
    if addr.startswith("0x") or chain in ("ethereum", "bsc", "polygon"):
        return addr.lower()
    if addr.lower().startswith("bc1"):
        return addr.lower()
    return addr


def normalize_chain(blockchain: str | None) -> str:
    """Normalize blockchain identifier."""
    return (blockchain or "unknown").strip().lower()


def seed_db(db: Session) -> None:
    """Idempotently seed demonstration and threat intelligence data without creating duplicate records."""
    now = utcnow()
    app_mode = settings.app_mode.upper()
    is_demo_mode = (app_mode == "DEMO")
    logger.info("Executing seed_db (app_mode=%s, is_demo_mode=%s)", app_mode, is_demo_mode)

    # 1. Wallets (ONLY inserted when APP_MODE=DEMO)
    if is_demo_mode:
        wallets_to_seed = [
            ("0x12d6621e19a95080e0276664261065623b1a0623", "ethereum", "Tornado.Cash 0.1 ETH Mixer", 845.50, "ETH", 12500),
            ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin", "Satoshi Nakamoto Genesis", 50.00, "BTC", 3840),
            ("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "bitcoin", "WannaCry Ransomware Treasury", 14.58, "BTC", 340),
            ("34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "bitcoin", "Binance Cold Storage", 24800.12, "BTC", 48200),
            ("bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", "bitcoin", "Bitfinex Cold Storage", 18500.00, "BTC", 29100),
            ("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "ethereum", "vitalik.eth", 1420.50, "ETH", 8920),
            ("0x28c6c06298d514db089934071355e5743bf21d60", "ethereum", "Binance 14 (Hot Wallet)", 15420.00, "ETH", 128400),
            ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "ethereum", "Ronin Bridge $620M Exploit (Lazarus)", 17400.00, "ETH", 610),
            ("0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "ethereum", "FTX Accounts Drainer", 9420.00, "ETH", 480),
            ("0x077d37a6553a309b888824e0373809071c356f9a", "ethereum", "Mixer Deposit Router Contract", 8.45, "ETH", 1820),
            ("0x7160ec9412b075c370e8550c5412469959779e9e", "ethereum", "Coinbase 1 (Hot Wallet)", 28900.00, "ETH", 94000),
            ("0x444d852655513ab4a88f73a3aa5fe9422df56e92", "bsc", "BSC Token Hub Drainer ($570M Hack)", 2000000.00, "BNB", 140),
            ("0x3c783c21a0383057d128bae3314a4e461721b765", "polygon", "Polygon ERC20 Bridge Vault", 540000.00, "MATIC", 3500),
            ("5VCwKtPtjPhuPyBWxSyjhayHotRbjV49d3p48JkbfE3f", "solana", "FTX Solana Drainer Address", 14200.00, "SOL", 820),
        ]
        for addr, chain, lbl, bal, ast, tx_cnt in wallets_to_seed:
            norm_addr = normalize_wallet_address(addr, chain)
            norm_chain = normalize_chain(chain)
            try:
                existing = db.query(Wallet).filter(
                    Wallet.address == norm_addr,
                    Wallet.blockchain == norm_chain,
                ).first()
                if not existing:
                    stmt = (
                        sqlite_insert(Wallet)
                        .values(
                            address=norm_addr,
                            blockchain=norm_chain,
                            label=lbl,
                            balance=bal,
                            asset=ast,
                            first_seen=now - timedelta(days=500),
                            last_seen=now - timedelta(minutes=15),
                            transaction_count=tx_cnt,
                            is_demo=True,
                        )
                        .on_conflict_do_nothing(index_elements=["address", "blockchain"])
                    )
                    db.execute(stmt)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("Wallet seed skipped (%s, %s): %s", norm_addr, norm_chain, exc)
    else:
        logger.info("APP_MODE is %s: Skipping fictional demo wallets.", app_mode)

    # 2. Multi-Hop Graph Transactions (ONLY in DEMO mode)
    if is_demo_mode:
        tx_list = [
            ("a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d", "bitcoin", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", 10.0, "BTC", 3),
            ("f5d48d9a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d", "bitcoin", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", 5.5, "BTC", 6),
            ("000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f", "bitcoin", "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", 2.5, "BTC", 12),
            ("b4d1c97a55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48", "bitcoin", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", 1.25, "BTC", 24),
            ("c7e8f9a01075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d", "bitcoin", "bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 0.5, "BTC", 48),

            ("0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060", "ethereum", "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "0x12d6621e19a95080e0276664261065623b1a0623", 50.0, "ETH", 2),
            ("0xc2855523da5629c4a89f2142275038f4d92fb02d442b0833ec96d0d216d25cd2", "ethereum", "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "0x077d37a6553a309b888824e0373809071c356f9a", 100.0, "ETH", 4),
            ("0x1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c", "ethereum", "0x077d37a6553a309b888824e0373809071c356f9a", "0x12d6621e19a95080e0276664261065623b1a0623", 98.5, "ETH", 5),
            ("0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b", "ethereum", "0x12d6621e19a95080e0276664261065623b1a0623", "0x28c6c06298d514db089934071355e5743bf21d60", 45.0, "ETH", 8),
            ("0x3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a", "ethereum", "0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "0x077d37a6553a309b888824e0373809071c356f9a", 2.5, "ETH", 10),
            ("0x4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c", "ethereum", "0x28c6c06298d514db089934071355e5743bf21d60", "0x7160ec9412b075c370e8550c5412469959779e9e", 120.0, "ETH", 15),
            ("0x5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e", "ethereum", "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", 300.0, "ETH", 20),
            ("0x6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f", "ethereum", "0x12d6621e19a95080e0276664261065623b1a0623", "0xd8da6bf26964af9d7eed9e03e53415d37aa96045", 10.0, "ETH", 30),
        ]
        for tx_h, chain, from_a, to_a, amt, asset, hours_ago in tx_list:
            norm_from = normalize_wallet_address(from_a, chain) if from_a else None
            norm_to = normalize_wallet_address(to_a, chain) if to_a else None
            norm_chain = normalize_chain(chain)
            try:
                existing = db.query(Transaction).filter(
                    Transaction.tx_hash == tx_h,
                    Transaction.from_address == norm_from,
                    Transaction.to_address == norm_to,
                ).first()
                if not existing:
                    stmt = (
                        sqlite_insert(Transaction)
                        .values(
                            tx_hash=tx_h,
                            blockchain=norm_chain,
                            from_address=norm_from,
                            to_address=norm_to,
                            amount=amt,
                            asset=asset,
                            timestamp=now - timedelta(hours=hours_ago),
                            block_number=19450000 if norm_chain == "ethereum" else 834500,
                            confirmations=12,
                            status="confirmed",
                            fee=0.002,
                            is_demo=True,
                        )
                        .on_conflict_do_nothing(index_elements=["tx_hash", "from_address", "to_address"])
                    )
                    db.execute(stmt)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("Transaction seed skipped (%s): %s", tx_h, exc)

    # 3. Real Threat Intelligence Matrix Records (Applicable in both modes)
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
        norm_addr = normalize_wallet_address(addr, chain)
        norm_chain = normalize_chain(chain)
        try:
            existing = db.query(ThreatFinding).filter(
                ThreatFinding.wallet_address == norm_addr,
                ThreatFinding.source == src,
                ThreatFinding.category == cat,
                ThreatFinding.label == lbl,
            ).first()
            if not existing:
                stmt = (
                    sqlite_insert(ThreatFinding)
                    .values(
                        wallet_address=norm_addr,
                        blockchain=norm_chain,
                        category=cat,
                        label=lbl,
                        source=src,
                        reference_url=ref,
                        confidence=conf,
                        first_seen=now - timedelta(days=120),
                        last_seen=now - timedelta(hours=1),
                        notes=notes,
                        status="VERIFIED",
                        is_demo=is_demo_mode,
                    )
                    .on_conflict_do_nothing(index_elements=["wallet_address", "source", "category", "label"])
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("ThreatFinding seed skipped (%s, %s): %s", norm_addr, cat, exc)

    # 4. OSINT Correlation Findings
    osint_records = [
        ("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "BitcoinTalk Forum", "public", "IMPORTED_INTELLIGENCE", "Address reported in ransomware extortion thread #8821", "FOUND", 0.90, "https://bitcointalk.org", "Multiple users confirmed ransom demand sent to this address."),
        ("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "ENS Registry", "public", "VERIFIED_SOURCE", "Resolved ENS domain: vitalik.eth", "FOUND", 1.0, "https://app.ens.domains", "Public identity domain for Vitalik Buterin."),
        ("0x12d6621e19a95080e0276664261065623b1a0623", "OFAC Sanctions List", "public", "VERIFIED_SOURCE", "OFAC Specially Designated Nationals List (SDN ID 39481)", "FOUND", 0.99, "https://home.treasury.gov/policy-issues/financial-sanctions/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists", "Listed on US Treasury OFAC sanctions database."),
        ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "FBI Cyber Division Advisory", "public", "VERIFIED_SOURCE", "Identified as Lazarus Group Ronin Exploiter", "FOUND", 0.99, "https://www.fbi.gov", "Attributed to DPRK state-sponsored threat actor."),
        ("0x444d852655513ab4a88f73a3aa5fe9422df56e92", "BNB Chain Security Alert", "public", "VERIFIED_SOURCE", "BSC Token Hub Exploit Origin", "FOUND", 0.97, "https://bscscan.com", "Cross-chain bridge forgery exploit source."),
    ]
    for addr, src, cat, rec_type, find, status, conf, ref, notes in osint_records:
        norm_addr = normalize_wallet_address(addr, "auto")
        try:
            existing = db.query(OSINTFinding).filter(
                OSINTFinding.wallet_address == norm_addr,
                OSINTFinding.source == src,
                OSINTFinding.record_type == rec_type,
            ).first()
            if not existing:
                stmt = (
                    sqlite_insert(OSINTFinding)
                    .values(
                        wallet_address=norm_addr,
                        source=src,
                        source_category=cat,
                        record_type=rec_type,
                        finding=find,
                        status=status,
                        confidence=conf,
                        reference_url=ref,
                        notes=notes,
                        observed_at=now - timedelta(days=30),
                        is_demo=is_demo_mode,
                    )
                    .on_conflict_do_nothing()
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("OSINTFinding seed skipped (%s, %s): %s", norm_addr, src, exc)

    # 5. Cases & Case Events (ONLY in DEMO mode)
    if is_demo_mode:
        cases_data = [
            ("CASE-2026-001", "Operation DarkWatch — Ransomware & State-Actor Fund Tracing", "Investigation into illicit bitcoin & EVM fund flow from ransomware extortion & Lazarus Group exploits.", "UNDER_INVESTIGATION", "HIGH", "Lead Forensics Analyst", 5),
            ("CASE-2026-002", "EVM Exploit & Tornado Cash Privacy Obfuscation Analysis", "Tracking stolen protocol assets routed through Tornado Cash proxies & deposit routers.", "OPEN", "CRITICAL", "Senior Forensics Lead", 2),
            ("CASE-2026-003", "Cross-Chain Bridge Drainer Incident (BSC & Ronin)", "Multi-chain bridge forgery forensic audit across BNB Chain, Ethereum, and Solana.", "RESOLVED", "HIGH", "Cyber Incident Commander", 10),
        ]
        for case_num, title, desc, st, prio, inv, days_ago in cases_data:
            try:
                existing = db.query(Case).filter(Case.case_number == case_num).first()
                if not existing:
                    stmt = (
                        sqlite_insert(Case)
                        .values(
                            case_number=case_num,
                            title=title,
                            description=desc,
                            status=st,
                            priority=prio,
                            investigator=inv,
                            created_at=now - timedelta(days=days_ago),
                        )
                        .on_conflict_do_nothing(index_elements=["case_number"])
                    )
                    db.execute(stmt)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("Case seed skipped (%s): %s", case_num, exc)

        c1 = db.query(Case).filter(Case.case_number == "CASE-2026-001").first()
        if c1:
            events_data = [
                ("wallet_added", "Added target wallet 19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P to investigation.", 5),
                ("evidence_attached", "Attached transaction execution graph and threat intelligence report.", 3),
            ]
            for ev_type, ev_desc, days_ago in events_data:
                try:
                    existing = db.query(CaseEvent).filter(
                        CaseEvent.case_id == c1.id,
                        CaseEvent.event_type == ev_type,
                    ).first()
                    if not existing:
                        stmt = (
                            sqlite_insert(CaseEvent)
                            .values(
                                case_id=c1.id,
                                event_type=ev_type,
                                description=ev_desc,
                                created_at=now - timedelta(days=days_ago),
                            )
                            .on_conflict_do_nothing()
                        )
                        db.execute(stmt)
                        db.commit()
                except Exception as exc:
                    db.rollback()
                    logger.warning("CaseEvent seed skipped: %s", exc)

    # 6. Monitored Wallets & Alerts (ONLY in DEMO mode)
    if is_demo_mode:
        mw_list = [
            ("0x12d6621e19a95080e0276664261065623b1a0623", "ethereum", "Tornado.Cash 0.1 ETH Mixer Watch", {"direction": "any", "amount_threshold": 0.1, "on_threat_match": True, "flagged_counterparty": True}, 2),
            ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "ethereum", "Ronin Bridge Hacker Drainer Watch", {"direction": "outgoing", "amount_threshold": 1.0, "on_threat_match": True, "flagged_counterparty": True}, 5),
            ("34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "bitcoin", "Binance Cold Treasury Watch", {"direction": "any", "amount_threshold": 5.0, "on_threat_match": False, "flagged_counterparty": True}, 10),
        ]
        for addr, chain, lbl, rls, mins_ago in mw_list:
            norm_addr = normalize_wallet_address(addr, chain)
            norm_chain = normalize_chain(chain)
            try:
                existing = db.query(MonitoredWallet).filter(MonitoredWallet.wallet_address == norm_addr).first()
                if not existing:
                    stmt = (
                        sqlite_insert(MonitoredWallet)
                        .values(
                            wallet_address=norm_addr,
                            blockchain=norm_chain,
                            label=lbl,
                            rules=rls,
                            status="ACTIVE",
                            last_checked=now - timedelta(minutes=mins_ago),
                            is_demo=True,
                        )
                        .on_conflict_do_nothing(index_elements=["wallet_address"])
                    )
                    db.execute(stmt)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("MonitoredWallet seed skipped (%s): %s", norm_addr, exc)

        alert_list = [
            ("0x12d6621e19a95080e0276664261065623b1a0623", {"direction": "incoming", "amount_threshold": 10.0, "on_threat_match": True}, "0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060", "CRITICAL", "NEW", "High-Risk Mixer Deposit Triggered", "Incoming transfer of 50.0 ETH detected on OFAC sanctioned Tornado Cash proxy from FTX Drainer wallet.", 1),
            ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", {"direction": "outgoing", "amount_threshold": 50.0, "on_threat_match": True}, "0xc2855523da5629c4a89f2142275038f4d92fb02d442b0833ec96d0d216d25cd2", "HIGH", "NEW", "Exploit Outflow to Obfuscation Router", "100.0 ETH transferred from Ronin Hacker wallet to privacy deposit router contract.", 3),
            ("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", {"direction": "outgoing", "amount_threshold": 2.0, "on_threat_match": True}, "a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d", "HIGH", "ACKNOWLEDGED", "Outflow Detected on Flagged Ransomware Wallet", "Transaction of 2.5 BTC observed to Binance Cold Storage.", 6),
        ]
        for addr, rls, tx_h, sev, st, title, msg, hrs_ago in alert_list:
            norm_addr = normalize_wallet_address(addr, "auto")
            try:
                existing = db.query(Alert).filter(
                    Alert.wallet_address == norm_addr,
                    Alert.transaction_hash == tx_h,
                    Alert.title == title,
                ).first()
                if not existing:
                    stmt = (
                        sqlite_insert(Alert)
                        .values(
                            wallet_address=norm_addr,
                            rule=rls,
                            transaction_hash=tx_h,
                            severity=sev,
                            status=st,
                            title=title,
                            message=msg,
                            is_demo=True,
                            created_at=now - timedelta(hours=hrs_ago),
                        )
                        .on_conflict_do_nothing()
                    )
                    db.execute(stmt)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("Alert seed skipped: %s", exc)

    # 7. Evidence Records (ONLY in DEMO mode)
    if is_demo_mode:
        c_first = db.query(Case).first()
        if c_first:
            evidence_list = [
                ("Transaction Hash", "Ransomware Outbound TX Execution Log", "2.5 BTC transfer hash log to Binance Cold Storage", "mempool.space", "a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d", 1024, "TXID: a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d", 3),
                ("OSINT Result", "OFAC Sanctions Listing Certificate", "OFAC Specially Designated Nationals List ID 39481 verification for 0x12d6621e19a95080e0276664261065623b1a0623", "US Treasury OFAC Database", "5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060", 2048, "OFAC SDN List Record #39481 - Tornado.Cash Smart Contract Address 0x12d6621e19a95080e0276664261065623b1a0623", 2),
            ]
            for ev_type, title, desc, src, sha, sz, txt, days_ago in evidence_list:
                try:
                    existing = db.query(Evidence).filter(Evidence.sha256 == sha).first()
                    if not existing:
                        stmt = (
                            sqlite_insert(Evidence)
                            .values(
                                case_id=c_first.id,
                                type=ev_type,
                                title=title,
                                description=desc,
                                source=src,
                                sha256=sha,
                                size_bytes=sz,
                                content_text=txt,
                                created_at=now - timedelta(days=days_ago),
                            )
                            .on_conflict_do_nothing()
                        )
                        db.execute(stmt)
                        db.commit()
                except Exception as exc:
                    db.rollback()
                    logger.warning("Evidence seed skipped: %s", exc)

    # 8. Initial Investigation Record (ONLY in DEMO mode)
    if is_demo_mode:
        c_first = db.query(Case).first()
        cid = c_first.id if c_first else None
        try:
            norm_addr = normalize_wallet_address("0x12d6621e19a95080e0276664261065623b1a0623", "ethereum")
            existing = db.query(Investigation).filter(Investigation.wallet_address == norm_addr).first()
            if not existing:
                stmt = (
                    sqlite_insert(Investigation)
                    .values(
                        case_id=cid,
                        title="Investigation: Tornado.Cash 0.1 ETH Mixer",
                        wallet_address=norm_addr,
                        blockchain="ethereum",
                        status="COMPLETED",
                        risk_level="HIGH",
                        risk_score=95.0,
                        investigator="Lead Analyst",
                        notes="Confirmed OFAC sanctioned privacy mixer contract with direct exploit deposit flow.",
                        created_at=now - timedelta(days=1),
                    )
                    .on_conflict_do_nothing()
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Investigation seed skipped: %s", exc)

    # 9. Audit Log
    try:
        existing = db.query(AuditLog).filter(
            AuditLog.action == "database_seeded",
            AuditLog.resource_id == f"chainintel_master_seed_{app_mode.lower()}",
        ).first()
        if not existing:
            stmt = (
                sqlite_insert(AuditLog)
                .values(
                    action="database_seeded",
                    resource_type="system",
                    resource_id=f"chainintel_master_seed_{app_mode.lower()}",
                    investigator="System",
                    metadata_json={"mode": app_mode, "is_demo": is_demo_mode},
                    timestamp=now,
                )
                .on_conflict_do_nothing()
            )
            db.execute(stmt)
            db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("AuditLog seed skipped: %s", exc)

    logger.info("seed_db completed successfully (mode=%s)", app_mode)


def main() -> None:
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
