"use client";

import { useState } from "react";
import {
  ArrowDownLeft,
  ArrowUpRight,
  Check,
  Clock,
  Copy,
  ExternalLink,
  Fingerprint,
  Hash,
  Layers,
  Network,
  Shield,
  ShieldAlert,
  Wallet,
} from "lucide-react";
import type { WalletSummary } from "@/types";
import { formatCrypto, formatDateTime, formatNumber, truncateMiddle } from "@/lib/formatters";

export function WalletOverview({ wallet }: { wallet: WalletSummary }) {
  const [copied, setCopied] = useState(false);

  const copyAddress = () => {
    navigator.clipboard.writeText(wallet.address);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const getExplorerLabel = (chain: string) => {
    switch (chain?.toLowerCase()) {
      case "bitcoin":
        return "MEMPOOL EXPLORER";
      case "ethereum":
        return "ETHERSCAN EXPLORER";
      case "bsc":
        return "BSCSCAN EXPLORER";
      case "polygon":
        return "POLYGONSCAN EXPLORER";
      case "solana":
        return "SOLSCAN EXPLORER";
      default:
        return "BLOCK EXPLORER";
    }
  };

  return (
    <div className="console-panel rounded-xl overflow-hidden shadow-lg border border-slate-200 dark:border-slate-800">
      {/* 1. Active Investigation Target Header */}
      <div className="border-b border-slate-200/90 bg-white p-4 sm:p-5 dark:border-slate-800/80 dark:bg-slate-900/90 backdrop-blur-xl">
        <div className="flex flex-col gap-3.5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-[10px] font-black uppercase tracking-widest text-sky-600 dark:text-cyan-400 bg-sky-50 dark:bg-cyan-950/60 px-2 py-0.5 rounded border border-sky-200 dark:border-cyan-800/50">
                ACTIVE TARGET UNDER INVESTIGATION
              </span>
              <span className="rounded bg-slate-900 px-2 py-0.5 font-mono text-[10px] font-black text-white dark:bg-slate-800 dark:text-cyan-300 uppercase tracking-wide">
                {wallet.blockchain}
              </span>
              {wallet.label && (
                <span className="rounded border border-purple-200 bg-purple-50 px-2 py-0.5 font-mono text-[10px] font-bold text-purple-700 dark:border-purple-900/80 dark:bg-purple-950/80 dark:text-purple-300">
                  {wallet.label}
                </span>
              )}
            </div>

            <div className="mt-2.5 flex flex-wrap items-center gap-2.5">
              <span className="font-mono text-base sm:text-xl font-extrabold text-slate-900 dark:text-white tracking-tight select-all">
                {wallet.address}
              </span>
              <button
                onClick={copyAddress}
                className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50/80 px-2.5 py-1 font-mono text-[11px] font-bold text-slate-700 hover:bg-slate-100 hover:text-slate-900 dark:border-slate-800 dark:bg-slate-800/90 dark:text-slate-300 dark:hover:bg-slate-700 transition-all active:scale-95"
                title="Copy Address"
              >
                {copied ? <Check size={13} className="text-emerald-500 stroke-[3]" /> : <Copy size={13} />}
                <span>{copied ? "COPIED" : "COPY"}</span>
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {wallet.explorer_url && (
              <a
                href={wallet.explorer_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 font-mono text-xs font-bold text-slate-800 shadow-sm hover:border-sky-500 hover:bg-sky-50 hover:text-sky-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:border-cyan-400 dark:hover:bg-cyan-950/50 transition-all"
              >
                <ExternalLink size={13} className="stroke-[2.5]" />
                <span>{getExplorerLabel(wallet.blockchain)}</span>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* 2. Flat Forensic Metrics Bar with Thin Separators (Bloomberg Style) */}
      <div className="grid grid-cols-2 divide-y divide-slate-200/60 sm:grid-cols-3 sm:divide-y-0 sm:divide-x lg:grid-cols-6 border-b border-slate-200 bg-slate-50/80 font-mono dark:border-slate-800 dark:bg-slate-950/80 dark:divide-slate-800">
        <div className="p-3.5">
          <p className="text-[10px] uppercase tracking-widest text-slate-400 font-extrabold">BALANCE</p>
          <p className="mt-1 text-base font-extrabold text-slate-900 dark:text-white truncate">
            {formatCrypto(wallet.balance, wallet.asset)}
          </p>
        </div>

        <div className="p-3.5">
          <p className="text-[10px] uppercase tracking-widest text-slate-400 font-extrabold">TRANSACTIONS</p>
          <p className="mt-1 text-base font-extrabold text-slate-900 dark:text-white">
            {formatNumber(wallet.transaction_count)}
          </p>
        </div>

        <div className="p-3.5">
          <p className="text-[10px] uppercase tracking-widest text-slate-400 font-extrabold">COUNTERPARTIES</p>
          <p className="mt-1 text-base font-extrabold text-slate-900 dark:text-white">
            {formatNumber(wallet.unique_counterparties)}
          </p>
        </div>

        <div className="p-3.5">
          <p className="text-[10px] uppercase tracking-widest text-slate-400 font-extrabold">TOTAL RECEIVED</p>
          <p className="mt-1 text-base font-extrabold text-emerald-600 dark:text-emerald-400 truncate">
            {formatCrypto(wallet.incoming_volume, wallet.asset)}
          </p>
        </div>

        <div className="p-3.5">
          <p className="text-[10px] uppercase tracking-widest text-slate-400 font-extrabold">FIRST SEEN</p>
          <p className="mt-1 text-xs font-bold text-slate-700 dark:text-slate-200">
            {wallet.first_activity ? wallet.first_activity.split("T")[0] : "Genesis"}
          </p>
        </div>

        <div className="p-3.5">
          <p className="text-[10px] uppercase tracking-widest text-slate-400 font-extrabold">LAST ACTIVITY</p>
          <p className="mt-1 text-xs font-bold text-slate-700 dark:text-slate-200">
            {wallet.last_activity ? wallet.last_activity.split("T")[0] : "Recent"}
          </p>
        </div>
      </div>
    </div>
  );
}
