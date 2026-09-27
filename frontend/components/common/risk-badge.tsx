"use client";

import { Badge } from "@/components/common/ui";
import { RISK_BAND_STYLES } from "@/lib/constants";

export function RiskBadge({ band, className }: { band: string | null | undefined; className?: string }) {
  const normalized = (band ?? "CLEAR").toUpperCase();
  return (
    <Badge
      className={className ?? (RISK_BAND_STYLES[normalized] ?? RISK_BAND_STYLES.CLEAR)}
      title="Risk band - analytical indicator, not a determination of unlawful activity"
    >
      {normalized}
    </Badge>
  );
}

/** Threat banner levels used on the wallet page with dual light/dark aesthetics. */
export function threatBanner(band: string): { label: string; className: string; description: string; glow: string; textClass: string } {
  switch (band) {
    case "HIGH":
      return {
        label: "CRITICAL THREAT IDENTIFIED",
        className:
          "border-rose-300 bg-gradient-to-r from-rose-50 via-red-50 to-white text-rose-950 shadow-md dark:border-rose-500/50 dark:bg-gradient-to-r dark:from-rose-950/80 dark:via-red-950/40 dark:to-slate-950/80 dark:text-rose-100 dark:shadow-2xl dark:shadow-rose-950/50",
        glow: "bg-rose-500",
        textClass: "text-rose-900 dark:text-rose-100",
        description: "Direct malicious activity identified in configured threat-intelligence feeds. Verify all evidence before enforcement.",
      };
    case "ELEVATED":
      return {
        label: "ELEVATED RISK LEVEL",
        className:
          "border-orange-300 bg-gradient-to-r from-orange-50 via-amber-50 to-white text-orange-950 shadow-md dark:border-orange-500/50 dark:bg-gradient-to-r dark:from-orange-950/80 dark:via-amber-950/40 dark:to-slate-950/80 dark:text-orange-100 dark:shadow-2xl dark:shadow-orange-950/40",
        glow: "bg-orange-500",
        textClass: "text-orange-900 dark:text-orange-100",
        description: "Suspicious heuristics or high-velocity counterparty mixing patterns detected. Deep inspection required.",
      };
    case "MODERATE":
      return {
        label: "MODERATE ADVISORY",
        className:
          "border-amber-300 bg-gradient-to-r from-amber-50 via-yellow-50/50 to-white text-amber-950 shadow-sm dark:border-amber-500/50 dark:bg-gradient-to-r dark:from-amber-950/70 dark:via-slate-900/60 dark:to-slate-950/80 dark:text-amber-100 dark:shadow-2xl dark:shadow-amber-950/30",
        glow: "bg-amber-500",
        textClass: "text-amber-900 dark:text-amber-100",
        description: "Indirect proximity to monitored clusters observed. No direct blacklist hits on target address.",
      };
    case "LOW":
      return {
        label: "LOW ADVISORY",
        className:
          "border-sky-200 bg-gradient-to-r from-sky-50 to-white text-sky-950 shadow-sm dark:border-sky-500/40 dark:bg-gradient-to-r dark:from-sky-950/70 dark:to-slate-950/80 dark:text-sky-100 dark:shadow-2xl dark:shadow-sky-950/30",
        glow: "bg-sky-400",
        textClass: "text-sky-900 dark:text-sky-100",
        description: "Standard peer-to-peer or exchange wallet activity with baseline forensic score.",
      };
    default:
      return {
        label: "VERIFIED CLEAR",
        className:
          "border-emerald-200 bg-gradient-to-r from-emerald-50 to-white text-emerald-950 shadow-sm dark:border-emerald-500/40 dark:bg-gradient-to-r dark:from-emerald-950/70 dark:to-slate-950/80 dark:text-emerald-100 dark:shadow-2xl dark:shadow-emerald-950/30",
        glow: "bg-emerald-400",
        textClass: "text-emerald-900 dark:text-emerald-100",
        description: "No threat-intelligence matches, sanctions flags, or forensic anomalies detected.",
      };
  }
}
