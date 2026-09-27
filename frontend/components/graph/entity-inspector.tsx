"use client";

import { useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Building2,
  Check,
  Copy,
  ExternalLink,
  Layers,
  Network,
  Route,
  ScanLine,
  Search,
  ShieldAlert,
  Target,
  UserX,
  Wallet,
  X,
} from "lucide-react";
import { Button } from "@/components/common/ui";
import { GRAPH_NODE_COLORS } from "@/lib/constants";
import { formatCrypto, truncateMiddle } from "@/lib/formatters";
import type { GraphNode } from "@/types";

interface EntityInspectorProps {
  node: GraphNode | null;
  onClose: () => void;
  onSetFocus: (address: string) => void;
  onTraceFromHere?: (address: string) => void;
  onExpandCluster?: (clusterId: string) => void;
}

export function EntityInspector({
  node,
  onClose,
  onSetFocus,
  onTraceFromHere,
  onExpandCluster,
}: EntityInspectorProps) {
  const [copied, setCopied] = useState(false);
  const [clusterSearch, setClusterSearch] = useState("");

  if (!node) return null;

  const isCluster = node.type === "cluster";
  const palette = GRAPH_NODE_COLORS[node.type] ?? GRAPH_NODE_COLORS.wallet;
  const isHighRisk = node.risk === "high" || node.type === "ransomware" || node.type === "scam";

  const copyText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const filteredMembers = (node.clusterMembers ?? []).filter((m) =>
    clusterSearch
      ? m.id.toLowerCase().includes(clusterSearch.toLowerCase()) ||
        m.label.toLowerCase().includes(clusterSearch.toLowerCase())
      : true
  );

  return (
    <div className="absolute right-3 top-3 bottom-3 z-30 w-84 max-w-[calc(100%-24px)] console-panel rounded-lg shadow-2xl flex flex-col font-mono text-xs overflow-hidden select-text">
      {/* 1. Forensic Header */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-3.5 py-2.5 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-2">
          <span className="font-bold text-[10px] uppercase tracking-wider text-slate-400">
            {isCluster ? "CLUSTER INTELLIGENCE" : "ENTITY INTELLIGENCE"}
          </span>
          <span
            className={`rounded px-1.5 py-0.2 text-[9px] font-bold uppercase ${
              isHighRisk
                ? "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-400"
                : "bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
            }`}
          >
            {node.type}
          </span>
        </div>

        <button
          onClick={onClose}
          className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          title="Close Drawer"
        >
          <X size={14} />
        </button>
      </div>

      {/* 2. Drawer Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 thin-scroll">
        {/* Wallet Address Block */}
        {!isCluster ? (
          <div>
            <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase font-semibold">
              <span>TARGET WALLET</span>
              <span>BTC</span>
            </div>
            <div className="mt-1 flex items-center justify-between gap-1 rounded border border-slate-200 bg-slate-50 p-2 text-ink dark:border-slate-800 dark:bg-slate-950">
              <span className="truncate select-all text-xs font-bold">{node.id}</span>
              <button
                onClick={() => copyText(node.id)}
                className="shrink-0 p-1 text-slate-400 hover:text-ink transition-colors"
                title="Copy Address"
              >
                {copied ? <Check size={12} className="text-emerald-500" /> : <Copy size={12} />}
              </button>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              {node.label || "Unlabeled Blockchain Wallet"} · {node.tx_count} observed transactions
            </p>
          </div>
        ) : (
          <div className="rounded border border-indigo-200 bg-indigo-50/50 p-3 dark:border-indigo-900/60 dark:bg-indigo-950/20">
            <div className="flex items-center justify-between">
              <span className="text-xs text-indigo-900 dark:text-indigo-200 font-bold uppercase">
                {node.clusterCount} WALLETS AGGREGATED
              </span>
              <span className="font-bold text-indigo-700 dark:text-indigo-300">
                {formatCrypto(node.clusterAmount ?? 0, "BTC")}
              </span>
            </div>
            <p className="mt-1 text-[10px] text-indigo-600/90 dark:text-indigo-400/90 leading-relaxed font-sans">
              Low-value leaf counterparties clustered to keep the primary fund flow clear.
            </p>
          </div>
        )}

        {/* Threat Attribution Section */}
        {!isCluster && (
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">THREAT ATTRIBUTION</div>
            <div className="mt-1 rounded border border-slate-200 p-2.5 bg-white dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between">
                <span className="font-bold text-ink">
                  {node.categories?.length ? node.categories[0] : isHighRisk ? "Suspicious Entity" : "Clear Forensic Standing"}
                </span>
                <span
                  className={`rounded px-1.5 py-0.2 text-[9px] font-bold uppercase ${
                    isHighRisk
                      ? "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-400"
                      : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400"
                  }`}
                >
                  {node.risk}
                </span>
              </div>
              {node.categories && node.categories.length > 1 && (
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {node.categories.slice(1).map((c) => (
                    <span
                      key={c}
                      className="rounded bg-slate-100 px-1 py-0.2 text-[9px] text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Connected Metrics */}
        <div>
          <div className="text-[10px] text-slate-400 uppercase font-semibold">GRAPH DISPERSION</div>
          <div className="mt-1 grid grid-cols-2 gap-2 text-[11px]">
            <div className="rounded border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-950">
              <span className="text-[9px] text-slate-400 uppercase block">ROLE</span>
              <span className="font-bold text-ink uppercase">{node.focus ? "TARGET FOCUS" : node.type}</span>
            </div>
            <div className="rounded border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-950">
              <span className="text-[9px] text-slate-400 uppercase block">ACTIVITY</span>
              <span className="font-bold text-ink">{node.tx_count} TXS</span>
            </div>
          </div>
        </div>

        {/* Cluster Member List */}
        {isCluster && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[10px] font-semibold text-slate-400 uppercase">
              <span>WALLETS IN CLUSTER ({node.clusterMembers?.length ?? 0})</span>
              {onExpandCluster && (
                <button
                  onClick={() => onExpandCluster(node.id)}
                  className="font-bold text-indigo-600 hover:underline dark:text-indigo-400"
                >
                  EXPAND ON CANVAS &rarr;
                </button>
              )}
            </div>

            <div className="relative">
              <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={clusterSearch}
                onChange={(e) => setClusterSearch(e.target.value)}
                placeholder="Filter wallets..."
                className="w-full rounded border border-slate-200 bg-slate-50 py-1 pl-7 pr-2 text-[10px] text-ink focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950"
              />
            </div>

            <div className="max-h-48 space-y-1 overflow-y-auto rounded border border-slate-200 p-1.5 dark:border-slate-800 thin-scroll">
              {filteredMembers.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center justify-between rounded p-1 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <span className="truncate max-w-[170px] text-[10px]" title={member.id}>
                    {truncateMiddle(member.id, 10, 6)}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => copyText(member.id)}
                      className="p-0.5 text-slate-400 hover:text-ink"
                      title="Copy Address"
                    >
                      <Copy size={9} />
                    </button>
                    <button
                      onClick={() => onSetFocus(member.id)}
                      className="text-blue-600 hover:underline text-[9px] font-bold dark:text-blue-400"
                    >
                      FOCUS
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 3. Action Buttons */}
      {!isCluster && (
        <div className="border-t border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900/60 space-y-1.5">
          {!node.focus && (
            <button
              onClick={() => onSetFocus(node.id)}
              className="flex w-full items-center justify-center gap-1.5 rounded bg-blue-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-blue-700 transition-colors"
            >
              <Target size={12} />
              <span>SET AS GRAPH FOCUS</span>
            </button>
          )}

          <div className="grid grid-cols-2 gap-1.5">
            <Link
              href={`/wallet?address=${encodeURIComponent(node.id)}`}
              className="flex items-center justify-center gap-1.5 rounded border border-slate-200 bg-white px-2 py-1.5 text-center text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200"
            >
              <ScanLine size={12} />
              <span>PROFILER</span>
            </Link>

            {onTraceFromHere && (
              <button
                onClick={() => onTraceFromHere(node.id)}
                className="flex items-center justify-center gap-1.5 rounded border border-slate-200 bg-white px-2 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200"
              >
                <Route size={12} />
                <span>TRACE PATH</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
