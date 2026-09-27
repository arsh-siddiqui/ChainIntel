"use client";

import { useState } from "react";
import { ArrowDownLeft, ArrowUpRight, ExternalLink } from "lucide-react";
import type { NormalizedTx } from "@/types";
import { DataTable, type Column } from "@/components/common/data-table";
import { Badge } from "@/components/common/ui";
import { Modal } from "@/components/common/modal";
import { CopyButton } from "@/components/common/copy-button";
import { formatCrypto, formatDateTime, truncateMiddle } from "@/lib/formatters";

function explorerTxUrl(blockchain: string, hash: string): string | null {
  switch (blockchain) {
    case "bitcoin":
      return `https://mempool.space/tx/${hash}`;
    case "ethereum":
      return `https://etherscan.io/tx/${hash}`;
    case "bsc":
      return `https://bscscan.com/tx/${hash}`;
    default:
      return null;
  }
}

export function TxTable({ transactions, focusAddress }: { transactions: NormalizedTx[]; focusAddress: string }) {
  const [selected, setSelected] = useState<NormalizedTx | null>(null);

  const columns: Column<NormalizedTx>[] = [
    {
      key: "hash",
      header: "TX Hash",
      render: (tx) => (
        <button type="button" onClick={() => setSelected(tx)} className="inline-flex items-center gap-1 font-mono text-xs font-medium text-primary hover:underline">
          {truncateMiddle(tx.tx_hash, 14, 6)}
        </button>
      ),
      sortValue: (tx) => tx.tx_hash,
      sortable: true,
    },
    {
      key: "direction",
      header: "Direction",
      render: (tx) =>
        tx.direction === "outgoing" ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-orange-600">
            <ArrowUpRight size={12} /> Out
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-teal-600">
            <ArrowDownLeft size={12} /> In
          </span>
        ),
      sortValue: (tx) => tx.direction ?? "",
      sortable: true,
    },
    {
      key: "from",
      header: "From",
      render: (tx) => <span className="font-mono text-[11px] text-slate-600">{truncateMiddle(tx.from_address ?? "—", 10, 6)}</span>,
      sortValue: (tx) => tx.from_address ?? "",
      sortable: true,
    },
    {
      key: "to",
      header: "To",
      render: (tx) => <span className="font-mono text-[11px] text-slate-600">{truncateMiddle(tx.to_address ?? "—", 10, 6)}</span>,
      sortValue: (tx) => tx.to_address ?? "",
      sortable: true,
    },
    {
      key: "amount",
      header: "Amount",
      align: "right",
      render: (tx) => <span className="font-mono text-xs font-medium text-ink">{formatCrypto(tx.amount, tx.asset)}</span>,
      sortValue: (tx) => tx.amount,
      sortable: true,
    },
    { key: "time", header: "Timestamp", render: (tx) => <span className="text-xs text-slate-500">{formatDateTime(tx.timestamp)}</span>, sortValue: (tx) => tx.timestamp ?? "", sortable: true },
    {
      key: "confirmations",
      header: "Confirmations",
      align: "right",
      render: (tx) => <span className="text-xs text-slate-500">{tx.confirmations.toLocaleString()}</span>,
      sortValue: (tx) => tx.confirmations,
      sortable: true,
    },
    { key: "status", header: "Status", render: (tx) => <Badge className={tx.status === "confirmed" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-amber-50 text-amber-700 border-amber-200"}>{tx.status}</Badge> },
  ];

  return (
    <>
      <DataTable columns={columns} rows={transactions} rowKey={(tx) => tx.tx_hash} pageSize={12} emptyMessage="No transactions found for this wallet." />
      <Modal open={selected !== null} onClose={() => setSelected(null)} title="Transaction detail" wide>
        {selected ? (
          <div className="space-y-3 text-sm">
            <DetailRow label="TX Hash" value={selected.tx_hash} copy />
            <DetailRow label="Block number" value={selected.block_number !== null ? String(selected.block_number) : "—"} />
            <DetailRow label="Timestamp" value={formatDateTime(selected.timestamp)} />
            <DetailRow label="Sender" value={selected.from_address ?? "—"} copy />
            <DetailRow label="Receiver" value={selected.to_address ?? "—"} copy />
            <DetailRow label="Amount" value={formatCrypto(selected.amount, selected.asset)} />
            <DetailRow label="Fee" value={selected.fee !== null ? formatCrypto(selected.fee, selected.asset) : "—"} />
            <DetailRow label="Confirmations" value={selected.confirmations.toLocaleString()} />
            <DetailRow label="Status" value={selected.status} />
            <DetailRow label="Data source" value="LIVE provider" />
            {explorerTxUrl(selected.blockchain, selected.tx_hash) ? (
              <a href={explorerTxUrl(selected.blockchain, selected.tx_hash)!} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50">
                <ExternalLink size={12} /> Open in block explorer
              </a>
            ) : null}
          </div>
        ) : null}
      </Modal>
    </>
  );
}

function DetailRow({ label, value, copy }: { label: string; value: string; copy?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-2">
      <span className="shrink-0 text-xs font-medium text-slate-500">{label}</span>
      <span className="flex min-w-0 items-center gap-1 font-mono text-xs text-ink">
        <span className="truncate" title={value}>
          {value}
        </span>
        {copy ? <CopyButton value={value} /> : null}
      </span>
    </div>
  );
}
