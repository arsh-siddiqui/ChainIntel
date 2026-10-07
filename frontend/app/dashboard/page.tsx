"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Bell,
  Boxes,
  Clock,
  ExternalLink,
  Eye,
  FileSearch,
  FileText,
  FolderLock,
  GitFork,
  Radio,
  ScanLine,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { formatCrypto, timeAgo, truncateMiddle } from "@/lib/formatters";
import { ActivityChart, CategoryDonut, CounterpartyBars, RiskBar } from "@/components/charts/charts";
import { CopyButton } from "@/components/common/copy-button";
import { RiskBadge } from "@/components/common/risk-badge";
import { Badge, Button, Skeleton } from "@/components/common/ui";
import type { Alert, DashboardSummary, InvestigationSummary } from "@/types";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: "easeOut" },
  },
};

export default function DashboardPage() {
  const router = useRouter();
  const [quickInput, setQuickInput] = useState("");
  const [investigationFilter, setInvestigationFilter] = useState<"ALL" | "HIGH_RISK" | "UNDER_INVESTIGATION" | "RESOLVED">("ALL");

  // Dashboard summary data
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get<DashboardSummary>("/dashboard/summary")).data,
    refetchInterval: 30000,
  });

  const handleLaunchTarget = (e: React.FormEvent, mode: "wallet" | "graph" = "wallet") => {
    e.preventDefault();
    const q = quickInput.trim();
    if (!q) return;
    if (mode === "graph") {
      router.push(`/graph?address=${encodeURIComponent(q)}`);
    } else {
      router.push(`/wallet?address=${encodeURIComponent(q)}`);
    }
  };

  const kpis = summary?.kpis;
  const recentAlerts = summary?.recent_alerts ?? [];

  const filteredInvestigations = useMemo(() => {
    const list = summary?.recent_investigations ?? [];
    if (investigationFilter === "HIGH_RISK") {
      return list.filter((i) => i.risk_level === "HIGH" || i.risk_level === "ELEVATED");
    }
    if (investigationFilter === "UNDER_INVESTIGATION") {
      return list.filter((i) => i.status === "UNDER_INVESTIGATION" || i.status === "OPEN");
    }
    if (investigationFilter === "RESOLVED") {
      return list.filter((i) => i.status === "RESOLVED" || i.status === "CLOSED");
    }
    return list;
  }, [summary?.recent_investigations, investigationFilter]);

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      {/* 1. Executive Forensics Header & Rapid Target Dispatcher */}
      <motion.div variants={itemVariants} className="relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white/95 p-5 shadow-sm backdrop-blur-xl dark:border-slate-800/90 dark:bg-slate-900/80 dark:shadow-2xl">
        <div className="absolute right-0 top-0 -mr-16 -mt-16 h-64 w-64 rounded-full bg-gradient-to-br from-blue-500/10 via-cyan-500/5 to-transparent blur-3xl pointer-events-none" />

        <div className="relative flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
              </span>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                FORENSICS INTELLIGENCE DESK · EXECUTIVE COMMAND
              </span>
            </div>
            <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 sm:text-3xl">
              Executive Forensics Overview
            </h1>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Real-time multi-chain telemetry, automated heuristics, and active investigation pipeline.
            </p>
          </div>

          {/* Quick Target Dispatch Bar */}
          <form
            onSubmit={(e) => handleLaunchTarget(e, "wallet")}
            className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full lg:w-auto"
          >
            <div className="relative flex-1 sm:w-80 lg:w-96">
              <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={quickInput}
                onChange={(e) => setQuickInput(e.target.value)}
                placeholder="Target wallet, TX hash, or case #..."
                className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-3 font-mono text-xs text-slate-900 placeholder-slate-400 transition-all focus:border-blue-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700/80 dark:bg-slate-950/70 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:border-cyan-400 dark:focus:ring-cyan-500/20"
              />
            </div>
            <div className="flex items-center gap-2">
              <button
                type="submit"
                disabled={!quickInput.trim()}
                className="flex flex-1 sm:flex-initial items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 font-mono text-xs font-bold text-white shadow-sm hover:from-blue-500 hover:to-indigo-500 disabled:opacity-40 transition-all"
              >
                <ScanLine size={14} />
                <span>PROFILE</span>
              </button>
              <button
                type="button"
                onClick={(e) => handleLaunchTarget(e, "graph")}
                disabled={!quickInput.trim()}
                className="flex flex-1 sm:flex-initial items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2.5 font-mono text-xs font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 disabled:opacity-40 transition-all"
              >
                <GitFork size={14} />
                <span>GRAPH</span>
              </button>
            </div>
          </form>
        </div>

        {/* Operational Status Telemetry Chips */}
        <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-slate-100 pt-3 font-mono text-xs text-slate-600 dark:border-slate-800/80 dark:text-slate-300">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 dark:text-slate-500">ENGINE:</span>
            <span className="font-semibold text-emerald-600 dark:text-emerald-400">OPERATIONAL</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 dark:text-slate-500">CHAINS:</span>
            <span className="font-semibold text-slate-800 dark:text-slate-200">BTC & EVM INDEXED</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 dark:text-slate-500">THREAT FEEDS:</span>
            <span className="font-semibold text-purple-600 dark:text-purple-400">8 SOURCES ACTIVE</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 dark:text-slate-500">OPEN CASES:</span>
            <span className="font-semibold text-blue-600 dark:text-blue-400">
              {kpis?.open_cases ?? 0} ACTIVE
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 dark:text-slate-500">ACTIVE ALERTS:</span>
            <span className="font-semibold text-rose-600 dark:text-rose-400">
              {kpis?.active_alerts ?? 0} TRIGGERED
            </span>
          </div>
        </div>
      </motion.div>

      {/* 2. Quick Actions Hub */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <Link
          href="/wallet"
          className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-blue-500/50 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-blue-500/50"
        >
          <div className="flex items-start justify-between">
            <div className="rounded-lg bg-blue-50 p-2.5 text-blue-600 dark:bg-blue-950/60 dark:text-blue-400 group-hover:scale-105 transition-transform">
              <ScanLine size={18} />
            </div>
            <ArrowUpRight size={15} className="text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
          </div>
          <div className="mt-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
              Investigate Target Wallet
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              Deep-dive heuristic scoring, balances, counterparty flows & timeline.
            </p>
          </div>
        </Link>

        <Link
          href="/graph"
          className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-purple-500/50 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-purple-500/50"
        >
          <div className="flex items-start justify-between">
            <div className="rounded-lg bg-purple-50 p-2.5 text-purple-600 dark:bg-purple-950/60 dark:text-purple-400 group-hover:scale-105 transition-transform">
              <GitFork size={18} />
            </div>
            <ArrowUpRight size={15} className="text-slate-400 group-hover:text-purple-600 dark:group-hover:text-purple-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
          </div>
          <div className="mt-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
              Visual Graph Canvas
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              Multi-hop peel chains, node clustering & interactive fund topology.
            </p>
          </div>
        </Link>

        <Link
          href="/threat-intelligence"
          className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-rose-500/50 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-rose-500/50"
        >
          <div className="flex items-start justify-between">
            <div className="rounded-lg bg-rose-50 p-2.5 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400 group-hover:scale-105 transition-transform">
              <ShieldAlert size={18} />
            </div>
            <ArrowUpRight size={15} className="text-slate-400 group-hover:text-rose-600 dark:group-hover:text-rose-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
          </div>
          <div className="mt-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 group-hover:text-rose-600 dark:group-hover:text-rose-400 transition-colors">
              Threat Intelligence Feeds
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              OFAC sanctions, ransomware attributions & darknet blacklist indices.
            </p>
          </div>
        </Link>

        <Link
          href="/investigations"
          className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-500/50 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-emerald-500/50"
        >
          <div className="flex items-start justify-between">
            <div className="rounded-lg bg-emerald-50 p-2.5 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400 group-hover:scale-105 transition-transform">
              <FolderLock size={18} />
            </div>
            <ArrowUpRight size={15} className="text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
          </div>
          <div className="mt-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
              Incident Case Dossiers
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              Chain of custody evidence files, investigator notes & audit packages.
            </p>
          </div>
        </Link>
      </div>

      {/* 3. The 8 KPI Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* KPI 1 */}
        <div className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm backdrop-blur-xl transition-all hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-slate-700">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-blue-500" />
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
              Total Investigations
            </span>
            <div className="rounded-lg bg-blue-50 p-1.5 text-blue-600 dark:bg-blue-950/60 dark:text-blue-400">
              <FileSearch size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <div className="font-mono text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              {isLoading ? <Skeleton className="h-7 w-16" /> : kpis?.total_investigations ?? 0}
            </div>
            <span className="rounded bg-blue-50 px-1.5 py-0.5 font-mono text-[10px] font-bold text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
              DOSSIERS
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Recorded forensic inquiries
          </p>
        </div>

        {/* KPI 2 */}
        <div className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm backdrop-blur-xl transition-all hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-slate-700">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-rose-500" />
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
              Suspicious Wallets
            </span>
            <div className="rounded-lg bg-rose-50 p-1.5 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400">
              <ShieldAlert size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <div className="font-mono text-2xl font-bold tracking-tight text-rose-600 dark:text-rose-400">
              {isLoading ? <Skeleton className="h-7 w-16" /> : kpis?.suspicious_wallets ?? 0}
            </div>
            <span className="rounded bg-rose-50 px-1.5 py-0.5 font-mono text-[10px] font-bold text-rose-700 dark:bg-rose-950/60 dark:text-rose-300">
              FLAGGED
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Threat-correlated targets
          </p>
        </div>

        {/* KPI 3 */}
        <div className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm backdrop-blur-xl transition-all hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-slate-700">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-emerald-500" />
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
              Transactions Analyzed
            </span>
            <div className="rounded-lg bg-emerald-50 p-1.5 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
              <Boxes size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <div className="font-mono text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              {isLoading ? <Skeleton className="h-7 w-16" /> : (kpis?.transactions_analyzed ?? 0).toLocaleString()}
            </div>
            <span className="rounded bg-emerald-50 px-1.5 py-0.5 font-mono text-[10px] font-bold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
              ON-CHAIN
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Parsed blockchain transfers
          </p>
        </div>

        {/* KPI 4 */}
        <div className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm backdrop-blur-xl transition-all hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-slate-700">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-amber-500" />
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
              Active Alerts
            </span>
            <div className="rounded-lg bg-amber-50 p-1.5 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400">
              <Bell size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <div className="font-mono text-2xl font-bold tracking-tight text-amber-600 dark:text-amber-400">
              {isLoading ? <Skeleton className="h-7 w-16" /> : kpis?.active_alerts ?? 0}
            </div>
            <span className="rounded bg-amber-50 px-1.5 py-0.5 font-mono text-[10px] font-bold text-amber-700 dark:bg-amber-950/60 dark:text-amber-300">
              PENDING
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Threshold notifications
          </p>
        </div>

        {/* KPI 5 */}
        <div className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm backdrop-blur-xl transition-all hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-slate-700">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-purple-500" />
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
              Threat Matches
            </span>
            <div className="rounded-lg bg-purple-50 p-1.5 text-purple-600 dark:bg-purple-950/60 dark:text-purple-400">
              <AlertTriangle size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <div className="font-mono text-2xl font-bold tracking-tight text-purple-600 dark:text-purple-400">
              {isLoading ? <Skeleton className="h-7 w-16" /> : kpis?.threat_matches ?? 0}
            </div>
            <span className="rounded bg-purple-50 px-1.5 py-0.5 font-mono text-[10px] font-bold text-purple-700 dark:bg-purple-950/60 dark:text-purple-300">
              INDEXED
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Malicious cluster signatures
          </p>
        </div>

        {/* KPI 6 */}
        <div className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm backdrop-blur-xl transition-all hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-slate-700">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-cyan-500" />
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
              Wallets Monitored
            </span>
            <div className="rounded-lg bg-cyan-50 p-1.5 text-cyan-600 dark:bg-cyan-950/60 dark:text-cyan-400">
              <Activity size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <div className="font-mono text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              {isLoading ? <Skeleton className="h-7 w-16" /> : kpis?.wallets_monitored ?? 0}
            </div>
            <span className="rounded bg-cyan-50 px-1.5 py-0.5 font-mono text-[10px] font-bold text-cyan-700 dark:bg-cyan-950/60 dark:text-cyan-300">
              WATCHING
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Continuous surveillance rules
          </p>
        </div>

        {/* KPI 7 */}
        <div className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm backdrop-blur-xl transition-all hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-slate-700">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-indigo-500" />
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
              Open Cases
            </span>
            <div className="rounded-lg bg-indigo-50 p-1.5 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
              <FolderLock size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <div className="font-mono text-2xl font-bold tracking-tight text-indigo-600 dark:text-indigo-400">
              {isLoading ? <Skeleton className="h-7 w-16" /> : kpis?.open_cases ?? 0}
            </div>
            <span className="rounded bg-indigo-50 px-1.5 py-0.5 font-mono text-[10px] font-bold text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
              IN PROGRESS
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Active investigator assignments
          </p>
        </div>

        {/* KPI 8 */}
        <div className="group relative overflow-hidden rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm backdrop-blur-xl transition-all hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/75 dark:hover:border-slate-700">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-slate-500" />
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
              Reports Generated
            </span>
            <div className="rounded-lg bg-slate-100 p-1.5 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              <FileText size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <div className="font-mono text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              {isLoading ? <Skeleton className="h-7 w-16" /> : kpis?.reports_generated ?? 0}
            </div>
            <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
              AUDITED
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Court-ready export bundles
          </p>
        </div>
      </div>

      {/* 4. Interactive Forensics Visualizations (4 Charts, 2x2 Grid) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Chart 1: Transaction Activity */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/80">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800/80">
            <div>
              <div className="flex items-center gap-2">
                <TrendingUp size={16} className="text-blue-600 dark:text-blue-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Transaction Activity (30 Days)
                </h3>
              </div>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Daily incoming vs outgoing volume across analyzed targets
              </p>
            </div>
            <span className="rounded-md bg-slate-100 px-2 py-0.5 font-mono text-[10px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
              BTC FLOW
            </span>
          </div>
          {isLoading ? <Skeleton className="h-64 w-full" /> : <ActivityChart data={summary?.activity ?? []} />}
        </div>

        {/* Chart 2: Threat Category Distribution */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/80">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800/80">
            <div>
              <div className="flex items-center gap-2">
                <ShieldAlert size={16} className="text-purple-600 dark:text-purple-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Threat Category Distribution
                </h3>
              </div>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Breakdown of detected threat signatures and malware/fraud types
              </p>
            </div>
            <span className="rounded-md bg-slate-100 px-2 py-0.5 font-mono text-[10px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
              CATEGORIES
            </span>
          </div>
          {isLoading ? <Skeleton className="h-64 w-full" /> : <CategoryDonut data={summary?.threat_distribution ?? []} />}
        </div>

        {/* Chart 3: Top Suspicious Counterparties */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/80">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800/80">
            <div>
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-600 dark:text-amber-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Top Flagged Counterparties
                </h3>
              </div>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Frequently transacting peer addresses with observed velocity
              </p>
            </div>
            <span className="rounded-md bg-slate-100 px-2 py-0.5 font-mono text-[10px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
              TRANSACTIONS
            </span>
          </div>
          {isLoading ? <Skeleton className="h-64 w-full" /> : <CounterpartyBars data={summary?.top_counterparties ?? []} />}
        </div>

        {/* Chart 4: Risk Rating Distribution */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/80">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800/80">
            <div>
              <div className="flex items-center gap-2">
                <ShieldCheck size={16} className="text-emerald-600 dark:text-emerald-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Investigation Risk Profile
                </h3>
              </div>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Evaluated risk severity distribution across recorded dossiers
              </p>
            </div>
            <span className="rounded-md bg-slate-100 px-2 py-0.5 font-mono text-[10px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
              SEVERITY
            </span>
          </div>
          {isLoading ? <Skeleton className="h-64 w-full" /> : <RiskBar data={summary?.risk_distribution ?? []} />}
        </div>
      </div>

      {/* 5. Bottom Split Pane: Recent Investigations Ledger & Watchlist Alerts Stream */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left 8 Cols: Recent Investigations Live Ledger */}
        <div className="rounded-2xl border border-slate-200/90 bg-white shadow-sm backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/80 lg:col-span-8 flex flex-col">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 p-5 dark:border-slate-800/80">
            <div>
              <div className="flex items-center gap-2">
                <FolderLock size={16} className="text-blue-600 dark:text-blue-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Recent Investigations Ledger
                </h3>
              </div>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Active and concluded forensic inquiries with direct dossier links
              </p>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1 dark:border-slate-800 dark:bg-slate-950/70">
              {(["ALL", "HIGH_RISK", "UNDER_INVESTIGATION", "RESOLVED"] as const).map((filterKey) => {
                const active = investigationFilter === filterKey;
                const labels: Record<string, string> = {
                  ALL: "All",
                  HIGH_RISK: "High Risk",
                  UNDER_INVESTIGATION: "Under Review",
                  RESOLVED: "Resolved",
                };
                return (
                  <button
                    key={filterKey}
                    type="button"
                    onClick={() => setInvestigationFilter(filterKey)}
                    className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${
                      active
                        ? "bg-white text-blue-600 shadow-sm dark:bg-slate-800 dark:text-blue-400"
                        : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
                    }`}
                  >
                    {labels[filterKey]}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/75 text-[11px] font-bold uppercase text-slate-500 dark:border-slate-800/80 dark:bg-slate-950/40 dark:text-slate-400">
                  <th className="px-5 py-3">TARGET WALLET</th>
                  <th className="px-4 py-3">DOSSIER / CASE</th>
                  <th className="px-3 py-3 text-center">CHAIN</th>
                  <th className="px-4 py-3">RISK EVALUATION</th>
                  <th className="px-3 py-3">STATUS</th>
                  <th className="px-4 py-3">UPDATED</th>
                  <th className="px-5 py-3 text-right">ACTIONS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono dark:divide-slate-800/60">
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="p-6 text-center text-xs text-slate-400">
                      Loading investigation records...
                    </td>
                  </tr>
                ) : filteredInvestigations.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-xs text-slate-400 font-mono">
                      No matching investigation dossiers found.
                    </td>
                  </tr>
                ) : (
                  filteredInvestigations.map((inv) => (
                    <tr
                      key={inv.id}
                      className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="px-5 py-3 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Link
                            href={`/wallet?address=${encodeURIComponent(inv.wallet_address)}`}
                            className="font-bold text-blue-600 hover:underline dark:text-blue-400"
                            title={inv.wallet_address}
                          >
                            {truncateMiddle(inv.wallet_address, 10, 6)}
                          </Link>
                          <CopyButton value={inv.wallet_address} label="Copy address" />
                        </div>
                      </td>
                      <td className="px-4 py-3 font-sans max-w-[200px]">
                        <p className="font-semibold text-slate-800 dark:text-slate-200 truncate" title={inv.title}>
                          {inv.title}
                        </p>
                        {inv.case_id ? (
                          <span className="font-mono text-[10px] text-slate-400">
                            CASE #{inv.case_id}
                          </span>
                        ) : (
                          <span className="font-mono text-[10px] text-slate-400">
                            Ad-hoc inquiry
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-3 text-center uppercase whitespace-nowrap">
                        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                          {inv.blockchain}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <RiskBadge band={inv.risk_level} />
                          {inv.risk_score !== null && inv.risk_score !== undefined ? (
                            <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                              {inv.risk_score}/100
                            </span>
                          ) : null}
                        </div>
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap">
                        <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                          {inv.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[11px] text-slate-500 dark:text-slate-400 whitespace-nowrap">
                        {timeAgo(inv.updated_at)}
                      </td>
                      <td className="px-5 py-3 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          <Link
                            href={`/wallet?address=${encodeURIComponent(inv.wallet_address)}`}
                            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50 hover:text-blue-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 dark:hover:text-cyan-300 transition-colors"
                          >
                            <span>Inspect</span>
                          </Link>
                          <Link
                            href={`/graph?address=${encodeURIComponent(inv.wallet_address)}`}
                            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50 hover:text-purple-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 dark:hover:text-purple-300 transition-colors"
                            title="Open in Graph"
                          >
                            <GitFork size={12} />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="border-t border-slate-100 p-3.5 text-right dark:border-slate-800/80">
            <Link
              href="/investigations"
              className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-blue-600 hover:underline dark:text-blue-400"
            >
              <span>VIEW ALL CASE DOSSIERS ({kpis?.total_investigations ?? 0})</span>
              <ArrowRight size={13} />
            </Link>
          </div>
        </div>

        {/* Right 4 Cols: Active Watchlist Alerts */}
        <div className="rounded-2xl border border-slate-200/90 bg-white shadow-sm backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/80 lg:col-span-4 flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-100 p-5 dark:border-slate-800/80">
            <div>
              <div className="flex items-center gap-2">
                <Bell size={16} className="text-rose-600 dark:text-rose-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Watchlist Alerts
                </h3>
              </div>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Trigger events from monitored wallets
              </p>
            </div>
            <Link
              href="/alerts"
              className="font-mono text-xs font-semibold text-blue-600 hover:underline dark:text-blue-400 flex items-center gap-1"
            >
              <span>View All</span>
              <ArrowRight size={12} />
            </Link>
          </div>

          <div className="divide-y divide-slate-100 overflow-y-auto max-h-[460px] flex-1 dark:divide-slate-800/60 p-2">
            {recentAlerts.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400 font-mono">
                No active trigger alerts. Monitored addresses are nominal.
              </div>
            ) : (
              recentAlerts.map((alert) => {
                const isCritical = alert.severity === "CRITICAL" || alert.severity === "HIGH";
                return (
                  <div
                    key={alert.id}
                    className="p-3 hover:bg-slate-50 rounded-xl dark:hover:bg-slate-800/50 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`rounded px-1.5 py-0.5 font-mono text-[9px] font-bold uppercase ${
                          isCritical
                            ? "bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border border-rose-200 dark:border-rose-900"
                            : "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-200 dark:border-amber-900"
                        }`}
                      >
                        {alert.severity}
                      </span>
                      <span className="font-mono text-[10px] text-slate-400">
                        {timeAgo(alert.created_at)}
                      </span>
                    </div>

                    <p className="mt-1.5 text-xs font-semibold text-slate-900 dark:text-slate-100">
                      {alert.title}
                    </p>
                    {alert.message ? (
                      <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
                        {alert.message}
                      </p>
                    ) : null}

                    <div className="mt-2 flex items-center justify-between border-t border-slate-100 pt-2 font-mono text-xs dark:border-slate-800/60">
                      <Link
                        href={`/wallet?address=${encodeURIComponent(alert.wallet_address)}`}
                        className="text-[11px] font-semibold text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400 truncate max-w-[160px]"
                        title={alert.wallet_address}
                      >
                        {truncateMiddle(alert.wallet_address, 8, 4)}
                      </Link>
                      <Link
                        href={`/wallet?address=${encodeURIComponent(alert.wallet_address)}`}
                        className="text-[11px] font-bold text-blue-600 hover:underline dark:text-blue-400"
                      >
                        Investigate &rarr;
                      </Link>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="border-t border-slate-100 p-3.5 text-center dark:border-slate-800/80">
            <Link
              href="/alerts"
              className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
            >
              <span>CONFIGURE MONITORING RULES</span>
              <ArrowRight size={13} />
            </Link>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
