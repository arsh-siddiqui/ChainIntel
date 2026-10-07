"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  FileText,
  Fingerprint,
  GitFork,
  Moon,
  Radar,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sun,
  Terminal,
} from "lucide-react";
import { useTheme } from "@/hooks/use-theme";
import { DEMO_TARGET_PRESETS } from "@/lib/constants";

export default function LandingPage() {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const [address, setAddress] = useState("");

  const handleQuickSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (address.trim().length >= 4) {
      router.push(`/wallet?address=${encodeURIComponent(address.trim())}`);
    } else {
      router.push("/wallet");
    }
  };

  return (
    <div className="relative min-h-screen overflow-x-hidden transition-colors duration-200 bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans selection:bg-sky-500 selection:text-white">
      {/* Dynamic Background Mesh */}
      <div className="pointer-events-none absolute left-1/2 top-0 -translate-x-1/2 h-[700px] w-full max-w-7xl overflow-hidden opacity-30 dark:opacity-40 blur-[130px] z-0">
        <div className="absolute top-10 left-1/3 h-96 w-96 rounded-full bg-gradient-to-tr from-sky-400 to-cyan-300 dark:from-sky-600 dark:to-cyan-400" />
        <div className="absolute top-48 right-1/3 h-96 w-96 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 dark:from-indigo-700 dark:to-purple-600" />
      </div>

      {/* Navigation Header */}
      <header className="relative z-30 flex h-20 items-center justify-between px-6 lg:px-16 border-b transition-colors duration-200 border-slate-200/80 bg-white/80 dark:border-slate-800/80 dark:bg-slate-950/75 backdrop-blur-xl shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-500 via-blue-600 to-indigo-600 text-white shadow-md shadow-sky-500/20 dark:shadow-cyan-500/25">
            <ShieldCheck size={22} className="stroke-[2.2]" />
          </div>
          <div>
            <span className="text-xl font-black tracking-tight text-slate-900 dark:text-white">ChainIntel</span>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-8 text-xs font-semibold text-slate-600 dark:text-slate-400">
          <Link href="/dashboard" className="hover:text-sky-600 dark:hover:text-cyan-400 transition-colors">Security Center</Link>
          <Link href="/wallet" className="hover:text-sky-600 dark:hover:text-cyan-400 transition-colors">Wallet Tracer</Link>
          <Link href="/graph" className="hover:text-sky-600 dark:hover:text-cyan-400 transition-colors">Graph Analysis</Link>
          <Link href="/threat-intelligence" className="hover:text-sky-600 dark:hover:text-cyan-400 transition-colors">Threat Matrix</Link>
          <Link href="/reports" className="hover:text-sky-600 dark:hover:text-cyan-400 transition-colors">Dossiers</Link>
        </div>

        <div className="flex items-center gap-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.92 }}
            type="button"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900/80 dark:text-slate-300 dark:hover:border-slate-700 transition-all backdrop-blur-md"
          >
            {theme === "dark" ? (
              <Sun size={17} className="text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.6)]" />
            ) : (
              <Moon size={17} className="text-sky-600 drop-shadow-[0_0_8px_rgba(2,132,199,0.3)]" />
            )}
          </motion.button>

          <Link
            href="/dashboard"
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 dark:from-sky-500 dark:via-cyan-500 dark:to-blue-600 px-5 py-2.5 text-xs font-bold text-white shadow-md shadow-sky-500/20 hover:from-sky-400 hover:to-indigo-500 transition-all active:scale-[0.98]"
          >
            <span>Launch Workstation</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 px-6 pt-20 pb-20 lg:px-16 lg:pt-28 max-w-7xl mx-auto">
        <div className="max-w-4xl">
          <div className="flex items-center gap-3 text-xs font-mono text-slate-500 dark:text-slate-400 mb-6">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
            <span className="font-bold text-slate-800 dark:text-slate-200">LIVE FORENSIC SUITE</span>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <span>MULTI-CHAIN INTELLIGENCE ENGINE</span>
          </div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-slate-900 dark:text-white leading-[1.08]"
          >
            Uncover On-Chain Intelligence with <span className="bg-gradient-to-r from-sky-600 via-blue-600 to-indigo-600 dark:from-sky-400 dark:via-cyan-300 dark:to-blue-500 bg-clip-text text-transparent">Absolute Precision</span>.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="mt-6 text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed"
          >
            Investigate target wallets, map fund-flow topologies across <strong className="text-slate-900 dark:text-slate-100">Bitcoin, Ethereum, BSC, Polygon & Solana</strong>, correlate OSINT threat vectors, and export court-ready dossiers.
          </motion.p>
        </div>

        {/* Quick Launch Search Input */}
        <motion.form
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          onSubmit={handleQuickSearch}
          className="mt-10 max-w-3xl flex flex-col sm:flex-row gap-3 p-2.5 rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-2xl backdrop-blur-xl ring-1 ring-slate-900/5 dark:ring-white/10"
        >
          <div className="relative flex-1 flex items-center">
            <Search size={18} className="absolute left-4 text-slate-400 dark:text-slate-500" />
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Paste target wallet address (e.g. 1A1zP..., bc1q..., 0x..., SOL...)"
              className="w-full rounded-xl bg-transparent py-3 pl-11 pr-4 text-sm font-mono text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 dark:from-cyan-500 dark:to-blue-600 hover:from-sky-400 hover:to-indigo-500 px-6 py-3 text-xs font-bold text-white shadow-md shadow-sky-500/20 dark:shadow-cyan-500/25 transition-all active:scale-[0.98]"
          >
            <Search size={14} className="stroke-[2.5]" />
            <span>Investigate Target</span>
          </button>
        </motion.form>

        {/* Target Presets Bar */}
        <div className="mt-5 max-w-3xl flex flex-wrap items-center gap-2 text-xs">
          <span className="font-mono text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wide mr-1">
            TARGET PRESETS:
          </span>
          {DEMO_TARGET_PRESETS.slice(0, 5).map((preset) => (
            <button
              key={preset.address}
              type="button"
              onClick={() => router.push(`/wallet?address=${encodeURIComponent(preset.address)}`)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 font-mono text-[11px] font-medium text-slate-700 hover:border-sky-500 hover:bg-sky-50 hover:text-sky-700 transition-all shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-cyan-400 dark:hover:bg-cyan-950/40"
              title={`Investigate ${preset.label} (${preset.address})`}
            >
              <span>{preset.label}</span>
              <span className="rounded bg-slate-100 px-1 py-0.2 text-[9px] font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                {preset.badge}
              </span>
            </button>
          ))}
        </div>

        {/* Telemetry Stats Bar */}
        <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-4 border-t border-slate-200 dark:border-slate-800/80 pt-8 max-w-4xl">
          <div>
            <p className="font-mono text-2xl font-extrabold text-slate-900 dark:text-white">5 CHAINS</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">BTC, ETH, BSC, Polygon, SOL</p>
          </div>
          <div>
            <p className="font-mono text-2xl font-extrabold text-sky-600 dark:text-cyan-400">10,000+</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Exchange & Threat Labels</p>
          </div>
          <div>
            <p className="font-mono text-2xl font-extrabold text-purple-600 dark:text-purple-400">MULTI-HOP</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">D3 Force Graph Canvas</p>
          </div>
          <div>
            <p className="font-mono text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">SHA-256</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Evidence Checksum Verification</p>
          </div>
        </div>
      </section>

      {/* Human Editorial Feature Matrix (Asymmetrical Layout) */}
      <section className="relative z-10 px-6 py-20 lg:px-16 max-w-7xl mx-auto border-t border-slate-200 dark:border-slate-800/80">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
          <div>
            <p className="font-mono text-xs font-bold text-slate-400 dark:text-slate-500">01 / CAPABILITIES</p>
            <h2 className="mt-2 text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">
              Forensic Intelligence Infrastructure
            </h2>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 max-w-md">
            Built from the ground up for digital forensics teams requiring deterministic blockchain analysis and chain-of-custody compliance.
          </p>
        </div>

        {/* Asymmetrical Hero Feature Section */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Large Feature: Graph Canvas */}
          <div className="lg:col-span-8 rounded-3xl border border-slate-200 bg-white p-8 dark:border-slate-800 dark:bg-slate-900/60 backdrop-blur-xl flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-sky-600 dark:text-cyan-400">INTERACTIVE GRAPH ENGINE</span>
                <span className="rounded bg-sky-50 px-2 py-0.5 font-mono text-[10px] font-bold text-sky-700 dark:bg-cyan-950/60 dark:text-cyan-300">
                  D3 VISUAL CANVAS
                </span>
              </div>
              <h3 className="mt-4 text-2xl font-bold text-slate-900 dark:text-white">
                Multi-Hop Fund Flow & Layering Graph
              </h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 leading-relaxed max-w-xl">
                Visualize complex peel chains, mixer interactions, and node clusters with real-time drag physics, value-proportional edge thickness, and node filtering.
              </p>

              {/* Terminal Code Mockup */}
              <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 shadow-inner">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 text-[11px] text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Terminal size={13} className="text-cyan-400" />
                    <span>graph-engine.py — Shortest Path Topology</span>
                  </div>
                  <span className="text-emerald-400">RUNNING</span>
                </div>
                <div className="mt-3 space-y-1 text-[11px] leading-relaxed">
                  <p><span className="text-sky-400">TRACE</span> target: 0x12d6621e... [Tornado Router]</p>
                  <p><span className="text-purple-400">HOPS</span> max_depth=4 | nodes_found=18 | edges=24</p>
                  <p><span className="text-rose-400">THREAT</span> Flagged mixer hop detected at node #3 (Confidence: 98%)</p>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
              <span className="text-xs font-mono text-slate-500">Bounded BFS Node Topology</span>
              <Link
                href="/graph"
                className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-sky-600 dark:text-cyan-400 hover:underline"
              >
                <span>OPEN GRAPH CANVAS</span>
                <ArrowRight size={13} />
              </Link>
            </div>
          </div>

          {/* Secondary Stacked Feature Cards */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            <div className="flex-1 rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60 backdrop-blur-xl flex flex-col justify-between shadow-sm">
              <div>
                <span className="font-mono text-xs font-bold text-rose-600 dark:text-rose-400">THREAT MATRIX</span>
                <h3 className="mt-2 text-lg font-bold text-slate-900 dark:text-white">
                  OFAC & Malicious Entity Index
                </h3>
                <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Correlate addresses against 10,000+ known entities including Binance, Kraken, and sanctioned mixers.
                </p>
              </div>
              <Link
                href="/threat-intelligence"
                className="mt-6 inline-flex items-center gap-1.5 font-mono text-xs font-bold text-rose-600 dark:text-rose-400 hover:underline"
              >
                <span>EXPLORE THREAT FEEDS</span>
                <ArrowRight size={13} />
              </Link>
            </div>

            <div className="flex-1 rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60 backdrop-blur-xl flex flex-col justify-between shadow-sm">
              <div>
                <span className="font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">EVIDENCE INTEGRITY</span>
                <h3 className="mt-2 text-lg font-bold text-slate-900 dark:text-white">
                  SHA-256 Chain-of-Custody
                </h3>
                <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Export court-ready PDF & JSON dossiers with cryptographic checksum integrity validation.
                </p>
              </div>
              <Link
                href="/reports"
                className="mt-6 inline-flex items-center gap-1.5 font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
              >
                <span>GENERATE DOSSIER</span>
                <ArrowRight size={13} />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-200 dark:border-slate-800/80 px-6 py-12 lg:px-16 max-w-7xl mx-auto text-xs text-slate-500 dark:text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono">
        <div className="flex items-center gap-2">
          <ShieldCheck size={16} className="text-sky-600 dark:text-cyan-400" />
          <span className="font-bold text-slate-800 dark:text-slate-300">ChainIntel Forensics</span>
          <span>© 2026 Workstation Edition</span>
        </div>
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="hover:text-slate-900 dark:hover:text-slate-300">Dashboard</Link>
          <Link href="/wallet" className="hover:text-slate-900 dark:hover:text-slate-300">Wallet</Link>
          <Link href="/graph" className="hover:text-slate-900 dark:hover:text-slate-300">Graph</Link>
          <Link href="/threat-intelligence" className="hover:text-slate-900 dark:hover:text-slate-300">Threats</Link>
          <Link href="/reports" className="hover:text-slate-900 dark:hover:text-slate-300">Reports</Link>
        </div>
      </footer>
    </div>
  );
}
