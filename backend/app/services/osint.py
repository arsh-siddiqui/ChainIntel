"""OSINT correlation service.

Two kinds of providers exist:

1. Link-only providers - real public sources that cannot be queried
   automatically (no stable free API). They NEVER return fabricated findings;
   they surface an external search URL and the status "UNAVAILABLE" with the
   note "Source unavailable for automated lookup".

2. Restricted/analyst records - internal intelligence stored in the database,
   added by investigators or imported from restricted sources.

Any future real API provider implements OSINTProvider and registers itself in
PROVIDERS - no other code changes are required.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import OSINTFinding
from app.utils.datetime import utcnow


@dataclass
class OSINTResult:
    source_name: str
    query: str
    status: str  # FOUND | NOT_FOUND | UNAVAILABLE | ERROR | REQUIRES_CONFIGURATION
    source_category: str = "public"
    finding: str | None = None
    confidence: float = 0.0
    reference_url: str | None = None
    external_search_url: str | None = None
    notes: str | None = None
    record_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_category": self.source_category,
            "query": self.query,
            "status": self.status,
            "finding": self.finding,
            "confidence": self.confidence,
            "reference_url": self.reference_url,
            "external_search_url": self.external_search_url,
            "notes": self.notes,
            "record_type": self.record_type,
        }


class OSINTProvider(ABC):
    """Interface every OSINT source adapter implements."""

    name: str = "abstract"
    source_category: str = "public"

    @abstractmethod
    def search_wallet(self, address: str) -> OSINTResult: ...

    def search_transaction(self, tx_hash: str) -> OSINTResult:
        return OSINTResult(
            source_name=self.name,
            query=tx_hash,
            status="UNAVAILABLE",
            source_category=self.source_category,
            notes="Transaction lookup is not supported by this source adapter.",
        )

    def get_reputation(self, address: str) -> OSINTResult:
        return self.search_wallet(address)

    def get_references(self, address: str) -> list[str]:
        result = self.search_wallet(address)
        return [result.reference_url] if result.reference_url else []


class LinkOnlyProvider(OSINTProvider):
    """A real public source queried by opening a pre-built external search URL.

    ChainIntel does NOT scrape these services and does not fabricate results.
    """

    base_url: str = ""
    description: str = ""

    def search_wallet(self, address: str) -> OSINTResult:
        note = self.description or "Source unavailable for automated lookup. Use the direct search link to query it manually."
        return OSINTResult(
            source_name=self.name,
            query=address,
            status="UNAVAILABLE",
            source_category=self.source_category,
            notes=note,
            external_search_url=self.base_url.format(q=quote_plus(address)),
        )


class ArkhamProvider(LinkOnlyProvider):
    name = "Arkham Intelligence"
    description = "Entity deanonymization, labeled owners & counterparty intelligence."
    base_url = "https://platform.arkhamintelligence.com/explorer/address/{q}"


class ChainabuseProvider(LinkOnlyProvider):
    name = "Chainabuse"
    description = "Community scam reports, victim statements & malicious activity flags."
    base_url = "https://www.chainabuse.com/address/{q}"


class EtherscanLabelsProvider(LinkOnlyProvider):
    name = "Etherscan Public Reports & Labels"
    description = "Explorer public labels, incident reports & community comments."
    base_url = "https://etherscan.io/address/{q}#comments"


class DeBankProvider(LinkOnlyProvider):
    name = "DeBank Web3 Profile"
    description = "DeFi portfolio, protocol interactions & web3 entity profile."
    base_url = "https://debank.com/profile/{q}"


class BitcoinWhosWhoProvider(LinkOnlyProvider):
    name = "Bitcoin Who's Who"
    description = "Bitcoin scam reports, blacklists & forum mentions."
    base_url = "https://www.bitcoinwhoswho.com/address/{q}"


class BlockstreamProvider(LinkOnlyProvider):
    name = "Blockstream Explorer"
    description = "Official open Bitcoin ledger explorer, UTXO validation & unconfirmed transaction analysis."
    base_url = "https://blockstream.info/address/{q}"


class BitRefProvider(LinkOnlyProvider):
    name = "BitRef"
    description = "Quick lightweight Bitcoin balance & ledger lookup."
    base_url = "https://bitref.com/{q}"


class BlockchairProvider(LinkOnlyProvider):
    name = "Blockchair Explorer"
    description = "Multichain explorer notes & privacy score analysis."

    def search_wallet(self, address: str) -> OSINTResult:
        chain = "ethereum" if address.strip().startswith("0x") else "bitcoin"
        return OSINTResult(
            source_name=self.name,
            query=address,
            status="UNAVAILABLE",
            source_category=self.source_category,
            notes=self.description,
            external_search_url=f"https://blockchair.com/{chain}/address/{quote_plus(address)}",
        )


class BlockchainComProvider(LinkOnlyProvider):
    name = "Blockchain.com Explorer"
    description = "Public Bitcoin block explorer ledger & transaction confirmation records."
    base_url = "https://www.blockchain.com/explorer/addresses/btc/{q}"


class WalletExplorerProvider(LinkOnlyProvider):
    name = "WalletExplorer (Clustering)"
    description = "Smart Bitcoin wallet clustering & co-spending entity attribution."
    base_url = "https://www.walletexplorer.com/address/{q}"




class TwitterForensicProvider(LinkOnlyProvider):
    name = "Community Forensics (X / Twitter)"
    description = "On-chain investigator mentions, breach reports & community alerts (ZachXBT, PeckShield)."
    base_url = "https://twitter.com/search?q={q}&f=live"


PROVIDERS: list[OSINTProvider] = [
    ArkhamProvider(),
    ChainabuseProvider(),
    EtherscanLabelsProvider(),
    DeBankProvider(),
    BitcoinWhosWhoProvider(),
    BlockchainComProvider(),
    BlockstreamProvider(),
    WalletExplorerProvider(),
    BitRefProvider(),
    BlockchairProvider(),
    TwitterForensicProvider(),
]


def correlate_wallet(address: str) -> dict[str, Any]:
    """Run chain-relevant wallet OSINT providers for an address."""
    addr = address.strip()
    is_evm = addr.startswith("0x")
    is_btc = addr.startswith(("1", "3", "bc1"))

    if is_evm:
        active_providers = [
            ArkhamProvider(),
            ChainabuseProvider(),
            EtherscanLabelsProvider(),
            DeBankProvider(),
            BlockchairProvider(),
            TwitterForensicProvider(),
        ]
    elif is_btc:
        active_providers = [
            BlockstreamProvider(),
            BlockchainComProvider(),
            BitRefProvider(),
            BitcoinWhosWhoProvider(),
            ChainabuseProvider(),
            WalletExplorerProvider(),
            BlockchairProvider(),
            TwitterForensicProvider(),
        ]
    else:
        active_providers = PROVIDERS

    results = [provider.search_wallet(address).to_dict() for provider in active_providers]
    found = [r for r in results if r["status"] == "FOUND"]
    return {
        "query": address,
        "results": results,
        "found_count": len(found),
        "provider_count": len(results),
        "note": (
            "Automated OSINT lookups require configured API providers; public sources are surfaced as external "
            "search links and are never scraped or fabricated. Restricted/analyst records from this database "
            "appear in the OSINT tab when present."
        ),
    }


def correlate_transaction(tx_hash: str) -> dict[str, Any]:
    results = [provider.search_transaction(tx_hash).to_dict() for provider in PROVIDERS]
    return {"query": tx_hash, "results": results, "note": "External transaction lookups are link-only in this deployment."}


def external_sources_status() -> list[dict[str, Any]]:
    return [
        {
            "name": p.name,
            "source_category": p.source_category,
            "automated": not isinstance(p, LinkOnlyProvider),
            "status": "LINK_ONLY",
        }
        for p in PROVIDERS
    ]


# ------------------------------------------------- restricted-source records
def restricted_findings(db: Session, address: str) -> list[OSINTFinding]:
    return (
        db.query(OSINTFinding)
        .filter(OSINTFinding.wallet_address == address, OSINTFinding.source_category.in_(("restricted", "analyst")))
        .order_by(OSINTFinding.observed_at.desc())
        .all()
    )


def add_restricted_record(db: Session, payload: dict[str, Any]) -> OSINTFinding:
    finding = OSINTFinding(
        wallet_address=payload["wallet_address"],
        source=payload["source"],
        source_category="restricted",
        record_type=payload.get("record_type", "ANALYST_NOTE"),
        finding=payload["finding"],
        status="FOUND",
        confidence=payload.get("confidence", 0.5),
        reference_url=payload.get("reference_url"),
        notes=payload.get("notes"),
        observed_at=utcnow(),
    )
    db.add(finding)
    db.commit()
    return finding
