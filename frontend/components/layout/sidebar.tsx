"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  FileSearch,
  FileText,
  FolderLock,
  Fingerprint,
  LayoutDashboard,
  Network,
  Radar,
  Settings,
  Shield,
  type LucideIcon,
} from "lucide-react";
import clsx from "clsx";
import { NAV_ITEMS } from "@/lib/constants";

const ICONS: Record<string, LucideIcon> = {
  "/dashboard": LayoutDashboard,
  "/wallet": Fingerprint,
  "/transactions": ArrowRight,
  "/graph": Network,
  "/threat-intelligence": AlertTriangle,
  "/osint": Radar,
  "/alerts": Activity,
  "/investigations": FolderLock,
  "/evidence": FileSearch,
  "/reports": FileText,
  "/settings": Settings,
};

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col border-r transition-colors duration-200 border-slate-200/90 bg-white/95 text-slate-900 dark:border-slate-800/80 dark:bg-slate-950/90 dark:text-slate-100 backdrop-blur-2xl">
      {/* Brand Header */}
      <div className="flex items-center gap-3 px-6 py-6 border-b border-slate-100 dark:border-slate-800/60">
        <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-500 via-blue-600 to-indigo-600 dark:from-blue-600 dark:via-indigo-600 dark:to-cyan-400 text-white shadow-md shadow-sky-500/20 dark:shadow-cyan-500/25 ring-1 ring-black/5 dark:ring-white/20">
          <Shield size={20} className="stroke-[2.2]" />
          <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-slate-950" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <p className="text-[16px] font-black tracking-tight text-slate-900 dark:text-white">ChainIntel</p>
            <span className="rounded px-1 py-0.2 text-[9px] font-mono font-bold border border-sky-500/30 bg-sky-50 text-sky-700 dark:border-cyan-500/20 dark:bg-cyan-500/10 dark:text-cyan-400">
              PRO
            </span>
          </div>
          <p className="text-[10px] font-mono tracking-wider uppercase text-slate-500 dark:text-slate-400">
            Forensic OSINT Engine
          </p>
        </div>
      </div>

      {/* Main Navigation */}
      <nav aria-label="Main navigation" className="thin-scroll flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-mono font-bold tracking-wider uppercase text-slate-400 dark:text-slate-500">
          Intelligence Suite
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = ICONS[item.href] ?? LayoutDashboard;
          const active =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(`${item.href}/`)) ||
            (item.href === "/dashboard" && pathname === "/");

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={clsx(
                "group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13px] font-semibold transition-all duration-150",
                active
                  ? "bg-sky-50 text-sky-700 border-l-2 border-sky-600 shadow-sm dark:bg-gradient-to-r dark:from-cyan-500/15 dark:via-blue-500/10 dark:to-transparent dark:border-cyan-400 dark:text-cyan-300 dark:shadow-[inset_0_0_15px_rgba(6,182,212,0.12)]"
                  : "text-slate-600 hover:bg-slate-100/80 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900/70 dark:hover:text-slate-200"
              )}
            >
              <Icon
                size={17}
                className={clsx(
                  "transition-colors duration-150",
                  active
                    ? "text-sky-600 dark:text-cyan-400 dark:drop-shadow-[0_0_6px_rgba(6,182,212,0.5)]"
                    : "text-slate-400 group-hover:text-slate-700 dark:text-slate-500 dark:group-hover:text-slate-300"
                )}
              />
              <span className="flex-1 truncate">{item.label}</span>
              {active && (
                <div className="h-1.5 w-1.5 rounded-full bg-sky-600 shadow-sm dark:bg-cyan-400 dark:shadow-[0_0_6px_#06b6d4]" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User Profile */}
      <div className="border-t p-4 border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-950/60">
        <div className="flex items-center gap-3 px-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold bg-slate-100 text-sky-700 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-cyan-400 dark:ring-cyan-500/30 shadow-sm">
            CI
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-bold text-slate-800 dark:text-slate-200">Lead Investigator</p>
            <p className="text-[10px] font-mono text-slate-400 dark:text-slate-500 truncate">Forensic Clearance L3</p>
          </div>
        </div>
      </div>
    </div>
  );
}
