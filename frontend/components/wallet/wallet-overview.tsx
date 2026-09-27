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

  const isBtc = wallet.blockchain.toLowerCase() === "bitcoin";

  return (
    <div className="console-panel rounded-lg overflow-hidden">
      {/* 1. Active Investigation Target Header */}
      <div className="border-b border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/90">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400">
                ACTIVE TARGET UNDER INVESTIGATION
              </span>
              <span className="rounded bg-slate-100 px-1.5 py-0.2 font-mono text-[9px] font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300 uppercase">
                {wallet.blockchain}
              </span>
              {wallet.label && (
                <span className="rounded border border-purple-200 bg-purple-50 px-1.5 py-0.2 font-mono text-[9px] font-bold text-purple-700 dark:border-purple-900 dark:bg-purple-950/60 dark:text-purple-300">
                  {wallet.label}
                </span>
              )}
            </div>

            <div className="mt-1 flex flex-wrap items-center gap-2">
              <span className="font-mono text-base sm:text-lg font-black text-ink tracking-tight select-all">
                {wallet.address}
              </span>
              <button
                onClick={copyAddress}
                className="flex items-center gap-1 rounded border border-slate-200 bg-slate-50 px-2 py-1 font-mono text-[11px] text-slate-600 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300"
                title="Copy Address"
              >
                {copied ? <Check size={12} className="text-emerald-500" /> : <Copy size={12} />}
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
                className="inline-flex items-center gap-1.5 rounded border border-slate-200 bg-white px-3 py-1.5 font-mono text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200"
              >
                <ExternalLink size={12} />
                <span>MEMPOOL EXPLORER</span>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* 2. Flat Forensic Metrics Bar with Thin Separators (Bloomberg Style) */}
      <div className="grid grid-cols-2 divide-y divide-slate-100 sm:grid-cols-3 sm:divide-y-0 sm:divide-x lg:grid-cols-6 border-b border-slate-200 bg-slate-50/70 font-mono dark:border-slate-800 dark:bg-slate-950/60 dark:divide-slate-800">
        <div className="p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">BALANCE</p>
          <p className="mt-1 text-sm font-bold text-ink truncate">
            {formatCrypto(wallet.balance, wallet.asset)}
          </p>
        </div>

        <div className="p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">TRANSACTIONS</p>
          <p className="mt-1 text-sm font-bold text-ink">
            {formatNumber(wallet.transaction_count)}
          </p>
        </div>

        <div className="p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">COUNTERPARTIES</p>
          <p className="mt-1 text-sm font-bold text-ink">
            {formatNumber(wallet.unique_counterparties)}
          </p>
        </div>

        <div className="p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">TOTAL RECEIVED</p>
          <p className="mt-1 text-sm font-bold text-emerald-600 dark:text-emerald-400 truncate">
            {formatCrypto(wallet.incoming_volume, wallet.asset)}
          </p>
        </div>

        <div className="p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">FIRST SEEN</p>
          <p className="mt-1 text-xs font-semibold text-slate-600 dark:text-slate-300">
            {wallet.first_activity ? wallet.first_activity.split("T")[0] : "Genesis"}
          </p>
        </div>

        <div className="p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">LAST ACTIVITY</p>
          <p className="mt-1 text-xs font-semibold text-slate-600 dark:text-slate-300">
            {wallet.last_activity ? wallet.last_activity.split("T")[0] : "Recent"}
          </p>
        </div>
      </div>
    </div>
  );
}
