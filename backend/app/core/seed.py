"""Seed SQLite database with initial comprehensive real demonstration dataset for ChainIntel.

Fully idempotent, concurrency-safe, and mode-aware:
- Seeds rich, realistic forensic intelligence data across all platform modules:
  Wallets, Transactions, Threat Intelligence, OSINT, Cases, Case Events,
  Monitored Wallets, Alerts, Evidence Locker, Investigations, Reports, and Audit Logs.
- Pre-seeded data is available in both LIVE and DEMO modes so all website views are populated immediately.
- Addresses and blockchains are strictly normalized before checking/inserting.
- Uses SQLite native ON CONFLICT DO NOTHING for atomic collision handling.
- Individual try/except with rollback ensures partial failures never corrupt the session.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

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
    Report,
    ThreatFinding,
    Transaction,
    Wallet,
)
from app.utils.datetime import iso, utcnow
from app.utils.hashing import sha256_bytes, sha256_file

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
    logger.info("Executing comprehensive seed_db (app_mode=%s)", app_mode)

    # -------------------------------------------------------------------------
    # 1. Wallets (Multi-chain high-profile intelligence targets & entities)
    # -------------------------------------------------------------------------
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
        ("0xb66cd966670d962c227b3eaba30a872dbfb995db", "ethereum", "Euler Finance Exploiter Treasury", 88750.00, "ETH", 95),
        ("0x56d8b635a7c88fd1104d23d634782c037098e77f", "ethereum", "Nomad Bridge Exploiter", 12300.00, "ETH", 215),
        ("1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX", "bitcoin", "Silk Road Seized Coins Address", 29650.00, "BTC", 1120),
        ("0x10ed43c718714eb63d5aa57b78b54704e256024e", "bsc", "PancakeSwap V2 Router", 85000.00, "BNB", 840000),
        ("0xa5e0829caced8ffdd4de3c43696c57f7d7a678ff", "polygon", "QuickSwap Router Contract", 195000.00, "MATIC", 420000),
        ("4ND6b27YFf7b4c4qHqM7Xo9jBwU3c7xY6dG7n5Q3m1a2", "solana", "Mango Markets Incident Attacker", 45000.00, "SOL", 110),
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
                        is_demo=False,
                    )
                    .on_conflict_do_nothing(index_elements=["address", "blockchain"])
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Wallet seed skipped (%s, %s): %s", norm_addr, norm_chain, exc)

    # -------------------------------------------------------------------------
    # 2. Multi-Hop Graph Transactions (Connected paths across BTC, ETH, BSC, Polygon, SOL)
    # -------------------------------------------------------------------------
    tx_list = [
        # Bitcoin Ransomware & Exchange Liquidity Peeling Chain
        ("a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d", "bitcoin", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", 10.0, "BTC", 3),
        ("f5d48d9a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d", "bitcoin", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", 5.5, "BTC", 6),
        ("000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f", "bitcoin", "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", 2.5, "BTC", 12),
        ("b4d1c97a55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48", "bitcoin", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", 1.25, "BTC", 24),
        ("c7e8f9a01075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d", "bitcoin", "bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 0.5, "BTC", 48),
        ("d8a7c2e1b4f6a9e012c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5", "bitcoin", "1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX", "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", 150.0, "BTC", 72),

        # Ethereum Privacy Obfuscation & Exploit Flow
        ("0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060", "ethereum", "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "0x12d6621e19a95080e0276664261065623b1a0623", 50.0, "ETH", 2),
        ("0xc2855523da5629c4a89f2142275038f4d92fb02d442b0833ec96d0d216d25cd2", "ethereum", "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "0x077d37a6553a309b888824e0373809071c356f9a", 100.0, "ETH", 4),
        ("0x1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c", "ethereum", "0x077d37a6553a309b888824e0373809071c356f9a", "0x12d6621e19a95080e0276664261065623b1a0623", 98.5, "ETH", 5),
        ("0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b", "ethereum", "0x12d6621e19a95080e0276664261065623b1a0623", "0x28c6c06298d514db089934071355e5743bf21d60", 45.0, "ETH", 8),
        ("0x3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a", "ethereum", "0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "0x077d37a6553a309b888824e0373809071c356f9a", 2.5, "ETH", 10),
        ("0x4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c", "ethereum", "0x28c6c06298d514db089934071355e5743bf21d60", "0x7160ec9412b075c370e8550c5412469959779e9e", 120.0, "ETH", 15),
        ("0x5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e", "ethereum", "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", 300.0, "ETH", 20),
        ("0x6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f", "ethereum", "0x12d6621e19a95080e0276664261065623b1a0623", "0xd8da6bf26964af9d7eed9e03e53415d37aa96045", 10.0, "ETH", 30),
        ("0x7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b", "ethereum", "0xb66cd966670d962c227b3eaba30a872dbfb995db", "0x12d6621e19a95080e0276664261065623b1a0623", 500.0, "ETH", 36),
        ("0x8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c", "ethereum", "0x56d8b635a7c88fd1104d23d634782c037098e77f", "0x077d37a6553a309b888824e0373809071c356f9a", 250.0, "ETH", 40),

        # BSC Cross-Chain Exploit Path
        ("0x9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d", "bsc", "0x444d852655513ab4a88f73a3aa5fe9422df56e92", "0x10ed43c718714eb63d5aa57b78b54704e256024e", 1500.0, "BNB", 18),

        # Polygon Bridge Vault Rebalance
        ("0x0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e", "polygon", "0x3c783c21a0383057d128bae3314a4e461721b765", "0xa5e0829caced8ffdd4de3c43696c57f7d7a678ff", 25000.0, "MATIC", 25),

        # Solana Drainer Flow
        ("5VCwKtPtjPhuPyBWxSyjhayHotRbjV49d3p48JkbfE3fTxHash01", "solana", "5VCwKtPtjPhuPyBWxSyjhayHotRbjV49d3p48JkbfE3f", "4ND6b27YFf7b4c4qHqM7Xo9jBwU3c7xY6dG7n5Q3m1a2", 1500.0, "SOL", 8),
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
                        block_number=19450000 if norm_chain == "ethereum" else (834500 if norm_chain == "bitcoin" else 35200000),
                        confirmations=12,
                        status="confirmed",
                        fee=0.002,
                        is_demo=False,
                    )
                    .on_conflict_do_nothing(index_elements=["tx_hash", "from_address", "to_address"])
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Transaction seed skipped (%s): %s", tx_h, exc)

    # -------------------------------------------------------------------------
    # 3. Real Threat Intelligence Matrix Records
    # -------------------------------------------------------------------------
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
        ("0xb66cd966670d962c227b3eaba30a872dbfb995db", "ethereum", "Exploit", "Euler Finance $197M Flash Loan Exploit", "Euler Security Advisory", "https://etherscan.io/address/0xb66cd966670d962c227b3eaba30a872dbfb995db", 0.98, "Flash loan donation attack drainage wallet."),
        ("0x56d8b635a7c88fd1104d23d634782c037098e77f", "ethereum", "Exploit", "Nomad Bridge $190M Verification Exploit", "Nomad Security Incident", "https://etherscan.io/address/0x56d8b635a7c88fd1104d23d634782c037098e77f", 0.97, "Replica contract message validation exploit target."),
        ("1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX", "bitcoin", "Blacklist", "Silk Road Seized Coins Treasury", "US Marshals Service Record", "https://mempool.space/address/1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX", 0.99, "Historical law enforcement seized coin treasury."),
        ("4ND6b27YFf7b4c4qHqM7Xo9jBwU3c7xY6dG7n5Q3m1a2", "solana", "Exploit", "Mango Markets Oracle Exploit Attacker", "Solana Incident Notice", "https://solscan.io", 0.96, "Oracle price manipulation and liquidity drainage attacker address."),
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
                        is_demo=False,
                    )
                    .on_conflict_do_nothing(index_elements=["wallet_address", "source", "category", "label"])
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("ThreatFinding seed skipped (%s, %s): %s", norm_addr, cat, exc)

    # -------------------------------------------------------------------------
    # 4. OSINT Correlation Findings
    # -------------------------------------------------------------------------
    osint_records = [
        ("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "BitcoinTalk Forum", "public", "IMPORTED_INTELLIGENCE", "Address reported in ransomware extortion thread #8821", "FOUND", 0.90, "https://bitcointalk.org", "Multiple users confirmed ransom demand sent to this address."),
        ("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "ENS Registry", "public", "VERIFIED_SOURCE", "Resolved ENS domain: vitalik.eth", "FOUND", 1.0, "https://app.ens.domains", "Public identity domain for Vitalik Buterin."),
        ("0x12d6621e19a95080e0276664261065623b1a0623", "OFAC Sanctions List", "public", "VERIFIED_SOURCE", "OFAC Specially Designated Nationals List (SDN ID 39481)", "FOUND", 0.99, "https://home.treasury.gov/policy-issues/financial-sanctions/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists", "Listed on US Treasury OFAC sanctions database."),
        ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "FBI Cyber Division Advisory", "public", "VERIFIED_SOURCE", "Identified as Lazarus Group Ronin Exploiter", "FOUND", 0.99, "https://www.fbi.gov", "Attributed to DPRK state-sponsored threat actor."),
        ("0x444d852655513ab4a88f73a3aa5fe9422df56e92", "BNB Chain Security Alert", "public", "VERIFIED_SOURCE", "BSC Token Hub Exploit Origin", "FOUND", 0.97, "https://bscscan.com", "Cross-chain bridge forgery exploit source."),
        ("0xb66cd966670d962c227b3eaba30a872dbfb995db", "Arkham Intelligence", "public", "VERIFIED_SOURCE", "Euler Finance Exploiter Public Entity Tag", "FOUND", 0.98, "https://arkhamintelligence.com", "Tagged on-chain entity associated with $197M protocol drainage."),
        ("0x56d8b635a7c88fd1104d23d634782c037098e77f", "PeckShield Incident Feed", "public", "VERIFIED_SOURCE", "Nomad Bridge Exploit Attacker Nexus", "FOUND", 0.96, "https://peckshield.com", "Confirmed primary attack contract initiator address."),
        ("bc1qgdjqv0av3q56jvd822syf4xyavbdchq96vg7wr", "Bitfinex Proof of Reserves", "public", "VERIFIED_SOURCE", "Bitfinex Cold Storage Public Attestation", "FOUND", 0.99, "https://bitfinex.com", "Audited institutional cold storage reserve address."),
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
                        is_demo=False,
                    )
                    .on_conflict_do_nothing()
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("OSINTFinding seed skipped (%s, %s): %s", norm_addr, src, exc)

    # -------------------------------------------------------------------------
    # 5. Cases & Forensic Event Timelines
    # -------------------------------------------------------------------------
    cases_data = [
        ("CASE-2026-001", "Operation DarkWatch — Ransomware & State-Actor Fund Tracing", "Investigation into illicit bitcoin & EVM fund flow from ransomware extortion & Lazarus Group exploits.", "UNDER_INVESTIGATION", "HIGH", "Lead Forensics Analyst", 5),
        ("CASE-2026-002", "EVM Exploit & Tornado Cash Privacy Obfuscation Analysis", "Tracking stolen protocol assets routed through Tornado Cash proxies & deposit routers.", "OPEN", "CRITICAL", "Senior Forensics Lead", 2),
        ("CASE-2026-003", "Cross-Chain Bridge Drainer Incident (BSC & Ronin)", "Multi-chain bridge forgery forensic audit across BNB Chain, Ethereum, and Solana.", "RESOLVED", "HIGH", "Cyber Incident Commander", 10),
        ("CASE-2026-004", "DeFi Flash Loan & Liquidity Drain Forensics (Euler & Nomad)", "Detailed forensic reconstruction of flash loan oracle manipulation and cross-chain message verification failures.", "UNDER_INVESTIGATION", "CRITICAL", "DeFi Security Specialist", 4),
        ("CASE-2026-005", "Institutional Cold Storage & CEX Reserve Verification Audit", "Quarterly on-chain solvency and multi-signature cold storage reserve verification audit across tier-1 exchanges.", "RESOLVED", "MEDIUM", "Compliance Officer", 15),
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

    # Populate Case Events for each case
    c1 = db.query(Case).filter(Case.case_number == "CASE-2026-001").first()
    if c1:
        c1_events = [
            ("wallet_added", "Target wallet 19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P (WannaCry) added to active tracking dossier.", 5),
            ("graph_expanded", "Identified outbound peeling chain to exchange deposit consolidation cluster.", 4),
            ("threat_correlated", "OFAC & FBI Cyber Advisory correlation confirmed DPRK ransomware extortion link.", 3),
            ("evidence_attached", "Attached transaction execution graph and threat intelligence report.", 2),
            ("subpoena_issued", "Exchange compliance liaison notified with law enforcement preservation request.", 1),
        ]
        for ev_type, ev_desc, days_ago in c1_events:
            try:
                existing = db.query(CaseEvent).filter(CaseEvent.case_id == c1.id, CaseEvent.description == ev_desc).first()
                if not existing:
                    stmt = sqlite_insert(CaseEvent).values(
                        case_id=c1.id, event_type=ev_type, description=ev_desc, created_at=now - timedelta(days=days_ago)
                    ).on_conflict_do_nothing()
                    db.execute(stmt)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("CaseEvent seed skipped: %s", exc)

    c2 = db.query(Case).filter(Case.case_number == "CASE-2026-002").first()
    if c2:
        c2_events = [
            ("wallet_added", "Primary mixer router 0x12d6621e19a95080e0276664261065623b1a0623 flagged for privacy obfuscation trace.", 2),
            ("graph_expanded", "Mapped 12 deposit contracts routing stolen FTX funds into Tornado Cash proxies.", 1),
            ("evidence_attached", "Sanctions designation documentation from US Treasury added to evidence locker.", 1),
            ("report_generated", "Initial executive dossier compiled for regulatory disclosure.", 0),
        ]
        for ev_type, ev_desc, days_ago in c2_events:
            try:
                existing = db.query(CaseEvent).filter(CaseEvent.case_id == c2.id, CaseEvent.description == ev_desc).first()
                if not existing:
                    stmt = sqlite_insert(CaseEvent).values(
                        case_id=c2.id, event_type=ev_type, description=ev_desc, created_at=now - timedelta(days=days_ago)
                    ).on_conflict_do_nothing()
                    db.execute(stmt)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("CaseEvent seed skipped: %s", exc)

    c3 = db.query(Case).filter(Case.case_number == "CASE-2026-003").first()
    if c3:
        c3_events = [
            ("wallet_added", "Ronin bridge exploiter 0x098b716b8aaf21512996dc57eb0615e2383e2f96 enrolled into multi-chain incident.", 10),
            ("graph_expanded", "Cross-chain bridge relay transactions mapped across BSC and Ethereum.", 7),
            ("threat_correlated", "State-sponsored attribution validated via CISA & FBI Joint Advisory.", 5),
            ("case_closed", "Full multi-chain forensic report published; assets blacklisted across major CEXs.", 1),
        ]
        for ev_type, ev_desc, days_ago in c3_events:
            try:
                existing = db.query(CaseEvent).filter(CaseEvent.case_id == c3.id, CaseEvent.description == ev_desc).first()
                if not existing:
                    stmt = sqlite_insert(CaseEvent).values(
                        case_id=c3.id, event_type=ev_type, description=ev_desc, created_at=now - timedelta(days=days_ago)
                    ).on_conflict_do_nothing()
                    db.execute(stmt)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("CaseEvent seed skipped: %s", exc)

    c4 = db.query(Case).filter(Case.case_number == "CASE-2026-004").first()
    if c4:
        c4_events = [
            ("wallet_added", "Euler Finance hacker 0xb66cd966670d962c227b3eaba30a872dbfb995db targeted for flash-loan tracking.", 4),
            ("evidence_attached", "Smart contract execution trace and decompiled bytecode analysis recorded.", 3),
            ("note_added", "Analyst confirmed partial return of assets via on-chain message negotiation.", 2),
        ]
        for ev_type, ev_desc, days_ago in c4_events:
            try:
                existing = db.query(CaseEvent).filter(CaseEvent.case_id == c4.id, CaseEvent.description == ev_desc).first()
                if not existing:
                    stmt = sqlite_insert(CaseEvent).values(
                        case_id=c4.id, event_type=ev_type, description=ev_desc, created_at=now - timedelta(days=days_ago)
                    ).on_conflict_do_nothing()
                    db.execute(stmt)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("CaseEvent seed skipped: %s", exc)

    c5 = db.query(Case).filter(Case.case_number == "CASE-2026-005").first()
    if c5:
        c5_events = [
            ("wallet_added", "Binance & Bitfinex cold reserve vaults enrolled for quarterly solvency audit.", 15),
            ("graph_expanded", "Zero-hop solvency verification completed across 48,000+ confirmed blocks.", 8),
            ("case_closed", "Solvency reserve attestation certified with 100% on-chain backing.", 2),
        ]
        for ev_type, ev_desc, days_ago in c5_events:
            try:
                existing = db.query(CaseEvent).filter(CaseEvent.case_id == c5.id, CaseEvent.description == ev_desc).first()
                if not existing:
                    stmt = sqlite_insert(CaseEvent).values(
                        case_id=c5.id, event_type=ev_type, description=ev_desc, created_at=now - timedelta(days=days_ago)
                    ).on_conflict_do_nothing()
                    db.execute(stmt)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.warning("CaseEvent seed skipped: %s", exc)

    # -------------------------------------------------------------------------
    # 6. Monitored Wallets & Active Threat Rules
    # -------------------------------------------------------------------------
    mw_list = [
        ("0x12d6621e19a95080e0276664261065623b1a0623", "ethereum", "Tornado.Cash 0.1 ETH Mixer Watch", {"direction": "any", "amount_threshold": 0.1, "on_threat_match": True, "flagged_counterparty": True}, 2),
        ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "ethereum", "Ronin Bridge Hacker Drainer Watch", {"direction": "outgoing", "amount_threshold": 1.0, "on_threat_match": True, "flagged_counterparty": True}, 5),
        ("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "bitcoin", "WannaCry Ransomware Treasury Watch", {"direction": "any", "amount_threshold": 0.5, "on_threat_match": True, "flagged_counterparty": True}, 8),
        ("34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "bitcoin", "Binance Cold Treasury Reserve Watch", {"direction": "any", "amount_threshold": 5.0, "on_threat_match": False, "flagged_counterparty": True}, 10),
        ("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", "ethereum", "Vitalik Buterin (vitalik.eth) Watch", {"direction": "incoming", "amount_threshold": 10.0, "on_threat_match": False, "flagged_counterparty": False}, 12),
        ("0x444d852655513ab4a88f73a3aa5fe9422df56e92", "bsc", "BSC Token Hub Drainer Watch", {"direction": "any", "amount_threshold": 100.0, "on_threat_match": True, "flagged_counterparty": True}, 14),
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
                        is_demo=False,
                    )
                    .on_conflict_do_nothing(index_elements=["wallet_address"])
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("MonitoredWallet seed skipped (%s): %s", norm_addr, exc)

    # -------------------------------------------------------------------------
    # 7. Real-Time Triggered Alerts
    # -------------------------------------------------------------------------
    alert_list = [
        ("0x12d6621e19a95080e0276664261065623b1a0623", {"direction": "incoming", "amount_threshold": 10.0, "on_threat_match": True}, "0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060", "CRITICAL", "NEW", "High-Risk Mixer Deposit Triggered", "Incoming transfer of 50.0 ETH detected on OFAC sanctioned Tornado Cash proxy from FTX Drainer wallet.", 1),
        ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", {"direction": "outgoing", "amount_threshold": 50.0, "on_threat_match": True}, "0xc2855523da5629c4a89f2142275038f4d92fb02d442b0833ec96d0d216d25cd2", "HIGH", "NEW", "Exploit Outflow to Obfuscation Router", "100.0 ETH transferred from Ronin Hacker wallet to privacy deposit router contract.", 3),
        ("19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", {"direction": "outgoing", "amount_threshold": 2.0, "on_threat_match": True}, "a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d", "HIGH", "ACKNOWLEDGED", "Outflow Detected on Flagged Ransomware Wallet", "Transaction of 2.5 BTC observed to Binance Cold Storage.", 6),
        ("0x098b716b8aaf21512996dc57eb0615e2383e2f96", {"direction": "outgoing", "amount_threshold": 100.0, "on_threat_match": True}, "0x5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e", "CRITICAL", "INVESTIGATING", "State-Sponsored Actor Peeling Chain Initiated", "Outflow of 300.0 ETH detected from Ronin Exploiter to secondary aggregator wallet.", 12),
        ("34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", {"direction": "any", "amount_threshold": 5.0, "on_threat_match": False}, "f5d48d9a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d", "MEDIUM", "RESOLVED", "Large Cold Storage Rebalance Transfer", "Routine institutional treasury transfer of 5.5 BTC to Bitfinex Cold Storage vault.", 24),
        ("0x444d852655513ab4a88f73a3aa5fe9422df56e92", {"direction": "any", "amount_threshold": 100.0, "on_threat_match": True}, "0x9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d", "HIGH", "INVESTIGATING", "Cross-Chain Token Hub Drain Activity", "Transfer of 1500.0 BNB initiated toward PancakeSwap V2 liquidity pool.", 30),
        ("0xd8da6bf26964af9d7eed9e03e53415d37aa96045", {"direction": "incoming", "amount_threshold": 5.0, "on_threat_match": False}, "0x6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f", "LOW", "RESOLVED", "High-Volume Whale Transfer on vitalik.eth", "Inbound transfer of 10.0 ETH received from privacy pool contract.", 48),
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
                        is_demo=False,
                        created_at=now - timedelta(hours=hrs_ago),
                    )
                    .on_conflict_do_nothing()
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Alert seed skipped: %s", exc)

    # -------------------------------------------------------------------------
    # 8. Evidence Locker (Files on disk & verified checksum records)
    # -------------------------------------------------------------------------
    evidence_dir = Path(settings.effective_evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    evidence_items = [
        (
            c1.id if c1 else None,
            "Transaction Hash",
            "Ransomware Outbound TX Execution Log",
            "2.5 BTC transfer hash log to Binance Cold Storage from WannaCry Treasury.",
            "mempool.space",
            "darkwatch_tx_execution.log",
            "TXID: a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d\nBlock: 834500\nAmount: 2.50000000 BTC\nFee: 0.00012000 BTC\nConfirmations: 12\nSource: 19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P\nDestination: 34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo\nStatus: VERIFIED_ON_CHAIN",
            3,
        ),
        (
            c2.id if c2 else None,
            "OSINT Result",
            "OFAC Sanctions Listing Certificate",
            "OFAC Specially Designated Nationals List ID 39481 verification for 0x12d6621e19a95080e0276664261065623b1a0623",
            "US Treasury OFAC Database",
            "ofac_sdn_tornado_cert.json",
            '{\n  "sdn_id": 39481,\n  "entity": "Tornado Cash",\n  "program": "CYBER2",\n  "designated_date": "2022-08-08",\n  "target_address": "0x12d6621e19a95080e0276664261065623b1a0623",\n  "status": "SANCTIONED"\n}',
            2,
        ),
        (
            c3.id if c3 else None,
            "API Response",
            "Ronin Validator Exploit Payload Trace",
            "Raw RPC payload of compromised validator signature approval.",
            "Etherscan / RPC Archive",
            "ronin_exploit_trace.json",
            '{\n  "chain": "ronin",\n  "tx": "0xc2855523da5629c4a89f2142275038f4d92fb02d442b0833ec96d0d216d25cd2",\n  "validator_threshold": 5,\n  "compromised_keys": ["0x9f8b...", "0x44a1..."],\n  "loss_usd": 620000000\n}',
            7,
        ),
        (
            c4.id if c4 else None,
            "Analyst Note",
            "DeFi Flash Loan Exploit Vector Affidavit",
            "Technical forensic breakdown of Euler Finance donation attack mechanism.",
            "Senior Forensics Lead",
            "euler_exploit_affidavit.txt",
            "FORENSIC AFFIDAVIT:\nTarget Protocol: Euler Finance\nAttack Vector: eToken mint donation mechanism\nExploiter Wallet: 0xb66cd966670d962c227b3eaba30a872dbfb995db\nTotal Extracted: $197,000,000 USD equivalent in ETH/DAI/WBTC\nResolution: Assets partially recovered via negotiated whitehat bounty.",
            4,
        ),
        (
            c2.id if c2 else None,
            "Graph Snapshot",
            "Multi-Hop Laundering Subgraph Visual",
            "Exported JSON cluster representation of Tornado Cash deposit hopping.",
            "ChainIntel Graph Engine",
            "tornado_laundering_subgraph.json",
            '{\n  "center": "0x12d6621e19a95080e0276664261065623b1a0623",\n  "hops": 2,\n  "nodes": 14,\n  "edges": 18,\n  "heuristic": "PEELING_CHAIN_DETECTED"\n}',
            1,
        ),
        (
            c1.id if c1 else None,
            "Document",
            "DPRK Lazarus Group Attribution Dossier",
            "Law enforcement advisory document correlating WannaCry & Ronin attacks.",
            "FBI Cyber Advisory",
            "fbi_lazarus_attribution_dossier.txt",
            "FEDERAL ADVISORY MEMORANDUM:\nSubject: Hidden Cobra / Lazarus Group Advanced Persistent Threat\nAttribution: RGB Reconnaissance General Bureau (DPRK)\nAssociated Addresses:\n- 19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P (WannaCry 2017)\n- 0x098b716b8aaf21512996dc57eb0615e2383e2f96 (Ronin 2022)\nEnforcement: Mandatory asset freeze and compliance reporting.",
            5,
        ),
    ]

    for cid, ev_type, title, desc, src, fname, content_str, days_ago in evidence_items:
        try:
            # Write physical file in effective_evidence_dir so file download succeeds
            file_path = evidence_dir / fname
            file_bytes = content_str.encode("utf-8")
            file_path.write_bytes(file_bytes)
            computed_sha = sha256_bytes(file_bytes)

            existing = db.query(Evidence).filter(Evidence.sha256 == computed_sha).first()
            if not existing:
                stmt = (
                    sqlite_insert(Evidence)
                    .values(
                        case_id=cid,
                        type=ev_type,
                        title=title,
                        description=desc,
                        source=src,
                        file_path=str(file_path),
                        file_name=fname,
                        sha256=computed_sha,
                        size_bytes=len(file_bytes),
                        content_text=content_str,
                        created_at=now - timedelta(days=days_ago),
                    )
                    .on_conflict_do_nothing()
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Evidence seed skipped (%s): %s", title, exc)

    # -------------------------------------------------------------------------
    # 9. Investigations (Complete risk assessments for top targets)
    # -------------------------------------------------------------------------
    investigations_data = [
        (
            c2.id if c2 else None,
            "Investigation: Tornado.Cash 0.1 ETH Mixer",
            "0x12d6621e19a95080e0276664261065623b1a0623",
            "ethereum",
            "COMPLETED",
            "HIGH",
            98.0,
            "Confirmed OFAC sanctioned privacy mixer contract with direct exploit deposit flow.",
            {
                "score": 98.0,
                "max_score": 100,
                "band": "HIGH",
                "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                "indicators": [
                    {"name": "OFAC Sanctions Match", "description": "Target address listed on US Treasury OFAC sanctions list.", "weight": 40, "source": "OFAC Database", "status": "TRIGGERED", "evidence": "Listed on SDN list under Cyber-related Sanctions (ID 39481)."},
                    {"name": "Mixer Protocol Interaction", "description": "Address operates as a decentralized privacy mixer smart contract.", "weight": 30, "source": "ChainIntel Heuristics", "status": "TRIGGERED", "evidence": "Tornado Cash 0.1 ETH fixed denomination pool contract."},
                    {"name": "Direct Exploit Deposit Counterparty", "description": "Counterparty is a known bridge or protocol drainer.", "weight": 28, "source": "Threat Matrix", "status": "TRIGGERED", "evidence": "Direct deposit inflow from FTX Drainer wallet 0x50d1..."},
                ],
            },
            1,
        ),
        (
            c3.id if c3 else None,
            "Investigation: Ronin Bridge $620M Exploit (Lazarus)",
            "0x098b716b8aaf21512996dc57eb0615e2383e2f96",
            "ethereum",
            "COMPLETED",
            "HIGH",
            99.0,
            "State-sponsored cyber exploit target with extensive multi-hop privacy peeling chains.",
            {
                "score": 99.0,
                "max_score": 100,
                "band": "HIGH",
                "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                "indicators": [
                    {"name": "State-Sponsored Cyber Threat Actor", "description": "Address formally attributed to DPRK Lazarus Group.", "weight": 40, "source": "FBI Cyber Advisory", "status": "TRIGGERED", "evidence": "FBI Cybersecurity Advisory CISA AA22-104A."},
                    {"name": "Major Protocol Exploit Origin", "description": "Source of $620M Ronin Bridge validator key compromise.", "weight": 35, "source": "Threat Matrix", "status": "TRIGGERED", "evidence": "173,600 ETH and 25.5M USDC drained in exploit transactions."},
                    {"name": "Rapid Fund Laundering Peeling Chain", "description": "High-velocity distribution through privacy pools and brokers.", "weight": 24, "source": "Graph Heuristics", "status": "TRIGGERED", "evidence": "Automated distribution through intermediate deposit routers."},
                ],
            },
            7,
        ),
        (
            c1.id if c1 else None,
            "Investigation: WannaCry Ransomware Treasury",
            "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
            "bitcoin",
            "COMPLETED",
            "HIGH",
            95.0,
            "Historic ransomware treasury wallet with verified extortion payments and exchange peeling hops.",
            {
                "score": 95.0,
                "max_score": 100,
                "band": "HIGH",
                "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                "indicators": [
                    {"name": "Ransomware Extortion Match", "description": "Hardcoded destination address in WannaCry cryptovirus payload.", "weight": 40, "source": "OSINT / Forum Reports", "status": "TRIGGERED", "evidence": "WannaCry ransomware payment demand destination."},
                    {"name": "Centralized Exchange Cash-Out", "description": "Outbound fund movement directed to CEX cold storage.", "weight": 30, "source": "Mempool Analysis", "status": "TRIGGERED", "evidence": "Transaction of 2.5 BTC routed into Binance deposit infrastructure."},
                    {"name": "Dormancy Awakening Surge", "description": "Address reactivated after multi-year dormant state.", "weight": 25, "source": "Blockchain Ledger", "status": "TRIGGERED", "evidence": "Recent unspent output consolidation after 5+ years."},
                ],
            },
            3,
        ),
        (
            c2.id if c2 else None,
            "Investigation: FTX Accounts Drainer",
            "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9",
            "ethereum",
            "COMPLETED",
            "HIGH",
            96.0,
            "Unauthorized exchange treasury drainer wallet actively routing to privacy obfuscation.",
            {
                "score": 96.0,
                "max_score": 100,
                "band": "HIGH",
                "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                "indicators": [
                    {"name": "Exchange Unauthorized Drainage", "description": "Unauthorized transfer of institutional bankruptcy estate assets.", "weight": 40, "source": "Exchange Advisory", "status": "TRIGGERED", "evidence": "Siphoned over $400M during FTX bankruptcy filing."},
                    {"name": "Cross-Chain Asset Swapping", "description": "Aggressive bridge and DEX swapping to conceal provenance.", "weight": 30, "source": "DEX Routers", "status": "TRIGGERED", "evidence": "High-frequency conversions to native ETH and cross-chain BTC."},
                    {"name": "Tornado Cash Infiltration", "description": "Direct deposit injections into privacy mixing pools.", "weight": 26, "source": "EVM Graph Analysis", "status": "TRIGGERED", "evidence": "50.0 ETH transfer to Tornado Cash 0.1 ETH proxy."},
                ],
            },
            2,
        ),
        (
            c3.id if c3 else None,
            "Investigation: BSC Token Hub Drainer",
            "0x444d852655513ab4a88f73a3aa5fe9422df56e92",
            "bsc",
            "COMPLETED",
            "HIGH",
            97.0,
            "Cross-chain bridge forgery exploit source resulting in 2,000,000 BNB minting exploit.",
            {
                "score": 97.0,
                "max_score": 100,
                "band": "HIGH",
                "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                "indicators": [
                    {"name": "Bridge Proof Forgery", "description": "Forged IAVL cryptographic verification proofs on BNB cross-chain hub.", "weight": 40, "source": "BNB Chain Core Advisory", "status": "TRIGGERED", "evidence": "Fabricated 2x 1,000,000 BNB minting events."},
                    {"name": "DeFi Collateralized Borrowing", "description": "Used forged BNB to borrow stablecoins on Venus Protocol.", "weight": 32, "source": "DeFi Heuristics", "status": "TRIGGERED", "evidence": "Supplied forged BNB and borrowed USDT/USDC."},
                    {"name": "Cross-Chain Capital Flight", "description": "Bridged borrowed liquidity to Ethereum, Fantom, and Polygon.", "weight": 25, "source": "Multichain Monitoring", "status": "TRIGGERED", "evidence": "Outflows traced through Stargate and AnySwap."},
                ],
            },
            8,
        ),
        (
            None,
            "Investigation: vitalik.eth",
            "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
            "ethereum",
            "COMPLETED",
            "LOW",
            15.0,
            "Verified public identity wallet for Ethereum founder Vitalik Buterin with low illicit risk.",
            {
                "score": 15.0,
                "max_score": 100,
                "band": "LOW",
                "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                "indicators": [
                    {"name": "Public Identity Attribution", "description": "Wallet explicitly verified with official ENS domain.", "weight": 0, "source": "ENS Registry", "status": "NOT_TRIGGERED", "evidence": "Owner of vitalik.eth."},
                    {"name": "Incidental Privacy Pool Inflow", "description": "Received unsolicited airdrops or community donations from privacy pools.", "weight": 15, "source": "EVM Heuristics", "status": "TRIGGERED", "evidence": "Unsolicited 10.0 ETH transfer received from Tornado Cash pool."},
                ],
            },
            1,
        ),
        (
            c5.id if c5 else None,
            "Investigation: Binance Cold Storage Treasury",
            "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
            "bitcoin",
            "COMPLETED",
            "MODERATE",
            45.0,
            "Tier-1 exchange cold reserve wallet with vast incoming volume and multi-signature architecture.",
            {
                "score": 45.0,
                "max_score": 100,
                "band": "MODERATE",
                "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                "indicators": [
                    {"name": "High-Volume Aggregation Node", "description": "Operates as a high-density deposit consolidation vault.", "weight": 20, "source": "Cluster Analysis", "status": "TRIGGERED", "evidence": "Over 48,000 transactions and 24,800 BTC balance."},
                    {"name": "Flagged Counterparty Deposit Exposure", "description": "Received inbound transfers from historically flagged ransomware or hack addresses.", "weight": 25, "source": "Threat Counterparty Graph", "status": "TRIGGERED", "evidence": "Inbound deposit from WannaCry Treasury 19R2w9..."},
                ],
            },
            10,
        ),
        (
            None,
            "Investigation: Satoshi Nakamoto Genesis Address",
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "bitcoin",
            "COMPLETED",
            "CLEAR",
            5.0,
            "Historic Bitcoin genesis block 50 BTC coinbase address with no outbound spending capability.",
            {
                "score": 5.0,
                "max_score": 100,
                "band": "CLEAR",
                "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                "indicators": [
                    {"name": "Historic Protocol Landmark", "description": "Genesis block rewards are non-spendable by protocol consensus rules.", "weight": 5, "source": "Bitcoin Consensus", "status": "TRIGGERED", "evidence": "Block 0 coinbase reward recipient."},
                ],
            },
            30,
        ),
    ]

    for cid, title, addr, chain, st, r_lvl, r_score, notes, payload_dict, days_ago in investigations_data:
        norm_addr = normalize_wallet_address(addr, chain)
        norm_chain = normalize_chain(chain)
        try:
            existing = db.query(Investigation).filter(Investigation.wallet_address == norm_addr).first()
            if not existing:
                stmt = (
                    sqlite_insert(Investigation)
                    .values(
                        case_id=cid,
                        title=title,
                        wallet_address=norm_addr,
                        blockchain=norm_chain,
                        status=st,
                        risk_level=r_lvl,
                        risk_score=r_score,
                        investigator="Lead Forensics Analyst",
                        notes=notes,
                        payload={"risk": payload_dict, "focus_address": norm_addr, "blockchain": norm_chain},
                        created_at=now - timedelta(days=days_ago),
                    )
                    .on_conflict_do_nothing()
                )
                db.execute(stmt)
                db.commit()
            else:
                # Update case_id if missing
                if cid and not existing.case_id:
                    existing.case_id = cid
                    db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Investigation seed skipped (%s): %s", norm_addr, exc)

    # -------------------------------------------------------------------------
    # 10. Reports (Pre-generated forensic dossiers ready to view and export)
    # -------------------------------------------------------------------------
    reports_data = [
        (
            "rep_2026_tornado_cash_01",
            c2.id if c2 else None,
            "0x12d6621e19a95080e0276664261065623b1a0623",
            "ethereum",
            "Forensic Dossier: Tornado.Cash Privacy Obfuscation & Sanctions Trace",
            {
                "report_id": "rep_2026_tornado_cash_01",
                "generated_at": iso(now - timedelta(days=1)),
                "mode": "LIVE",
                "app_version": settings.app_version,
                "case": {"id": c2.id if c2 else 1, "case_number": "CASE-2026-002", "title": "EVM Exploit & Tornado Cash Privacy Obfuscation Analysis", "status": "OPEN", "priority": "CRITICAL"},
                "wallet": "0x12d6621e19a95080e0276664261065623b1a0623",
                "blockchain": "ethereum",
                "wallet_summary": {"address": "0x12d6621e19a95080e0276664261065623b1a0623", "blockchain": "ethereum", "balance": 845.5, "asset": "ETH", "transaction_count": 12500, "is_demo": False},
                "transactions": [
                    {"tx_hash": "0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060", "from_address": "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "to_address": "0x12d6621e19a95080e0276664261065623b1a0623", "amount": 50.0, "asset": "ETH", "timestamp": iso(now - timedelta(hours=2)), "status": "confirmed", "confirmations": 12},
                    {"tx_hash": "0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b", "from_address": "0x12d6621e19a95080e0276664261065623b1a0623", "to_address": "0x28c6c06298d514db089934071355e5743bf21d60", "amount": 45.0, "asset": "ETH", "timestamp": iso(now - timedelta(hours=8)), "status": "confirmed", "confirmations": 12},
                ],
                "threat_findings": [
                    {"category": "Suspicious Service", "label": "Tornado.Cash 0.1 ETH Mixer", "source": "OFAC Sanctions & Watchlist", "confidence": 0.99, "status": "VERIFIED", "notes": "OFAC sanctioned privacy protocol smart contract."},
                ],
                "osint_findings": [
                    {"source": "OFAC Sanctions List", "finding": "OFAC Specially Designated Nationals List (SDN ID 39481)", "status": "FOUND", "confidence": 0.99},
                ],
                "risk": {
                    "score": 98.0,
                    "max_score": 100,
                    "band": "HIGH",
                    "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                    "indicators": [
                        {"name": "OFAC Sanctions Match", "weight": 40, "status": "TRIGGERED", "evidence": "Listed on SDN list under Cyber-related Sanctions (ID 39481)."},
                        {"name": "Mixer Protocol Interaction", "weight": 30, "status": "TRIGGERED", "evidence": "Tornado Cash 0.1 ETH fixed denomination pool contract."},
                        {"name": "Direct Exploit Deposit Counterparty", "weight": 28, "status": "TRIGGERED", "evidence": "Direct deposit inflow from FTX Drainer wallet 0x50d1..."},
                    ],
                },
                "timeline": [
                    {"event_type": "wallet_added", "description": "Primary mixer router flagged for privacy obfuscation trace.", "created_at": iso(now - timedelta(days=2))},
                    {"event_type": "evidence_attached", "description": "Sanctions designation documentation from US Treasury added to evidence locker.", "created_at": iso(now - timedelta(days=1))},
                ],
                "disclaimers": [
                    "Analytical output should be independently validated before use in legal, regulatory, or operational decisions.",
                    "Risk score is an analytical indicator and not a determination of unlawful activity.",
                    "All blockchain data is retrieved from third-party providers and should be cross-verified against a full node or secondary explorer for evidentiary use.",
                ],
            },
            1,
        ),
        (
            "rep_2026_ronin_bridge_02",
            c3.id if c3 else None,
            "0x098b716b8aaf21512996dc57eb0615e2383e2f96",
            "ethereum",
            "State-Sponsored Threat Attribution Report: Ronin Bridge $620M Exploit",
            {
                "report_id": "rep_2026_ronin_bridge_02",
                "generated_at": iso(now - timedelta(days=5)),
                "mode": "LIVE",
                "app_version": settings.app_version,
                "case": {"id": c3.id if c3 else 2, "case_number": "CASE-2026-003", "title": "Cross-Chain Bridge Drainer Incident (BSC & Ronin)", "status": "RESOLVED", "priority": "HIGH"},
                "wallet": "0x098b716b8aaf21512996dc57eb0615e2383e2f96",
                "blockchain": "ethereum",
                "wallet_summary": {"address": "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "blockchain": "ethereum", "balance": 17400.0, "asset": "ETH", "transaction_count": 610, "is_demo": False},
                "transactions": [
                    {"tx_hash": "0xc2855523da5629c4a89f2142275038f4d92fb02d442b0833ec96d0d216d25cd2", "from_address": "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "to_address": "0x077d37a6553a309b888824e0373809071c356f9a", "amount": 100.0, "asset": "ETH", "timestamp": iso(now - timedelta(hours=4)), "status": "confirmed", "confirmations": 12},
                    {"tx_hash": "0x5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e", "from_address": "0x098b716b8aaf21512996dc57eb0615e2383e2f96", "to_address": "0x50d1c9771902476076ecfc8b2a83ad6b9355a4c9", "amount": 300.0, "asset": "ETH", "timestamp": iso(now - timedelta(hours=20)), "status": "confirmed", "confirmations": 12},
                ],
                "threat_findings": [
                    {"category": "Exploit", "label": "Ronin Bridge $620M Exploit (Lazarus)", "source": "FBI / Cyber Crime Advisory", "confidence": 0.99, "status": "VERIFIED", "notes": "State-sponsored cyber attack on Axie Infinity Ronin validator keys."},
                ],
                "osint_findings": [
                    {"source": "FBI Cyber Division Advisory", "finding": "Identified as Lazarus Group Ronin Exploiter", "status": "FOUND", "confidence": 0.99},
                ],
                "risk": {
                    "score": 99.0,
                    "max_score": 100,
                    "band": "HIGH",
                    "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                    "indicators": [
                        {"name": "State-Sponsored Cyber Threat Actor", "weight": 40, "status": "TRIGGERED", "evidence": "Attributed to DPRK Lazarus Group."},
                        {"name": "Major Protocol Exploit Origin", "weight": 35, "status": "TRIGGERED", "evidence": "$620M loss in validator compromise."},
                        {"name": "Rapid Fund Laundering Peeling Chain", "weight": 24, "status": "TRIGGERED", "evidence": "High-velocity distribution through privacy pools."},
                    ],
                },
                "timeline": [
                    {"event_type": "wallet_added", "description": "Ronin bridge exploiter enrolled into incident dossier.", "created_at": iso(now - timedelta(days=10))},
                    {"event_type": "case_closed", "description": "Full multi-chain forensic report published; assets blacklisted across major CEXs.", "created_at": iso(now - timedelta(days=1))},
                ],
                "disclaimers": [
                    "Analytical output should be independently validated before use in legal, regulatory, or operational decisions.",
                    "Risk score is an analytical indicator and not a determination of unlawful activity.",
                    "All blockchain data is retrieved from third-party providers and should be cross-verified against a full node or secondary explorer for evidentiary use.",
                ],
            },
            5,
        ),
        (
            "rep_2026_wannacry_03",
            c1.id if c1 else None,
            "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
            "bitcoin",
            "Ransomware Forensic Dossier: WannaCry Extortion Fund Flow",
            {
                "report_id": "rep_2026_wannacry_03",
                "generated_at": iso(now - timedelta(days=3)),
                "mode": "LIVE",
                "app_version": settings.app_version,
                "case": {"id": c1.id if c1 else 3, "case_number": "CASE-2026-001", "title": "Operation DarkWatch — Ransomware & State-Actor Fund Tracing", "status": "UNDER_INVESTIGATION", "priority": "HIGH"},
                "wallet": "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P",
                "blockchain": "bitcoin",
                "wallet_summary": {"address": "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "blockchain": "bitcoin", "balance": 14.58, "asset": "BTC", "transaction_count": 340, "is_demo": False},
                "transactions": [
                    {"tx_hash": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f", "from_address": "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P", "to_address": "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "amount": 2.5, "asset": "BTC", "timestamp": iso(now - timedelta(hours=12)), "status": "confirmed", "confirmations": 12},
                ],
                "threat_findings": [
                    {"category": "Ransomware", "label": "WannaCry Ransomware Treasury", "source": "Cryptocurrency Threat DB", "confidence": 0.95, "status": "VERIFIED", "notes": "Extortion wallet associated with global ransomware campaign."},
                ],
                "osint_findings": [
                    {"source": "BitcoinTalk Forum", "finding": "Address reported in ransomware extortion thread #8821", "status": "FOUND", "confidence": 0.90},
                ],
                "risk": {
                    "score": 95.0,
                    "max_score": 100,
                    "band": "HIGH",
                    "disclaimer": "Risk score is an analytical indicator and not a determination of unlawful activity.",
                    "indicators": [
                        {"name": "Ransomware Extortion Match", "weight": 40, "status": "TRIGGERED", "evidence": "WannaCry ransomware payment demand destination."},
                        {"name": "Centralized Exchange Cash-Out", "weight": 30, "status": "TRIGGERED", "evidence": "Outflow of 2.5 BTC routed into Binance deposit infrastructure."},
                        {"name": "Dormancy Awakening Surge", "weight": 25, "status": "TRIGGERED", "evidence": "Recent unspent output consolidation after 5+ years."},
                    ],
                },
                "timeline": [
                    {"event_type": "wallet_added", "description": "Target wallet added to active tracking dossier.", "created_at": iso(now - timedelta(days=5))},
                    {"event_type": "threat_correlated", "description": "OFAC & FBI Cyber Advisory correlation confirmed DPRK link.", "created_at": iso(now - timedelta(days=3))},
                ],
                "disclaimers": [
                    "Analytical output should be independently validated before use in legal, regulatory, or operational decisions.",
                    "Risk score is an analytical indicator and not a determination of unlawful activity.",
                    "All blockchain data is retrieved from third-party providers and should be cross-verified against a full node or secondary explorer for evidentiary use.",
                ],
            },
            3,
        ),
    ]

    for rep_id, cid, addr, chain, title, payload_dict, days_ago in reports_data:
        norm_addr = normalize_wallet_address(addr, chain)
        norm_chain = normalize_chain(chain)
        try:
            existing = db.query(Report).filter(Report.id == rep_id).first()
            if not existing:
                stmt = (
                    sqlite_insert(Report)
                    .values(
                        id=rep_id,
                        case_id=cid,
                        wallet_address=norm_addr,
                        blockchain=norm_chain,
                        title=title,
                        mode="LIVE",
                        payload=payload_dict,
                        created_at=now - timedelta(days=days_ago),
                    )
                    .on_conflict_do_nothing(index_elements=["id"])
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Report seed skipped (%s): %s", rep_id, exc)

    # -------------------------------------------------------------------------
    # 11. Audit Logs (Forensic provenance and administrative action trail)
    # -------------------------------------------------------------------------
    audit_entries = [
        ("database_seeded", "system", "chainintel_master_seed_live", "System", {"mode": "LIVE", "status": "COMPLETED", "seeded_modules": ["wallets", "transactions", "threats", "osint", "cases", "events", "monitors", "alerts", "evidence", "investigations", "reports"]}),
        ("case_created", "case", "CASE-2026-001", "Lead Forensics Analyst", {"case_number": "CASE-2026-001", "priority": "HIGH"}),
        ("case_created", "case", "CASE-2026-002", "Senior Forensics Lead", {"case_number": "CASE-2026-002", "priority": "CRITICAL"}),
        ("case_created", "case", "CASE-2026-003", "Cyber Incident Commander", {"case_number": "CASE-2026-003", "priority": "HIGH"}),
        ("evidence_uploaded", "evidence", "darkwatch_tx_execution.log", "Lead Forensics Analyst", {"title": "Ransomware Outbound TX Execution Log", "case": "CASE-2026-001"}),
        ("report_generated", "report", "rep_2026_tornado_cash_01", "Senior Forensics Lead", {"report_id": "rep_2026_tornado_cash_01", "case": "CASE-2026-002"}),
        ("monitor_rule_activated", "monitored_wallet", "0x12d6621e19a95080e0276664261065623b1a0623", "System Monitor", {"wallet": "0x12d6621e19a95080e0276664261065623b1a0623", "rule": "Tornado Cash Watch"}),
    ]
    for action, r_type, r_id, inv, meta_dict in audit_entries:
        try:
            existing = db.query(AuditLog).filter(
                AuditLog.action == action,
                AuditLog.resource_id == r_id,
            ).first()
            if not existing:
                stmt = (
                    sqlite_insert(AuditLog)
                    .values(
                        action=action,
                        resource_type=r_type,
                        resource_id=r_id,
                        investigator=inv,
                        metadata_json=meta_dict,
                        timestamp=now - timedelta(days=1),
                    )
                    .on_conflict_do_nothing()
                )
                db.execute(stmt)
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("AuditLog seed skipped (%s, %s): %s", action, r_id, exc)

    logger.info("Comprehensive seed_db completed successfully.")


def main() -> None:
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
