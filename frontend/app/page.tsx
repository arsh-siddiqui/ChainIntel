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
  Zap,
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
      {/* Background Ambient Glows */}
      <div className="pointer-events-none absolute left-1/2 top-0 -translate-x-1/2 h-[600px] w-full max-w-7xl overflow-hidden opacity-30 dark:opacity-40 blur-[120px] z-0">
        <div className="absolute top-10 left-1/4 h-96 w-96 rounded-full bg-gradient-to-tr from-sky-400 to-cyan-300 dark:from-sky-500 dark:to-cyan-400" />
        <div className="absolute top-40 right-1/4 h-96 w-96 rounded-full bg-gradient-to-tr from-blue-400 to-indigo-300 dark:from-indigo-600 dark:to-purple-500" />
      </div>

      {/* Top Navigation Bar */}
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
          <Link href="/reports" className="hover:text-sky-600 dark:hover:text-cyan-400 transition-colors">Dossier Generator</Link>
        </div>

        <div className="flex items-center gap-3">
          {/* Animated Light/Dark Theme Toggle */}
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
      <section className="relative z-10 px-6 pt-16 pb-24 lg:px-16 lg:pt-24 max-w-7xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-xs font-mono font-semibold shadow-sm mb-8 border-sky-200 bg-sky-50/80 text-sky-700 dark:border-cyan-500/30 dark:bg-cyan-500/10 dark:text-cyan-300 dark:shadow-[0_0_15px_rgba(6,182,212,0.15)]"
        >
          <Zap size={13} className="text-sky-600 dark:text-cyan-400 animate-pulse" />
          <span>INSTANT BLOCKCHAIN OSINT & FORENSIC ENGINE</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-slate-900 dark:text-white max-w-5xl mx-auto leading-[1.1]"
        >
          Uncover On-Chain Intelligence with <span className="bg-gradient-to-r from-sky-600 via-blue-600 to-indigo-600 dark:from-sky-400 dark:via-cyan-300 dark:to-blue-500 bg-clip-text text-transparent">Absolute Precision</span>.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-6 text-base sm:text-lg text-slate-600 dark:text-slate-400 max-w-3xl mx-auto leading-relaxed"
        >
          Investigate cryptocurrency wallets, trace fund flows across <strong className="text-slate-900 dark:text-slate-200">Bitcoin, Ethereum, BSC, Polygon & Solana</strong>, correlate OSINT threat telemetry, and generate court-ready dossiers.
        </motion.p>

        {/* Quick Launch Search Input */}
        <motion.form
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          onSubmit={handleQuickSearch}
          className="mt-10 max-w-3xl mx-auto flex flex-col sm:flex-row gap-3 p-2.5 rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-2xl backdrop-blur-xl ring-1 ring-slate-900/5 dark:ring-white/10"
        >
          <div className="relative flex-1 flex items-center">
            <Search size={18} className="absolute left-4 text-slate-400 dark:text-slate-500" />
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Paste target address (e.g. 1A1zP..., bc1q..., 0x..., SOL...)"
              className="w-full rounded-xl bg-transparent py-3 pl-11 pr-4 text-sm font-mono text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 dark:from-cyan-500 dark:to-blue-600 hover:from-sky-400 hover:to-indigo-500 px-6 py-3 text-xs font-bold text-white shadow-md shadow-sky-500/20 dark:shadow-cyan-500/25 transition-all active:scale-[0.98]"
          >
            <Search size={14} className="stroke-[2.5]" />
            <span>Investigate Now</span>
          </button>
        </motion.form>

        {/* Curated Demo Target Presets */}
        <div className="mt-5 max-w-3xl mx-auto flex flex-wrap items-center justify-center gap-2 text-xs">
          <span className="font-mono text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wide mr-1">
            DEMO TARGETS:
          </span>
          {DEMO_TARGET_PRESETS.slice(0, 6).map((preset) => (
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

        {/* Feature Badges */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs font-mono text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1.5"><CheckCircle2 size={14} className="text-sky-600 dark:text-cyan-400" /> Multi-Chain Live Tracing</span>
          <span className="flex items-center gap-1.5"><CheckCircle2 size={14} className="text-sky-600 dark:text-cyan-400" /> 10,000+ Exchange Labels</span>
          <span className="flex items-center gap-1.5"><CheckCircle2 size={14} className="text-sky-600 dark:text-cyan-400" /> Zero-Knowledge Heuristics</span>
          <span className="flex items-center gap-1.5"><CheckCircle2 size={14} className="text-sky-600 dark:text-cyan-400" /> Automated RPC Failover</span>
        </div>
      </section>

      {/* Feature Capabilities Grid */}
      <section className="relative z-10 px-6 py-20 lg:px-16 max-w-7xl mx-auto border-t border-slate-200 dark:border-slate-800/80">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-xs font-mono font-bold tracking-wider text-sky-600 dark:text-cyan-400 uppercase">Core Capabilities</span>
          <h2 className="mt-3 text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">Built for High-Stakes Crypto Investigations</h2>
          <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
            From single wallet inspections to multi-hop cluster graph tracing, ChainIntel equips cybersecurity analysts with direct blockchain telemetry.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard
            icon={<Fingerprint className="text-sky-600 dark:text-cyan-400" size={24} />}
            title="Multi-Chain Wallet Inspection"
            description="Inspect balances, UTXO distributions, ERC-20/SPL token holdings, and normalized transaction histories across Bitcoin, Ethereum, BSC, Polygon, and Solana."
            href="/wallet"
          />
          <FeatureCard
            icon={<GitFork className="text-blue-600 dark:text-blue-400" size={24} />}
            title="Interactive Fund-Flow Graph"
            description="Map flow of funds with D3 force-directed visual canvas. Features value-proportional edge thickness, leaf-node clustering, and multi-hop node tracing."
            href="/graph"
          />
          <FeatureCard
            icon={<ShieldAlert className="text-rose-600 dark:text-rose-400" size={24} />}
            title="Threat Intel & Entity Tagging"
            description="Auto-match addresses against 10,000+ known entities including Binance, Coinbase, Kraken, and OFAC sanctioned mixers like Tornado Cash."
            href="/threat-intelligence"
          />
          <FeatureCard
            icon={<Radar className="text-purple-600 dark:text-purple-400" size={24} />}
            title="Public OSINT Correlation"
            description="Cross-reference wallet addresses with public intelligence sources including Etherscan Labels, Arkham Intelligence, DeBank, and Bitcoin Who's Who."
            href="/osint"
          />
          <FeatureCard
            icon={<Activity className="text-emerald-600 dark:text-emerald-400" size={24} />}
            title="Real-Time Alerts & SSE Engine"
            description="Set automated watchers on high-risk wallets and receive real-time Server-Sent Event (SSE) streaming notifications directly in your workstation."
            href="/alerts"
          />
          <FeatureCard
            icon={<FileText className="text-amber-600 dark:text-amber-400" size={24} />}
            title="Chain-of-Custody Dossiers"
            description="Export court-ready PDF, JSON, and CSV forensic reports with embedded disclaimers and SHA-256 evidence integrity validation."
            href="/reports"
          />
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

function FeatureCard({ icon, title, description, href }: { icon: React.ReactNode; title: string; description: string; href: string }) {
  return (
    <Link
      href={href}
      className="group relative rounded-2xl border p-6 transition-all duration-300 hover:-translate-y-1 flex flex-col justify-between border-slate-200 bg-white shadow-sm hover:border-sky-400 hover:shadow-xl hover:shadow-sky-500/10 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-cyan-500/40 dark:hover:bg-slate-900/90 dark:hover:shadow-cyan-500/10 backdrop-blur-xl"
    >
      <div>
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 border border-slate-200 group-hover:border-sky-300 dark:bg-slate-800/80 dark:border-slate-700 dark:group-hover:border-cyan-500/40 transition-colors">
          {icon}
        </div>
        <h3 className="mt-5 text-lg font-bold text-slate-900 group-hover:text-sky-600 dark:text-white dark:group-hover:text-cyan-300 transition-colors">{title}</h3>
        <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{description}</p>
      </div>
      <div className="mt-6 flex items-center gap-1 text-xs font-mono font-bold text-sky-600 dark:text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity">
        <span>EXPLORE MODULE</span>
        <ArrowRight size={12} />
      </div>
    </Link>
  );
}
