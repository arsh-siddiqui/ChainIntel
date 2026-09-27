"use client";

import { AlertTriangle, ExternalLink, Shield, ShieldAlert, ShieldCheck } from "lucide-react";
import type { RiskAssessment, ThreatFinding } from "@/types";

export function ThreatBanner({ risk, threats }: { risk: RiskAssessment; threats: ThreatFinding[] }) {
  const isHigh = risk.band === "HIGH" || risk.band === "ELEVATED";
  const isModerate = risk.band === "MODERATE";

  return (
    <div
      className={`console-panel rounded-lg p-3.5 border ${
        isHigh
          ? "border-rose-300 bg-rose-50/40 dark:border-rose-900/80 dark:bg-rose-950/20"
          : isModerate
          ? "border-amber-300 bg-amber-50/40 dark:border-amber-900/80 dark:bg-amber-950/20"
          : "border-emerald-300 bg-emerald-50/40 dark:border-emerald-900/80 dark:bg-emerald-950/20"
      }`}
      role="status"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div
            className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded font-mono text-xs font-black ${
              isHigh
                ? "bg-rose-600 text-white"
                : isModerate
                ? "bg-amber-500 text-white"
                : "bg-emerald-600 text-white"
            }`}
          >
            {isHigh ? "!" : isModerate ? "▲" : "✓"}
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink">
                FORENSIC ATTRIBUTION STATUS:
              </span>
              <span
                className={`font-mono text-xs font-black uppercase ${
                  isHigh
                    ? "text-rose-700 dark:text-rose-400"
                    : isModerate
                    ? "text-amber-700 dark:text-amber-400"
                    : "text-emerald-700 dark:text-emerald-400"
                }`}
              >
                {risk.band} RISK
              </span>
            </div>

            <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              {risk.disclaimer || "Multi-source blockchain forensic assessment over indexed mempool and threat records."}
            </p>

            {threats.length > 0 && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5 font-mono text-[10px]">
                <span className="font-bold text-rose-700 dark:text-rose-400 uppercase">
                  MATCHED FEEDS ({threats.length}):
                </span>
                {threats.map((t, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 rounded border border-rose-200 bg-rose-50 px-1.5 py-0.5 font-semibold text-rose-800 dark:border-rose-900 dark:bg-rose-950/80 dark:text-rose-300"
                  >
                    <span>{t.category}</span>
                    <span className="text-slate-400">({t.source})</span>
                    {t.reference_url && (
                      <a
                        href={t.reference_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-rose-950 dark:hover:text-white"
                        title="View Advisory Reference"
                      >
                        <ExternalLink size={9} />
                      </a>
                    )}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0 font-mono text-xs sm:text-right border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-200/60 dark:border-slate-800/60">
          <div>
            <p className="text-[10px] text-slate-400 uppercase">EVIDENCE WEIGHT</p>
            <p className="font-bold text-ink">
              {risk.score} / {risk.max_score} pts
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
