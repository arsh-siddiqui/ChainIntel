"use client";

import { motion } from "framer-motion";
import {
  ExternalLink,
  ShieldCheck,
  Radar,
  Info,
  Layers,
  Search,
  AlertTriangle,
  Network,
  Wallet,
  MessageSquare,
} from "lucide-react";
import type { OSINTCorrelation, OSINTResult } from "@/types";
import { Card, CardHeader, Badge } from "@/components/common/ui";
import { confidencePercent } from "@/lib/formatters";

function getSourceIcon(name: string) {
  const n = name.toLowerCase();
  if (n.includes("blockstream") || n.includes("blockchain.com")) return <Layers size={18} className="text-sky-600 dark:text-cyan-400" />;
  if (n.includes("chainabuse") || n.includes("scam")) return <AlertTriangle size={18} className="text-rose-600 dark:text-rose-400" />;
  if (n.includes("who's who") || n.includes("whoswho")) return <ShieldCheck size={18} className="text-amber-600 dark:text-amber-400" />;
  if (n.includes("walletexplorer") || n.includes("graph")) return <Network size={18} className="text-purple-600 dark:text-purple-400" />;
  if (n.includes("bitref")) return <Wallet size={18} className="text-emerald-600 dark:text-emerald-400" />;
  if (n.includes("twitter") || n.includes("community")) return <MessageSquare size={18} className="text-blue-600 dark:text-sky-400" />;
  return <Radar size={18} className="text-sky-600 dark:text-blue-400" />;
}

export function OsintPanel({ correlation }: { correlation: OSINTCorrelation }) {
  return (
    <Card className="shadow-2xl">
      <CardHeader
        title={
          <div className="flex items-center gap-2.5">
            <div className="relative flex h-6 w-6 items-center justify-center">
              <Radar size={18} className="text-sky-600 dark:text-cyan-400" />
              <span className="absolute inset-0 rounded-full border border-sky-500/30 dark:border-cyan-400/30 radar-ping" />
            </div>
            <span className="font-extrabold text-slate-900 dark:text-slate-100">
              Public OSINT & Cross-Ledger Attribution
            </span>
          </div>
        }
        subtitle="Multi-source correlation verifying against public threat aggregators, block explorers, and co-spending clusters."
        action={
          correlation.found_count > 0 ? (
            <Badge className="border-purple-300 bg-purple-50 text-purple-700 dark:border-purple-500/30 dark:bg-purple-500/10 dark:text-purple-300 font-mono shadow-sm">
              {correlation.found_count} Findings Identified
            </Badge>
          ) : (
            <Badge className="border-sky-300 bg-sky-50 text-sky-700 dark:border-cyan-500/30 dark:bg-cyan-500/10 dark:text-cyan-300 font-mono shadow-sm">
              {correlation.provider_count} Feeds Synchronized
            </Badge>
          )
        }
      />

      {/* Forensic Integrity Banner */}
      <div className="border-b px-6 py-3 border-slate-100 dark:border-slate-800/80 bg-slate-50/70 dark:bg-slate-950/60">
        <p className="flex items-center gap-2 text-xs font-mono text-slate-600 dark:text-slate-400">
          <Info size={13} className="text-sky-600 dark:text-cyan-400 shrink-0" />
          <span>
            Forensic Integrity Standard: Direct public links preserve cryptographic chain of custody without synthetic fabrication.
          </span>
        </p>
      </div>

      {/* Intelligence Cards Grid with Staggered Animations */}
      <div className="grid gap-4 p-6 md:grid-cols-2">
        {correlation.results.map((result, idx) => (
          <OsintCard key={result.source_name} result={result} delay={idx * 0.04} />
        ))}
      </div>
    </Card>
  );
}

function OsintCard({ result, delay = 0 }: { result: OSINTResult; delay?: number }) {
  const isLinkOnly = Boolean(result.external_search_url && result.status === "UNAVAILABLE");

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay }}
      whileHover={{ y: -2 }}
      className="group relative flex flex-col justify-between rounded-2xl border p-4.5 transition-all duration-200 border-slate-200/90 bg-white/95 text-slate-900 shadow-sm hover:border-sky-400 hover:shadow-lg dark:border-slate-800/80 dark:bg-slate-950/70 dark:text-slate-100 dark:hover:border-cyan-500/40 dark:hover:bg-slate-900/60 dark:hover:shadow-cyan-500/10"
    >
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 shadow-inner group-hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900 dark:group-hover:border-slate-700 transition-colors">
              {getSourceIcon(result.source_name)}
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900 dark:text-slate-100 group-hover:text-sky-600 dark:group-hover:text-cyan-300 transition-colors">
                {result.source_name}
              </p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-sky-500 dark:bg-cyan-400" />
                </span>
                <span className="font-mono text-[10px] tracking-wide uppercase text-slate-500 dark:text-slate-400">
                  {isLinkOnly ? "Direct Public Feed" : result.status.replace("_", " ")}
                </span>
              </div>
            </div>
          </div>

          {result.status === "FOUND" ? (
            <span className="rounded-lg bg-purple-50 text-purple-700 border border-purple-200 dark:bg-purple-500/10 dark:text-purple-300 dark:border-purple-500/20 px-2 py-0.5 font-mono text-[10px] font-bold">
              {confidencePercent(result.confidence)} Match
            </span>
          ) : null}
        </div>

        {result.notes ? (
          <p className="mt-3 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            {result.notes}
          </p>
        ) : null}
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/60 flex items-center justify-between">
        {result.external_search_url ? (
          <motion.a
            whileTap={{ scale: 0.98 }}
            href={result.external_search_url}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full inline-flex items-center justify-center gap-2 rounded-xl border px-3 py-2 text-xs font-bold transition-all border-sky-500/30 bg-sky-50 text-sky-700 hover:bg-sky-600 hover:text-white shadow-sm dark:border-cyan-500/30 dark:bg-cyan-500/10 dark:text-cyan-300 dark:hover:bg-cyan-500 dark:hover:text-white dark:hover:shadow-cyan-500/20"
          >
            <span>Query Live Feed on {result.source_name}</span>
            <ExternalLink size={12} className="stroke-[2.5]" />
          </motion.a>
        ) : null}
      </div>
    </motion.div>
  );
}
