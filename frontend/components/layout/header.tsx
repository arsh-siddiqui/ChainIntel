"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Bell, Command, Menu, Moon, Search, ShieldCheck, Sun } from "lucide-react";
import { api } from "@/lib/api";
import { truncateMiddle } from "@/lib/formatters";
import { useTheme } from "@/hooks/use-theme";
import type { Alert, CaseRecord, NormalizedTx, ThreatFinding, WalletSummary } from "@/types";

interface SearchResults {
  wallets: WalletSummary[];
  transactions: NormalizedTx[];
  cases: CaseRecord[];
  threats: ThreatFinding[];
}

const TITLES: Record<string, string> = {
  "/dashboard": "Security Command Center",
  "/wallet": "Wallet Investigation",
  "/transactions": "Transaction Explorer",
  "/graph": "Link Analysis & Attribution Graph",
  "/threat-intelligence": "Threat Intelligence Feeds",
  "/osint": "Public OSINT Correlation",
  "/alerts": "Real-time Alerts & Monitoring",
  "/investigations": "Forensic Investigation Cases",
  "/evidence": "Chain of Custody Evidence",
  "/reports": "Forensic Report Generator",
  "/settings": "Node & Provider Settings",
};

export function Header({ onOpenMenu }: { onOpenMenu: () => void }) {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(query.trim()), 250);
    return () => clearTimeout(timer);
  }, [query]);

  // Global Ctrl+K / Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        setShowResults(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setShowResults(false);
        setShowNotifications(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const { data: results, isFetching } = useQuery({
    queryKey: ["search", debounced],
    queryFn: async () => (await api.get<SearchResults>(`/search?q=${encodeURIComponent(debounced)}`)).data,
    enabled: debounced.length >= 2,
  });

  const { data: alertsData } = useQuery({
    queryKey: ["header-alerts"],
    queryFn: async () => (await api.get<Alert[]>("/alerts?page=1&page_size=5")).data,
    refetchInterval: 60_000,
  });
  const newAlerts = (alertsData ?? []).filter((a) => a.status === "NEW");

  const hasResults =
    results && (results.wallets.length + results.transactions.length + results.cases.length + results.threats.length > 0);

  return (
    <header
      className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b px-4 lg:px-8 transition-colors duration-200 border-slate-200/80 bg-white/80 dark:border-slate-800/80 dark:bg-slate-950/75 backdrop-blur-2xl"
      ref={containerRef}
    >
      <button
        type="button"
        className="rounded-xl p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-100 lg:hidden"
        onClick={onOpenMenu}
        aria-label="Open navigation menu"
      >
        <Menu size={18} />
      </button>

      {/* Page Title & Breadcrumb */}
      <div className="hidden md:flex items-center gap-2.5">
        <div className="h-2 w-2 rounded-full bg-sky-500 dark:bg-cyan-400 shadow-[0_0_8px_#0284c7] dark:shadow-[0_0_8px_#06b6d4]" />
        <h1 className="text-sm font-bold tracking-tight text-slate-900 dark:text-slate-100">
          {TITLES[pathname] ?? "ChainIntel Platform"}
        </h1>
      </div>

      {/* Futuristic Global Search Bar */}
      <div className="relative mx-auto w-full max-w-lg">
        <Search size={15} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setShowResults(true);
          }}
          onFocus={() => setShowResults(true)}
          placeholder="Search target wallets, hashes, threats, entities…"
          aria-label="Global search"
          className="w-full rounded-xl border py-2 pl-9 pr-16 text-xs transition-all shadow-inner focus:outline-none focus:ring-2 border-slate-200 bg-slate-100/80 text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:bg-white focus:ring-sky-500/20 dark:border-slate-800 dark:bg-slate-900/80 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-cyan-400 dark:focus:ring-cyan-500/20"
        />
        <div className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-mono border border-slate-200 bg-white text-slate-500 shadow-sm dark:border-slate-700/60 dark:bg-slate-800/80 dark:text-slate-400">
          <Command size={10} />
          <span>K</span>
        </div>

        {/* Live Search Results Dropdown */}
        {showResults && debounced.length >= 2 ? (
          <div className="absolute left-0 right-0 top-full z-40 mt-2 max-h-96 overflow-y-auto rounded-2xl border p-2 shadow-2xl backdrop-blur-2xl border-slate-200 bg-white/95 text-slate-900 dark:border-slate-800 dark:bg-slate-900/95 dark:text-slate-100">
            {isFetching && !hasResults ? <p className="px-3 py-3 text-xs text-slate-400 font-mono">Querying indexed data…</p> : null}
            {!isFetching && !hasResults ? <p className="px-3 py-3 text-xs text-slate-400">No records found for “{debounced}”.</p> : null}
            {results?.wallets.length ? (
              <SearchGroup title="Wallets & Entities">
                {results.wallets.map((w) => (
                  <SearchItem key={w.address} href={`/wallet?address=${encodeURIComponent(w.address)}`} title={truncateMiddle(w.address, 18, 10)} meta={w.label ?? w.blockchain} onNavigate={() => setShowResults(false)} />
                ))}
              </SearchGroup>
            ) : null}
            {results?.transactions.length ? (
              <SearchGroup title="Transactions">
                {results.transactions.map((t) => (
                  <SearchItem key={t.tx_hash} href={`/transactions?search=${encodeURIComponent(t.tx_hash)}`} title={truncateMiddle(t.tx_hash, 16, 8)} meta={`${t.amount} ${t.asset}`} onNavigate={() => setShowResults(false)} />
                ))}
              </SearchGroup>
            ) : null}
            {results?.cases.length ? (
              <SearchGroup title="Active Cases">
                {results.cases.map((c) => (
                  <SearchItem key={c.id} href={`/investigations/${c.id}`} title={`${c.case_number} — ${c.title}`} meta={c.status} onNavigate={() => setShowResults(false)} />
                ))}
              </SearchGroup>
            ) : null}
            {results?.threats.length ? (
              <SearchGroup title="Threat Matches">
                {results.threats.map((t, index) => (
                  <SearchItem key={`${t.wallet_address}-${index}`} href={`/threat-intelligence?search=${encodeURIComponent(t.wallet_address)}`} title={truncateMiddle(t.wallet_address, 16, 8)} meta={`${t.category} · ${t.source}`} onNavigate={() => setShowResults(false)} />
                ))}
              </SearchGroup>
            ) : null}
          </div>
        ) : null}
      </div>

      {/* Header Actions */}
      <div className="ml-auto flex items-center gap-3">
        {/* Animated Light/Dark Theme Toggle */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.92 }}
          type="button"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm hover:bg-slate-50 hover:text-slate-900 dark:border-slate-800 dark:bg-slate-900/70 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-white transition-all backdrop-blur-md"
        >
          {theme === "dark" ? (
            <Sun size={17} className="text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.6)]" />
          ) : (
            <Moon size={17} className="text-sky-600 drop-shadow-[0_0_8px_rgba(2,132,199,0.3)]" />
          )}
        </motion.button>

        {/* Notifications */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowNotifications((v) => !v)}
            className="relative rounded-xl border p-2 transition-all border-slate-200 bg-white text-slate-600 shadow-sm hover:bg-slate-50 hover:text-slate-900 dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-white"
            aria-label={`Notifications${newAlerts.length ? `, ${newAlerts.length} new alerts` : ""}`}
          >
            <Bell size={17} />
            {newAlerts.length > 0 ? (
              <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[9px] font-bold text-white shadow-lg shadow-rose-500/50">
                {newAlerts.length}
              </span>
            ) : null}
          </button>
          {showNotifications ? (
            <div className="absolute right-0 top-full z-40 mt-2 w-80 rounded-2xl border p-3 shadow-2xl backdrop-blur-2xl border-slate-200 bg-white/95 text-slate-900 dark:border-slate-800 dark:bg-slate-900/95 dark:text-slate-100">
              <div className="flex items-center justify-between border-b pb-2 px-1 border-slate-100 dark:border-slate-800">
                <p className="text-xs font-bold text-slate-900 dark:text-slate-200">Security Alerts</p>
                <span className="rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-rose-600 dark:text-rose-400 border border-rose-500/20">
                  {newAlerts.length} New
                </span>
              </div>
              <div className="mt-2 space-y-1">
                {(alertsData ?? []).length === 0 ? <p className="px-2 py-4 text-xs text-slate-400 dark:text-slate-500 text-center">No alerts triggered.</p> : null}
                {(alertsData ?? []).map((alert) => (
                  <Link key={alert.id} href="/alerts" onClick={() => setShowNotifications(false)} className="block rounded-xl p-2 hover:bg-slate-100/80 dark:hover:bg-slate-800/60 transition-colors">
                    <p className="truncate text-xs font-semibold text-slate-900 dark:text-slate-200">{alert.title}</p>
                    <p className="truncate text-[11px] font-mono text-slate-500 dark:text-slate-400">
                      {truncateMiddle(alert.wallet_address, 12, 6)} · <span className="text-rose-600 dark:text-rose-400 font-medium">{alert.severity}</span>
                    </p>
                  </Link>
                ))}
              </div>
              <Link href="/alerts" onClick={() => setShowNotifications(false)} className="mt-2 block border-t pt-2 text-center text-xs font-semibold text-sky-600 hover:text-sky-700 dark:text-cyan-400 dark:hover:text-cyan-300 border-slate-100 dark:border-slate-800">
                View all alerts →
              </Link>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}

function SearchGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-2">
      <p className="px-2 py-1 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">{title}</p>
      {children}
    </div>
  );
}

function SearchItem({ href, title, meta, onNavigate }: { href: string; title: string; meta: string; onNavigate: () => void }) {
  return (
    <Link href={href} onClick={onNavigate} className="flex items-center justify-between rounded-xl px-3 py-2 hover:bg-slate-100/80 dark:hover:bg-slate-800/70 transition-colors">
      <span className="truncate font-mono text-xs text-slate-800 dark:text-slate-200 font-medium">{title}</span>
      <span className="ml-2 shrink-0 truncate rounded px-1.5 py-0.5 text-[10px] font-mono bg-slate-100 text-slate-600 dark:bg-slate-800/80 dark:text-slate-400">{meta}</span>
    </Link>
  );
}
