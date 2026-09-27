"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import {
  AlertTriangle,
  Building2,
  Check,
  Copy,
  Layers,
  Network,
  Radio,
  Shuffle,
  Target,
  UserX,
  Wallet,
} from "lucide-react";
import { useState } from "react";
import { GRAPH_NODE_COLORS } from "@/lib/constants";
import { formatCrypto, truncateMiddle } from "@/lib/formatters";
import type { GraphNode } from "@/types";

export interface CustomNodeData extends GraphNode {
  isSelected?: boolean;
  onSelectNode?: (node: GraphNode) => void;
  onExpandCluster?: (clusterId: string) => void;
  [key: string]: unknown;
}

// 1. Central Focus Node Component
export const FocusNode = memo(({ data, selected }: NodeProps) => {
  const node = data as unknown as CustomNodeData;
  const [copied, setCopied] = useState(false);

  const copyAddress = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(node.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div
      onClick={() => node.onSelectNode?.(node)}
      className={`group relative min-w-[210px] cursor-pointer rounded-2xl border-2 bg-white/95 p-3.5 shadow-xl backdrop-blur transition-all dark:bg-slate-900/95 ${
        selected || node.isSelected
          ? "border-primary ring-4 ring-primary/25 shadow-primary/20"
          : "border-primary/80 hover:border-primary hover:shadow-2xl"
      }`}
      style={{
        boxShadow: "0 0 25px rgba(37, 99, 235, 0.2)",
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-3 !w-3 !border-2 !border-white !bg-primary dark:!border-slate-900"
      />

      <div className="flex items-center justify-between gap-2 border-b border-primary/15 pb-2">
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-primary" />
          </span>
          <span className="text-[10px] font-black uppercase tracking-wider text-primary">
            Target Focus
          </span>
        </div>
        <Target size={14} className="text-primary animate-spin-slow" />
      </div>

      <div className="mt-2">
        <h4 className="max-w-[200px] truncate text-xs font-bold text-ink">
          {node.label || "Target Wallet"}
        </h4>
        <div className="mt-1 flex items-center justify-between gap-1 rounded-md bg-slate-100/80 px-2 py-1 font-mono text-[10px] text-slate-600 dark:bg-slate-800/80 dark:text-slate-300">
          <span>{truncateMiddle(node.id, 10, 6)}</span>
          <button
            onClick={copyAddress}
            className="text-slate-400 hover:text-ink transition-colors"
            title="Copy full address"
          >
            {copied ? <Check size={11} className="text-emerald-500" /> : <Copy size={11} />}
          </button>
        </div>
      </div>

      <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-500">
        <span className="font-medium">Active Root</span>
        <span className="rounded bg-primary/10 px-1.5 py-0.5 font-bold text-primary dark:bg-primary/20">
          {node.tx_count} txs
        </span>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="!h-3 !w-3 !border-2 !border-white !bg-primary dark:!border-slate-900"
      />
    </div>
  );
});
FocusNode.displayName = "FocusNode";

// 2. Standard Entity Node (Exchanges, Scams, Ransomware, Wallets, etc.)
export const EntityNode = memo(({ data, selected }: NodeProps) => {
  const node = data as unknown as CustomNodeData;
  const palette = GRAPH_NODE_COLORS[node.type] ?? GRAPH_NODE_COLORS.wallet;
  const isHighRisk = node.risk === "high" || node.type === "ransomware" || node.type === "scam";

  const getEntityIcon = () => {
    switch (node.type) {
      case "exchange":
        return <Building2 size={13} className="text-teal-600 dark:text-teal-400" />;
      case "mixer":
        return <Shuffle size={13} className="text-purple-600 dark:text-purple-400" />;
      case "ransomware":
      case "scam":
        return <AlertTriangle size={13} className="text-rose-600 dark:text-rose-400 animate-pulse" />;
      case "victim":
        return <UserX size={13} className="text-blue-600 dark:text-blue-400" />;
      case "intermediate":
        return <Network size={13} className="text-amber-600 dark:text-amber-400" />;
      default:
        return <Wallet size={13} className="text-slate-500 dark:text-slate-400" />;
    }
  };

  return (
    <div
      onClick={() => node.onSelectNode?.(node)}
      className={`group relative min-w-[170px] max-w-[210px] cursor-pointer rounded-xl border px-3 py-2 shadow-sm transition-all dark:bg-slate-900/90 ${
        selected || node.isSelected
          ? "border-primary ring-2 ring-primary/40 shadow-md scale-[1.03]"
          : "hover:border-slate-400 hover:shadow-md hover:scale-[1.01]"
      } ${isHighRisk ? "border-rose-400/80 bg-rose-50/40 dark:bg-rose-950/20" : "bg-white/90"}`}
      style={{
        borderColor: selected ? undefined : isHighRisk ? "#EF4444" : palette.border,
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-slate-400 dark:!border-slate-900"
      />

      <div className="flex items-center gap-1.5">
        <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800">
          {getEntityIcon()}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[11px] font-semibold text-ink leading-tight">
            {node.label || truncateMiddle(node.id, 8, 4)}
          </p>
          <p className="font-mono text-[9px] text-slate-400 truncate">{truncateMiddle(node.id, 8, 4)}</p>
        </div>
      </div>

      <div className="mt-1.5 flex items-center justify-between gap-1 pt-1 border-t border-slate-100 dark:border-slate-800">
        <span
          className="rounded px-1.5 py-0.2 text-[8px] font-bold uppercase tracking-wider"
          style={{ background: palette.bg, color: palette.text }}
        >
          {palette.label}
        </span>

        {isHighRisk ? (
          <span className="rounded bg-rose-100 px-1 py-0.2 text-[8px] font-black uppercase text-rose-700 dark:bg-rose-900/50 dark:text-rose-300">
            {node.risk}
          </span>
        ) : (
          <span className="text-[9px] font-medium text-slate-400">
            {node.tx_count} {node.tx_count === 1 ? "tx" : "txs"}
          </span>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="!h-2.5 !w-2.5 !border-2 !border-white !bg-slate-400 dark:!border-slate-900"
      />
    </div>
  );
});
EntityNode.displayName = "EntityNode";

// 3. Smart Aggregated Cluster Node (for 10-100+ low-value leaf wallets)
export const ClusterNode = memo(({ data, selected }: NodeProps) => {
  const node = data as unknown as CustomNodeData;

  return (
    <div
      onClick={() => node.onSelectNode?.(node)}
      className={`group relative min-w-[190px] cursor-pointer rounded-2xl border-2 border-dashed border-indigo-400/90 bg-indigo-50/70 p-3 shadow-md backdrop-blur transition-all dark:border-indigo-500/80 dark:bg-indigo-950/30 ${
        selected || node.isSelected
          ? "ring-4 ring-indigo-500/25 border-indigo-600 shadow-indigo-500/20 scale-[1.03]"
          : "hover:border-indigo-500 hover:shadow-lg hover:scale-[1.02]"
      }`}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-3 !w-3 !border-2 !border-white !bg-indigo-500 dark:!border-slate-900"
      />

      <div className="flex items-center justify-between gap-1.5 border-b border-indigo-200/60 pb-1.5 dark:border-indigo-800/60">
        <div className="flex items-center gap-1.5 text-indigo-700 dark:text-indigo-300">
          <Layers size={13} className="animate-bounce" />
          <span className="text-[10px] font-bold uppercase tracking-wider">
            Aggregated Cluster
          </span>
        </div>
        <span className="rounded-full bg-indigo-600 px-1.5 py-0.5 text-[9px] font-black text-white">
          {node.clusterCount} Wallets
        </span>
      </div>

      <div className="mt-2">
        <p className="text-xs font-semibold text-ink">{node.label}</p>
        <p className="mt-0.5 text-[10px] font-mono text-indigo-600 dark:text-indigo-400">
          Σ {formatCrypto(node.clusterAmount ?? 0, "BTC")}
        </p>
      </div>

      <div className="mt-2 flex items-center justify-between pt-1 border-t border-indigo-100 text-[9px] text-indigo-500 dark:border-indigo-900/50">
        <span>Leaf endpoints</span>
        <span className="underline font-semibold group-hover:text-indigo-700 dark:group-hover:text-indigo-300">
          Inspect list &rarr;
        </span>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="!h-3 !w-3 !border-2 !border-white !bg-indigo-500 dark:!border-slate-900"
      />
    </div>
  );
});
ClusterNode.displayName = "ClusterNode";
