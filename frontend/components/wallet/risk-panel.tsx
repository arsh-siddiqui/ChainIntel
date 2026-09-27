"use client";

import { CheckCircle2, MinusCircle, AlertTriangle, ShieldCheck, ShieldAlert, FileText } from "lucide-react";
import type { RiskAssessment } from "@/types";

export function RiskPanel({ risk }: { risk: RiskAssessment }) {
  const isHigh = risk.band === "HIGH" || risk.band === "ELEVATED";
  const isModerate = risk.band === "MODERATE";

  return (
    <div className="console-panel rounded-lg overflow-hidden">
      {/* 1. Header with Concrete Risk Status */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900/90">
        <div className="flex items-center gap-2.5">
          <div
            className={`flex h-6 w-6 items-center justify-center rounded font-mono text-xs font-black ${
              isHigh
                ? "bg-rose-100 text-rose-700 dark:bg-rose-950/80 dark:text-rose-400"
                : isModerate
                ? "bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-400"
                : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/80 dark:text-emerald-400"
            }`}
          >
            !
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink">
                FORENSIC RISK ASSESSMENT
              </span>
              <span
                className={`rounded px-2 py-0.5 font-mono text-[10px] font-black uppercase tracking-wider border ${
                  isHigh
                    ? "border-rose-300 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950/60 dark:text-rose-400"
                    : isModerate
                    ? "border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/60 dark:text-amber-400"
                    : "border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-400"
                }`}
              >
                STATUS: {risk.band}
              </span>
            </div>
            <p className="font-mono text-[10px] text-slate-400 mt-0.5">
              Cumulative Evidence Weight: {risk.score} / {risk.max_score} points
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-[11px] text-slate-400">
          <span>{risk.indicators.filter((i) => i.status === "TRIGGERED").length} TRIGGERED</span>
          <span>·</span>
          <span>{risk.indicators.filter((i) => i.status !== "TRIGGERED").length} CLEARED</span>
        </div>
      </div>

      {/* 2. Concrete Evidence Indicators Checklist */}
      <div className="divide-y divide-slate-100 dark:divide-slate-800/80 bg-white dark:bg-slate-900/40">
        {risk.indicators.map((indicator) => {
          const triggered = indicator.status === "TRIGGERED";

          return (
            <div
              key={indicator.name}
              className={`p-3.5 transition-colors ${
                triggered ? "bg-rose-50/25 dark:bg-rose-950/15" : "hover:bg-slate-50/60 dark:hover:bg-slate-800/30"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <div className="mt-0.5 shrink-0">
                    {triggered ? (
                      <span className="flex h-4 w-4 items-center justify-center rounded bg-rose-600 font-mono text-[10px] font-bold text-white">
                        ✓
                      </span>
                    ) : (
                      <span className="flex h-4 w-4 items-center justify-center rounded bg-slate-200 font-mono text-[10px] text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                        —
                      </span>
                    )}
                  </div>

                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`text-xs font-bold tracking-tight ${
                          triggered ? "text-ink" : "text-slate-500 dark:text-slate-400"
                        }`}
                      >
                        {indicator.name}
                      </span>
                      <span className="rounded bg-slate-100 px-1.5 py-0.2 font-mono text-[9px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                        FEED: {indicator.source}
                      </span>
                      {triggered && (
                        <span className="rounded border border-rose-200 bg-rose-50 px-1.5 py-0.2 font-mono text-[9px] font-bold text-rose-700 dark:border-rose-900 dark:bg-rose-950/60 dark:text-rose-400">
                          +{indicator.weight} PTS
                        </span>
                      )}
                    </div>

                    <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                      {indicator.description}
                    </p>

                    {triggered && indicator.evidence && (
                      <div className="mt-1.5 flex items-start gap-1.5 rounded border border-slate-200 bg-slate-50 p-2 font-mono text-[10px] text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
                        <span className="font-bold text-slate-400 shrink-0 uppercase">EVIDENCE:</span>
                        <span className="break-all">{indicator.evidence}</span>
                      </div>
                    )}
                  </div>
                </div>

                <span
                  className={`font-mono text-[10px] font-bold shrink-0 uppercase ${
                    triggered ? "text-rose-600 dark:text-rose-400" : "text-slate-400"
                  }`}
                >
                  {triggered ? "TRIGGERED" : "CLEAR"}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 3. Evidentiary Disclaimer */}
      <div className="border-t border-slate-200 bg-slate-50 px-4 py-2 text-[10px] font-mono text-slate-400 dark:border-slate-800 dark:bg-slate-950">
        Forensic weights derived from verified on-chain heuristics and OFAC/CISA/FBI threat feeds.
      </div>
    </div>
  );
}
